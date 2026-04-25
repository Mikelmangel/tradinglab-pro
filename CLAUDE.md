# TradingLab Pro v2.0 — CLAUDE.md

## 1. Overview

**TradingLab Pro v2.0** — Desktop algorithmic trading research platform.
PyQt6 GUI, Python backend, Claude AI assistant.

**Purpose:** Strategy development, backtesting, optimization, multi-asset portfolio analysis, market scanning, AI-assisted trading research.

**Repo:** https://github.com/Mikelmangel/tradinglab-pro

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| GUI | PyQt6 6.11 |
| Data | yfinance 1.3 + SQLite (`~/.tradinglab_pro/market_data.db`) |
| Computation | pandas 3, numpy 2.4, scipy 1.17, matplotlib 3.10 |
| AI | Anthropic Claude API via REST `/v1/messages` |
| Testing | pytest |
| Linting | ruff |
| Type check | mypy + types-requests |
| CI/CD | GitHub Actions |

---

## 3. Architecture

```
main.py                  # Entry: splash screen + app init
src/
  __init__.py            # __version__ = "2.0"
  core/
    backtest_engine.py   # Bar-by-bar backtester, no look-ahead
    indicators.py        # 40+ technical indicators (INDICATOR_REGISTRY)
    optimizer.py         # GridSearch, Genetic, WalkForward, MonteCarlo
    portfolio.py         # Multi-asset backtester + correlation
    ai_assistant.py      # Claude API integration
    data_manager.py      # yfinance download, SQLite cache, MTF
    scanner.py           # Market scanner (14 built-in + custom)
    fundamentals.py      # yfinance info + score 0-100
  ui/
    main_window.py      # 9 tabs, menu bar, status bar
    data_tab.py         # Download, symbol table, watchlists
    chart_tab.py        # Candlestick/OHLC/Line/Area + 40+ indicators
    strategy_tab.py      # Code editor (Python highlighting, 10 templates)
    backtest_tab.py      # Backtest runner, equity/DD/Monte Carlo plots
    optimizer_tab.py     # Grid/Genetic/WF, 2D heatmap
    portfolio_tab.py     # Multi-symbol + correlation matrix
    scanner_tab.py      # Market scanner UI
    fundamentals_tab.py  # Fundamental metrics + score
    ai_tab.py           # Claude chat + code extraction
  styles/
    theme.py            # Catppuccin Mocha palette (C dict) + QSS
```

---

## 4. Key Design Decisions

### Backtest Engine
- **No look-ahead:** Signal from `i-1`, execution at `i` open
- **Intra-bar stops:** Uses High/Low of current bar (not just close) for SL/TP
- **Position sizing:** pct_equity, fixed_dollar, fixed_shares, atr_risk, fixed_risk_pct, kelly
- **Returns:** equity_curve (Series), daily_returns, metrics dict, trades_df, annual_breakdown, monthly_heatmap
- **Metrics:** Sharpe, Sortino, Calmar, Omega, Win Rate, Profit Factor, VaR 95/99

### Data Manager
- Downloads via yfinance, stores in SQLite (`~/.tradinglab_pro/market_data.db`)
- MTF alignment: `sec.reindex(pri.index, method='ffill')` — no look-ahead
- Tables: `ohlcv`, `symbols`, `watchlists`, `watchlist_symbols`

### AI Assistant
- Model: `claude-opus-4-6`, endpoint `/v1/messages`
- System prompt: trading analysis + strategy code generation in Spanish
- Context injection: backtest metrics (first 25), annual breakdown, strategy code
- `extract_code()` → regex ` ```python\n(.*?)``` `

### Optimizer
- `GridSearchOptimizer.run()` — exhaustive param sweep
- `GeneticOptimizer.run()` — tournament selection, elite 15%, cx 0.8, mut 0.15
- `WalkForwardTester.run()` — 70% in-sample, 5 windows, wf_efficiency = oos/is
- `MonteCarloSimulator.run()` — bootstrap equity paths, ruin probability

### Strategy Format
```python
def generate_signals(data, fast_period=10, slow_period=30, **params):
    # data: DataFrame with Open, High, Low, Close, Volume
    # Returns: pd.Series with 1=long, -1=short, 0=neutral
    import pandas as pd; import numpy as np
    # ...
    return signals
```
Injected via `exec()` with namespace `{'pd': pd, 'np': np}`.

---

## 5. Installation

### Linux (Debian/Ubuntu)
```bash
# Install system deps
sudo apt install libxcb-cursor0 libxcb-xinerama0

# Clone or navigate to repo
cd tradinglab-pro

# Option A: with venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py

# Option B: with installer
chmod +x installer/install.sh
./installer/install.sh
./run.sh
```

### No-display / SSH server
```bash
QT_QPA_PLATFORM=offscreen python3 main.py
```

---

## 6. CI/CD

**GitHub Actions** (`main` branch):
- `ruff check src/` — lint
- `mypy src/ --ignore-missing-imports` — type check
- `pytest tests/ -v` — unit tests
- `python -m build` — build package

**Status:** ✅ Passing

---

## 7. Agent Swarm

Team located at `~/.claude/projects/-home-miguel-angel-Escritorio-Proyectos-tlpro/agents/`

| Agent | Color | Domain | Trigger |
|---|---|---|---|
| `tradinglab-lead` | 🔴 Red | Coordinator — decides which agent to call | Any task, unsure which agent |
| `tradinglab-core-engine` | 🔵 Blue | backtest_engine, optimizer, portfolio, indicators | Logic changes, new indicators, strategy engine |
| `tradinglab-ui-dev` | 🟢 Green | PyQt6 tabs, charts, theme | UI changes, tab additions |
| `tradinglab-data-dev` | 🟡 Yellow | data_manager, scanner, fundamentals | Data downloads, watchlists, scanner |
| `tradinglab-ai-integration` | 🟣 Purple | ai_assistant, ai_tab | AI prompts, Claude API, context injection |
| `tradinglab-devops` | 🩶 Gray | setup.py, CI/CD, install.py, .gitignore | Packaging, deployment |
| `tradinglab-testing` | 🟠 Orange | tests/ | Add/modify tests |

### Invoking an agent
```
Agent(subagent_type="general-purpose",
      prompt="[task description] — check agents/tradinglab-[domain].md for context")
```

---

## 8. Known Issues (Fixed)

| Issue | File | Fix |
|---|---|---|
| `C['bg']` KeyError | `src/styles/theme.py` | Added `'bg': '#1e1e2e'` alias |
| `code_requested` double emit | `src/ui/ai_tab.py` | Removed duplicate `.emit()` |
| Portfolio weight normalization | `src/core/portfolio.py` | Fixed formula |
| `DownloadThread.start` overwritten | `src/ui/data_tab.py` | Renamed params to `start_date`/`end_date` |
| Pandas compat (equity_curve iloc) | `src/core/backtest_engine.py` | `iloc[:,0]` → `.values` |
| Mypy type errors | `src/core/ai_assistant.py` | Added type annotations |
| Unused `json` import | `src/core/ai_assistant.py` | Removed |

---

## 9. Key Files

| File | Purpose |
|---|---|
| [main.py](main.py) | Entry point, splash, app init |
| [src/core/backtest_engine.py](src/core/backtest_engine.py) | Bar-by-bar backtester |
| [src/core/optimizer.py](src/core/optimizer.py) | Grid/Genetic/WF/MonteCarlo |
| [src/core/ai_assistant.py](src/core/ai_assistant.py) | Claude API |
| [src/ui/data_tab.py](src/ui/data_tab.py) | Download thread bug fix reference |
| [src/styles/theme.py](src/styles/theme.py) | Catppuccin Mocha palette |
| [tests/test_backtest_engine.py](tests/test_backtest_engine.py) | Core engine tests |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | CI/CD pipeline |

---

## 10. Dependencies

```
PyQt6>=6.6.0
yfinance>=0.2.36
pandas>=2.1.0
numpy>=1.26.0
matplotlib>=3.8.0
scipy>=1.11.0
requests>=2.31.0
```