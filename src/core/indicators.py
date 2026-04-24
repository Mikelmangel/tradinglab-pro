"""TradingLab Pro — Indicators (40+). Pure NumPy/Pandas, no TA-Lib."""
from __future__ import annotations
import numpy as np
import pandas as pd
import inspect

def _ema(s,p): return s.ewm(span=p,adjust=False).mean()
def _sma(s,p): return s.rolling(p).mean()
def _wma(s,p):
    w=np.arange(1,p+1,dtype=float)
    return s.rolling(p).apply(lambda x:np.dot(x,w)/w.sum(),raw=True)
def _std(s,p): return s.rolling(p).std()
def _tr(h,l,c):
    return pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)

# ── TREND ─────────────────────────────────────────────────────────────────
def sma(close,period=20):   return _sma(close,period).rename(f'SMA_{period}')
def ema(close,period=20):   return _ema(close,period).rename(f'EMA_{period}')
def wma(close,period=20):   return _wma(close,period).rename(f'WMA_{period}')
def dema(close,period=20):
    e=_ema(close,period); return (2*e-_ema(e,period)).rename(f'DEMA_{period}')
def tema(close,period=20):
    e1=_ema(close,period);e2=_ema(e1,period);e3=_ema(e2,period)
    return (3*e1-3*e2+e3).rename(f'TEMA_{period}')
def hma(close,period=14):
    h=max(2,period//2);sq=max(2,int(np.sqrt(period)))
    return _wma(2*_wma(close,h)-_wma(close,period),sq).rename(f'HMA_{period}')
def zlema(close,period=21):
    lag=max(1,(period-1)//2)
    return _ema(close+(close-close.shift(lag)),period).rename(f'ZLEMA_{period}')
def vwma(close,volume,period=20):
    return ((close*volume).rolling(period).sum()/volume.rolling(period).sum()).rename(f'VWMA_{period}')
def alma(close,period=21,sigma=6.0,offset=0.85):
    m=offset*(period-1);s=period/sigma
    w=np.array([np.exp(-0.5*((i-m)/s)**2) for i in range(period)]);w/=w.sum()
    return close.rolling(period).apply(lambda x:np.dot(x,w),raw=True).rename(f'ALMA_{period}')
def t3(close,period=5,vf=0.7):
    c1,c2,c3,c4=-(vf**3),3*vf**2+3*vf**3,-6*vf**2-3*vf-3*vf**3,1+3*vf+vf**3+3*vf**2
    e1=_ema(close,period);e2=_ema(e1,period);e3=_ema(e2,period)
    e4=_ema(e3,period);e5=_ema(e4,period);e6=_ema(e5,period)
    return (c1*e6+c2*e5+c3*e4+c4*e3).rename(f'T3_{period}')

# ── OSCILLATORS ───────────────────────────────────────────────────────────
def rsi(close,period=14):
    d=close.diff();g=d.clip(lower=0).ewm(com=period-1,adjust=False).mean()
    l=(-d.clip(upper=0)).ewm(com=period-1,adjust=False).mean()
    return (100-100/(1+g/l.replace(0,np.nan))).rename(f'RSI_{period}')
def stochastic(high,low,close,k=14,d=3,smooth_k=3):
    lo=low.rolling(k).min();hi=high.rolling(k).max()
    ks=((close-lo)/(hi-lo).replace(0,np.nan)*100).rolling(smooth_k).mean()
    return pd.DataFrame({'STOCH_K':ks,'STOCH_D':ks.rolling(d).mean()},index=close.index)
def stoch_rsi(close,period=14,k=3,d=3):
    r=rsi(close,period);lo=r.rolling(period).min();hi=r.rolling(period).max()
    ks=((r-lo)/(hi-lo).replace(0,np.nan)*100).rolling(k).mean()
    return pd.DataFrame({'SRSI_K':ks,'SRSI_D':ks.rolling(d).mean()},index=close.index)
def cci(high,low,close,period=20):
    tp=(high+low+close)/3;sma_=tp.rolling(period).mean()
    mad=tp.rolling(period).apply(lambda x:np.mean(np.abs(x-x.mean())),raw=True)
    return ((tp-sma_)/(0.015*mad)).rename(f'CCI_{period}')
def williams_r(high,low,close,period=14):
    return (100*(close-high.rolling(period).max())/(high.rolling(period).max()-low.rolling(period).min()).replace(0,np.nan)).rename(f'WILLR_{period}')
def mfi(high,low,close,volume,period=14):
    tp=(high+low+close)/3;mf=tp*volume
    pos=mf.where(tp>tp.shift(1),0).rolling(period).sum()
    neg=mf.where(tp<tp.shift(1),0).rolling(period).sum()
    return (100-100/(1+pos/neg.replace(0,np.nan))).rename(f'MFI_{period}')
def roc(close,period=12): return (100*(close/close.shift(period)-1)).rename(f'ROC_{period}')
def momentum(close,period=10): return (close-close.shift(period)).rename(f'MOM_{period}')
def trix(close,period=15):
    e=_ema(_ema(_ema(close,period),period),period)
    return (100*e.diff()/e.shift(1)).rename(f'TRIX_{period}')
def cmo(close,period=14):
    d=close.diff()
    up=d.clip(lower=0).rolling(period).sum();dn=(-d.clip(upper=0)).rolling(period).sum()
    return (100*(up-dn)/(up+dn).replace(0,np.nan)).rename(f'CMO_{period}')
def awesome_oscillator(high,low,fast=5,slow=34):
    mp=(high+low)/2
    return (_sma(mp,fast)-_sma(mp,slow)).rename('AO')
def ultimate_oscillator(high,low,close,p1=7,p2=14,p3=28):
    tr=_tr(high,low,close)
    bp=close-pd.concat([low,close.shift(1)],axis=1).min(axis=1)
    avg=lambda p:bp.rolling(p).sum()/tr.rolling(p).sum()
    return (100*(4*avg(p1)+2*avg(p2)+avg(p3))/7).rename('UO')

# ── VOLATILITY ────────────────────────────────────────────────────────────
def atr(high,low,close,period=14):
    return _tr(high,low,close).ewm(com=period-1,adjust=False).mean().rename(f'ATR_{period}')
def bollinger_bands(close,period=20,std_dev=2.0):
    mid=_sma(close,period);std=_std(close,period)
    upper=mid+std_dev*std;lower=mid-std_dev*std
    return pd.DataFrame({'BB_UPPER':upper,'BB_MID':mid,'BB_LOWER':lower,
        'BB_PCT_B':(close-lower)/(upper-lower).replace(0,np.nan),
        'BB_BW':(upper-lower)/mid.replace(0,np.nan)*100},index=close.index)
def keltner_channel(high,low,close,period=20,mult=2.0):
    mid=_ema(close,period);a=atr(high,low,close,period)
    return pd.DataFrame({'KC_UPPER':mid+mult*a,'KC_MID':mid,'KC_LOWER':mid-mult*a},index=close.index)
def donchian_channel(high,low,period=20):
    u=high.rolling(period).max();l=low.rolling(period).min()
    return pd.DataFrame({'DC_UPPER':u,'DC_MID':(u+l)/2,'DC_LOWER':l},index=high.index)
def historical_volatility(close,period=21,annualize=True):
    hv=np.log(close/close.shift(1)).rolling(period).std()
    return (hv*np.sqrt(252)*100 if annualize else hv).rename(f'HV_{period}')
def chaikin_volatility(high,low,period=10):
    e=_ema(high-low,period)
    return (100*(e-e.shift(period))/e.shift(period)).rename(f'CHVOL_{period}')

# ── VOLUME ────────────────────────────────────────────────────────────────
def obv(close,volume):
    return (np.sign(close.diff()).fillna(0)*volume).cumsum().rename('OBV')
def vwap(high,low,close,volume,period=20):
    tp=(high+low+close)/3
    return ((tp*volume).rolling(period).sum()/volume.rolling(period).sum()).rename(f'VWAP_{period}')
def cmf(high,low,close,volume,period=20):
    mf=((close-low)-(high-close))/(high-low).replace(0,np.nan)
    return ((mf*volume).rolling(period).sum()/volume.rolling(period).sum()).rename(f'CMF_{period}')
def ad_line(high,low,close,volume):
    mf=((close-low)-(high-close))/(high-low).replace(0,np.nan)
    return (mf*volume).cumsum().rename('ADL')
def force_index(close,volume,period=13):
    return _ema(close.diff()*volume,period).rename(f'FI_{period}')
def pvt(close,volume):
    return ((close.diff()/close.shift(1))*volume).cumsum().rename('PVT')

# ── TREND STRENGTH ────────────────────────────────────────────────────────
def adx(high,low,close,period=14):
    tr=_tr(high,low,close)
    pdm=(high-high.shift(1)).clip(lower=0)
    ndm=(low.shift(1)-low).clip(lower=0)
    pdm=pdm.where(pdm>ndm,0);ndm=ndm.where(ndm>pdm,0)
    atr_=tr.ewm(com=period-1,adjust=False).mean()
    pdi=100*pdm.ewm(com=period-1,adjust=False).mean()/atr_.replace(0,np.nan)
    ndi=100*ndm.ewm(com=period-1,adjust=False).mean()/atr_.replace(0,np.nan)
    dx=100*(pdi-ndi).abs()/(pdi+ndi).replace(0,np.nan)
    return pd.DataFrame({'ADX':dx.ewm(com=period-1,adjust=False).mean(),'DI_PLUS':pdi,'DI_MINUS':ndi},index=close.index)
def aroon(high,low,period=25):
    def sm(x): return (period-np.argmax(x[::-1]))/period*100
    def sm2(x): return (period-np.argmin(x[::-1]))/period*100
    up=high.rolling(period+1).apply(sm,raw=True)
    dn=low.rolling(period+1).apply(sm2,raw=True)
    return pd.DataFrame({'AROON_UP':up,'AROON_DOWN':dn,'AROON_OSC':up-dn},index=high.index)
def psar(high,low,close,af_start=0.02,af_step=0.02,af_max=0.2):
    n=len(close);sar=np.full(n,np.nan);ep=np.full(n,np.nan)
    af=np.full(n,af_start);bull=np.full(n,True,dtype=bool)
    sar[0]=low.iloc[0];ep[0]=high.iloc[0]
    for i in range(1,n):
        pb=bull[i-1]
        if pb:
            sar[i]=sar[i-1]+af[i-1]*(ep[i-1]-sar[i-1])
            sar[i]=min(sar[i],low.iloc[i-1],low.iloc[max(0,i-2)])
            if low.iloc[i]<sar[i]: bull[i]=False;sar[i]=ep[i-1];ep[i]=low.iloc[i];af[i]=af_start
            else: bull[i]=True;ep[i]=max(ep[i-1],high.iloc[i]);af[i]=min(af_max,af[i-1]+af_step if high.iloc[i]>ep[i-1] else af[i-1])
        else:
            sar[i]=sar[i-1]+af[i-1]*(ep[i-1]-sar[i-1])
            sar[i]=max(sar[i],high.iloc[i-1],high.iloc[max(0,i-2)])
            if high.iloc[i]>sar[i]: bull[i]=True;sar[i]=ep[i-1];ep[i]=high.iloc[i];af[i]=af_start
            else: bull[i]=False;ep[i]=min(ep[i-1],low.iloc[i]);af[i]=min(af_max,af[i-1]+af_step if low.iloc[i]<ep[i-1] else af[i-1])
    return pd.DataFrame({'PSAR':sar,'PSAR_BULL':bull.astype(int)},index=close.index)
def supertrend(high,low,close,period=10,mult=3.0):
    a=atr(high,low,close,period);hl2=(high+low)/2
    ub=hl2+mult*a;lb=hl2-mult*a
    upper=ub.copy();lower=lb.copy()
    trend=pd.Series(1,index=close.index,dtype=float)
    for i in range(1,len(close)):
        upper.iloc[i]=ub.iloc[i] if ub.iloc[i]<upper.iloc[i-1] or close.iloc[i-1]>upper.iloc[i-1] else upper.iloc[i-1]
        lower.iloc[i]=lb.iloc[i] if lb.iloc[i]>lower.iloc[i-1] or close.iloc[i-1]<lower.iloc[i-1] else lower.iloc[i-1]
        trend.iloc[i]=(-1 if close.iloc[i]<lower.iloc[i] else 1) if trend.iloc[i-1]==1 else (1 if close.iloc[i]>upper.iloc[i] else -1)
    st=lower.where(trend==1,upper)
    return pd.DataFrame({'ST':st,'ST_TREND':trend,'ST_UPPER':upper,'ST_LOWER':lower},index=close.index)
def macd(close,fast=12,slow=26,signal=9):
    m=_ema(close,fast)-_ema(close,slow);s=_ema(m,signal)
    return pd.DataFrame({'MACD':m,'MACD_SIG':s,'MACD_HIST':m-s},index=close.index)
def ichimoku(high,low,close,tenkan=9,kijun=26,senkou_b=52,chikou=26):
    def mid(h,l,p): return (h.rolling(p).max()+l.rolling(p).min())/2
    ten=mid(high,low,tenkan);kij=mid(high,low,kijun)
    return pd.DataFrame({'ICH_TENKAN':ten,'ICH_KIJUN':kij,
        'ICH_SENKOU_A':((ten+kij)/2).shift(kijun),
        'ICH_SENKOU_B':mid(high,low,senkou_b).shift(kijun),
        'ICH_CHIKOU':close.shift(-chikou)},index=close.index)
def pivot_points(high,low,close):
    pp=(high.shift(1)+low.shift(1)+close.shift(1))/3
    return pd.DataFrame({'PP':pp,'R1':2*pp-low.shift(1),'S1':2*pp-high.shift(1),
        'R2':pp+(high.shift(1)-low.shift(1)),'S2':pp-(high.shift(1)-low.shift(1)),
        'R3':high.shift(1)+2*(pp-low.shift(1)),'S3':low.shift(1)-2*(high.shift(1)-pp)},index=close.index)
def heikin_ashi(open_,high,low,close):
    hc=(open_+high+low+close)/4;ho=pd.Series(np.nan,index=open_.index)
    ho.iloc[0]=(open_.iloc[0]+close.iloc[0])/2
    for i in range(1,len(open_)): ho.iloc[i]=(ho.iloc[i-1]+hc.iloc[i-1])/2
    hh=pd.concat([high,ho,hc],axis=1).max(axis=1);hl=pd.concat([low,ho,hc],axis=1).min(axis=1)
    return pd.DataFrame({'HA_OPEN':ho,'HA_HIGH':hh,'HA_LOW':hl,'HA_CLOSE':hc},index=close.index)
def zscore(close,period=20):
    mu=_sma(close,period);std=_std(close,period)
    return ((close-mu)/std.replace(0,np.nan)).rename(f'ZSCORE_{period}')
def linear_regression(close,period=14):
    x=np.arange(period);xm=x.mean()
    def lr(y):
        ym=y.mean();sl=np.sum((x-xm)*(y-ym))/np.sum((x-xm)**2)
        yh=sl*x+(ym-sl*xm);ss=np.sum((y-yh)**2);st=np.sum((y-ym)**2)
        return yh[-1],sl,1-ss/st if st>0 else 1.0
    v=close.rolling(period).apply(lambda y:lr(y)[0],raw=True)
    s=close.rolling(period).apply(lambda y:lr(y)[1],raw=True)
    r=close.rolling(period).apply(lambda y:lr(y)[2],raw=True)
    return pd.DataFrame({'LR_VAL':v,'LR_SLOPE':s,'LR_R2':r},index=close.index)
def efficiency_ratio(close,period=10):
    d=(close-close.shift(period)).abs();n=close.diff().abs().rolling(period).sum()
    return (d/n.replace(0,np.nan)).rename(f'ER_{period}')

# ── REGISTRY ─────────────────────────────────────────────────────────────
INDICATOR_REGISTRY = {
    'SMA':{'func':sma,'params':{'period':20},'cat':'Trend','overlay':True},
    'EMA':{'func':ema,'params':{'period':20},'cat':'Trend','overlay':True},
    'WMA':{'func':wma,'params':{'period':20},'cat':'Trend','overlay':True},
    'DEMA':{'func':dema,'params':{'period':20},'cat':'Trend','overlay':True},
    'TEMA':{'func':tema,'params':{'period':20},'cat':'Trend','overlay':True},
    'HMA':{'func':hma,'params':{'period':14},'cat':'Trend','overlay':True},
    'ZLEMA':{'func':zlema,'params':{'period':21},'cat':'Trend','overlay':True},
    'VWMA':{'func':vwma,'params':{'period':20},'cat':'Trend','overlay':True},
    'ALMA':{'func':alma,'params':{'period':21},'cat':'Trend','overlay':True},
    'T3':{'func':t3,'params':{'period':5},'cat':'Trend','overlay':True},
    'RSI':{'func':rsi,'params':{'period':14},'cat':'Oscillator','overlay':False},
    'Stochastic':{'func':stochastic,'params':{'k':14,'d':3},'cat':'Oscillator','overlay':False},
    'Stoch RSI':{'func':stoch_rsi,'params':{'period':14},'cat':'Oscillator','overlay':False},
    'CCI':{'func':cci,'params':{'period':20},'cat':'Oscillator','overlay':False},
    'Williams %R':{'func':williams_r,'params':{'period':14},'cat':'Oscillator','overlay':False},
    'MFI':{'func':mfi,'params':{'period':14},'cat':'Oscillator','overlay':False},
    'ROC':{'func':roc,'params':{'period':12},'cat':'Oscillator','overlay':False},
    'Momentum':{'func':momentum,'params':{'period':10},'cat':'Oscillator','overlay':False},
    'TRIX':{'func':trix,'params':{'period':15},'cat':'Oscillator','overlay':False},
    'CMO':{'func':cmo,'params':{'period':14},'cat':'Oscillator','overlay':False},
    'Awesome Oscillator':{'func':awesome_oscillator,'params':{'fast':5,'slow':34},'cat':'Oscillator','overlay':False},
    'Ultimate Oscillator':{'func':ultimate_oscillator,'params':{'p1':7,'p2':14,'p3':28},'cat':'Oscillator','overlay':False},
    'ATR':{'func':atr,'params':{'period':14},'cat':'Volatility','overlay':False},
    'Bollinger Bands':{'func':bollinger_bands,'params':{'period':20,'std_dev':2.0},'cat':'Volatility','overlay':True},
    'Keltner Channel':{'func':keltner_channel,'params':{'period':20,'mult':2.0},'cat':'Volatility','overlay':True},
    'Donchian Channel':{'func':donchian_channel,'params':{'period':20},'cat':'Volatility','overlay':True},
    'Hist Volatility':{'func':historical_volatility,'params':{'period':21},'cat':'Volatility','overlay':False},
    'Chaikin Vol':{'func':chaikin_volatility,'params':{'period':10},'cat':'Volatility','overlay':False},
    'OBV':{'func':obv,'params':{},'cat':'Volume','overlay':False},
    'VWAP':{'func':vwap,'params':{'period':20},'cat':'Volume','overlay':True},
    'CMF':{'func':cmf,'params':{'period':20},'cat':'Volume','overlay':False},
    'A/D Line':{'func':ad_line,'params':{},'cat':'Volume','overlay':False},
    'Force Index':{'func':force_index,'params':{'period':13},'cat':'Volume','overlay':False},
    'PVT':{'func':pvt,'params':{},'cat':'Volume','overlay':False},
    'ADX':{'func':adx,'params':{'period':14},'cat':'Trend Strength','overlay':False},
    'Aroon':{'func':aroon,'params':{'period':25},'cat':'Trend Strength','overlay':False},
    'Parabolic SAR':{'func':psar,'params':{'af_start':0.02,'af_max':0.2},'cat':'Trend Strength','overlay':True},
    'SuperTrend':{'func':supertrend,'params':{'period':10,'mult':3.0},'cat':'Trend Strength','overlay':True},
    'MACD':{'func':macd,'params':{'fast':12,'slow':26,'signal':9},'cat':'MACD','overlay':False},
    'Ichimoku':{'func':ichimoku,'params':{'tenkan':9,'kijun':26,'senkou_b':52},'cat':'Complex','overlay':True},
    'Pivot Points':{'func':pivot_points,'params':{},'cat':'Complex','overlay':True},
    'Z-Score':{'func':zscore,'params':{'period':20},'cat':'Statistical','overlay':False},
    'Linear Regression':{'func':linear_regression,'params':{'period':14},'cat':'Statistical','overlay':False},
    'Efficiency Ratio':{'func':efficiency_ratio,'params':{'period':10},'cat':'Statistical','overlay':False},
}

def compute(name, data, **override):
    if name not in INDICATOR_REGISTRY:
        raise ValueError(f"Indicator '{name}' not found")
    info=INDICATOR_REGISTRY[name];func=info['func'];params={**info['params'],**override}
    sig=inspect.signature(func)
    kw={}
    sm={'close':data['Close'],'high':data['High'],'low':data['Low'],'open_':data['Open'],'volume':data['Volume']}
    for pn in sig.parameters:
        if pn in sm: kw[pn]=sm[pn]
        elif pn in params: kw[pn]=params[pn]
    r=func(**kw)
    return r.to_frame() if isinstance(r,pd.Series) else r

def list_by_category():
    cats={}
    for n,info in INDICATOR_REGISTRY.items():
        cats.setdefault(info['cat'],[]).append(n)
    return cats
