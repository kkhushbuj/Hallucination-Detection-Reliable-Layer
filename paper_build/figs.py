import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8})
BLUE='#2f6fb0'; ORANGE='#d9780f'; GREY='#6b7280'; GREEN='#2e7d5b'
d=pd.read_csv('../evaluation/results_seed7_final.csv'); y=d.correct.astype(int).values; s=d.trust_score.values.astype(float)

# Fig 1 pipeline
fig,ax=plt.subplots(figsize=(6.4,3.0)); ax.set_xlim(0,100); ax.set_ylim(0,50); ax.axis('off')
def box(x,y0,w,h,t,c='#eef3f9',ec=BLUE,fs=6.6,bold=False):
    ax.add_patch(FancyBboxPatch((x,y0),w,h,boxstyle='round,pad=0.2,rounding_size=1.0',fc=c,ec=ec,lw=1))
    ax.text(x+w/2,y0+h/2,t,ha='center',va='center',fontsize=fs,fontweight='bold' if bold else 'normal',linespacing=1.3)
def arr(x1,y1,x2,y2): ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=8,lw=0.9,color=GREY))
box(0.5,19,11,12,'Question',c='#f6f6f6',ec=GREY)
box(15,19,17,12,'Writer\ngpt-4o-mini\n3 answers, T = 0.9')
box(37,34,21,12,'Agreement checker\nGemini 3.5 Flash-Lite\ncompares answer pairs',c='#fdf3e7',ec=ORANGE)
box(37,19,21,12,'Web search (Tavily)\ntop 3 results for\nquestion + answer',c='#eef6f1',ec=GREEN)
box(37,3,21,12,'Three judges\nQwen3.8, Mistral, Llama\nCORRECT or HALLUCINATED')
box(63,19,15,12,'Score\n(judges + agreement)\nbest answer wins')
box(82,34,17,12,'Tie-breaker\nNemotron 3.5\nchecks winner only',c='#fdf3e7',ec=ORANGE)
box(82,3,17,13,'Trust score\n0 to 100 + label',c='#e6f2ec',ec=GREEN,bold=True)
arr(11.8,25,14.7,25); arr(32.3,28,36.7,38); arr(32.3,25,36.7,25); arr(47.5,18.7,47.5,15.4)
arr(58.3,40,62.7,30); arr(58.3,9,62.7,20.5); arr(78.3,29,81.7,36); arr(90.5,33.7,90.5,16.3)
ax.text(50,-1.2,'Orange: agreement and tie-breaker checks.  Green: web grounding and final output.',ha='center',fontsize=6.2,color=GREY)
fig.savefig('fig_pipeline.png',dpi=220,bbox_inches='tight'); plt.close(fig)

# Fig 2 histogram
bins=[('0–49',s<50),('50–74',(s>=50)&(s<75)),('75',s==75),('76–99',(s>75)&(s<100)),('100',s==100)]
fig,ax=plt.subplots(figsize=(5.6,2.5))
x=np.arange(len(bins)); c=[(m&(y==1)).sum() for _,m in bins]; w=[(m&(y==0)).sum() for _,m in bins]
ax.bar(x,c,color=BLUE,label='correct'); ax.bar(x,w,bottom=c,color=ORANGE,label='incorrect')
for i,(a,b) in enumerate(zip(c,w)):
    ax.text(i,a+b+2,f'{b}/{a+b} wrong',ha='center',fontsize=7)
ax.set_xticks(x); ax.set_xticklabels([b for b,_ in bins]); ax.set_xlabel('Trust score of the winning answer'); ax.set_ylabel('Questions (n = 200)')
ax.set_ylim(0,max(np.array(c)+np.array(w))+22); ax.legend(frameon=False,fontsize=7,loc='upper left'); ax.spines[['top','right']].set_visible(False)
fig.savefig('fig_hist.png',dpi=220,bbox_inches='tight'); plt.close(fig)

# Fig 3 per benchmark
fig,ax=plt.subplots(figsize=(5.6,2.5)); srcs=['HaluEval','TriviaQA','TruthfulQA']; X=np.arange(3); wd=0.26
acc=[d[d.source==k].correct.mean()*100 for k in srcs]
mc=[d[(d.source==k)&d.correct].trust_score.mean() for k in srcs]; mw=[d[(d.source==k)&~d.correct].trust_score.mean() for k in srcs]
for off,v,col,l in ((-wd,acc,GREY,'accuracy (%)'),(0,mc,BLUE,'mean trust, correct answers'),(wd,mw,ORANGE,'mean trust, incorrect answers')):
    b=ax.bar(X+off,v,wd,color=col,label=l)
    for xi,vi in zip(X+off,v): ax.text(xi,vi+1.5,f'{vi:.0f}',ha='center',fontsize=7)
ax.set_xticks(X); ax.set_xticklabels([f'{k}\n(n = {(d.source==k).sum()})' for k in srcs]); ax.set_ylim(0,125); ax.set_yticks([0,25,50,75,100])
ax.legend(frameon=False,fontsize=6.8,ncol=3,loc='upper center',bbox_to_anchor=(0.5,1.14)); ax.spines[['top','right']].set_visible(False)
fig.savefig('fig_bench.png',dpi=220,bbox_inches='tight'); plt.close(fig)

# Fig 4 labels + reliability
fig,(a1,a2)=plt.subplots(1,2,figsize=(6.3,2.55),gridspec_kw={'width_ratios':[1,1.05]})
lab=d.label.str.split(' ').str[0]; names=['Low','Medium','High']
accs=[d[lab==n].correct.mean()*100 for n in names]; ns=[(lab==n).sum() for n in names]
a1.bar(names,accs,color=[ORANGE,'#c9a227',BLUE],width=0.6)
for i,(v,n) in enumerate(zip(accs,ns)): a1.text(i,v+2,f'{v:.0f}%\n(n = {n})',ha='center',fontsize=7)
a1.axhline(d.correct.mean()*100,color=GREY,ls='--',lw=0.8); a1.text(-0.45,d.correct.mean()*100+1.5,'overall 61%',ha='left',fontsize=6.5,color=GREY)
a1.set_ylim(0,100); a1.set_ylabel('Accuracy (%)'); a1.set_title('(a) Accuracy by confidence label',fontsize=7.5); a1.spines[['top','right']].set_visible(False)
edges=[0,.5,.75,.9,1.0001]; xs=[];ys=[];ns=[]
p=s/100
for lo,hi in zip(edges[:-1],edges[1:]):
    m=(p>=lo)&(p<hi)
    if m.sum(): xs.append(p[m].mean()); ys.append(y[m].mean()); ns.append(m.sum())
a2.plot([0,1],[0,1],ls='--',color=GREY,lw=0.9); a2.plot(xs,ys,'o-',color=BLUE,lw=1.2)
for xi,yi,n in zip(xs,ys,ns): a2.text(xi,yi-0.09,f'n={n}',ha='center',fontsize=6.5)
a2.set_xlim(0,1.02); a2.set_ylim(0,1.02); a2.set_xlabel('Mean trust score (as a fraction)'); a2.set_ylabel('Observed share correct'); a2.set_title('(b) Reliability diagram',fontsize=7.5); a2.spines[['top','right']].set_visible(False)
fig.tight_layout(); fig.savefig('fig_calib.png',dpi=220,bbox_inches='tight'); plt.close(fig)
print([ (b,int(a),int(c_)) for (b,_),a,c_ in zip(bins,c,w)], xs, ys, ns)
