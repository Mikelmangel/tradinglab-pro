"""TradingLab Pro — Portfolio Multi-Asset Backtester."""
import numpy as np, pandas as pd

class PortfolioBacktester:
    def run(self,datasets,code,cfg,allocation='equal',custom_weights=None,progress_cb=None):
        from src.core.backtest_engine import BacktestEngine
        syms=list(datasets.keys());n=len(syms)
        if not syms: return {}
        weights=({s:1/n for s in syms} if allocation=='equal'
                 else {s:custom_weights.get(s,1/n) for s in syms})
        results={};equity_curves={}
        for i,sym in enumerate(syms):
            data=datasets[sym];sub_cap=cfg.initial_capital*weights[sym]
            from dataclasses import replace
            sub_cfg=replace(cfg,initial_capital=sub_cap)
            try:
                ns={'pd':pd,'np':np};exec(code,ns)
                fn=ns.get('generate_signals')
                if fn is None: continue
                sig=fn(data)
                r=BacktestEngine().run(data,sig,sub_cfg,sym)
                results[sym]=r
                if not r['equity_curve'].empty:
                    equity_curves[sym]=r['equity_curve']['value']
            except: pass
            if progress_cb: progress_cb(int((i+1)/len(syms)*100),f"Procesando {sym}...")
        if not equity_curves: return {'individual':results,'portfolio_metrics':{},'correlation':None,'combined_equity':pd.DataFrame()}
        # Align and combine
        common=equity_curves[list(equity_curves.keys())[0]].index
        for s in equity_curves: common=common.intersection(equity_curves[s].index)
        aligned={s:equity_curves[s].reindex(common).ffill() for s in equity_curves}
        combined=pd.DataFrame(aligned)
        # Normalize each to initial capital contribution then sum
        for s in combined.columns:
            alloc = cfg.initial_capital * weights[s]
            combined[s] = equity_curves[s].ffill().fillna(alloc) * weights[s]
        combined['Portfolio']=combined.drop(columns=['Portfolio']).sum(axis=1)
        rets={s:combined[s].pct_change().dropna() for s in list(equity_curves.keys())}
        corr=None
        if len(rets)>1:
            ret_df=pd.DataFrame(rets).dropna()
            corr=ret_df.corr() if not ret_df.empty else None
        summary={}
        for sym,r in results.items():
            m=r['metrics']
            def g(k):
                for mk,mv in m.items():
                    if k.lower() in mk.lower():
                        try: return float(str(mv).replace('%','').replace('$','').replace(',','').replace('+',''))
                        except: return mv
                return 'N/A'
            summary[sym]={'Retorno':g('Retorno total'),'Sharpe':g('Sharpe'),
                          'Max DD':g('Max Drawdown'),'Trades':g('Total')}
        from src.core.backtest_engine import BacktestEngine
        port_eq=combined['Portfolio']
        port_ret=port_eq.pct_change().dropna()
        port_results=BacktestEngine()._metrics(
            port_eq.to_frame('value'),port_ret,
            [t for r in results.values() for t in (r.get('trades_df',pd.DataFrame()).to_dict('records') if not r.get('trades_df',pd.DataFrame()).empty else [])],
            cfg.initial_capital,
            list(datasets.values())[0] if datasets else pd.DataFrame())
        return {'individual':results,'portfolio_metrics':{'metrics':port_results,'asset_summary':summary},
                'correlation':corr,'combined_equity':combined}
