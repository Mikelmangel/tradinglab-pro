"""TradingLab Pro — Fundamentals (yfinance)."""
from __future__ import annotations
import pandas as pd, numpy as np

FUNDAMENTAL_FIELDS = {
    'Valoración': ['trailingPE','forwardPE','priceToBook','priceToSalesTrailingTwelvemonths',
                   'enterpriseToEbitda','pegRatio','enterpriseValue','marketCap'],
    'Rentabilidad': ['returnOnEquity','returnOnAssets','profitMargins','grossMargins',
                     'operatingMargins','ebitdaMargins'],
    'Crecimiento': ['revenueGrowth','earningsGrowth','earningsQuarterlyGrowth'],
    'Deuda': ['debtToEquity','currentRatio','quickRatio','totalDebt','totalCash'],
    'Dividendos': ['dividendYield','payoutRatio','trailingAnnualDividendRate','fiveYearAvgDividendYield'],
    'Analistas': ['targetMeanPrice','targetHighPrice','targetLowPrice','recommendationMean',
                  'numberOfAnalystOpinions'],
    'Empresa': ['longName','sector','industry','country','fullTimeEmployees',
                'website','longBusinessSummary'],
}

LABELS = {
    'trailingPE':'P/E TTM','forwardPE':'P/E Forward','priceToBook':'P/B',
    'priceToSalesTrailingTwelvemonths':'P/S','enterpriseToEbitda':'EV/EBITDA',
    'pegRatio':'PEG','enterpriseValue':'EV','marketCap':'Market Cap',
    'returnOnEquity':'ROE','returnOnAssets':'ROA','profitMargins':'Net Margin',
    'grossMargins':'Gross Margin','operatingMargins':'Operating Margin','ebitdaMargins':'EBITDA Margin',
    'revenueGrowth':'Revenue Growth','earningsGrowth':'Earnings Growth',
    'earningsQuarterlyGrowth':'EPS Growth QoQ','debtToEquity':'Debt/Equity',
    'currentRatio':'Current Ratio','quickRatio':'Quick Ratio',
    'totalDebt':'Total Debt','totalCash':'Total Cash',
    'dividendYield':'Dividend Yield','payoutRatio':'Payout Ratio',
    'trailingAnnualDividendRate':'Annual Dividend','fiveYearAvgDividendYield':'5Y Avg Yield',
    'targetMeanPrice':'Target Price (mean)','targetHighPrice':'Target (high)',
    'targetLowPrice':'Target (low)','recommendationMean':'Recommendation',
    'numberOfAnalystOpinions':'# Analysts',
    'longName':'Nombre','sector':'Sector','industry':'Industria',
    'country':'País','fullTimeEmployees':'Empleados',
    'website':'Web','longBusinessSummary':'Descripción',
}

def _fmt(k,v):
    if v is None: return 'N/A'
    pct_keys={'returnOnEquity','returnOnAssets','profitMargins','grossMargins','operatingMargins',
               'ebitdaMargins','revenueGrowth','earningsGrowth','earningsQuarterlyGrowth',
               'dividendYield','payoutRatio','fiveYearAvgDividendYield'}
    big_keys={'enterpriseValue','marketCap','totalDebt','totalCash'}
    if k in pct_keys and isinstance(v,(int,float)): return f"{v*100:.2f}%"
    if k in big_keys and isinstance(v,(int,float)):
        if v>=1e12: return f"${v/1e12:.2f}T"
        if v>=1e9:  return f"${v/1e9:.2f}B"
        if v>=1e6:  return f"${v/1e6:.2f}M"
        return f"${v:,.0f}"
    if isinstance(v,float): return f"{v:.4f}"
    return str(v)

def get_fundamentals(symbol: str) -> dict | None:
    try:
        import yfinance as yf
        t=yf.Ticker(symbol)
        info=t.info
        if not info: return None
        result: dict[str, dict[str, str]] = {}
        for cat,fields in FUNDAMENTAL_FIELDS.items():
            result[cat]={}
            for f in fields:
                v=info.get(f)
                result[cat][LABELS.get(f,f)]=_fmt(f,v)
        return result
    except Exception as e:
        return {'Error':{'Mensaje':str(e)}}

def get_financials(symbol: str) -> dict:
    try:
        import yfinance as yf
        t=yf.Ticker(symbol)
        return {'income':t.financials,'balance':t.balance_sheet,'cashflow':t.cashflow,
                'quarterly':t.quarterly_financials}
    except: return {}

def get_analyst_upgrades(symbol: str) -> pd.DataFrame:
    try:
        import yfinance as yf
        t=yf.Ticker(symbol)
        return t.upgrades_downgrades if hasattr(t,'upgrades_downgrades') else pd.DataFrame()
    except: return pd.DataFrame()

def fundamental_score(info: dict) -> tuple[float,str]:
    """Score 0-100 based on fundamentals."""
    score=50.0;reasons=[]
    raw=info  # flat dict
    pe=raw.get('trailingPE')
    if pe and isinstance(pe,(int,float)):
        if pe<15: score+=10;reasons.append("P/E bajo (<15)")
        elif pe>40: score-=10;reasons.append("P/E alto (>40)")
    roe=raw.get('returnOnEquity')
    if roe and isinstance(roe,(int,float)):
        if roe>0.15: score+=10;reasons.append("ROE alto (>15%)")
        elif roe<0: score-=10;reasons.append("ROE negativo")
    de=raw.get('debtToEquity')
    if de and isinstance(de,(int,float)):
        if de<50: score+=5;reasons.append("Deuda baja")
        elif de>200: score-=10;reasons.append("Deuda alta")
    gr=raw.get('revenueGrowth')
    if gr and isinstance(gr,(int,float)):
        if gr>0.1: score+=8;reasons.append("Crecimiento revenue >10%")
        elif gr<0: score-=8;reasons.append("Revenue en caída")
    score=max(0,min(100,score))
    rating=("🟢 Fuerte" if score>=70 else "🟡 Neutral" if score>=40 else "🔴 Débil")
    return round(score,1), rating+f" ({score:.0f}/100)\n• "+"\n• ".join(reasons)
