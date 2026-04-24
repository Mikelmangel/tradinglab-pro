"""TradingLab Pro — Portfolio Tab."""
import traceback, numpy as np, pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from src.core.backtest_engine import BacktestConfig
from src.core.portfolio import PortfolioBacktester
from src.styles.theme import C as TC

C = TC

class PortThread(QThread):
    progress=pyqtSignal(int,str); finished=pyqtSignal(dict); error=pyqtSignal(str)
    def __init__(self,datasets,code,cfg): super().__init__(); self.ds=datasets;self.code=code;self.cfg=cfg
    def run(self):
        try: self.finished.emit(PortfolioBacktester().run(self.ds,self.code,self.cfg,progress_cb=self.progress.emit))
        except Exception as e: self.error.emit(f"{e}\n\n{traceback.format_exc()}")

class PortfolioTab(QWidget):
    status_msg=pyqtSignal(str)
    def __init__(self,dm,strat):
        super().__init__(); self.dm=dm;self.strat=strat; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        cfg=QGroupBox("Portfolio"); cfg.setMaximumHeight(80); cl=QHBoxLayout(cfg)
        cl.addWidget(QLabel("Capital:")); self.cap=QDoubleSpinBox(); self.cap.setRange(100,1e8); self.cap.setValue(10000); self.cap.setGroupSeparatorShown(True); cl.addWidget(self.cap)
        cl.addWidget(QLabel("Comisión:")); self.comm=QDoubleSpinBox(); self.comm.setRange(0,0.05); self.comm.setValue(0.001); self.comm.setDecimals(4); cl.addWidget(self.comm)
        self.equal=QCheckBox("Pesos iguales"); self.equal.setChecked(True); cl.addWidget(self.equal)
        cl.addStretch()
        self.run_btn=QPushButton("🗂️ Ejecutar Portfolio"); self.run_btn.setObjectName("primary")
        self.run_btn.setFixedHeight(40); self.run_btn.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        self.run_btn.clicked.connect(self._run); cl.addWidget(self.run_btn)
        L.addWidget(cfg)
        self.prog=QProgressBar(); self.prog.setVisible(False); L.addWidget(self.prog)
        sp=QSplitter(Qt.Orientation.Horizontal)
        left=QGroupBox("Activos"); ll=QVBoxLayout(left)
        ll.addWidget(QLabel("Ctrl+click para múltiple:"))
        self.sym_list=QListWidget(); self.sym_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection); ll.addWidget(self.sym_list)
        sr=QHBoxLayout(); a=QPushButton("✅ Todos"); a.clicked.connect(self.sym_list.selectAll)
        n=QPushButton("❌ Ninguno"); n.clicked.connect(self.sym_list.clearSelection)
        sr.addWidget(a); sr.addWidget(n); ll.addLayout(sr); sp.addWidget(left)
        right=QTabWidget()
        self.met_tbl=QTableWidget(); self.met_tbl.setColumnCount(2)
        self.met_tbl.setHorizontalHeaderLabels(["Métrica","Valor"])
        self.met_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.met_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.met_tbl.setAlternatingRowColors(True); right.addTab(self.met_tbl,"📊 Métricas")
        self.asset_tbl=QTableWidget(); self.asset_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.asset_tbl.setAlternatingRowColors(True); right.addTab(self.asset_tbl,"📋 Por Activo")
        self.corr_tbl=QTableWidget(); self.corr_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.corr_tbl.setAlternatingRowColors(True); right.addTab(self.corr_tbl,"🔗 Correlación")
        self._fig=Figure(facecolor=C['bg']); self._cv=FigureCanvasQTAgg(self._fig)
        w=QWidget(); vl=QVBoxLayout(w); vl.setContentsMargins(0,0,0,0)
        vl.addWidget(NavigationToolbar2QT(self._cv,self)); vl.addWidget(self._cv)
        right.addTab(w,"📈 Equity")
        sp.addWidget(right); sp.setSizes([200,1100]); L.addWidget(sp,1)
        self.log=QLabel(""); self.log.setStyleSheet("color:#6c7086;font-size:10px;"); L.addWidget(self.log)

    def update_symbols(self,syms):
        self.sym_list.clear()
        for s in syms: self.sym_list.addItem(s)

    def _run(self):
        sel=[item.text() for item in self.sym_list.selectedItems()]
        if not sel: return
        datasets={s:self.dm.get_data(s) for s in sel}
        datasets={s:d for s,d in datasets.items() if d is not None and not d.empty}
        code=self.strat.get_code()
        cfg=BacktestConfig(initial_capital=self.cap.value(),commission=self.comm.value())
        self.run_btn.setEnabled(False); self.prog.setVisible(True); self.prog.setValue(0)
        self.log.setText(f"⏳ Portfolio: {', '.join(sel)}")
        self._t=PortThread(datasets,code,cfg)
        self._t.progress.connect(lambda p,m: (self.prog.setValue(p),self.log.setText(m)))
        self._t.finished.connect(self._done); self._t.error.connect(self._err); self._t.start()

    def _done(self,r):
        self.run_btn.setEnabled(True); self.prog.setVisible(False)
        pm=r.get('portfolio_metrics',{}); self._fill_metrics(pm.get('metrics',{}))
        self._fill_assets(pm.get('asset_summary',{}))
        if r.get('correlation') is not None: self._fill_corr(r['correlation'])
        ce=r.get('combined_equity')
        if ce is not None and not ce.empty: self._plot(ce)
        self.log.setText(f"✅ Portfolio — {len(r.get('individual',{}))} activos")

    def _err(self,e):
        self.run_btn.setEnabled(True); self.prog.setVisible(False); self.log.setText(f"❌ {e.split(chr(10))[0][:80]}")

    def _fill_metrics(self,m):
        rows=list(m.items()); self.met_tbl.setRowCount(len(rows))
        for i,(k,v) in enumerate(rows):
            sep=k.startswith('──'); ki=QTableWidgetItem(k.replace('──','').strip() if sep else k); vi=QTableWidgetItem(str(v))
            if sep:
                for it in (ki,vi): it.setBackground(QColor(C['surface0'])); it.setForeground(QColor(C['blue']))
            else:
                vi.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                try:
                    n=float(str(v).replace('%','').replace('$','').replace(',','').replace('+',''))
                    if ('%' in str(v) or '$' in str(v)) and n!=0: vi.setForeground(QColor(C['green'] if n>0 else C['red']))
                except: pass
            self.met_tbl.setItem(i,0,ki); self.met_tbl.setItem(i,1,vi)

    def _fill_assets(self,s):
        if not s: return
        syms=list(s.keys()); fields=list(next(iter(s.values())).keys()) if syms else []
        self.asset_tbl.setColumnCount(len(fields)+1); self.asset_tbl.setHorizontalHeaderLabels(["Símbolo"]+fields)
        self.asset_tbl.setRowCount(len(syms)); self.asset_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i,sym in enumerate(syms):
            self.asset_tbl.setItem(i,0,QTableWidgetItem(sym))
            for j,f in enumerate(fields):
                self.asset_tbl.setItem(i,j+1,QTableWidgetItem(str(s[sym].get(f,'N/A'))))

    def _fill_corr(self,corr):
        syms=list(corr.columns); self.corr_tbl.setColumnCount(len(syms)+1); self.corr_tbl.setRowCount(len(syms))
        self.corr_tbl.setHorizontalHeaderLabels([""]+syms); self.corr_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i,rs in enumerate(syms):
            self.corr_tbl.setItem(i,0,QTableWidgetItem(rs))
            for j,cs in enumerate(syms):
                v=corr.loc[rs,cs]; it=QTableWidgetItem(f"{v:.3f}"); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if rs==cs: it.setBackground(QColor(C['surface0']))
                elif v>0.7: it.setForeground(QColor(C['red']))
                elif v<0.3: it.setForeground(QColor(C['green']))
                self.corr_tbl.setItem(i,j+1,it)

    def _plot(self,combined):
        self._fig.clear()
        gs=gridspec.GridSpec(2,1,figure=self._fig,hspace=0.1,height_ratios=[3,1],left=0.02,right=0.95,top=0.93,bottom=0.08)
        ax1=self._fig.add_subplot(gs[0]); ax2=self._fig.add_subplot(gs[1],sharex=ax1)
        x=np.arange(len(combined))
        COLS=[C['blue'],C['green'],C['yellow'],C['mauve'],C['peach'],C['teal'],C['red'],C['pink'],C['lavender'],C['sapphire']]
        for i,col in enumerate(combined.columns):
            lw=2.5 if col=='Portfolio' else 0.9; alpha=1.0 if col=='Portfolio' else 0.6
            ax1.plot(x,combined[col].values,color=COLS[i%len(COLS)],lw=lw,alpha=alpha,label=col,zorder=5 if col=='Portfolio' else 1)
        ax1.legend(loc='upper left',facecolor=C['surface0'],labelcolor=C['text'],fontsize=7,framealpha=0.8)
        ax1.set_title('Portfolio Multi-Activo',color=C['text'],fontsize=12,fontweight='bold')
        self._sa(ax1)
        self._sa(ax2)
        if 'Portfolio' in combined.columns:
            eq=combined['Portfolio'].values; rm=np.maximum.accumulate(eq)
            dd=(eq-rm)/rm*100 if rm.max()>0 else eq-eq
            ax2.fill_between(x,dd,0,alpha=0.6,color=C['red']); ax2.plot(x,dd,color=C['red'],lw=0.8)
            ax2.set_title('Portfolio Drawdown',color=C['text'],fontsize=9)
        dates=[str(d)[:10] for d in combined.index]; step=max(1,len(x)//8)
        ax2.set_xticks(list(range(0,len(x),step)))
        ax2.set_xticklabels([dates[i] for i in range(0,len(x),step)],rotation=30,fontsize=7,color=C['text'])
        ax2.set_xlim(-1,len(x))
        self._fig.patch.set_facecolor(C['bg']); self._cv.draw()

    def _sa(self,ax):
        ax.set_facecolor(C['bg']); ax.tick_params(colors=C['text'],labelsize=7)
        ax.grid(color=C['surface0'],lw=0.4,alpha=0.5)
        for sp in ax.spines.values(): sp.set_color(C['surface1']); sp.set_lw(0.6)
        ax.yaxis.tick_right()
