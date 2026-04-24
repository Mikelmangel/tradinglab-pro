"""TradingLab Pro — Optimizer: Grid Search, Genetic Algorithm, Walk-Forward, Monte Carlo."""
from __future__ import annotations
import numpy as np, pandas as pd
from dataclasses import dataclass, field
from itertools import product as iterproduct

@dataclass
class ParamRange:
    start: float; stop: float; step: float = 1.0; as_int: bool = True
    def __iter__(self):
        v=np.arange(self.start,self.stop+self.step/2,self.step)
        return iter(int(x) if self.as_int else float(round(x,6)) for x in v)
    def __len__(self): return max(1,int((self.stop-self.start)/self.step)+1)
    def random(self):
        n=len(self);idx=np.random.randint(0,n);v=self.start+idx*self.step
        return int(v) if self.as_int else float(round(v,6))

def _run_one(data,code,params,cfg_dict,metric):
    try:
        ns={'pd':pd,'np':np};exec(code,ns)
        fn=ns.get('generate_signals')
        if fn is None: return None
        sig=fn(data,**params)
        from src.core.backtest_engine import BacktestEngine,BacktestConfig
        c=BacktestConfig(**{k:v for k,v in cfg_dict.items() if hasattr(BacktestConfig(),k)})
        r=BacktestEngine().run(data,sig,c)
        m=r['metrics']
        key_map={'Sharpe Ratio':'Sharpe','Sharpe':'Sharpe','Retorno total':'Retorno total',
                 'Sortino Ratio':'Sortino','Calmar Ratio':'Calmar',
                 'Profit Factor':'Profit Factor','Win Rate':'Win Rate',
                 'CAGR':'CAGR','Max Drawdown':'Max Drawdown'}
        target=key_map.get(metric,metric)
        for k,v in m.items():
            if target.lower() in k.lower():
                try:
                    val=float(str(v).replace('%','').replace('$','').replace(',','').replace('+','').replace('∞','999'))
                    if 'drawdown' in metric.lower() or 'Drawdown' in metric: val=-val
                    return val
                except: pass
        return None
    except: return None

class GridSearchOptimizer:
    def run(self,data,code,param_grid,cfg_dict,metric,progress_cb=None):
        keys=list(param_grid.keys());ranges=list(param_grid.values())
        combos=list(iterproduct(*ranges));total=len(combos)
        results=[]
        for i,combo in enumerate(combos):
            params=dict(zip(keys,combo))
            val=_run_one(data,code,params,cfg_dict,metric)
            if val is not None: results.append({**params,metric:val})
            if progress_cb: progress_cb(int((i+1)/total*100),str(params),val or 0)
        if not results: return pd.DataFrame()
        df=pd.DataFrame(results).sort_values(metric,ascending=False).reset_index(drop=True)
        return df

class GeneticOptimizer:
    def __init__(self,population_size=40,generations=30,crossover_rate=0.8,
                 mutation_rate=0.15,elite_pct=0.15):
        self.pop_size=population_size;self.gens=generations
        self.cx_rate=crossover_rate;self.mut_rate=mutation_rate
        self.elite=max(1,int(population_size*elite_pct))

    def run(self,data,code,param_grid,cfg_dict,metric,progress_cb=None):
        keys=list(param_grid.keys());ranges=list(param_grid.values())
        def random_ind(): return [r.random() for r in ranges]
        pop=[random_ind() for _ in range(self.pop_size)]
        def fitness(ind):
            v=_run_one(data,code,dict(zip(keys,ind)),cfg_dict,metric)
            return v if v is not None else -9999
        best_rows=[];best_fit=-9999;best_ind=pop[0]
        total=self.gens*self.pop_size
        done=0
        for g in range(self.gens):
            scored=sorted([(fitness(ind),ind) for ind in pop],key=lambda x:-x[0])
            if scored[0][0]>best_fit: best_fit=scored[0][0];best_ind=scored[0][1]
            best_rows.append({**dict(zip(keys,best_ind)),'generation':g+1,metric:best_fit})
            elite=[ind for _,ind in scored[:self.elite]]
            new_pop=list(elite)
            while len(new_pop)<self.pop_size:
                p1=scored[np.random.randint(0,self.elite)][1]
                p2=scored[np.random.randint(0,self.elite)][1]
                if np.random.random()<self.cx_rate:
                    pt=np.random.randint(1,len(keys))
                    child=p1[:pt]+p2[pt:]
                else: child=list(p1)
                for j in range(len(child)):
                    if np.random.random()<self.mut_rate: child[j]=ranges[j].random()
                new_pop.append(child)
            pop=new_pop
            done+=self.pop_size
            if progress_cb: progress_cb(int(done/total*100),f"Gen {g+1}/{self.gens} best={best_fit:.3f}",best_fit)
        return pd.DataFrame(best_rows)

class WalkForwardTester:
    def run(self,data,code,param_grid,cfg_dict,is_pct=0.7,n_windows=5,metric='Sharpe',progress_cb=None):
        n=len(data);window=n//n_windows;windows_rows=[]
        for w in range(n_windows):
            start=w*window;end=start+window
            if end>n: end=n
            split=int((end-start)*is_pct)+start
            is_data=data.iloc[start:split];oos_data=data.iloc[split:end]
            if len(is_data)<30 or len(oos_data)<10: continue
            opt=GridSearchOptimizer()
            is_res=opt.run(is_data,code,param_grid,cfg_dict,metric)
            if is_res.empty: continue
            best_params={k:is_res.iloc[0][k] for k in param_grid.keys()}
            is_val=float(is_res.iloc[0][metric])
            oos_val=_run_one(oos_data,code,best_params,cfg_dict,metric) or 0
            windows_rows.append({'Window':w+1,'IS start':str(is_data.index[0])[:10],
                                  'IS end':str(is_data.index[-1])[:10],
                                  'OOS start':str(oos_data.index[0])[:10],
                                  'OOS end':str(oos_data.index[-1])[:10],
                                  f'IS {metric}':round(is_val,3),
                                  f'OOS {metric}':round(oos_val,3),
                                  **{k:best_params[k] for k in best_params}})
            if progress_cb: progress_cb(int((w+1)/n_windows*100),f"Window {w+1}/{n_windows}")
        df=pd.DataFrame(windows_rows)
        is_mean=df[f'IS {metric}'].mean() if not df.empty else 0
        oos_mean=df[f'OOS {metric}'].mean() if not df.empty else 0
        wf_eff=oos_mean/is_mean if is_mean else 0
        return {'windows_df':df,'wf_efficiency':round(wf_eff,4),'is_mean':is_mean,'oos_mean':oos_mean}

class MonteCarloSimulator:
    def run(self,pnl_pcts,initial_capital,n_simulations=500):
        if len(pnl_pcts)<3: return None
        pnl=np.array(pnl_pcts)/100
        paths=[]
        for _ in range(n_simulations):
            idx=np.random.choice(len(pnl),size=len(pnl),replace=True)
            sample=pnl[idx];eq=initial_capital*np.cumprod(1+sample)
            paths.append(np.insert(eq,0,initial_capital))
        finals=np.array([p[-1] for p in paths])
        mds=[]
        for p in paths:
            rm=np.maximum.accumulate(p);dd=(p-rm)/rm*100;mds.append(dd.min())
        mds=np.array(mds)
        ny=len(pnl)/252
        cagrs=((finals/initial_capital)**(1/max(ny,0.01))-1)*100
        prob_ruin=np.sum(finals<initial_capital*0.5)/n_simulations*100
        return {'equity_paths':paths,'final_equities':finals,'max_drawdowns':mds,
                'q5_final':float(np.percentile(finals,5)),'q50_final':float(np.percentile(finals,50)),
                'q95_final':float(np.percentile(finals,95)),
                'median_max_dd':float(np.median(mds)),'prob_of_ruin':float(prob_ruin),
                'cagr_p5':float(np.percentile(cagrs,5)),'cagr_p50':float(np.percentile(cagrs,50)),
                'cagr_p95':float(np.percentile(cagrs,95))}
