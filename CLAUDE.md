# TradingLab Pro — CLAUDE.md

## 1. Overview

**TradingLab Pro v2.0** — Desktop trading research platform. PyQt6 GUI, Python backend.

**Purpose:** Algorithmic trading strategy development, backtesting, optimization, and AI-assisted analysis.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| GUI | PyQt6 |
| Data | yfinance (Yahoo Finance) + SQLite local cache |
| Computation | pandas, numpy, scipy, matplotlib |
| AI | Anthropic Claude API (via requests) |
| Storage | SQLite (`~/.tradinglab_pro/market_data.db`) |

---

## 3. Architecture

```
main.py                  # Entry point — splash screen, app init
src/
  core/
    data_manager.py      # Download, cache, MTF alignment, watchlists
    backtest_engine.py   # Bar-by-bar backtester (intrabar stops, OHLC path)
    indicators.py        # Technical indicators (RSI, SMA, EMA, ATR, etc.)
    ai_assistant.py      # Claude API chat integration
    optimizer.py         # GridSearch, Genetic, WalkForward, MonteCarlo
    portfolio.py         # Multi-asset portfolio backtester
    scanner.py           # Market scanner with built-in conditions
    fundamentals.py      # Fundamental data handler
  ui/
    main_window.py      # Main window layout
    chart_tab.py        # Price charts + overlays
    strategy_tab.py     # Code editor for strategies
    backtest_tab.py     # Backtest runner + results
    optimizer_tab.py    # Strategy optimization UI
    scanner_tab.py      # Market scanner UI
    portfolio_tab.py   # Portfolio backtester
    ai_tab.py          # AI assistant chat
    fundamentals_tab.py # Fundamental data
    data_tab.py        # Data management UI
```

---

## 4. Key Design Decisions

### Backtest Engine
- **Strict no look-ahead:** Signal from previous bar, executed at next bar open
- **Intragar stop/tp:** Checks High/Low for OHLC path, not just close
- **Position sizing:** pct_equity, fixed_dollar, fixed_shares, atr_risk, fixed_risk_pct, kelly
- **Metrics:** Sharpe, Sortino, Calmar, Omega, Win Rate, Profit Factor, VaR 95/99, annual breakdown, monthly heatmap

### Data Manager
- Downloads via yfinance, stores in SQLite
- MTF alignment: secondary TF ffill-reindexed to primary (no look-ahead)
- Watchlists stored in DB

### AI Assistant
- Uses Claude Opus via `/v1/messages` REST API
- System prompt: trading analysis, strategy code generation
- Context injection: current backtest metrics + code

### Optimizer
- **GridSearch:** Exhaustive parameter sweep
- **Genetic:** Tournament selection, crossover, mutation
- **WalkForward:** In-sample / out-of-sample windows
- **MonteCarlo:** Bootstrap resampling for equity paths, ruin probability

### Scanner
- Built-in conditions: RSI, SMA cross, MACD, Bollinger, Donchian, SuperTrend, ADX, Volume spike, 52W high
- Custom Python condition via `scan_condition(data)` function

---

## 5. Strategy Code Format

Strategies are Python functions injected via `exec()`:

```python
def generate_signals(data, fast_period=10, slow_period=30, **params):
    # data: DataFrame with Open, High, Low, Close, Volume
    # Returns: pd.Series with 1=long, -1=short, 0=neutral
    import pandas as pd
    import numpy as np
    # ...
    return signals
```

AI assistant extracts code from markdown fenced blocks.

---

## 6. Key Files

- [main.py](main.py) — Entry point, splash, app init
- [src/core/backtest_engine.py](src/core/backtest_engine.py) — Bar-by-bar backtester
- [src/core/ai_assistant.py](src/core/ai_assistant.py) — Claude API integration
- [src/core/optimizer.py](src/core/optimizer.py) — Grid/Genetic/WF/MonteCarlo
- [src/core/data_manager.py](src/core/data_manager.py) — Data + SQLite + MTF
- [src/ui/main_window.py](src/ui/main_window.py) — Main window

---

## 7. CLI Commands

```bash
python main.py  # Launch GUI
```

---

## 8. Dependencies

```
PyQt6>=6.6.0
yfinance>=0.2.36
pandas>=2.1.0
numpy>=1.26.0
matplotlib>=3.8.0
scipy>=1.11.0
requests>=2.31.0
```