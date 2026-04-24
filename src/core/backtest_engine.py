"""TradingLab Pro — Backtest Engine v2: bar-by-bar, intra-bar stops, MTF, annual breakdown."""
from __future__ import annotations
import numpy as np, pandas as pd
from dataclasses import dataclass
from typing import Optional

@dataclass
class BacktestConfig:
    initial_capital: float = 10_000.0
    sizing_method: str = 'pct_equity'
    position_size: float = 1.0
    commission: float = 0.001
    allow_short: bool = False
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    max_bars_in_trade: Optional[int] = None
    max_positions: int = 1
    slippage_pct: float = 0.0
    reinvest: bool = True
    use_ohlc_path: bool = True

class _Trade:
    __slots__=['symbol','direction','entry_bar','exit_bar','entry_price','exit_price',
               'shares','commission','exit_reason','entry_date','exit_date','_trail_stop']
    def __init__(self,symbol,direction,entry_bar,entry_price,shares,commission,entry_date):
        self.symbol=symbol;self.direction=direction;self.entry_bar=entry_bar
        self.exit_bar=None;self.entry_price=entry_price;self.exit_price=None
        self.shares=shares;self.commission=commission;self.exit_reason=''
        self.entry_date=entry_date;self.exit_date=None;self._trail_stop=None
    @property
    def gross_pnl(self):
        if self.exit_price is None: return 0.0
        d=1 if self.direction=='long' else -1
        return (self.exit_price-self.entry_price)*self.shares*d
    @property
    def net_pnl(self): return self.gross_pnl-self.commission
    @property
    def pnl_pct(self):
        if not self.exit_price: return 0.0
        d=1 if self.direction=='long' else -1
        return (self.exit_price/self.entry_price-1)*100*d

def _intra_bar_check(o,h,l,c,stop,tp,direction):
    if direction=='long':
        if c<o:
            if stop and l<=stop: return stop,'stop_loss'
            if tp and h>=tp: return tp,'take_profit'
        else:
            if tp and h>=tp: return tp,'take_profit'
            if stop and l<=stop: return stop,'stop_loss'
    else:
        if c>o:
            if stop and h>=stop: return stop,'stop_loss'
            if tp and l<=tp: return tp,'take_profit'
        else:
            if tp and l<=tp: return tp,'take_profit'
            if stop and h>=stop: return stop,'stop_loss'
    return None,None

def _calc_shares(cfg,cash,equity,price,atr_v,wr,aw,al):
    if cfg.sizing_method=='pct_equity': dollar=equity*cfg.position_size
    elif cfg.sizing_method=='fixed_dollar': dollar=cfg.position_size
    elif cfg.sizing_method=='fixed_shares': return cfg.position_size
    elif cfg.sizing_method=='atr_risk' and atr_v and atr_v>0:
        dollar=equity*0.01*cfg.position_size/(atr_v/price)
    elif cfg.sizing_method=='fixed_risk_pct' and cfg.stop_loss_pct:
        dollar=equity*cfg.position_size/cfg.stop_loss_pct
    elif cfg.sizing_method=='kelly':
        if aw>0 and al>0 and 0<wr<1:
            b=aw/al; k=max(0,min(0.5,wr-(1-wr)/b)); dollar=equity*k
        else: dollar=equity*0.1
    else: dollar=equity*cfg.position_size
    return max(1,dollar/price) if price>0 else 1

class BacktestEngine:
    def run(self,data,signals,cfg,symbol='SYM'):
        data=data.copy().dropna()
        signals=signals.reindex(data.index).fillna(0)
        n=len(data)
        if n<2: return self._empty()
        opens=data['Open'].values;highs=data['High'].values
        lows=data['Low'].values;closes=data['Close'].values
        sigs=signals.values;dates=data.index
        cash=cfg.initial_capital;equity_curve=np.zeros(n);daily_ret=np.zeros(n)
        equity_curve[0]=cash
        open_trades=[];closed_trades=[]
        wins_pct=[];losses_pct=[]

        for i in range(1,n):
            o,h,l,c=opens[i],highs[i],lows[i],closes[i]
            sig=sigs[i-1]  # signal from PREVIOUS bar — strict no look-ahead
            still_open=[]
            for t in open_trades:
                stop=None;tp_p=None
                if cfg.trailing_stop_pct:
                    if t.direction=='long':
                        new_trail=h*(1-cfg.trailing_stop_pct)
                        t._trail_stop=max(t._trail_stop or 0,new_trail)
                        stop=t._trail_stop
                    else:
                        new_trail=l*(1+cfg.trailing_stop_pct)
                        t._trail_stop=min(t._trail_stop or 1e9,new_trail)
                        stop=t._trail_stop
                if cfg.stop_loss_pct and not stop:
                    stop=(t.entry_price*(1-cfg.stop_loss_pct) if t.direction=='long'
                          else t.entry_price*(1+cfg.stop_loss_pct))
                if cfg.take_profit_pct:
                    tp_p=(t.entry_price*(1+cfg.take_profit_pct) if t.direction=='long'
                          else t.entry_price*(1-cfg.take_profit_pct))
                exit_p=None;reason=''
                if cfg.use_ohlc_path:
                    exit_p,reason=_intra_bar_check(o,h,l,c,stop,tp_p,t.direction)
                if not exit_p and cfg.max_bars_in_trade and (i-t.entry_bar)>=cfg.max_bars_in_trade:
                    exit_p=c;reason='max_bars'
                if not exit_p:
                    if t.direction=='long' and sig==-1: exit_p=o;reason='signal_exit'
                    elif t.direction=='short' and sig==1: exit_p=o;reason='signal_exit'
                if exit_p:
                    slip=exit_p*cfg.slippage_pct
                    exit_p=exit_p-slip if t.direction=='long' else exit_p+slip
                    comm=exit_p*t.shares*cfg.commission
                    t.exit_price=exit_p;t.exit_bar=i;t.exit_date=dates[i]
                    t.commission+=comm;t.exit_reason=reason
                    proceeds=exit_p*t.shares*(1 if t.direction=='long' else -1)
                    cash+=proceeds-comm
                    if t.net_pnl>0: wins_pct.append(abs(t.pnl_pct))
                    else: losses_pct.append(abs(t.pnl_pct))
                    closed_trades.append(t)
                else:
                    still_open.append(t)
            open_trades=still_open

            if sig!=0 and len(open_trades)<cfg.max_positions:
                direction='long' if sig==1 else ('short' if cfg.allow_short else None)
                if direction:
                    entry_p=o*(1+cfg.slippage_pct) if direction=='long' else o*(1-cfg.slippage_pct)
                    atr_v=None
                    try:
                        from src.core.indicators import atr as ci
                        atr_v=ci(data['High'].iloc[:i],data['Low'].iloc[:i],data['Close'].iloc[:i],14).iloc[-1]
                    except: pass
                    eq=cash+sum((closes[i-1]-t.entry_price)*t.shares*(1 if t.direction=='long' else -1) for t in open_trades)
                    wr=len(wins_pct)/(len(wins_pct)+len(losses_pct)) if (wins_pct or losses_pct) else 0.5
                    aw=np.mean(wins_pct) if wins_pct else 1.0
                    al=np.mean(losses_pct) if losses_pct else 1.0
                    shares=int(max(1,_calc_shares(cfg,cash,eq if cfg.reinvest else cfg.initial_capital,entry_p,atr_v,wr,aw,al)))
                    if direction=='long' and entry_p*shares*(1+cfg.commission)<=cash:
                        comm=entry_p*shares*cfg.commission
                        cash-=entry_p*shares+comm
                        open_trades.append(_Trade(symbol,direction,i,entry_p,shares,comm,dates[i]))
                    elif direction=='short':
                        comm=entry_p*shares*cfg.commission
                        cash+=entry_p*shares-comm
                        open_trades.append(_Trade(symbol,direction,i,entry_p,shares,comm,dates[i]))

            mkt=sum((c-t.entry_price)*t.shares*(1 if t.direction=='long' else -1) for t in open_trades)
            equity_curve[i]=cash+mkt
            daily_ret[i]=(equity_curve[i]/equity_curve[i-1]-1) if equity_curve[i-1]!=0 else 0

        for t in open_trades:
            lc=closes[-1];comm=lc*t.shares*cfg.commission
            t.exit_price=lc;t.exit_bar=n-1;t.exit_date=dates[-1]
            t.commission+=comm;t.exit_reason='end_of_data';closed_trades.append(t)

        eq=pd.Series(equity_curve,index=dates,name='value')
        ret=pd.Series(daily_ret,index=dates,name='returns')
        return {
            'equity_curve':eq.to_frame(),'daily_returns':ret,
            'metrics':self._metrics(eq,ret,closed_trades,cfg.initial_capital,data),
            'trades_df':self._trades_df(closed_trades),
            'annual_breakdown':self._annual(eq,ret,closed_trades),
            'monthly_heatmap':self._monthly(ret),
        }

    def _metrics(self,eq,ret,trades,init,data):
        fin=eq.iloc[-1];tr=(fin/init-1)*100
        ny=(eq.index[-1]-eq.index[0]).days/365.25
        cagr=((fin/init)**(1/max(ny,0.01))-1)*100
        bh=(data['Close'].iloc[-1]/data['Close'].iloc[0]-1)*100
        vol=ret.std()*np.sqrt(252)*100
        dd=(eq.iloc[:,0]-eq.iloc[:,0].cummax())/eq.iloc[:,0].cummax()*100
        mdd=dd.min();avg_dd=dd[dd<0].mean() if (dd<0).any() else 0
        sh=(ret.mean()/ret.std()*np.sqrt(252)) if ret.std()>0 else 0
        neg=ret[ret<0];so=(ret.mean()/neg.std()*np.sqrt(252)) if len(neg)>1 else 0
        cal=cagr/abs(mdd) if mdd else 0
        ab=ret[ret>0];bl=ret[ret<=0]
        om=(ab.sum()/abs(bl.sum())) if bl.sum()!=0 else 999
        v95=float(np.percentile(ret.dropna(),5))*100
        v99=float(np.percentile(ret.dropna(),1))*100
        tc=sum(t.commission for t in trades);n=len(trades)
        ws=[t for t in trades if t.net_pnl>0];ls=[t for t in trades if t.net_pnl<=0]
        wr=len(ws)/n*100 if n else 0
        pf=sum(t.net_pnl for t in ws)/abs(sum(t.net_pnl for t in ls)) if ls and sum(t.net_pnl for t in ls)!=0 else 999
        aw=np.mean([t.pnl_pct for t in ws]) if ws else 0
        al=np.mean([t.pnl_pct for t in ls]) if ls else 0
        po=abs(aw/al) if al else 999;ev=wr/100*aw+(1-wr/100)*al
        sw=sl=cw=cl=0
        for t in trades:
            if t.net_pnl>0: cw+=1;cl=0
            else: cl+=1;cw=0
            sw=max(sw,cw);sl=max(sl,cl)
        s=lambda x: f"── {x} ──────────────────"
        return {
            s('Capital'):'','Capital inicial':f"${init:,.0f}",'Capital final':f"${fin:,.0f}",
            'Beneficio neto':f"${fin-init:+,.0f}",'Comisiones':f"${tc:,.2f}",
            s('Rendimiento'):'','Retorno total':f"{tr:+.2f}%",'CAGR':f"{cagr:+.2f}%",
            'Buy & Hold':f"{bh:+.2f}%",'Alpha vs B&H':f"{tr-bh:+.2f}%",'Volatilidad anual':f"{vol:.2f}%",
            s('Riesgo'):'','Max Drawdown':f"{mdd:.2f}%",'Avg Drawdown':f"{avg_dd:.2f}%",
            'Recovery Factor':f"{(tr/abs(mdd)) if mdd else 0:.2f}",'VaR 95%':f"{v95:.2f}%",'VaR 99%':f"{v99:.2f}%",
            s('Ratios'):'','Sharpe':f"{sh:.3f}",'Sortino':f"{so:.3f}",'Calmar':f"{cal:.3f}",'Omega':f"{om:.3f}",
            s('Trades'):'','Total':str(n),'Longs':str(sum(1 for t in trades if t.direction=='long')),
            'Shorts':str(sum(1 for t in trades if t.direction=='short')),
            'Win Rate':f"{wr:.1f}%",'Profit Factor':f"{pf:.3f}",'Payoff Ratio':f"{po:.3f}",
            'Expected Value':f"{ev:.3f}%",'Avg ganancia':f"{aw:.2f}%",'Avg pérdida':f"{al:.2f}%",
            'Mayor ganancia':f"{max((t.pnl_pct for t in ws),default=0):.2f}%",
            'Mayor pérdida':f"{min((t.pnl_pct for t in ls),default=0):.2f}%",
            'Racha ganadora':str(sw),'Racha perdedora':str(sl),
        }

    def _trades_df(self,trades):
        if not trades: return pd.DataFrame()
        return pd.DataFrame([{
            'Símbolo':t.symbol,'Dir':'📈 Long' if t.direction=='long' else '📉 Short',
            'Apertura':str(t.entry_date)[:10],'Cierre':str(t.exit_date)[:10],
            'Precio entrada':f"{t.entry_price:.4f}",
            'Precio salida':f"{t.exit_price:.4f}" if t.exit_price else '—',
            'Acciones':int(t.shares),'P&L $':f"{t.net_pnl:+.2f}",'P&L %':f"{t.pnl_pct:.2f}",
            'Comisión':f"{t.commission:.2f}",'Salida':t.exit_reason,
            'Resultado':'✅ Win' if t.net_pnl>0 else '❌ Loss',
        } for t in trades])

    def _annual(self,eq,ret,trades):
        rows=[]
        for yr in sorted(eq.index.year.unique()):
            m=eq.index.year==yr;ey=eq.iloc[:,0][m];ry=ret[m]
            if len(ey)<2: continue
            yr_r=(ey.iloc[-1]/ey.iloc[0]-1)*100
            dd=(ey-ey.cummax())/ey.cummax()*100;mdd=dd.min()
            sh=(ry.mean()/ry.std()*np.sqrt(252)) if ry.std()>0 else 0
            ty=[t for t in trades if t.entry_date and t.entry_date.year==yr]
            n=len(ty);w=sum(1 for t in ty if t.net_pnl>0);wr=w/n*100 if n else 0
            wp=[t.net_pnl for t in ty if t.net_pnl>0];lp=[t.net_pnl for t in ty if t.net_pnl<=0]
            pf=sum(wp)/abs(sum(lp)) if lp and sum(lp)!=0 else 999
            rows.append({'Año':yr,'Retorno':f"{yr_r:+.1f}%",'Max DD':f"{mdd:.1f}%",
                         'Sharpe':f"{sh:.2f}",'Trades':n,'Win%':f"{wr:.0f}%",
                         'Profit Factor':f"{pf:.2f}" if pf!=999 else "∞",'_ret':yr_r})
        return pd.DataFrame(rows)

    def _monthly(self,ret):
        m=(1+ret).resample('ME').prod()-1
        m*=100
        df=pd.DataFrame({'r':m,'y':m.index.year,'mo':m.index.month})
        try: return df.pivot(index='y',columns='mo',values='r')
        except: return pd.DataFrame()

    def _empty(self):
        return {'equity_curve':pd.DataFrame(),'daily_returns':pd.Series(dtype=float),
                'metrics':{},'trades_df':pd.DataFrame(),
                'annual_breakdown':pd.DataFrame(),'monthly_heatmap':pd.DataFrame()}
