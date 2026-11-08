"""Offline corpus-trained latent semantic search. No network calls or API keys."""
import hashlib
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from core import ROOT

def passages():
    out=[]
    for p in sorted((ROOT/'data/pilot_text').glob('*.json')):
        doc=json.loads(p.read_text(encoding='utf-8'));words=re.findall(r'\S+',doc['text'])
        for number,start in enumerate(range(0,len(words),160),1):
            text=' '.join(words[start:start+200])
            if len(text)<100: continue
            if doc.get('bilingual'):
                from langdetect import detect_langs,DetectorFactory
                DetectorFactory.seed=42
                try:
                    languages=detect_langs(text)
                    if languages[0].lang!='en' or languages[0].prob<.8:continue
                except Exception:continue
            out.append({'passage_id':f'{p.stem}:P{number:04d}','doc_id':p.stem,'title':doc['title'],'url':doc['url'],'text':text,'word_start':start})
    return out

def fingerprint(chunks):
    return hashlib.sha256(json.dumps(chunks,sort_keys=True).encode()).hexdigest()

def fit_index(chunks):
    tf=TfidfVectorizer(strip_accents='unicode',stop_words='english',ngram_range=(1,2),max_features=25000,min_df=2,sublinear_tf=True,dtype=np.float32)
    matrix=tf.fit_transform([p['text'] for p in chunks])
    dimensions=min(96,matrix.shape[0]-1,matrix.shape[1]-1)
    svd=TruncatedSVD(n_components=dimensions,random_state=42,n_iter=5)
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        vectors=normalize(svd.fit_transform(matrix)).astype(np.float32)
    return tf,matrix,svd,vectors

def search(chunks,query,allowed,mode='Keyword',index=None):
    indices=[i for i,p in enumerate(chunks) if p['doc_id'] in allowed]
    if not query.strip() or not indices:return []
    if mode=='Exact phrase':
        scores=np.array([chunks[i]['text'].casefold().count(query.casefold()) for i in indices],dtype=float)
    else:
        tf,matrix,svd,vectors=index
        q=tf.transform([query])
        if q.nnz==0:return []
        if mode=='Semantic': scores=(vectors[indices] @ normalize(svd.transform(q))[0]).ravel()
        else: scores=(matrix[indices] @ q.T).toarray().ravel()
    results=[];seen={}
    for pos in np.argsort(-scores):
        if scores[pos]<=0:continue
        p=chunks[indices[pos]]
        if seen.get(p['doc_id'],0)>=2:continue
        seen[p['doc_id']]=seen.get(p['doc_id'],0)+1
        results.append(dict(p,relevance=float(scores[pos])))
        if len(results)>=20:break
    return results

class Projection:
    def __init__(self,components):self.components_=components
    def transform(self,matrix):return matrix @ self.components_.T

def save_index(chunks,index,path=None):
    from scipy.sparse import save_npz
    path=path or ROOT/'data/search_index';path.mkdir(parents=True,exist_ok=True)
    tf,matrix,svd,vectors=index
    meta={'schema':1,'fingerprint':fingerprint(chunks),'vocabulary':{k:int(v) for k,v in tf.vocabulary_.items()},'passages':len(chunks)}
    (path/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
    np.savez_compressed(path/'model.npz',idf=tf.idf_,components=svd.components_,vectors=vectors)
    save_npz(path/'keyword_matrix.npz',matrix)

def load_index(chunks,path=None):
    from scipy.sparse import load_npz
    path=path or ROOT/'data/search_index'
    meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
    if meta.get('schema')!=1 or meta['fingerprint']!=fingerprint(chunks):raise ValueError('Index does not match corpus.')
    arrays=np.load(path/'model.npz',allow_pickle=False)
    tf=TfidfVectorizer(strip_accents='unicode',stop_words='english',ngram_range=(1,2),vocabulary=meta['vocabulary'],sublinear_tf=True,dtype=np.float32)
    tf.idf_=arrays['idf']
    matrix=load_npz(path/'keyword_matrix.npz')
    return tf,matrix,Projection(arrays['components']),arrays['vectors']

def get_index(chunks):
    try:return load_index(chunks)
    except (OSError,ValueError,KeyError):return fit_index(chunks)
