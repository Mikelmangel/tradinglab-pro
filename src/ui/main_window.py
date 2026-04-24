"""TradingLab Pro — Main Window (9 tabs)."""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
from src.ui.data_tab import DataTab
from src.ui.chart_tab import ChartTab
from src.ui.strategy_tab import StrategyTab
from src.ui.backtest_tab import BacktestTab
from src.ui.optimizer_tab import OptimizerTab
from src.ui.portfolio_tab import PortfolioTab
from src.ui.scanner_tab import ScannerTab
from src.ui.fundamentals_tab import FundamentalsTab
from src.ui.ai_tab import AITab

class MainWindow(QMainWindow):
    def __init__(self, dm):
        super().__init__()
        self.dm = dm
        self.setWindowTitle("TradingLab Pro v2.0 — Bar-by-Bar · MTF · Fundamentales · IA")
        self.setMinimumSize(1280, 800)
        self._build_ui()
        self._connect()
        self._refresh_symbols()

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11))
        self.setCentralWidget(self.tabs)

        self.data_tab   = DataTab(self.dm)
        self.chart_tab  = ChartTab(self.dm)
        self.strat_tab  = StrategyTab()
        self.bt_tab     = BacktestTab(self.dm, self.strat_tab)
        self.opt_tab    = OptimizerTab(self.dm, self.strat_tab)
        self.port_tab   = PortfolioTab(self.dm, self.strat_tab)
        self.scan_tab   = ScannerTab(self.dm)
        self.fund_tab   = FundamentalsTab(self.dm)
        self.ai_tab     = AITab()

        for tab, label in [
            (self.data_tab,  "📥 Datos"),
            (self.chart_tab, "📈 Gráficos"),
            (self.strat_tab, "💻 Estrategia"),
            (self.bt_tab,    "🔬 Backtest"),
            (self.opt_tab,   "⚙️ Optimización"),
            (self.port_tab,  "🗂️ Portfolio"),
            (self.scan_tab,  "🔍 Scanner"),
            (self.fund_tab,  "📊 Fundamentales"),
            (self.ai_tab,    "🤖 IA"),
        ]:
            self.tabs.addTab(tab, label)

        self._build_menu()
        self.statusBar().showMessage("TradingLab Pro v2.0 listo")

    def _build_menu(self):
        mb = self.menuBar()
        file_m = mb.addMenu("Archivo")
        for name, key, fn in [("Salir", "Ctrl+Q", self.close)]:
            a = QAction(name, self); a.setShortcut(key); a.triggered.connect(fn); file_m.addAction(a)
        nav_m = mb.addMenu("Navegar")
        labels=["📥 Datos","📈 Gráficos","💻 Estrategia","🔬 Backtest",
                "⚙️ Optimización","🗂️ Portfolio","🔍 Scanner","📊 Fundamentales","🤖 IA"]
        for i,lbl in enumerate(labels):
            a=QAction(f"{lbl}  Ctrl+{i+1}",self); a.setShortcut(f"Ctrl+{i+1}")
            a.triggered.connect(lambda chk,idx=i: self.tabs.setCurrentIndex(idx)); nav_m.addAction(a)
        help_m = mb.addMenu("Ayuda")
        about = QAction("Acerca de", self); about.triggered.connect(self._about); help_m.addAction(about)

    def _connect(self):
        self.data_tab.data_loaded.connect(self._refresh_symbols)
        self.data_tab.data_loaded.connect(lambda s: self.statusBar().showMessage(f"{s} cargado"))
        for t in (self.bt_tab, self.opt_tab, self.port_tab, self.scan_tab, self.fund_tab, self.ai_tab):
            if hasattr(t,'status_msg'): t.status_msg.connect(self.statusBar().showMessage)
        # After backtest → inject context to AI
        self.bt_tab.status_msg.connect(self._inject_ai_context)
        # AI code → strategy editor
        self.ai_tab.code_requested.connect(self.strat_tab.set_code)
        self.ai_tab.code_requested.connect(lambda _: self.tabs.setCurrentIndex(2))

    def _inject_ai_context(self, msg):
        if "completado" in msg.lower():
            r = self.bt_tab.get_result()
            if r:
                ann = None
                if not r.get('annual_breakdown', None) is None and not r['annual_breakdown'].empty:
                    ann = r['annual_breakdown'].to_dict('records')
                self.ai_tab.inject_context(
                    metrics=r.get('metrics'),
                    annual=ann,
                    code=self.strat_tab.get_code()
                )

    def _refresh_symbols(self, sym=None):
        syms = self.dm.get_all_symbols()
        for t in (self.chart_tab, self.bt_tab, self.opt_tab, self.port_tab, self.scan_tab):
            if hasattr(t, 'update_symbols'): t.update_symbols(syms)
        stats = self.dm.get_stats()
        self.statusBar().showMessage(
            f"Símbolos: {stats['symbols']}  |  Barras: {stats['bars']:,}  |  "
            f"DB: {stats['db_mb']}MB  |  TradingLab Pro v2.0")

    def _about(self):
        QMessageBox.about(self, "TradingLab Pro v2.0",
            "<b>TradingLab Pro v2.0</b><br><br>"
            "🕯️ Motor bar-by-bar (zero look-ahead bias)<br>"
            "⏱️ Multi-Timeframe (MTF) analysis<br>"
            "📊 40+ indicadores técnicos<br>"
            "⚙️ Grid Search + Algoritmo Genético + Walk-Forward<br>"
            "🎲 Monte Carlo (500 simulaciones)<br>"
            "🗂️ Portfolio multi-activo + correlación<br>"
            "🔍 Market Scanner (14 condiciones)<br>"
            "📅 Reporte anual + Heatmap calendar<br>"
            "📊 Fundamentales (P/E, ROE, EV/EBITDA, etc.)<br>"
            "🤖 Asistente IA (Claude API)<br><br>"
            "Python 3.10+  ·  PyQt6  ·  yfinance  ·  Anthropic Claude")

    def closeEvent(self, e):
        self.dm.close(); super().closeEvent(e)
