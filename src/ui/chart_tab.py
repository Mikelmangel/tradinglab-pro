"""TradingLab Pro — Chart Tab with 40+ indicators and MTF support."""
import numpy as np, pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from src.styles.theme import C as TC
from src.core.indicators import INDICATOR_REGISTRY, compute, list_by_category

C = TC

class ChartTab(QWidget):
    def __init__(self, dm):
        super().__init__(); self.dm = dm; self._setup_ui()
    def _setup_ui(self):
        L = QVBoxLayout(self); L.setContentsMargins(4,4,4,4)
        top = QHBoxLayout()
        top.addWidget(QLabel("Símbolo:")); self.sym = QComboBox(); self.sym.setMinimumWidth(100); top.addWidget(self.sym)
        top.addWidget(QLabel("Intervalo:")); self.interval = QComboBox()
        self.interval.addItems(['1d','1wk','1mo','1h','4h','15m','5m']); top.addWidget(self.interval)
        top.addWidget(QLabel("Tipo:")); self.ctype = QComboBox()
        self.ctype.addItems(['Candlestick','OHLC','Línea','Área','Heikin-Ashi']); top.addWidget(self.ctype)
        top.addWidget(QLabel("Barras:")); self.nbars = QSpinBox()
        self.nbars.setRange(20,2000); self.nbars.setValue(200); top.addWidget(self.nbars)
        top.addWidget(QLabel("MTF:")); self.mtf = QComboBox()
        self.mtf.addItems(['—','1wk','1mo','4h','1h']); top.addWidget(self.mtf)
        btn=QPushButton("📈 Dibujar"); btn.setObjectName("primary"); btn.clicked.connect(self._draw); top.addWidget(btn)
        top.addStretch(); L.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        # Indicator tree
        ind_box=QGroupBox("Indicadores"); ind_l=QVBoxLayout(ind_box)
        self.ind_tree=QTreeWidget(); self.ind_tree.setHeaderHidden(True)
        self.ind_tree.setMaximumWidth(220)
        for cat,names in list_by_category().items():
            parent=QTreeWidgetItem(self.ind_tree,[cat])
            for n in names:
                child=QTreeWidgetItem(parent,[n]); child.setCheckState(0,Qt.CheckState.Unchecked)
        self.ind_tree.expandAll(); ind_l.addWidget(self.ind_tree)
        ind_box.setMaximumWidth(230); split.addWidget(ind_box)
        # Chart
        self._fig=Figure(facecolor=C['bg'])
        self._canvas=FigureCanvasQTAgg(self._fig)
        cw=QWidget(); cl=QVBoxLayout(cw); cl.setContentsMargins(0,0,0,0)
        cl.addWidget(NavigationToolbar2QT(self._canvas,self)); cl.addWidget(self._canvas)
        split.addWidget(cw); split.setSizes([230,1200]); L.addWidget(split,1)
    def update_symbols(self,syms):
        cur=self.sym.currentText(); self.sym.blockSignals(True); self.sym.clear()
        self.sym.addItems(syms)
        if cur in syms: self.sym.setCurrentText(cur)
        self.sym.blockSignals(False)
    def _get_checked(self):
        checked=[]
        root=self.ind_tree.invisibleRootItem()
        for i in range(root.childCount()):
            cat=root.child(i)
            for j in range(cat.childCount()):
                ch=cat.child(j)
                if ch.checkState(0)==Qt.CheckState.Checked: checked.append(ch.text(0))
        return checked
    def _draw(self):
        sym=self.sym.currentText()
        if not sym: return
        data=self.dm.get_data(sym,self.interval.currentText())
        if data is None or data.empty: return
        data=data.tail(self.nbars.value())
        checked=self._get_checked()
        overlays=[n for n in checked if INDICATOR_REGISTRY[n]['overlay']]
        panels=[n for n in checked if not INDICATOR_REGISTRY[n]['overlay']]
        panels=panels[:3]  # max 3 sub-panels
        n_panels=1+len(panels)+1  # price + indicators + volume
        ratios=[4]+[1.5]*len(panels)+[1]
        self._fig.clear()
        gs=gridspec.GridSpec(n_panels,1,figure=self._fig,hspace=0.05,
                             left=0.02,right=0.97,top=0.95,bottom=0.06,height_ratios=ratios)
        axes=[self._fig.add_subplot(gs[i]) for i in range(n_panels)]
        ax=axes[0]
        x=np.arange(len(data)); dates=[str(d)[:10] for d in data.index]
        ct=self.ctype.currentText()
        if ct=='Heikin-Ashi':
            from src.core.indicators import heikin_ashi
            ha=heikin_ashi(data['Open'],data['High'],data['Low'],data['Close'])
            o_=ha['HA_OPEN'].values; h_=ha['HA_HIGH'].values; l_=ha['HA_LOW'].values; c_=ha['HA_CLOSE'].values
        else:
            o_=data['Open'].values; h_=data['High'].values; l_=data['Low'].values; c_=data['Close'].values
        if ct in ('Candlestick','OHLC','Heikin-Ashi'):
            for i,(o,hi,lo,cl) in enumerate(zip(o_,h_,l_,c_)):
                col=C['green'] if cl>=o else C['red']
                ax.plot([i,i],[lo,hi],color=col,lw=0.8)
                if ct!='OHLC': ax.bar(i,cl-o,bottom=o,width=0.7,color=col,alpha=0.9)
                else:
                    ax.plot([i-0.3,i],[o,o],color=col,lw=1.2)
                    ax.plot([i,i+0.3],[cl,cl],color=col,lw=1.2)
        elif ct=='Área':
            ax.fill_between(x,c_,c_.min(),alpha=0.3,color=C['blue'])
            ax.plot(x,c_,color=C['blue'],lw=1.2)
        else:
            ax.plot(x,c_,color=C['blue'],lw=1.2)
        # Overlays
        COLORS=[C['yellow'],C['mauve'],C['peach'],C['teal'],C['green'],C['red'],C['pink'],C['lavender']]
        for ci,name in enumerate(overlays):
            try:
                r=compute(name,data); col=COLORS[ci%len(COLORS)]
                if isinstance(r,pd.DataFrame):
                    for col_name,series in r.items():
                        ax.plot(x,series.values,lw=1.0,alpha=0.8,color=col,label=col_name)
                        if 'UPPER' in col_name: ax.fill_between(x,series.values,r.filter(like='LOWER').iloc[:,0].values if r.filter(like='LOWER').shape[1]>0 else series.values,alpha=0.05,color=col)
                else:
                    ax.plot(x,r.values,lw=1.0,color=col,label=name)
            except: pass
        # MTF line
        mtf_sel=self.mtf.currentText()
        if mtf_sel!='—':
            try:
                _,sec=self.dm.get_mtf(sym,self.interval.currentText(),mtf_sel)
                if sec is not None:
                    sec=sec.reindex(data.index,method='ffill').tail(self.nbars.value())
                    mtf_sma=sec['Close'].rolling(20).mean().values
                    ax.plot(x,mtf_sma,color=C['pink'],lw=2.0,ls='--',label=f'SMA20 {mtf_sel}',alpha=0.8)
            except: pass
        ax.set_title(f"{sym}  —  {self.interval.currentText()}  ({len(data)} barras)",color=C['text'],fontsize=11,fontweight='bold')
        ax.legend(fontsize=7,facecolor=C['surface0'],labelcolor=C['text'],loc='upper left') if overlays else None
        self._sa(ax); ax.set_xlim(-1,len(x))
        step=max(1,len(x)//8)
        ax.set_xticks(list(range(0,len(x),step)))
        ax.set_xticklabels([])
        # Sub-panels
        for pi,name in enumerate(panels):
            pax=axes[pi+1]
            try:
                r=compute(name,data); col=COLORS[pi%len(COLORS)]
                self._sa(pax); pax.set_xlim(-1,len(x))
                if isinstance(r,pd.DataFrame):
                    for cn,series in r.items():
                        if 'HIST' in cn: pax.bar(x,series.values,color=[C['green'] if v>=0 else C['red'] for v in series.values],alpha=0.7,width=0.7)
                        else: pax.plot(x,series.values,lw=1.0,label=cn)
                else:
                    pax.plot(x,r.values,lw=1.0,color=col)
                # Reference lines
                if 'RSI' in name: pax.axhline(30,color=C['green'],lw=0.7,ls='--'); pax.axhline(70,color=C['red'],lw=0.7,ls='--'); pax.axhline(50,color=C['surface1'],lw=0.5,ls=':')
                elif 'MACD' in name or 'CMO' in name or 'AO' in name: pax.axhline(0,color=C['surface1'],lw=0.7)
                elif 'ADX' in name: pax.axhline(25,color=C['yellow'],lw=0.7,ls='--')
                pax.set_title(name,color=C['text'],fontsize=9,loc='left')
                pax.yaxis.tick_right(); pax.set_xticklabels([])
            except: pass
        # Volume
        vax=axes[-1]; self._sa(vax); vax.set_xlim(-1,len(x))
        vc=[C['green'] if c_[i]>=o_[i] else C['red'] for i in range(len(x))]
        vax.bar(x,data['Volume'].values,color=vc,alpha=0.6,width=0.7)
        vax.set_title('Volume',color=C['text'],fontsize=8,loc='left')
        vax.yaxis.tick_right()
        vax.set_xticks(list(range(0,len(x),step)))
        vax.set_xticklabels([dates[i] for i in range(0,len(x),step)],rotation=30,fontsize=6,color=C['text'])
        self._fig.patch.set_facecolor(C['bg']); self._canvas.draw()
    def _sa(self,ax):
        ax.set_facecolor(C['bg']); ax.tick_params(colors=C['text'],labelsize=7)
        ax.grid(color=C['surface0'],lw=0.4,alpha=0.5)
        for sp in ax.spines.values(): sp.set_color(C['surface1']); sp.set_lw(0.6)
        ax.yaxis.tick_right()
