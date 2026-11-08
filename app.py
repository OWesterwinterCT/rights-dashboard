from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from core import ROOT, RIGHTS, RATINGS, load_scores, catalogue, aggregate
from search import passages, get_index, search

st.set_page_config(page_title='Rights & Development Observatory', page_icon='◈', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f9fb} .block-container {padding-top:2rem;max-width:1450px}
h1,h2,h3 {color:#122b3b} [data-testid="stMetric"] {background:white;padding:18px;border:1px solid #dce5e9;border-radius:12px}
[data-testid="stSidebar"] {background:#eaf1f4} .stCaption {color:#536779}
</style>''',unsafe_allow_html=True)

@st.cache_data
def bundled(): return load_scores(),catalogue()
@st.cache_resource
def corpus(): return passages()
@st.cache_resource
def search_index(): return get_index(corpus())

try: scores,docs=bundled()
except Exception as e: st.error(f'Data could not be loaded: {e}');st.stop()
st.sidebar.title('◈ Rights Observatory')
st.sidebar.caption('Development frameworks · evidence · trends')
page=st.sidebar.radio('Explore',['Overview','Country trends','Regional comparison','Document library','Topic search','Data & methods'])
with st.sidebar.expander('Use another cleaned dataset'):
    uploaded=st.file_uploader('CSV with year, country, six rights and CL/PR ratings',type='csv')
    if uploaded:
        try: scores=load_scores(uploaded);st.success('Using uploaded data for this session.')
        except Exception as e: st.error(str(e));st.stop()
st.sidebar.caption('Research pilot • document coverage is not a measure of rights implementation.')
st.title('Rights & Development Observatory')
st.caption('Explore country trajectories and the evidence inside UN development frameworks.')

def download(d,name):
    st.download_button('Download table as CSV',d.to_csv(index=False).encode('utf-8-sig'),name,'text/csv')

def chart(d,x,y,color=None,title=None):
    fig=px.line(d,x=x,y=y,color=color,markers=True,title=title,template='plotly_white')
    fig.update_traces(connectgaps=False)
    fig.update_layout(legend=dict(orientation='h',yanchor='top',y=-.25,x=0),height=460,margin=dict(b=130),paper_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(dtick=2)
    st.plotly_chart(fig,width='stretch')

def years(key):
    lo,hi=int(scores.year.min()),int(scores.year.max())
    if lo==hi: return lo,hi
    return st.slider('Years',lo,hi,(lo,min(2023,hi) if lo<=2023 else hi),key=key)

def document_filter(key,english_only=False):
    pool=docs[docs.searchable] if english_only else docs
    a,b=st.columns(2)
    regions=a.multiselect('Regions',sorted(pool.region.unique()),key=key+'regions')
    if regions: pool=pool[pool.region.isin(regions)]
    countries=b.multiselect('Country / geographic scope',sorted(pool.country.unique()),key=key+'countries')
    if countries: pool=pool[pool.country.isin(countries)]
    return pool

if page=='Overview':
    st.subheader('The collection at a glance')
    a,b,c,d=st.columns(4)
    a.metric('Documents in catalogue',len(docs))
    b.metric('Country / economy scopes',docs.loc[docs.scope=='Country / economy','country'].nunique())
    c.metric('English documents searchable',int(docs.indexed.sum()))
    d.metric('Score years',f'{scores.year.min()}–{scores.year.max()}')
    st.info('The catalogue counts files, not necessarily unique frameworks. Search includes unique English texts with sufficient readable content. Regional and historical frameworks are shown separately.')
    a,b=st.columns([3,2])
    with a:
        st.subheader('Rights data coverage')
        count=scores.groupby('year')[RIGHTS].count().reset_index().melt('year',var_name='Right',value_name='Non-missing country-year entries')
        chart(count,'year','Non-missing country-year entries','Right')
    with b:
        st.subheader('Documents by region')
        coverage=docs.groupby('region').agg(Files=('doc_id','count'),Searchable=('search_doc_id',lambda x:x[x!=''].nunique())).reset_index()
        st.dataframe(coverage,hide_index=True,width='stretch')
        st.caption('A document may span several years. Counts include versions and language variants in the full catalogue.')
    st.subheader('Three ways to explore')
    st.markdown('**Country trends:** compare six rights and freedom ratings.\n\n**Regional comparison:** inspect equal-country averages and changing coverage.\n\n**Topic search:** retrieve source passages, then compare evidence by country or region.')

elif page=='Country trends':
    country=st.selectbox('Country / geographic scope',sorted(scores.country.unique()))
    period=years('countryyears'); selected=st.multiselect('Rights',RIGHTS,default=RIGHTS)
    d=scores[(scores.country==country)&scores.year.between(*period)]
    if selected: chart(d.melt('year',value_vars=selected,var_name='Right',value_name='Score'),'year','Score','Right',country+' · rights scores')
    rating=st.radio('Freedom rating',RATINGS,horizontal=True)
    chart(d,'year',rating,title=rating+' · higher values mean less freedom')
    st.caption('Ratings and rights scores use different scales and are displayed separately. Missing values remain gaps. The supplied cleaned CSV may already contain imputations; original versus imputed values cannot be identified from this file.')
    overlap=docs[(docs.country==country)&(docs.start_year<=period[1])&(docs.end_year>=period[0])]
    st.subheader('Frameworks overlapping this period')
    st.dataframe(overlap[['title','start_year','end_year','url']],column_config={'url':st.column_config.LinkColumn('Document')},hide_index=True,width='stretch')
    st.caption('Links are matched by geographic label and filename period; they are not verified provenance for individual scores.')
    download(d,'country_scores.csv')

elif page=='Regional comparison':
    period=years('regionyears');metric=st.selectbox('Measure',RIGHTS+RATINGS)
    regions=st.multiselect('World Bank regions',sorted(scores.loc[scores.scope=='Country / economy','region'].unique()),default=sorted(scores.loc[scores.scope=='Country / economy','region'].unique()))
    balanced=st.toggle('Fixed country composition',value=False,help='For this measure, retain only countries with a non-missing observation in every selected calendar year. Cohorts are separate for each region.')
    rows=[]
    for region in regions:
        d=aggregate(scores[scores.region==region],metric,period,balanced); d['Region']=region; rows.append(d)
    if rows:
        result=pd.concat(rows,ignore_index=True)
        if result.countries.sum()==0:st.warning('No countries have complete data for this measure and period. Shorten the interval or turn off fixed composition.')
        chart(result,'year','mean','Region',metric+' · equal-country mean')
        chart(result,'year','countries','Region','Countries contributing each year')
        st.dataframe(result,hide_index=True,width='stretch');download(result,'regional_averages.csv')
    st.info('Exploratory aggregation: each observed country has equal weight. Available-country means can change when coverage changes. Fixed composition holds the cohort constant for the selected measure and period; it may leave very few countries. Regional and historical entities are excluded. Region membership uses one World Bank snapshot, not historical boundaries.')

elif page=='Document library':
    pool=document_filter('library')
    term=st.text_input('Filter filenames')
    if term: pool=pool[pool.title.str.contains(term,case=False,regex=False)]
    st.write(f'{len(pool)} files')
    st.dataframe(pool[['title','country','region','start_year','end_year','indexed','language_status','period_review','url']],column_config={'url':st.column_config.LinkColumn('Open source'),'indexed':st.column_config.CheckboxColumn('Primary search copy'),'language_status':'Corpus decision'},hide_index=True,width='stretch')
    download(pool,'document_catalogue.csv')
    st.caption('Source links may require Drive permission. A period marked for review was not reliably parsed from its filename.')
    readable=pool[pool.searchable]
    if len(readable) and st.checkbox('Read extracted English text'):
        selected_id=st.selectbox('Document',readable.doc_id.tolist(),format_func=lambda value:readable.set_index('doc_id').loc[value,'title'])
        representative=readable.set_index('doc_id').loc[selected_id,'search_doc_id']
        document=json.loads((ROOT/'data/pilot_text'/f'{representative}.json').read_text(encoding='utf-8'))
        st.caption('Extracted text may contain table/OCR errors. Consult the original document for layout and verification.')
        st.text_area('Document text',document['text'],height=400,disabled=True)
        st.download_button('Download extracted text',document['text'].encode('utf-8'),selected_id+'.txt','text/plain')

elif page=='Topic search':
    chunks=corpus()
    st.subheader('Find evidence across English frameworks')
    st.caption('Search retrieves passages from the English corpus; results are evidence to inspect, not proof of policy implementation. Semantic scores indicate similarity, not confidence.')
    pool=document_filter('search',english_only=True)
    st.write(f'{pool.search_doc_id.nunique()} unique searchable documents selected across {pool.country.nunique()} geographic scopes.')
    with st.form('query'):
        query=st.text_input('Term or topic',placeholder='For example: access to justice for women')
        mode=st.radio('Search method',['Keyword','Exact phrase','Semantic'],horizontal=True,help='Semantic uses a local latent semantic model trained on this English corpus. It detects word co-occurrence; paraphrase understanding is limited. No downloads or API keys.')
        submitted=st.form_submit_button('Search documents',type='primary')
    signature=(query,mode,tuple(sorted(pool.doc_id)))
    if submitted:
        if not query.strip(): st.warning('Enter a topic or phrase.')
        else:
            with st.spinner('Retrieving source passages…'):
                try:
                    results=search(chunks,query,set(pool.search_doc_id),mode,search_index() if mode!='Exact phrase' else None)
                    st.session_state['search_result']=(signature,results)
                except Exception as e:
                    st.error('Search could not initialize. Exact-phrase search remains available. Details: '+str(e)[:350])
    saved=st.session_state.get('search_result')
    if saved and saved[0]==signature:
        results=saved[1]
        st.caption('Up to 20 passages, at most two per document. For semantic search, even the highest-ranked passage may be irrelevant; check the text. Passage IDs refer to extracted text, not PDF pages.')
        if not results: st.info('No matching passages in the selected readable English corpus.')
        else:
            tags=pool.groupby('search_doc_id').agg(country=('country',lambda x:' / '.join(sorted(set(x)))),region=('region',lambda x:' / '.join(sorted(set(x))))).reset_index().rename(columns={'search_doc_id':'doc_id'})
            result=pd.DataFrame(results).merge(tags,on='doc_id',validate='many_to_one')
            group=st.radio('Group evidence by',['country','region'],horizontal=True)
            for label,grouped in result.groupby(group,sort=True):
                st.markdown('### '+label)
                for row in grouped.itertuples():
                    with st.expander(row.title+' · '+row.passage_id.split(':')[-1]):
                        st.text(row.text)
                        st.markdown(f'[Open source document]({row.url})')
                        st.caption(f'Passage {row.passage_id} · relevance {row.relevance:.3f}')
            st.subheader('Evidence overview')
            st.dataframe(result.groupby(group).agg(Retrieved_documents=('doc_id','nunique'),Retrieved_passages=('passage_id','count')).reset_index(),hide_index=True)
            st.caption('Geographic tags come from filenames, including duplicate copies. Shared frameworks are indexed once; passages may not address every country listed. Counts describe this capped retrieval result, not how common a topic is in the region. This first version provides an extractive evidence overview; it does not generate unsupported narrative claims.')
            download(result,'topic_evidence.csv')
    elif saved: st.info('Filters or query changed. Run search again to update the evidence.')

else:
    st.subheader('Sources, coverage and interpretation')
    st.markdown('''- **Scores:** supplied `df_rights.csv`, used without additional imputation or score changes. Country aliases are normalized for display; missing country codes are resolved separately. Uploaded replacements stay in session memory.
- **Frameworks:** the Drive folder catalogue and extracted English texts. Document periods come from filenames and may need correction. Search citations use stable passage IDs rather than unverified page numbers.
- **Freedom ratings:** CL and PR ratings increase as freedom decreases. The year alignment and previous cleaning are inherited from your CSV, not recomputed here.
- **Regions:** World Bank country metadata snapshot, retrieved 7 November 2026. Contemporary classifications are exploratory groupings across all years. Historical and regional entities do not enter national averages.
- **Search:** keyword TF–IDF, literal phrase matching, or corpus-trained latent semantic analysis (96 latent dimensions). No API key is required. Documents are untrusted evidence, never executable instructions.
- **Limits:** extracted text can contain OCR and table errors. Similarity is not factual support. Document language and duplicate decisions are recorded in the corpus audit. Non-English, unreadable and duplicate files remain in the catalogue.
- **Public deployment:** the packaged extracted text and CSV become accessible to app users and anyone with repository access. Confirm you have permission to redistribute them before making the repository public. Source Drive permissions do not protect text bundled in the app.''')
    audit_path=ROOT/'data/corpus_audit.csv'
    if audit_path.exists():
        audit=pd.read_csv(audit_path);st.subheader('Corpus audit');st.dataframe(audit,hide_index=True,width='stretch');download(audit,'corpus_audit.csv')
    st.subheader('Data checks')
    st.write({'rows':len(scores),'geographic_labels':scores.country.nunique(),'duplicate_country_years':int(scores.duplicated(['country','year']).sum()),'unmapped_labels':sorted(scores.loc[scores.scope=='Unmapped','country'].unique().tolist())})
    download(scores,'dashboard_data.csv')
