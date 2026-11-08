"""Build audited English corpus from extracted JSON files. See README for schema."""
import argparse,hashlib,json,re,sys,shutil
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from langdetect import detect_langs,DetectorFactory
from core import ROOT,catalogue
DetectorFactory.seed=42

def classify(text):
    words=re.findall(r'[A-Za-zÀ-ž]{3,}',text)
    if len(words)<150:return 'unreadable',0.0,{}
    # Dispersed windows: cover body text, not just the cover page.
    votes=[]
    for fraction in [0.05,0.2,0.4,0.6,0.8]:
        start=int(max(0,len(words)-600)*fraction)
        try:
            langs=detect_langs(' '.join(words[start:start+600]));votes.append((langs[0].lang,langs[0].prob))
        except Exception:continue
    english=sum(lang=='en' and prob>=.8 for lang,prob in votes)
    counts=Counter(lang for lang,_ in votes)
    if english>=4:return 'english',english/5,dict(counts)
    if counts and counts.most_common(1)[0][1]>=4 and counts.most_common(1)[0][0] in {'fr','es','pt','ru','ar','zh-cn','zh-tw'}:
        return 'non_english',english/5,dict(counts)
    return 'review',english/5,dict(counts)

def main(source):
    out=ROOT/'data/pilot_text';out.mkdir(exist_ok=True)
    for p in out.glob('*.json'):p.unlink()
    catalogue_rows=json.loads((ROOT/'data/catalogue_raw.json').read_text(encoding='utf-8'))
    audit=[];seen={}
    override_path=ROOT/'data/language_overrides.json'
    overrides=json.loads(override_path.read_text(encoding='utf-8')) if override_path.exists() else {}
    for r in catalogue_rows:
        path=source/(r['doc_id']+'.json')
        record=dict(r)
        if not path.exists():
            record.update(status='missing_extraction',words=0);audit.append(record);continue
        obj=json.loads(path.read_text(encoding='utf-8'));text=obj.get('text','');status,share,votes=classify(text)
        normalized=' '.join(re.findall(r'\w+',text.casefold()))
        digest=hashlib.sha256(normalized.encode()).hexdigest()
        override=overrides.get(r['doc_id'],{})
        if override: status=override['status']
        tokens=text.split()
        fragment_share=sum(len(w)<=2 for w in tokens)/max(1,len(tokens))
        record.update(extraction=obj.get('extraction',''),bilingual=override.get('bilingual',False),language_override=override.get('reason',''),fragment_share=round(fragment_share,3),status=status,words=len(text.split()),english_windows=share,language_votes=json.dumps(votes),text_sha256=digest,duplicate_of=override.get('duplicate_of',''),error=obj.get('error') or '')
        if obj.get('error'):record['status']='extraction_error'
        elif status=='english':
            if digest in seen:record.update(status='duplicate',duplicate_of=seen[digest])
            else:
                seen[digest]=r['doc_id']
                obj['bilingual']=override.get('bilingual',False)
                (out/path.name).write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
        audit.append(record)
    pd.DataFrame(audit).to_csv(ROOT/'data/corpus_audit.csv',index=False)
    catalogue().to_csv(ROOT/'data/catalogue.csv',index=False)
    print(pd.DataFrame(audit).status.value_counts().to_string())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);main(p.parse_args().source)
