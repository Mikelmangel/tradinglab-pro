"""TradingLab Pro — Data Manager (SQLite + Yahoo Finance + MTF + Watchlists)"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

DB_PATH = Path.home() / ".tradinglab_pro" / "market_data.db"

RESAMPLE_MAP = {
    '1m':'1min','2m':'2min','5m':'5min','10m':'10min','15m':'15min',
    '30m':'30min','1h':'1h','2h':'2h','4h':'4h','1d':'1D','1wk':'1W','1mo':'1ME',
}

def _resample_ohlcv(df, rule):
    return df.resample(rule).agg(
        {'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}
    ).dropna()

class DataManager:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS ohlcv(
            symbol TEXT, interval TEXT, date TEXT,
            open REAL, high REAL, low REAL, close REAL, volume REAL,
            PRIMARY KEY(symbol,interval,date));
        CREATE TABLE IF NOT EXISTS symbols(
            symbol TEXT, interval TEXT, name TEXT, sector TEXT,
            market TEXT, currency TEXT, last_update TEXT,
            PRIMARY KEY(symbol,interval));
        CREATE TABLE IF NOT EXISTS watchlists(
            name TEXT PRIMARY KEY, created TEXT);
        CREATE TABLE IF NOT EXISTS watchlist_symbols(
            list_name TEXT, symbol TEXT,
            PRIMARY KEY(list_name,symbol));
        """)
        self.conn.commit()

    def download(self, symbol, start, end, interval='1d', progress_cb=None):
        try:
            import yfinance as yf
            t = yf.Ticker(symbol)
            df = t.history(start=start, end=end, interval=interval, auto_adjust=True)
            if df.empty: return None
            df = df[['Open','High','Low','Close','Volume']].copy()
            df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC').tz_localize(None)
            info = {}
            try: info = t.info
            except: pass
            self._save(symbol, interval, df, {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', ''),
                'market': info.get('exchange', ''),
                'currency': info.get('currency', 'USD'),
            })
            return df
        except Exception as e:
            if progress_cb: progress_cb(0, str(e))
            return None

    def _save(self, symbol, interval, df, meta):
        rows = [(symbol, interval,
                 str(idx.date() if hasattr(idx,'date') else idx),
                 float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume))
                for idx, r in df.iterrows()]
        self.conn.executemany(
            "INSERT OR REPLACE INTO ohlcv VALUES(?,?,?,?,?,?,?,?)", rows)
        self.conn.execute(
            "INSERT OR REPLACE INTO symbols VALUES(?,?,?,?,?,?,?)",
            (symbol, interval, meta.get('name',''), meta.get('sector',''),
             meta.get('market',''), meta.get('currency','USD'), datetime.now().isoformat()))
        self.conn.commit()

    def get_data(self, symbol, interval='1d', resample_to=None):
        df = pd.read_sql(
            "SELECT date,open,high,low,close,volume FROM ohlcv "
            "WHERE symbol=? AND interval=? ORDER BY date",
            self.conn, params=(symbol, interval))
        if df.empty: return None
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df.columns = ['Open','High','Low','Close','Volume']
        if resample_to and resample_to != interval:
            df = _resample_ohlcv(df, RESAMPLE_MAP.get(resample_to, resample_to))
        return df

    def get_mtf(self, symbol, tf_primary, tf_secondary):
        """Primary + secondary aligned (no look-ahead: ffill)."""
        pri = self.get_data(symbol, tf_primary)
        sec_raw = self.get_data(symbol, tf_secondary)
        if pri is None: return None, None
        if sec_raw is None:
            # try resampling primary
            rule = RESAMPLE_MAP.get(tf_secondary, tf_secondary)
            sec_raw = _resample_ohlcv(pri, rule)
        sec = sec_raw.reindex(pri.index, method='ffill')
        return pri, sec

    def resample_to(self, df, rule):
        return _resample_ohlcv(df, RESAMPLE_MAP.get(rule, rule))

    def get_symbols(self, interval='1d'):
        c = self.conn.execute(
            "SELECT symbol FROM symbols WHERE interval=? ORDER BY symbol", (interval,))
        return [r[0] for r in c.fetchall()]

    def get_all_symbols(self):
        c = self.conn.execute("SELECT DISTINCT symbol FROM symbols ORDER BY symbol")
        return [r[0] for r in c.fetchall()]

    def get_symbol_info(self, symbol, interval='1d'):
        c = self.conn.execute(
            "SELECT name,sector,market,currency,last_update FROM symbols "
            "WHERE symbol=? AND interval=?", (symbol, interval))
        r = c.fetchone()
        return dict(zip(['name','sector','market','currency','last_update'], r)) if r else {}

    def get_stats(self):
        syms = self.conn.execute("SELECT COUNT(DISTINCT symbol) FROM symbols").fetchone()[0]
        bars = self.conn.execute("SELECT COUNT(*) FROM ohlcv").fetchone()[0]
        wls  = self.conn.execute("SELECT COUNT(*) FROM watchlists").fetchone()[0]
        size = DB_PATH.stat().st_size/1024/1024 if DB_PATH.exists() else 0
        return {'symbols':syms,'bars':bars,'watchlists':wls,'db_mb':round(size,2)}

    def delete_symbol(self, symbol, interval=None):
        if interval:
            self.conn.execute("DELETE FROM ohlcv WHERE symbol=? AND interval=?", (symbol,interval))
            self.conn.execute("DELETE FROM symbols WHERE symbol=? AND interval=?", (symbol,interval))
        else:
            self.conn.execute("DELETE FROM ohlcv WHERE symbol=?", (symbol,))
            self.conn.execute("DELETE FROM symbols WHERE symbol=?", (symbol,))
        self.conn.commit()

    def create_watchlist(self, name):
        self.conn.execute("INSERT OR IGNORE INTO watchlists VALUES(?,?)",
                          (name, datetime.now().isoformat()))
        self.conn.commit()

    def delete_watchlist(self, name):
        self.conn.execute("DELETE FROM watchlists WHERE name=?", (name,))
        self.conn.execute("DELETE FROM watchlist_symbols WHERE list_name=?", (name,))
        self.conn.commit()

    def add_to_watchlist(self, list_name, symbol):
        self.conn.execute("INSERT OR IGNORE INTO watchlist_symbols VALUES(?,?)",
                          (list_name, symbol))
        self.conn.commit()

    def remove_from_watchlist(self, list_name, symbol):
        self.conn.execute("DELETE FROM watchlist_symbols WHERE list_name=? AND symbol=?",
                          (list_name, symbol))
        self.conn.commit()

    def get_watchlists(self):
        c = self.conn.execute("SELECT name FROM watchlists ORDER BY name")
        return [r[0] for r in c.fetchall()]

    def get_watchlist_symbols(self, name):
        c = self.conn.execute(
            "SELECT symbol FROM watchlist_symbols WHERE list_name=? ORDER BY symbol", (name,))
        return [r[0] for r in c.fetchall()]

    def close(self):
        self.conn.close()
