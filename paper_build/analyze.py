import pandas as pd, numpy as np, json
d=pd.read_csv('evaluation/results_seed7_final.csv')
y=d.correct.astype(int).values; s=d.trust_score.values.astype(float)
def auroc(y,s):
    r=pd.Series(s).rank().values; n1=y.sum(); n0=len(y)-n1
    return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
rng=np.random.default_rng(7)
B=5000; gaps=[];aus=[];accs=[]
for _ in range(B):
    i=rng.integers(0,len(y),len(y)); yy=y[i]; ss=s[i]
    if yy.min()==yy.max(): continue
    gaps.append(ss[yy==1].mean()-ss[yy==0].mean()); aus.append(auroc(yy,ss)); accs.append(yy.mean())
ci=lambda a:(float(np.percentile(a,2.5)),float(np.percentile(a,97.5)))
out={'n':len(d),'acc':float(y.mean()),'acc_ci':ci(accs),'mean_correct':float(s[y==1].mean()),'mean_wrong':float(s[y==0].mean()),
 'gap':float(s[y==1].mean()-s[y==0].mean()),'gap_ci':ci(gaps),'auroc':float(auroc(y,s)),'auroc_ci':ci(aus)}
per={}
for src,g in d.groupby('source'):
    yy=g.correct.astype(int).values; ss=g.trust_score.values.astype(float)
    per[src]={'n':len(g),'acc':float(yy.mean()),'mc':float(ss[yy==1].mean()),'mw':float(ss[yy==0].mean()),'gap':float(ss[yy==1].mean()-ss[yy==0].mean()),'auroc':float(auroc(yy,ss))}
out['per']=per
# labels
lab={}
for l,g in d.groupby(d.label.str.split(' ').str[0]):
    lab[l]={'n':len(g),'acc':float(g.correct.mean())}
out['labels']=lab
# threshold: flag if trust < t  (flag = predict wrong)
th=[]
for t in (100,87.5,80,75,66.7,50):
    flag=s<t; tp=(flag&(y==0)).sum(); 
    th.append({'t':t,'flagged':int(flag.sum()),'prec':float(tp/max(flag.sum(),1)),'recall':float(tp/(y==0).sum()),'acc_kept':float(y[~flag].mean()) if (~flag).sum() else None,'kept':int((~flag).sum())})
out['thresholds']=th
# score distribution
dist=d.groupby('trust_score').correct.agg(['count','sum']).reset_index(); out['dist']=dist.values.tolist()
# top-score wrong
top=d[d.trust_score==100]; out['top100']={'n':len(top),'wrong':int((~top.correct).sum()),'wrong_share':float((~top.correct).mean())}
# calibration
p=s/100; out['brier']=float(((p-y)**2).mean()); out['brier_base']=float(((y.mean()-y)**2).mean())
bins=np.linspace(0,1,6); ece=0; rel=[]
for a,b in zip(bins[:-1],bins[1:]):
    m=(p>=a)&((p<b)|(b==1)&(p<=1)); 
    if m.sum(): rel.append([float(p[m].mean()),float(y[m].mean()),int(m.sum())]); ece+=m.sum()/len(y)*abs(p[m].mean()-y[m].mean())
out['ece5']=float(ece); out['rel']=rel
# judge-only baseline from flagged_count (winner's judges)
fc=d.flagged_count.str.split('/',expand=True).astype(int); jonly=1-fc[0]/fc[1]
out['auroc_judges_only']=float(auroc(y,jonly.values.astype(float)))
out['judges_only_mean_gap']=float(jonly[y==1].mean()-jonly[y==0].mean())
mf=d.majority_flagged.astype(bool).values
out['majority_flag']={'flagged':int(mf.sum()),'prec_wrong':float((mf&(y==0)).sum()/max(mf.sum(),1)),'recall_wrong':float((mf&(y==0)).sum()/(y==0).sum())}
out['any_flag']={'flagged':int((fc[0]>0).sum()),'prec_wrong':float(((fc[0]>0)&(y==0)).sum()/max((fc[0]>0).sum(),1)),'recall_wrong':float(((fc[0]>0)&(y==0)).sum()/(y==0).sum())}
out['zero_rows']=int((s==0).sum())
json.dump(out,open('paper_build/metrics.json','w'),indent=1)
print(json.dumps(out,indent=1))
