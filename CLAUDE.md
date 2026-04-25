# TradingLab Pro v2.0 — CLAUDE.md

## 1. Overview

**TradingLab Pro v2.0** — Desktop algorithmic trading research platform.
PyQt6 GUI, Python backend, Claude AI assistant.

**Purpose:** Strategy development, backtesting, optimization, multi-asset portfolio analysis, market scanning, AI-assisted trading research.

**Repo:** https://github.com/Mikelmangel/tradinglab-pro

**WORKING DIRECTORY:** `/home/miguel-angel/Escritorio/Proyectos/tlpro`
**ALL AGENTS MUST operate within this directory.** Every Agent invocation, file edit, and command execution happens here.
When invoking agents, include: `"cd /home/miguel-angel/Escritorio/Proyectos/tlpro && [task]"`.

---

## 2. Routing — Auto-Delegate Table

**How it works:** Read the user's request → match keyword(s) → invoke the correct agent automatically.

| Trigger keywords in request | Agent to invoke | Color |
|---|---|---|
| "backtest" / "optimizar" / "estrategia" / "signals" / "trading engine" | `tradinglab-core-engine` | 🔵 Blue |
| "descargar" / "watchlist" / "yfinance" / "datos" / "market data" / "ticker" / "scanner" | `tradinglab-data-dev` | 🟡 Yellow |
| "UI" / "chart" / "tab" / "ventana" / "gráfico" / "PyQt" / "theme" / "estilo" | `tradinglab-ui-dev` | 🟢 Green |
| "API key" / "Claude" / "prompt IA" / "asistente" / "chat" / "AI context" | `tradinglab-ai-integration` | 🟣 Purple |
| "CI/CD" / "deploy" / "GitHub" / "package" / "install" / "setup.py" / "build" | `tradinglab-devops` | 🩶 Gray |
| "test" / "pytest" / "coverage" / "unit" | `tradinglab-testing` | 🟠 Orange |
| "bug" / "crash" / "error" / "fix" | delegate to correct domain agent based on file location | — |
| multi-domain request (e.g., "backtest AND chart") | `tradinglab-lead` for coordination | 🔴 Red |
| no keyword match / unsure | `tradinglab-lead` | 🔴 Red |

**If the task requires multiple agents:** invoke `tradinglab-lead` with full context and let it orchestrate.

**CRITICAL — Working directory for ALL agents:**
`cd /home/miguel-angel/Escritorio/Proyectos/tlpro` must precede every command, Agent invocation, and file path reference.

---

## 3. Agent Chain of Command

**Hierarchy:**

```
tradinglab-lead (🔴)
  └── delegates to specific domain agent
  └── OR orchestrates multi-agent task

tradinglab-core-engine (🔵)
  └── can delegate to: tradinglab-ai-integration (code review), tradinglab-testing (tests for new logic)
  └── can CREATE skills if recurring pattern found

tradinglab-ui-dev (🟢)
  └── can delegate to: tradinglab-devops (CI integration for new UI components)

tradinglab-data-dev (🟡)
  └── can delegate to: tradinglab-core-engine (backtest on new data fetch)

tradinglab-ai-integration (🟣)
  └── can delegate to: tradinglab-core-engine (validate strategy code), tradinglab-ui-dev (UI for AI features)

tradinglab-devops (🩶)
  └── can delegate to: tradinglab-testing (CI tests)

tradinglab-testing (🟠)
  └── may delegate to domain agent for implementation guidance
```

**Delegation rule:** After completing sub-task, agent returns to parent with results. Parent integrates and reports back.

---

## 4. Skill Creation Protocol

**When an agent encounters a pattern 3+ times:** It SHOULD create a skill to avoid re-deriving the solution.

**Pattern → Skill trigger examples:**
- `tradinglab-core-engine` sees repeated `exec()` namespace setup → create `tradinglab-exec-helper` skill
- `tradinglab-ui-dev` creates same QSS color mapping repeatedly → create `theme-helper` skill
- `tradinglab-data-dev` handles same yfinance date parsing → create `yfinance-utils` skill
- `tradinglab-testing` sets up same synthetic OHLCV fixture → create `synthetic-data-fixture` skill

**Skill creation steps:**
1. Agent identifies recurring pattern
2. Agent writes skill file at `~/.claude/skills/tradinglab-[name].md`
3. Agent updates CLAUDE.md Section 11 (Skills Registry) with new skill
4. Agent notifies via note in summary: "Created skill: `tradinglab-[name]`"

**Skill file format:**
```markdown
# TradingLab — [Skill Name]

## When to use
[Trigger condition]

## What it does
[Description]

## Usage
[Code pattern / template]
```

---

## 5. Agent Swarm

Team located at `~/.claude/projects/-home-miguel-angel-Escritorio-Proyectos-tlpro/agents/`

### `tradinglab-lead` 🔴
- **Domain:** Coordinator. Decides which agent to call.
- **Files:** Knows all agent contexts, routes tasks.
- **Auto-invoke:** When request spans multiple domains or no keyword matches.

### `tradinglab-core-engine` 🔵
- **Domain:** backtest_engine, optimizer, portfolio, indicators
- **Files:** `src/core/backtest_engine.py`, `src/core/optimizer.py`, `src/core/portfolio.py`, `src/core/indicators.py`
- **Skills can create:** exec-helper, indicator-registry, backtest-fixtures

### `tradinglab-ui-dev` 🟢
- **Domain:** PyQt6 tabs, charts, theme
- **Files:** `src/ui/*.py`, `src/styles/theme.py`
- **Rules:** No modify core engine, ai_assistant, data_manager

### `tradinglab-data-dev` 🟡
- **Domain:** data_manager, scanner, fundamentals
- **Files:** `src/core/data_manager.py`, `src/core/scanner.py`, `src/core/fundamentals.py`
- **Key:** MTF alignment always `sec.reindex(pri.index, method='ffill')`

### `tradinglab-ai-integration` 🟣
- **Domain:** ai_assistant, ai_tab, Claude API
- **Files:** `src/core/ai_assistant.py`, `src/ui/ai_tab.py`
- **Context:** Always read `agents/tradinglab-ai-integration.md` for system prompt and API details

### `tradinglab-devops` 🩶
- **Domain:** setup.py, pyproject.toml, CI/CD, installer
- **Files:** `setup.py`, `pyproject.toml`, `installer/`, `.github/workflows/`

### `tradinglab-testing` 🟠
- **Domain:** pytest tests
- **Files:** `tests/test_*.py`
- **Rule:** Always run tests locally before reporting "done"

---

## 6. Tech Stack

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

## 7. Architecture

```
main.py                  # Entry: splash screen + app init
src/
  __init__.py            # __version__ = "2.0"
  core/
    backtest_engine.py   # Bar-by-bar backtester, no look-ahead
    indicators.py        # 40+ technical indicators (INDICATOR_REGISTRY)
    optimizer.py         # GridSearch, Genetic, WalkForward, MonteCarlo
    portfolio.py        # Multi-asset backtester + correlation
    ai_assistant.py      # Claude API integration
    data_manager.py      # yfinance download, SQLite cache, MTF
    scanner.py           # Market scanner (14 built-in + custom)
    fundamentals.py      # yfinance info + score 0-100
  ui/
    main_window.py       # 9 tabs, menu bar, status bar
    data_tab.py          # Download, symbol table, watchlists
    chart_tab.py         # Candlestick/OHLC/Line/Area + 40+ indicators
    strategy_tab.py      # Code editor (Python highlighting, 10 templates)
    backtest_tab.py      # Backtest runner, equity/DD/Monte Carlo plots
    optimizer_tab.py     # Grid/Genetic/WF, 2D heatmap
    portfolio_tab.py     # Multi-symbol + correlation matrix
    scanner_tab.py       # Market scanner UI
    fundamentals_tab.py  # Fundamental metrics + score
    ai_tab.py            # Claude chat + code extraction
  styles/
    theme.py             # Catppuccin Mocha palette (C dict) + QSS
```

---

## 8. Key Design Decisions

### Backtest Engine
- **No look-ahead:** Signal from `i-1`, execution at `i` open
- **Intra-bar stops:** Uses High/Low of current bar (not just close) for SL/TP
- **Position sizing:** pct_equity, fixed_dollar, fixed_shares, atr_risk, fixed_risk_pct, kelly
- **Returns:** equity_curve (Series), daily_returns, metrics dict, trades_df, annual_breakdown, monthly_heatmap

### Data Manager
- Downloads via yfinance, stores in SQLite (`~/.tradinglab_pro/market_data.db`)
- MTF alignment: `sec.reindex(pri.index, method='ffill')` — no look-ahead
- Tables: `ohlcv`, `symbols`, `watchlists`, `watchlist_symbols`

### AI Assistant
- Model: `claude-opus-4-6`, endpoint `/v1/messages`
- System prompt: trading analysis + strategy code generation in Spanish
- Context injection: backtest metrics (first 25), annual breakdown, strategy code

### Strategy Format
```python
def generate_signals(data, fast_period=10, slow_period=30, **params):
    # data: DataFrame with Open, High, Low, Close, Volume
    # Returns: pd.Series with 1=long, -1=short, 0=neutral
    import pandas as pd; import numpy as np
    return signals
```
Injected via `exec()` with namespace `{'pd': pd, 'np': np}`.

---

## 9. Installation

### Linux (Debian/Ubuntu)
```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0
cd tradinglab-pro

# Option A: venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python3 main.py

# Option B: installer
chmod +x installer/install.sh && ./installer/install.sh && ./run.sh
```

### SSH / No-display
```bash
QT_QPA_PLATFORM=offscreen python3 main.py
```

---

## 10. CI/CD

**GitHub Actions** (`main` branch): ruff → mypy → pytest → build
**Status:** ✅ Passing

---

## 11. Skills Registry

Skills created by agents to avoid re-deriving solutions.

| Skill | Created by | Trigger |
|---|---|---|
| *(none yet — agents create on-demand)* | | |

**How to create:** Agent identifies pattern 3+ times → write `~/.claude/skills/tradinglab-[name].md` → update this table → notify in summary.

---

## 12. Known Issues (Fixed)

| Issue | File | Fix |
|---|---|---|
| `C['bg']` KeyError | `src/styles/theme.py` | Added `'bg': '#1e1e2e'` alias |
| `code_requested` double emit | `src/ui/ai_tab.py` | Removed duplicate `.emit()` |
| Portfolio weight normalization | `src/core/portfolio.py` | Fixed formula |
| `DownloadThread.start` overwritten | `src/ui/data_tab.py` | Params → `start_date`/`end_date` |
| Pandas compat (equity_curve iloc) | `src/core/backtest_engine.py` | `iloc[:,0]` → `.values` |
| Mypy type errors | `src/core/ai_assistant.py` | Type annotations added |
| Unused `json` import | `src/core/ai_assistant.py` | Removed |

---

## 13. Key Files

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

## 14. Dependencies

```
PyQt6>=6.6.0
yfinance>=0.2.36
pandas>=2.1.0
numpy>=1.26.0
matplotlib>=3.8.0
scipy>=1.11.0
requests>=2.31.0
```