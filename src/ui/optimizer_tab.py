"""TradingLab Pro — Optimizer Tab."""
import traceback, numpy as np, pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from src.core.optimizer import GridSearchOptimizer, GeneticOptimizer, WalkForwardTester, ParamRange
from src.styles.theme import C as TC

C = TC

class OptThread(QThread):
    progress=pyqtSignal(int,str,float); finished=pyqtSignal(object); error=pyqtSignal(str)
    def __init__(self,mode,data,code,param_grid,cfg,metric,ga_pop,ga_gen):
        super().__init__(); self.mode=mode;self.data=data;self.code=code
        self.param_grid=param_grid;self.cfg=cfg;self.metric=metric
        self.ga_pop=ga_pop;self.ga_gen=ga_gen
    def run(self):
        try:
            cb=lambda pct,params=None,val=0.0,**kw: self.progress.emit(pct,str(params) if params else '',float(val) if val else 0.0)
            if self.mode=='grid':
                r=GridSearchOptimizer().run(self.data,self.code,self.param_grid,self.cfg,self.metric,progress_cb=cb)
            elif self.mode=='genetic':
                r=GeneticOptimizer(population_size=self.ga_pop,generations=self.ga_gen).run(self.data,self.code,self.param_grid,self.cfg,self.metric,progress_cb=cb)
            else:
                r=WalkForwardTester().run(self.data,self.code,self.param_grid,self.cfg,metric=self.metric,progress_cb=lambda p,m='': self.progress.emit(p,m,0.0))
            self.finished.emit(r)
        except Exception as e: self.error.emit(f"{e}\n\n{traceback.format_exc()}")

class OptimizerTab(QWidget):
    status_msg=pyqtSignal(str)
    def __init__(self,dm,strat):
        super().__init__(); self.dm=dm;self.strat=strat; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        cfg=QGroupBox("Configuración"); cfg.setMaximumHeight(110); cl=QHBoxLayout(cfg)
        def add(l,w): cl.addWidget(QLabel(l)); cl.addWidget(w)
        self.sym=QComboBox(); add("Símbolo:",self.sym)
        self.method=QComboBox(); self.method.addItems(["Grid Search","Genético","Walk-Forward"]); add("Método:",self.method)
        self.metric=QComboBox(); self.metric.addItems(["Sharpe","Retorno total","Sortino","Calmar","Profit Factor","Win Rate","CAGR","Max Drawdown"]); add("Métrica:",self.metric)
        self.p1n=QComboBox(); self.p1n.setEditable(True); self.p1n.addItems(["fast_period","period","fast"]); add("P1 nombre:",self.p1n)
        self.p1a=QSpinBox(); self.p1a.setRange(1,500); self.p1a.setValue(5); add("min:",self.p1a)
        self.p1b=QSpinBox(); self.p1b.setRange(1,500); self.p1b.setValue(30); add("max:",self.p1b)
        self.p1s=QSpinBox(); self.p1s.setRange(1,50); self.p1s.setValue(5); add("step:",self.p1s)
        self.p2n=QComboBox(); self.p2n.setEditable(True); self.p2n.addItems(["slow_period","slow","None"]); add("P2:",self.p2n)
        self.p2a=QSpinBox(); self.p2a.setRange(1,500); self.p2a.setValue(20); add("min:",self.p2a)
        self.p2b=QSpinBox(); self.p2b.setRange(1,500); self.p2b.setValue(100); add("max:",self.p2b)
        self.p2s=QSpinBox(); self.p2s.setRange(1,50); self.p2s.setValue(10); add("step:",self.p2s)
        add("Gen:",self._mk_spin(5,200,30,'ga_gen')); add("Pop:",self._mk_spin(10,200,40,'ga_pop'))
        cl.addStretch()
        self.run_btn=QPushButton("⚙️ Optimizar"); self.run_btn.setObjectName("warning")
        self.run_btn.setFixedHeight(44); self.run_btn.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        self.run_btn.clicked.connect(self._run); cl.addWidget(self.run_btn)
        L.addWidget(cfg)
        self.prog=QProgressBar(); self.prog.setVisible(False); L.addWidget(self.prog)
        sp=QSplitter(Qt.Orientation.Horizontal)
        self.tbl=QTableWidget(); self.tbl.setAlternatingRowColors(True)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        sp.addWidget(self.tbl)
        self._fig=Figure(facecolor=C['bg']); self._cv=FigureCanvasQTAgg(self._fig)
        w=QWidget(); vl=QVBoxLayout(w); vl.setContentsMargins(0,0,0,0)
        vl.addWidget(NavigationToolbar2QT(self._cv,self)); vl.addWidget(self._cv)
        sp.addWidget(w); sp.setSizes([500,900]); L.addWidget(sp,1)
        self.log=QLabel(""); self.log.setStyleSheet("color:#6c7086;font-size:10px;"); L.addWidget(self.log)

    def _mk_spin(self,mn,mx,val,attr):
        s=QSpinBox(); s.setRange(mn,mx); s.setValue(val); setattr(self,attr,s); return s

    def update_symbols(self,syms):
        cur=self.sym.currentText(); self.sym.blockSignals(True); self.sym.clear()
        self.sym.addItems(syms)
        if cur in syms: self.sym.setCurrentText(cur)
        self.sym.blockSignals(False)

    def _run(self):
        sym=self.sym.currentText()
        if not sym: return
        data=self.dm.get_data(sym)
        if data is None or data.empty: return
        code=self.strat.get_code()
        pg={}
        p1=self.p1n.currentText().strip()
        if p1 and p1.lower()!='none': pg[p1]=ParamRange(self.p1a.value(),self.p1b.value(),self.p1s.value())
        p2=self.p2n.currentText().strip()
        if p2 and p2.lower()!='none': pg[p2]=ParamRange(self.p2a.value(),self.p2b.value(),self.p2s.value())
        if not pg: self.log.setText("❌ Define al menos un parámetro"); return
        cfg={'initial_capital':10000.0,'commission':0.001,'sizing_method':'pct_equity','position_size':1.0}
        mode={'Grid Search':'grid','Genético':'genetic','Walk-Forward':'wf'}[self.method.currentText()]
        self.run_btn.setEnabled(False); self.prog.setVisible(True); self.prog.setValue(0)
        self.log.setText(f"⏳ {self.method.currentText()} | métrica: {self.metric.currentText()}")
        self._t=OptThread(mode,data,code,pg,cfg,self.metric.currentText(),self.ga_pop.value(),self.ga_gen.value())
        self._t.progress.connect(lambda p,ps,v: (self.prog.setValue(p),self.log.setText(f"⚙️ {p}% | {ps[:50]} → {v:.3f}")))
        self._t.finished.connect(self._done); self._t.error.connect(self._err); self._t.start()

    def _done(self,r):
        self.run_btn.setEnabled(True); self.prog.setVisible(False)
        if isinstance(r,dict) and 'windows_df' in r:
            df=r['windows_df']; self.log.setText(f"✅ Walk-Forward | WF Efficiency: {r['wf_efficiency']:.3f}")
        else:
            df=r; self.log.setText(f"✅ Completado — {len(df) if df is not None else 0} combinaciones")
        if df is not None and not df.empty:
            self._fill(df); self._plot(df)

    def _err(self,e):
        self.run_btn.setEnabled(True); self.prog.setVisible(False); self.log.setText(f"❌ {e.split(chr(10))[0][:80]}")

    def _fill(self,df):
        cols=list(df.columns); self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols); self.tbl.setRowCount(min(len(df),500))
        for i,(_,row) in enumerate(df.head(500).iterrows()):
            for j,col in enumerate(cols):
                it=QTableWidgetItem(str(round(row[col],4)) if isinstance(row[col],float) else str(row[col]))
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if i==0: it.setForeground(QColor(C['green']))
                self.tbl.setItem(i,j,it)

    def _plot(self,df):
        self._fig.clear(); metric=self.metric.currentText()
        if metric not in df.columns: return
        num_p=[c for c in df.columns if c not in (metric,'generation','Window') and df[c].dtype in ('int64','float64')]
        ax=self._fig.add_subplot(111)
        ax.set_facecolor(C['bg']); ax.tick_params(colors=C['text'],labelsize=7)
        ax.grid(color=C['surface0'],lw=0.4,alpha=0.5)
        for sp in ax.spines.values(): sp.set_color(C['surface1'])
        if len(num_p)>=2:
            p1,p2=num_p[:2]
            try:
                import numpy as np
                piv=df.pivot_table(index=p1,columns=p2,values=metric,aggfunc='max')
                im=ax.imshow(piv.values,cmap='RdYlGn',aspect='auto')
                ax.set_xticks(range(len(piv.columns))); ax.set_yticks(range(len(piv.index)))
                ax.set_xticklabels([str(v) for v in piv.columns],rotation=45,fontsize=7,color=C['text'])
                ax.set_yticklabels([str(v) for v in piv.index],fontsize=7,color=C['text'])
                ax.set_xlabel(p2,color=C['text']); ax.set_ylabel(p1,color=C['text'])
                ax.set_title(f'Heatmap: {metric}',color=C['text'],fontsize=11,fontweight='bold')
                self._fig.colorbar(im,ax=ax)
            except: pass
        elif len(num_p)>=1:
            p1=num_p[0]; ds=df.sort_values(p1)
            ax.plot(ds[p1],ds[metric],color=C['blue'],lw=1.5,marker='o',ms=3)
            ax.fill_between(ds[p1],ds[metric],ds[metric].min(),alpha=0.1,color=C['blue'])
            ax.set_xlabel(p1,color=C['text']); ax.set_ylabel(metric,color=C['text'])
            ax.set_title(f'{p1} vs {metric}',color=C['text'],fontsize=11,fontweight='bold')
        ax.yaxis.tick_right(); self._fig.patch.set_facecolor(C['bg']); self._cv.draw()
