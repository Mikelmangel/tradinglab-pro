"""TradingLab Pro — Optimizer Tests."""
import numpy as np, pandas as pd, pytest
from src.core.optimizer import GridSearchOptimizer, GeneticOptimizer, MonteCarloSimulator

def _synthetic_ohlcv(n=200, seed=42):
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1e6, 5e6, n)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)

STRATEGY_CODE = """
def generate_signals(data, fast_period=10, slow_period=30):
    sma_fast = data['Close'].rolling(fast_period).mean()
    sma_slow = data['Close'].rolling(slow_period).mean()
    sig = pd.Series(0, index=data.index)
    sig[sma_fast > sma_slow] = 1
    sig[sma_fast < sma_slow] = -1
    return sig
"""

class TestGridSearchOptimizer:
    def test_returns_dataframe(self):
        opt = GridSearchOptimizer()
        data = _synthetic_ohlcv(200)
        param_grid = {"fast_period": [5, 10], "slow_period": [20, 30]}
        cfg_dict = {"initial_capital": 10000, "commission": 0.001}
        result = opt.run(data, STRATEGY_CODE, param_grid, cfg_dict, "Sharpe")
        assert isinstance(result, pd.DataFrame)

    def test_results_sorted_descending(self):
        opt = GridSearchOptimizer()
        data = _synthetic_ohlcv(200)
        param_grid = {"fast_period": [5, 10], "slow_period": [20, 30]}
        cfg_dict = {"initial_capital": 10000}
        result = opt.run(data, STRATEGY_CODE, param_grid, cfg_dict, "Sharpe")
        if not result.empty:
            assert result.iloc[0]["Sharpe"] >= result.iloc[-1]["Sharpe"]

class TestMonteCarloSimulator:
    def test_runs_with_enough_pnl(self):
        mc = MonteCarloSimulator()
        pnl_pcts = [1.0, -0.5, 2.0, 1.5, -0.3, 0.8, 1.2, -0.1, 0.5, 0.9]
        result = mc.run(pnl_pcts, 10000, n_simulations=100)
        assert result is not None
        assert "equity_paths" in result
        assert "prob_of_ruin" in result
        assert 0 <= result["prob_of_ruin"] <= 100

    def test_returns_none_for_short_pnl(self):
        mc = MonteCarloSimulator()
        result = mc.run([1.0, -0.5], 10000)
        assert result is None