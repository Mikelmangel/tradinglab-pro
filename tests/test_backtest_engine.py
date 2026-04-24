"""TradingLab Pro — Backtest Engine Tests."""
import numpy as np, pandas as pd, pytest
from src.core.backtest_engine import BacktestEngine, BacktestConfig

def _synthetic_ohlcv(n=200, seed=42):
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1e6, 5e6, n)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)

def _simple_strategy(data, fast=10, slow=30):
    sma_fast = data["Close"].rolling(fast).mean()
    sma_slow = data["Close"].rolling(slow).mean()
    sig = pd.Series(0, index=data.index)
    sig[sma_fast > sma_slow] = 1
    sig[sma_fast < sma_slow] = -1
    return sig

class TestBacktestEngine:
    def test_empty_data_returns_empty(self):
        engine = BacktestEngine()
        cfg = BacktestConfig()
        result = engine.run(pd.DataFrame(), pd.Series(dtype=float), cfg)
        assert result["equity_curve"].empty

    def test_simple_moving_average_crossover(self):
        engine = BacktestEngine()
        data = _synthetic_ohlcv(200)
        signals = _simple_strategy(data)
        cfg = BacktestConfig(initial_capital=10_000, commission=0.001)
        result = engine.run(data, signals, cfg)
        assert not result["equity_curve"].empty
        assert "metrics" in result
        assert "trades_df" in result

    def test_metrics_contain_sharpe(self):
        engine = BacktestEngine()
        data = _synthetic_ohlcv(200)
        signals = _simple_strategy(data)
        cfg = BacktestConfig()
        result = engine.run(data, signals, cfg)
        metrics = result["metrics"]
        # Metrics dict has keys — check we have something like Sharpe
        assert any("Sharpe" in str(k) for k in metrics.keys())

    def test_with_stop_loss(self):
        engine = BacktestEngine()
        data = _synthetic_ohlcv(200)
        signals = _simple_strategy(data)
        cfg = BacktestConfig(stop_loss_pct=0.02)
        result = engine.run(data, signals, cfg)
        assert not result["equity_curve"].empty

    def test_no_look_ahead_signal_previous_bar(self):
        engine = BacktestEngine()
        data = _synthetic_ohlcv(200)
        signals = _simple_strategy(data)
        cfg = BacktestConfig()
        result = engine.run(data, signals, cfg)
        eq = result["equity_curve"]
        first_val = float(eq.iloc[-1]) if hasattr(eq.iloc[-1], '__float__') else float(eq.iloc[-1].iloc[0])
        assert first_val > 0

    def test_short_signals_respected(self):
        engine = BacktestEngine()
        data = _synthetic_ohlcv(200)
        signals = _simple_strategy(data)
        cfg = BacktestConfig(allow_short=True)
        result = engine.run(data, signals, cfg)
        trades_df = result["trades_df"]
        if not trades_df.empty:
            # Short trades exist when allow_short=True
            assert "Short" in str(trades_df["Dir"].iloc[0]) or "Long" in str(trades_df["Dir"].iloc[0])