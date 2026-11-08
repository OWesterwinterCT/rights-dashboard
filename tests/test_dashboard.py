import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest
from core import load_scores,aggregate,catalogue,ROOT,RIGHTS,RATINGS
from search import search,fit_index

def test_data_unique_and_numeric():
    d=load_scores()
    assert not d.duplicated(['year','country']).any()
    assert not d[RIGHTS+RATINGS].select_dtypes('number').empty
    assert not (d.scope=='Unmapped').any()

def test_region_equal_weights_and_fixed_cohort():
    d=pd.DataFrame({'year':[2000,2001,2000,2000],'country':['A','A','B','Regional'],'scope':['Country / economy']*3+['Regional'],'x':[2.,4.,10.,1000.]})
    available=aggregate(d,'x',(2000,2001));fixed=aggregate(d,'x',(2000,2001),True)
    assert available['mean'].tolist()==[6.,4.]
    assert available.countries.tolist()==[2,1]
    assert fixed['mean'].tolist()==[2.,4.]
    assert fixed.countries.tolist()==[1,1]

def test_duplicate_input_rejected(tmp_path):
    d=pd.read_csv(ROOT/'data/df_rights.csv').head(1);p=tmp_path/'bad.csv';pd.concat([d,d]).to_csv(p,index=False)
    with pytest.raises(ValueError,match='Duplicate'):load_scores(p)

def test_search_filters_and_limits():
    chunks=[dict(doc_id=str(i//3),passage_id=str(i),text='women justice courts protection equality '+('health hospital' if i%2 else 'legal access'),title=str(i),url='https://example.org') for i in range(12)]
    index=fit_index(chunks)
    for mode in ['Keyword','Semantic','Exact phrase']:
        results=search(chunks,'justice',{'1'},mode,index)
        assert len(results)==2
        assert {r['doc_id'] for r in results}=={'1'}
    assert search(chunks,'unfindableword',{'1'},'Keyword',index)==[]

def test_catalogue_scope_and_bad_dates():
    d=catalogue();assert len(d)==599
    assert d.loc[d.title.str.contains('_025-2030'),'period_review'].all()
    assert d.loc[d.title.str.contains('Pacific'),'scope'].eq('Regional').all()

def test_streamlit_pages():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
    assert not app.exception
    for page in ['Country trends','Regional comparison','Document library','Topic search','Data & methods']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page

def test_full_corpus_audited_and_english_unique():
    audit=pd.read_csv(ROOT/'data/corpus_audit.csv')
    assert len(audit)==599 and audit.doc_id.nunique()==599
    selected=audit[audit.status=='english']
    assert selected.text_sha256.is_unique
    assert set(selected.doc_id)=={p.stem for p in (ROOT/'data/pilot_text').glob('*.json')}
    assert not (audit.status=='missing_extraction').any()

def test_source_csv_unchanged():
    import hashlib,json
    provenance=json.loads((ROOT/'data/provenance.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'data/df_rights.csv').read_bytes()).hexdigest()==provenance['sha256']

def test_saved_index_roundtrip(tmp_path):
    import numpy as np
    from search import save_index,load_index
    chunks=[dict(doc_id=str(i),passage_id=str(i),text='justice courts women equality '+('health hospital' if i%2 else 'legal protection'),title=str(i),url='https://example.org') for i in range(8)]
    index=fit_index(chunks);save_index(chunks,index,tmp_path);loaded=load_index(chunks,tmp_path)
    before=search(chunks,'justice women',{'1','2'},'Semantic',index)
    after=search(chunks,'justice women',{'1','2'},'Semantic',loaded)
    assert [r['passage_id'] for r in before]==[r['passage_id'] for r in after]
    assert np.allclose([r['relevance'] for r in before],[r['relevance'] for r in after])

def test_duplicate_country_tags_preserved():
    d=catalogue();duplicates=d[d.language_status=='duplicate']
    assert len(duplicates)>0
    assert duplicates.searchable.all()
    assert set(duplicates.search_doc_id).issubset(set(d.loc[d.indexed,'doc_id']))
