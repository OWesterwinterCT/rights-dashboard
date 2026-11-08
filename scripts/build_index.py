"""Rebuild the safe, non-pickle search index; no network access."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from search import passages,fit_index,save_index,load_index,search
if __name__=='__main__':
    start=time.time();chunks=passages();index=fit_index(chunks);save_index(chunks,index)
    loaded=load_index(chunks)
    results=search(chunks,'access to justice for women',{p['doc_id'] for p in chunks},'Semantic',loaded)
    print(f'{len(chunks)} passages; {time.time()-start:.1f}s; {len(results)} example results')
    for r in results[:5]:print(r['title'],round(r['relevance'],3))
