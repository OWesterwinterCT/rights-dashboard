"""Offline data preparation and transparent, equal-country aggregation."""
import json
import re
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
RIGHTS = ['CIVIL AND POLITICAL RIGHTS', 'ECONOMIC, SOCIAL, AND CULTURAL', "WOMEN'S RIGHTS", "CHILDREN'S RIGHTS", "MIGRANTS' RIGHTS", 'INDIGENOUS RIGHTS']
RATINGS = ['CL Rating', 'PR Rating']
ALIASES = {'afghanistan':'Afghanistan', 'hondudras':'Honduras','guinea bissau':'Guinea-Bissau','sierra':'Sierra Leone','cote':"Cote d'Ivoire",'montenegro and serbia':'Serbia and Montenegro'}
WB_ALIASES = {'CAR':'CAF','Congo':'COG','DRC':'COD','DPR Korea':'PRK',"Cote d'Ivoire":'CIV','Egypt':'EGY','Gambia':'GMB','Iran':'IRN','Kyrgyzstan':'KGZ','Macedonia':'MKD','Palestine':'PSE','Swaziland':'SWZ','Syria':'SYR','Timor Leste':'TLS','Turkey':'TUR','Venezuela':'VEN','Yemen':'YEM','Kosovo':'XKX','Vietnam':'VNM','Lao PDR':'LAO','Somalia':'SOM'}

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(c)).replace('’',"'").strip()

def canonical(s):
    s=str(s).strip()
    return 'Region Pacific' if s=='Pacific Region' else ALIASES.get(norm(s),s)

def geography():
    wb=json.loads((ROOT/'data/world_bank_countries.json').read_text(encoding='utf-8'))[1]
    countries=[x for x in wb if x['region']['id']!='NA']
    bycode={x['id']:x for x in countries}
    byname={norm(x['name']):x['id'] for x in countries}
    def lookup(name,code=None):
        name=canonical(name)
        if name.startswith('Region '): return '', 'Regional framework', 'Regional'
        if name=='Serbia and Montenegro': return 'SCG','Historical entity','Historical'
        code = code if code in bycode else WB_ALIASES.get(name,byname.get(norm(name)))
        if code in bycode: return code,bycode[code]['region']['value'].strip(),'Country / economy'
        return '', 'Unmapped', 'Unmapped'
    return lookup

def load_scores(source=None):
    d=pd.read_csv(source if source is not None else ROOT/'data/df_rights.csv')
    d=d.rename(columns={c:c.strip() for c in d.columns})
    d=d.rename(columns={'Year':'year','Country':'country'})
    missing=set(['year','country']+RIGHTS+RATINGS)-set(d.columns)
    if missing: raise ValueError('Missing required columns: '+', '.join(sorted(missing)))
    if d.country.isna().any(): raise ValueError('Country names cannot be missing.')
    d['country']=d.country.map(canonical)
    for c in ['year']+RIGHTS+RATINGS:
        converted=pd.to_numeric(d[c],errors='coerce')
        if (d[c].notna() & converted.isna()).any(): raise ValueError('Non-numeric entries in '+c)
        if np.isinf(converted).any(): raise ValueError('Infinite values in '+c)
        d[c]=converted
    if d.year.isna().any() or (d.year%1!=0).any(): raise ValueError('Years must be non-missing integers.')
    d['year']=d.year.astype(int)
    if d.duplicated(['country','year']).any(): raise ValueError('Duplicate country-year rows; resolve before loading.')
    lookup=geography()
    geo=[lookup(row.country,getattr(row,'wb_code',None)) for row in d.itertuples()]
    d[['resolved_code','region','scope']]=pd.DataFrame(geo,index=d.index)
    return d.sort_values(['country','year'])

def aggregate(d, metric, years, balanced=False):
    """A fixed cohort must have nonmissing values in every selected calendar year."""
    d=d[(d.scope=='Country / economy') & d.year.between(*years)].copy()
    if balanced:
        n=d.groupby('country')[metric].count()
        d=d[d.country.isin(n[n==years[1]-years[0]+1].index)]
    out=d.groupby('year')[metric].agg(mean='mean',countries='count').reindex(range(years[0],years[1]+1))
    out['countries']=out.countries.fillna(0).astype(int)
    return out.reset_index(names='year')

def catalogue():
    lookup=geography(); rows=[]
    indexed={p.stem for p in (ROOT/'data/pilot_text').glob('*.json')}
    audit_path=ROOT/'data/corpus_audit.csv'
    audit=pd.read_csv(audit_path).fillna('').set_index('doc_id').to_dict('index') if audit_path.exists() else {}
    for r in json.loads((ROOT/'data/catalogue_raw.json').read_text(encoding='utf-8')):
        r=r.copy(); title=r['title']; name=re.split(r'_(?:UNDAF|UINDAF)|[_ ](?=(?:19|20)\d{2})',title)[0].replace('xxx_','').strip()
        r['country']=canonical(name)
        r['code'],r['region'],r['scope']=lookup(r['country'])
        match=re.search(r'(?<!\d)((?:19|20)\d{2})\s*[-–_]\s*((?:19|20)\d{2})(?!\d)',title)
        r['start_year'],r['end_year']=(map(int,match.groups()) if match else (None,None))
        r['period_review']=not bool(match) or r['start_year']>r['end_year']
        r['indexed']=r['doc_id'] in indexed
        decision=audit.get(r['doc_id'],{})
        r['language_status']=decision.get('status','not yet audited')
        r['duplicate_of']=decision.get('duplicate_of','')
        representative=r['doc_id']
        visited=set()
        while representative not in indexed and representative not in visited:
            visited.add(representative)
            representative=audit.get(representative,{}).get('duplicate_of','')
            if not representative:break
        r['search_doc_id']=representative if representative in indexed else ''
        r['searchable']=bool(r['search_doc_id'])
        rows.append(r)
    return pd.DataFrame(rows)
