import pandas as pd, numpy as np, re, difflib, sys
import os
BASE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+os.sep
c=pd.read_excel(BASE+'data/coded.xlsx',sheet_name='Coding')
ex=pd.read_excel(BASE+'data/coded.xlsx',sheet_name='Excluded_check')
s=pd.read_csv(BASE+'data/sentences_coded.csv',encoding='utf-8-sig')
c=c.merge(s[['sid','OFFICIAL_VOICE']],on='sid',how='left')
c['type']=c['source type'].str[0]
DIM=['LEG','MOB','LAB_ACC','LAB_PROT','DEP','ADM']; GAP=['GAP_ABS','GAP_DES','GAP_IMP']; FRM=['FRM_HUM','FRM_ECO','FRM_BUR','FRM_SEC','FRM_SRL']
CODES=DIM+GAP+FRM
for k in CODES+['POP_CAMP','POP_URBAN','POP_MIGR','Unsure (1)']: c[k]=c[k].notna().astype(int)
c['Note']=c['Note'].fillna('').astype(str)
n=c['Note'].str.lower()
c['f_heading']=n.str.contains(r'headline|title|heading|label|^table')
c['f_split']=n.str.contains('split sentence')
c['f_notcontent']=n.str.contains(r'not (?:substantive )?content|no (?:substantive )?content|mission|not relevant|low relevance|not closely related|no substantive|operating, not content|unclear what|cannot categori')
c['f_impliedgap']=n.str.contains('implied')
CAMPDOCS={'B04','A01','A02','A03','A04','A05','B01','B02','D01','D02','D03','D04','D05','D08'}
c['camp_view']=((c.POP_CAMP==1)|(c.doc.isin(CAMPDOCS)&(c.POP_URBAN==0)&(c.POP_MIGR==0))).astype(int)
c['any_code']=c[CODES].max(axis=1)
out={}
# QA
qa=pd.DataFrame({'item':['rows','rows with Done=x','rows with any dimension/gap/frame code','rows with no such code','  of which Unsure','Unsure total','heading/label (note)','split sentence (note)','not substantive/mission/not relevant (note)','implied gap (note)','POP_CAMP marked','POP_URBAN marked','POP_MIGR marked','camp view (marked + inherited)','official-voice view'],
 'n':[len(c),(c['Done (x)']=='x').sum(),c.any_code.sum(),(c.any_code==0).sum(),((c.any_code==0)&(c['Unsure (1)']==1)).sum(),c['Unsure (1)'].sum(),c.f_heading.sum(),c.f_split.sum(),c.f_notcontent.sum(),c.f_impliedgap.sum(),c.POP_CAMP.sum(),c.POP_URBAN.sum(),c.POP_MIGR.sum(),c.camp_view.sum(),c.OFFICIAL_VOICE.sum()]})
out['QA']=qa
# denominators
d0=c; d1=c[~c.f_heading]; d2=c[~c.f_heading&~c.f_notcontent]
def share_table(df,by='source type'):
    g=df.groupby(by)
    t=pd.DataFrame({'n':g.size()})
    for k in CODES: t[k]=g[k].sum()
    tot=pd.DataFrame({'n':[len(df)],**{k:[df[k].sum()] for k in CODES}},index=['ALL'])
    t=pd.concat([t,tot])
    cnt=t.copy()
    pct=t[CODES].div(t['n'],axis=0).mul(100).round(1); pct.insert(0,'n',t['n'])
    return cnt,pct
for nm,df in [('all857',d0),('excl_heading',d1),('excl_heading_notcontent',d2)]:
    cnt,pct=share_table(df); out['T_src_pct_'+nm]=pct.rename_axis('source type').reset_index(); out['T_src_cnt_'+nm]=cnt.rename_axis('source type').reset_index()
# views
def view(df,label):
    cnt={'n':len(df),**{k:int(df[k].sum()) for k in CODES}}
    return pd.Series(cnt,name=label)
v=pd.DataFrame([view(d1[d1.camp_view==1],'camp view'),view(d1[d1.POP_URBAN==1],'urban marked'),view(d1[d1.POP_MIGR==1],'migrant marked'),view(d1[d1.OFFICIAL_VOICE==1],'official voice'),view(d1[(d1.camp_view==1)&(d1.OFFICIAL_VOICE==0)],'camp view, not official voice'),view(d1,'all (excl heading)')])
out['T_views_cnt']=v.reset_index().rename(columns={'index':'view'})
vp=v[CODES].div(v['n'],axis=0).mul(100).round(1); vp.insert(0,'n',v['n']); out['T_views_pct']=vp.reset_index().rename(columns={'index':'view'})
# camp view by source type
cv=d1[d1.camp_view==1]; a,b=share_table(cv); out['T_campview_by_src_pct']=b.rename_axis('source type').reset_index()
# official voice by source type
ov=d1[d1.OFFICIAL_VOICE==1]; a,b=share_table(ov); out['T_ov_by_src_pct']=b.rename_axis('source type').reset_index()
# gap forms: gap sentences by source and implied gaps
g=d1[(d1[GAP].sum(axis=1)>0)]
out['gap_by_source']=pd.DataFrame({'n_gap_sentences':g.groupby('source type').size(),'n_all':d1.groupby('source type').size()}).assign(pct=lambda x:(x.n_gap_sentences/x.n_all*100).round(1)).reset_index()
# near duplicates
txt=c['SENTENCE TO CODE'].astype(str).str.lower().str.replace(r'\W+',' ',regex=True).str.strip().tolist()
pairs=[]
for i in range(len(txt)):
    if len(txt[i])<40: continue
    for j in range(i):
        if len(txt[j])<40: continue
        if abs(len(txt[i])-len(txt[j]))>0.25*max(len(txt[i]),len(txt[j])): continue
        sm=difflib.SequenceMatcher(None,txt[j],txt[i],autojunk=False)
        if sm.real_quick_ratio()>=0.8 and sm.quick_ratio()>=0.8 and sm.ratio()>=0.8: pairs.append((j,i,round(sm.ratio(),3)))
pairs=sorted(set(pairs))
dp=pd.DataFrame([{'row_a':c.sid[a],'doc_a':c.doc[a],'row_b':c.sid[b],'doc_b':c.doc[b],'sim':r,'text':c['SENTENCE TO CODE'][a][:140],'codes_a':','.join(k for k in CODES if c[k][a]),'codes_b':','.join(k for k in CODES if c[k][b])} for a,b,r in pairs])
out['near_duplicates']=dp
drop=set(b for a,b,r in pairs)
cd=c.drop(index=list(drop)); cd1=cd[~cd.f_heading]
cnt,pct=share_table(cd1); out['T_src_pct_no_dups']=pct.rename_axis('source type').reset_index()
base=out['T_src_pct_excl_heading'].set_index('source type')[CODES]
alt=out['T_src_pct_no_dups'].set_index('source type')[CODES]
diff=(alt-base).abs()
out['dup_sensitivity_maxdiff']=pd.DataFrame({'max abs change (pp)':diff.max(axis=1).round(1)}).reset_index()
# promise: TBC docs with 'will'
tbc=c[c.doc.isin(['C04','C05','C06'])&c['SENTENCE TO CODE'].str.contains(r'\bwill\b',case=False)]
pl=tbc[['sid','doc','SENTENCE TO CODE','Note']+CODES].copy(); pl['codes']=pl[CODES].apply(lambda r:','.join(k for k in CODES if r[k]),axis=1)
out['promise_will_TBC']=pl[['sid','doc','SENTENCE TO CODE','Note','codes']]
# excluded check
e=ex.copy(); e['relevant']=e['Relevant? (1 = yes)'].notna().astype(int)
e['stratum']=np.where(e.doc.str.startswith('B04'),'B04 appeal (10)','first 26 documents (50)')
out['excluded_check']=e.groupby('stratum').agg(n=('sid','size'),judged_relevant=('relevant','sum')).reset_index()
out['excluded_check_rows']=e[e.relevant==1][['sid','doc','SENTENCE TO CODE','NOTE']]
# evidence
ev=[]
for k in CODES+['POP_URBAN']:
    t=c[c[k]==1]
    for _,r in t.iterrows(): ev.append({'code':k,'sid':r.sid,'doc':r.doc,'type':r.type,'official_voice':r.OFFICIAL_VOICE,'camp_view':r.camp_view,'sentence':r['SENTENCE TO CODE'],'note':r.Note,'unsure':r['Unsure (1)']})
out['evidence_long']=pd.DataFrame(ev)
# notes classes
nc=c[c.Note!=''][['sid','doc','Note','f_heading','f_split','f_notcontent','f_impliedgap']]
out['notes_flagged']=nc

doc=c.groupby(['doc','source type']).agg(n=('sid','size'),with_code=('any_code','sum'),unsure=('Unsure (1)','sum'),heading=('f_heading','sum'),not_content=('f_notcontent','sum')).reset_index()
doc['pct_with_code']=(doc.with_code/doc.n*100).round(0); doc['pct_unsure']=(doc.unsure/doc.n*100).round(0)
out['per_document']=doc
# promise sensitivity: FRM_SRL and all codes in C if TBC 'will' sentences are dropped
tb=c.index.isin(tbc.index)
cc=c[~c.f_heading]; cp=cc[~cc.index.isin(tbc.index)]
def shc(df): g=df[df.type=='C']; return (g[CODES].mean()*100).round(1)
out['promise_sensitivity_C']=pd.DataFrame({'with TBC will-sentences (n=%d)'%len(cc[cc.type=='C']):shc(cc),'without (n=%d)'%len(cp[cp.type=='C']):shc(cp)}).reset_index().rename(columns={'index':'code'})
readme=pd.DataFrame({'item':[
 'Source','Denominator 1 (main)','Denominator 2 (exploratory)','Camp view','Official-voice view','Urban / migrant','Near-duplicates','Promise rule','Excluded check','Unsure','Free-text notes','Not computed'],
 'definition':[
 'coding_sheet_857.xlsx as returned by the author (all 857 rows marked Done); official-voice flag from the keyword rule in the pipeline (b04run), not hand coding',
 '857 minus rows whose note says heading/headline/title/label/table (n=27) = 830. Shares in T_src_* sheets use this unless the sheet name says all857',
 'Denominator 1 minus rows whose note says not content / mission / not relevant / no substantive content / unclear what the topic is / cannot categorise (n=%d more)'%int((c.f_notcontent&~c.f_heading).sum()),
 'POP_CAMP marked by hand, or the sentence is in one of the 14 camp-wide documents (A01-A05, B01, B02, B04, D01-D05, D08) and is not marked urban or migrant',
 'Type A sentences plus sentences naming a Thai official body with a speech verb (rule in pipeline); 89 rows, 84 after removing headings',
 'POP_URBAN marked n=39; POP_MIGR marked n=1 (too few to report shares)',
 'pairs with text similarity of 0.8 or more (12 pairs); sensitivity drops the later row of each pair',
 'C04-C06 sentences containing "will" (47): listed in promise_will_TBC; promise_sensitivity_C shows the C shares with and without them',
 'Excluded_check sheet: sentences marked 1 = relevant, by stratum',
 'Unsure (1) flag; per_document shows where it concentrates',
 'Notes are free text; headings/not-content groups were identified by keyword search in notes (notes_flagged lists every note with its group)',
 'No hypothesis tests or reliability figures (single coder, descriptive only)']})
out={'README':readme,**out}
c.to_pickle(BASE+'output/coded_flags.pkl')
with pd.ExcelWriter(BASE+'output/results_for_ch5.xlsx') as w:
    for k,v in out.items(): v.to_excel(w,sheet_name=k[:31],index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
for k in ['QA','T_src_pct_excl_heading','T_src_cnt_excl_heading','T_views_pct','excluded_check','dup_sensitivity_maxdiff','gap_by_source']:
    print('==',k); print(out[k].to_string())
print('near dup pairs',len(pairs)); print(dp.to_string()[:3500])
print('promise rows',len(pl)); print(out['promise_will_TBC'].to_string()[:3000])
print(out['excluded_check_rows'].to_string()[:2500])
