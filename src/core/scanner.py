"""TradingLab Pro — Market Scanner."""
import numpy as np, pandas as pd

BUILT_IN_SCANS = {
    'RSI Sobreventa (<30)': '''
def scan_condition(data):
    c=data['Close']; d=c.diff(); g=d.clip(lower=0).ewm(com=13,adjust=False).mean(); l=(-d.clip(upper=0)).ewm(com=13,adjust=False).mean()
    rsi=100-100/(1+g/l.replace(0,float('nan')))
    return float(rsi.iloc[-1]) < 30
''',
    'RSI Sobrecompra (>70)': '''
def scan_condition(data):
    c=data['Close']; d=c.diff(); g=d.clip(lower=0).ewm(com=13,adjust=False).mean(); l=(-d.clip(upper=0)).ewm(com=13,adjust=False).mean()
    rsi=100-100/(1+g/l.replace(0,float('nan')))
    return float(rsi.iloc[-1]) > 70
''',
    'SMA Cross Alcista (10>30)': '''
def scan_condition(data):
    c=data['Close']
    return float(c.rolling(10).mean().iloc[-1]) > float(c.rolling(30).mean().iloc[-1]) and float(c.rolling(10).mean().iloc[-2]) <= float(c.rolling(30).mean().iloc[-2])
''',
    'SMA Cross Bajista (10<30)': '''
def scan_condition(data):
    c=data['Close']
    return float(c.rolling(10).mean().iloc[-1]) < float(c.rolling(30).mean().iloc[-1]) and float(c.rolling(10).mean().iloc[-2]) >= float(c.rolling(30).mean().iloc[-2])
''',
    'MACD Cross Alcista': '''
def scan_condition(data):
    c=data['Close']; m=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean(); s=m.ewm(span=9,adjust=False).mean()
    return float(m.iloc[-1])>float(s.iloc[-1]) and float(m.iloc[-2])<=float(s.iloc[-2])
''',
    'MACD Cross Bajista': '''
def scan_condition(data):
    c=data['Close']; m=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean(); s=m.ewm(span=9,adjust=False).mean()
    return float(m.iloc[-1])<float(s.iloc[-1]) and float(m.iloc[-2])>=float(s.iloc[-2])
''',
    'Bollinger Band Superior Break': '''
def scan_condition(data):
    c=data['Close']; mid=c.rolling(20).mean(); std=c.rolling(20).std()
    return float(c.iloc[-1]) > float(mid.iloc[-1]+2*std.iloc[-1])
''',
    'Bollinger Band Inferior Break': '''
def scan_condition(data):
    c=data['Close']; mid=c.rolling(20).mean(); std=c.rolling(20).std()
    return float(c.iloc[-1]) < float(mid.iloc[-1]-2*std.iloc[-1])
''',
    'Donchian Breakout 20': '''
def scan_condition(data):
    return float(data['Close'].iloc[-1]) >= float(data['High'].rolling(20).max().iloc[-2])
''',
    'SuperTrend Alcista': '''
def scan_condition(data):
    h=data['High'];l=data['Low'];c=data['Close']
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(com=9,adjust=False).mean();hl2=(h+l)/2
    ub=hl2+3*atr;lb=hl2-3*atr
    upper=ub.copy();lower=lb.copy()
    for i in range(1,len(c)):
        upper.iloc[i]=min(ub.iloc[i],upper.iloc[i-1]) if c.iloc[i-1]<=upper.iloc[i-1] else ub.iloc[i]
        lower.iloc[i]=max(lb.iloc[i],lower.iloc[i-1]) if c.iloc[i-1]>=lower.iloc[i-1] else lb.iloc[i]
    trend=pd.Series(1,index=c.index)
    for i in range(1,len(c)):
        trend.iloc[i]=1 if c.iloc[i]>upper.iloc[i] else (-1 if c.iloc[i]<lower.iloc[i] else trend.iloc[i-1])
    return int(trend.iloc[-1])==1
''',
    'ADX Tendencia Fuerte (>25)': '''
def scan_condition(data):
    h=data['High'];l=data['Low'];c=data['Close']
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    pdm=(h-h.shift(1)).clip(lower=0);ndm=(l.shift(1)-l).clip(lower=0)
    pdm=pdm.where(pdm>ndm,0);ndm=ndm.where(ndm>pdm,0)
    atr=tr.ewm(com=13,adjust=False).mean()
    pdi=100*pdm.ewm(com=13,adjust=False).mean()/atr.replace(0,float('nan'))
    ndi=100*ndm.ewm(com=13,adjust=False).mean()/atr.replace(0,float('nan'))
    dx=100*(pdi-ndi).abs()/(pdi+ndi).replace(0,float('nan'))
    adx=dx.ewm(com=13,adjust=False).mean()
    return float(adx.iloc[-1]) > 25
''',
    'Volumen 2x Promedio': '''
def scan_condition(data):
    v=data['Volume']
    return float(v.iloc[-1]) > float(v.rolling(20).mean().iloc[-1]*2)
''',
    'Precio Máximo 52 semanas': '''
def scan_condition(data):
    c=data['Close']
    return float(c.iloc[-1]) >= float(c.rolling(252).max().iloc[-1]*0.99)
''',
    'Condición personalizada': '''
def scan_condition(data):
    # Escribe tu condición aquí
    # data tiene: Open, High, Low, Close, Volume
    # Retorna True si el símbolo cumple la condición
    close = data['Close']
    sma20 = close.rolling(20).mean()
    return float(close.iloc[-1]) > float(sma20.iloc[-1])
''',
}

class MarketScanner:
    def run(self,datasets,code,progress_cb=None):
        results=[]
        syms=list(datasets.keys());total=len(syms)
        ns={'pd':pd,'np':np}
        try: exec(code,ns)
        except Exception as e: return pd.DataFrame()
        fn=ns.get('scan_condition')
        if fn is None: return pd.DataFrame()
        for i,sym in enumerate(syms):
            data=datasets[sym]
            if data is None or len(data)<30: continue
            try:
                match=fn(data)
                if match:
                    c=data['Close'].iloc[-1]
                    r1=(c/data['Close'].iloc[-2]-1)*100 if len(data)>1 else 0
                    r5=(c/data['Close'].iloc[-6]-1)*100 if len(data)>5 else 0
                    r20=(c/data['Close'].iloc[-21]-1)*100 if len(data)>20 else 0
                    d=data['Close'].diff(); g=d.clip(lower=0).ewm(com=13,adjust=False).mean()
                    ll=(-d.clip(upper=0)).ewm(com=13,adjust=False).mean()
                    rsi_v=float((100-100/(1+g/ll.replace(0,float('nan')))).iloc[-1])
                    tr=pd.concat([data['High']-data['Low'],(data['High']-data['Close'].shift(1)).abs(),(data['Low']-data['Close'].shift(1)).abs()],axis=1).max(axis=1)
                    atr_v=float(tr.ewm(com=13,adjust=False).mean().iloc[-1])
                    hi52=data['Close'].rolling(min(252,len(data))).max().iloc[-1]
                    lo52=data['Close'].rolling(min(252,len(data))).min().iloc[-1]
                    rng52=(c-lo52)/(hi52-lo52)*100 if hi52!=lo52 else 50
                    results.append({'Símbolo':sym,'Precio':f"{c:.2f}",'1D%':f"{r1:+.2f}",
                                    '5D%':f"{r5:+.2f}",'20D%':f"{r20:+.2f}",
                                    'RSI':f"{rsi_v:.1f}",'ATR':f"{atr_v:.4f}",
                                    'Volumen':f"{data['Volume'].iloc[-1]:,.0f}",
                                    'Rango 52W%':f"{rng52:.1f}",'Fecha':str(data.index[-1])[:10]})
            except: pass
            if progress_cb: progress_cb(int((i+1)/total*100),sym)
        return pd.DataFrame(results) if results else pd.DataFrame()
