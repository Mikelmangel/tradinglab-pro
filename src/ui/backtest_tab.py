"""TradingLab Pro — Backtest Tab v2: bar-by-bar, annual breakdown, Monte Carlo, heatmap."""
import traceback, numpy as np, pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from src.core.backtest_engine import BacktestEngine, BacktestConfig
from src.styles.theme import C as TC

C = TC

class BtThread(QThread):
    finished=pyqtSignal(dict); error=pyqtSignal(str)
    def __init__(self,data,code,cfg,sym):
        super().__init__(); self.data=data;self.code=code;self.cfg=cfg;self.sym=sym
    def run(self):
        try:
            ns={'pd':pd,'np':np}; exec(self.code,ns)
            fn=ns.get('generate_signals')
            if not fn: self.error.emit("Falta generate_signals(data)"); return
            sig=fn(self.data)
            r=BacktestEngine().run(self.data,sig,self.cfg,self.sym)
            self.finished.emit(r)
        except Exception as e: self.error.emit(f"{e}\n\n{traceback.format_exc()}")

class BacktestTab(QWidget):
    status_msg=pyqtSignal(str)
    def __init__(self,dm,strat_tab):
        super().__init__(); self.dm=dm; self.strat=strat_tab; self._r=None; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        cfg=QGroupBox("Configuración"); cfg.setMaximumHeight(110); cl=QHBoxLayout(cfg)
        def add(lbl,w): cl.addWidget(QLabel(lbl)); cl.addWidget(w)
        self.sym=QComboBox(); self.sym.setMinimumWidth(100); add("Símbolo:",self.sym)
        self.capital=QDoubleSpinBox(); self.capital.setRange(100,1e8); self.capital.setValue(10000); self.capital.setGroupSeparatorShown(True); add("Capital:",self.capital)
        self.sizing=QComboBox(); self.sizing.addItems(["% equity","$ fijo","Acciones","ATR risk","% riesgo","Kelly"]); add("Sizing:",self.sizing)
        self.sz_val=QDoubleSpinBox(); self.sz_val.setRange(0.001,1e6); self.sz_val.setValue(1.0); self.sz_val.setDecimals(3); add("Valor:",self.sz_val)
        self.sl=QDoubleSpinBox(); self.sl.setRange(0,0.5); self.sl.setValue(0); self.sl.setDecimals(3); self.sl.setSpecialValueText("—"); add("SL%:",self.sl)
        self.tp=QDoubleSpinBox(); self.tp.setRange(0,2.0); self.tp.setValue(0); self.tp.setDecimals(3); self.tp.setSpecialValueText("—"); add("TP%:",self.tp)
        self.trail=QDoubleSpinBox(); self.trail.setRange(0,0.5); self.trail.setValue(0); self.trail.setDecimals(3); self.trail.setSpecialValueText("—"); add("Trail%:",self.trail)
        self.comm=QDoubleSpinBox(); self.comm.setRange(0,0.05); self.comm.setValue(0.001); self.comm.setDecimals(4); add("Comisión:",self.comm)
        self.shorts=QCheckBox("Shorts"); cl.addWidget(self.shorts)
        cl.addStretch()
        self.run_btn=QPushButton("▶  Ejecutar"); self.run_btn.setObjectName("success")
        self.run_btn.setFixedHeight(44); self.run_btn.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        self.run_btn.clicked.connect(self._run); cl.addWidget(self.run_btn)
        L.addWidget(cfg)
        # Main split
        sp=QSplitter(Qt.Orientation.Horizontal)
        left=QTabWidget()
        # Metrics
        self.met_table=QTableWidget(); self.met_table.setColumnCount(2)
        self.met_table.setHorizontalHeaderLabels(["Métrica","Valor"])
        self.met_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.met_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.met_table.setAlternatingRowColors(True); left.addTab(self.met_table,"📊 Métricas")
        # Annual
        self.ann_table=QTableWidget(); self.ann_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ann_table.setAlternatingRowColors(True); left.addTab(self.ann_table,"📅 Por Año")
        # Trades
        self.tr_table=QTableWidget(); self.tr_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tr_table.setAlternatingRowColors(True); left.addTab(self.tr_table,"📋 Trades")
        sp.addWidget(left)
        # Charts
        right=QTabWidget()
        for attr,title in [('_fig','📈 Equity & DD'),('_fig2','📅 Heatmap Mensual'),('_fig3','📊 Análisis'),('_fig4','🎲 Monte Carlo')]:
            fig=Figure(facecolor=C['bg']); setattr(self,attr,fig)
            canvas=FigureCanvasQTAgg(fig); setattr(self,attr.replace('_fig','_cv') if attr!='_fig' else '_cv',canvas)
            w=QWidget(); vl=QVBoxLayout(w); vl.setContentsMargins(0,0,0,0)
            vl.addWidget(NavigationToolbar2QT(canvas,self)); vl.addWidget(canvas)
            right.addTab(w,title)
        sp.addWidget(right); sp.setSizes([420,1100]); L.addWidget(sp,1)
        self.log=QLabel("Ejecuta un backtest para ver resultados.")
        self.log.setStyleSheet("color:#6c7086;font-size:10px;padding:2px 6px;"); L.addWidget(self.log)

    def update_symbols(self,syms):
        cur=self.sym.currentText(); self.sym.blockSignals(True); self.sym.clear()
        self.sym.addItems(syms)
        if cur in syms: self.sym.setCurrentText(cur)
        self.sym.blockSignals(False)

    def _cfg(self):
        sm={"% equity":"pct_equity","$ fijo":"fixed_dollar","Acciones":"fixed_shares",
            "ATR risk":"atr_risk","% riesgo":"fixed_risk_pct","Kelly":"kelly"}
        return BacktestConfig(
            initial_capital=self.capital.value(),
            sizing_method=sm[self.sizing.currentText()],
            position_size=self.sz_val.value(),
            commission=self.comm.value(),
            stop_loss_pct=self.sl.value() or None,
            take_profit_pct=self.tp.value() or None,
            trailing_stop_pct=self.trail.value() or None,
            allow_short=self.shorts.isChecked(),
        )

    def _run(self):
        sym=self.sym.currentText()
        if not sym: return
        data=self.dm.get_data(sym)
        if data is None or data.empty: QMessageBox.warning(self,"Sin datos",f"Descarga {sym} primero"); return
        code=self.strat.get_code()
        if not code.strip(): return
        self.run_btn.setEnabled(False)
        self.log.setText(f"⏳ Ejecutando '{self.strat.get_name()}' en {sym}...")
        self._t=BtThread(data,code,self._cfg(),sym)
        self._t.finished.connect(self._done); self._t.error.connect(self._err); self._t.start()

    def _done(self,r):
        self.run_btn.setEnabled(True); self._r=r
        self._fill_metrics(r['metrics'])
        self._fill_annual(r['annual_breakdown'])
        self._fill_trades(r['trades_df'])
        self._plot_equity(r)
        self._plot_heatmap(r['monthly_heatmap'])
        self._plot_analysis(r)
        self._plot_monte_carlo(r)
        n=len(r['trades_df']) if not r['trades_df'].empty else 0
        self.log.setText(f"✅ Completado — {n} trades")
        self.status_msg.emit("Backtest completado")

    def _err(self,e):
        self.run_btn.setEnabled(True)
        self.log.setText(f"❌ {e.split(chr(10))[0][:100]}")
        QMessageBox.critical(self,"Error",e[:1500])

    def _fill_metrics(self,m):
        rows=list(m.items()); self.met_table.setRowCount(len(rows))
        for i,(k,v) in enumerate(rows):
            sep=k.startswith('──')
            ki=QTableWidgetItem(k.replace('──','').strip() if sep else k)
            vi=QTableWidgetItem(str(v))
            if sep:
                for it in (ki,vi): it.setBackground(QColor(C['surface0'])); it.setForeground(QColor(C['blue']))
            else:
                vi.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                try:
                    n=float(str(v).replace('%','').replace('$','').replace(',','').replace('+',''))
                    if ('%' in str(v) or '$' in str(v)) and n!=0:
                        vi.setForeground(QColor(C['green'] if n>0 else C['red']))
                except: pass
            self.met_table.setItem(i,0,ki); self.met_table.setItem(i,1,vi)

    def _fill_annual(self,df):
        if df is None or df.empty: return
        df2=df.drop(columns=['_ret'],errors='ignore')
        cols=list(df2.columns); self.ann_table.setColumnCount(len(cols))
        self.ann_table.setHorizontalHeaderLabels(cols); self.ann_table.setRowCount(len(df2))
        self.ann_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i,(_,row) in enumerate(df2.iterrows()):
            for j,col in enumerate(cols):
                it=QTableWidgetItem(str(row[col]))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col=='Retorno':
                    try:
                        v=float(str(row[col]).replace('%','').replace('+',''))
                        it.setForeground(QColor(C['green'] if v>0 else C['red']))
                    except: pass
                self.ann_table.setItem(i,j,it)

    def _fill_trades(self,df):
        if df is None or df.empty: return
        cols=list(df.columns); self.tr_table.setColumnCount(len(cols))
        self.tr_table.setHorizontalHeaderLabels(cols); self.tr_table.setRowCount(len(df))
        self.tr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i,(_,row) in enumerate(df.iterrows()):
            for j,col in enumerate(cols):
                it=QTableWidgetItem(str(row[col]))
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if 'P&L' in col:
                    try: v=float(str(row[col]).replace('+','').replace('$',''))
                    except: v=0
                    it.setForeground(QColor(C['green'] if v>0 else C['red']))
                self.tr_table.setItem(i,j,it)

    def _plot_equity(self,r):
        self._fig.clear()
        eq=r['equity_curve']
        if eq.empty: return
        x=np.arange(len(eq)); dates=[str(d)[:10] for d in eq.index]
        init=float(r['equity_curve']['value'].iloc[0])
        gs=gridspec.GridSpec(3,1,figure=self._fig,hspace=0.08,height_ratios=[4,1.5,1],
                             left=0.02,right=0.95,top=0.95,bottom=0.08)
        ax1=self._fig.add_subplot(gs[0]); ax2=self._fig.add_subplot(gs[1],sharex=ax1); ax3=self._fig.add_subplot(gs[2])
        ev=eq['value'].values
        ax1.plot(x,ev,color=C['blue'],lw=1.6)
        ax1.fill_between(x,ev,init,where=ev>=init,alpha=0.12,color=C['green'])
        ax1.fill_between(x,ev,init,where=ev<init,alpha=0.12,color=C['red'])
        ax1.axhline(init,color=C['surface1'],lw=0.7,ls='--')
        ann=r.get('annual_breakdown')
        if ann is not None and not ann.empty and '_ret' in ann.columns:
            for _,row in ann.iterrows():
                yr=row['Año']
                try:
                    yr_mask=eq.index.year==yr
                    if yr_mask.any():
                        xi=np.where(yr_mask)[0][0]
                        ax1.axvline(xi,color=C['surface1'],lw=0.5,alpha=0.5)
                        ret_v=float(str(row['_ret']))
                        ax1.text(xi+1,ev[xi]*1.01,f"{ret_v:+.0f}%",fontsize=6,color=C['green'] if ret_v>0 else C['red'])
                except: pass
        ax1.set_title("Curva de Capital",color=C['text'],fontsize=11,fontweight='bold')
        self._sa(ax1); self._xt(ax1,x,dates,show=False)
        rm=np.maximum.accumulate(ev); dd=(ev-rm)/rm*100 if rm.max()>0 else ev-ev
        ax2.fill_between(x,dd,0,alpha=0.6,color=C['red']); ax2.plot(x,dd,color=C['red'],lw=0.8)
        ax2.set_title("Drawdown %",color=C['text'],fontsize=9); self._sa(ax2); self._xt(ax2,x,dates,show=False)
        ret=r['daily_returns']
        try:
            monthly=(1+ret).resample('ME').prod()-1
            mx=np.arange(len(monthly)); bc=[C['green'] if v>=0 else C['red'] for v in monthly]
            ax3.bar(mx,monthly*100,color=bc,width=0.7,alpha=0.8)
            ax3.axhline(0,color=C['surface1'],lw=0.6)
            step=max(1,len(mx)//6)
            ml=[str(d)[:7] for d in monthly.index]
            ax3.set_xticks(list(mx[::step])); ax3.set_xticklabels(ml[::step],rotation=30,fontsize=6,color=C['text'])
        except: pass
        ax3.set_title("Retornos Mensuales %",color=C['text'],fontsize=9); self._sa(ax3)
        self._fig.patch.set_facecolor(C['bg']); self._cv.draw()

    def _plot_heatmap(self,hm):
        self._fig2.clear()
        if hm is None or hm.empty: return
        ax=self._fig2.add_subplot(111); self._sa(ax)
        months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
        years=list(hm.index)
        import matplotlib.colors as mcolors
        cmap=mcolors.LinearSegmentedColormap.from_list('rg',["#f38ba8","#313244","#a6e3a1"])
        data_arr=hm.reindex(columns=range(1,13)).values
        im=ax.imshow(data_arr,cmap=cmap,aspect='auto',vmin=-20,vmax=20)
        ax.set_xticks(range(12)); ax.set_xticklabels(months,color=C['text'],fontsize=8)
        ax.set_yticks(range(len(years))); ax.set_yticklabels([str(y) for y in years],color=C['text'],fontsize=8)
        for i in range(len(years)):
            for j in range(12):
                try:
                    v=data_arr[i,j]
                    if not np.isnan(v): ax.text(j,i,f"{v:.1f}",ha='center',va='center',fontsize=7,color=C['text'])
                except: pass
        ax.set_title("Retornos Mensuales % (Heatmap Calendar)",color=C['text'],fontsize=11,fontweight='bold')
        self._fig2.colorbar(im,ax=ax,shrink=0.6)
        self._fig2.patch.set_facecolor(C['bg']); self._fig2.tight_layout()
        self._cv2.draw() if hasattr(self,'_cv2') else None
    def _cv2_canvas(self):
        return getattr(self,'_cv2',None)

    def _plot_analysis(self,r):
        fig=getattr(self,'_fig3',None)
        if fig is None: return
        fig.clear(); df=r['trades_df']
        if df is None or df.empty: return
        gs=gridspec.GridSpec(2,2,figure=fig,hspace=0.45,wspace=0.35,left=0.06,right=0.97,top=0.93,bottom=0.1)
        axes=[fig.add_subplot(gs[i//2,i%2]) for i in range(4)]
        for ax in axes: self._sa(ax)
        if 'P&L %' in df.columns:
            pnl=df['P&L %'].astype(float)
            ws=pnl[pnl>=0]; ls=pnl[pnl<0]
            if len(ws): axes[0].hist(ws,bins=min(15,max(1,len(ws)//2+1)),color=C['green'],alpha=0.7,label=f'Win ({len(ws)})')
            if len(ls): axes[0].hist(ls,bins=min(15,max(1,len(ls)//2+1)),color=C['red'],alpha=0.7,label=f'Loss ({len(ls)})')
            axes[0].axvline(0,color=C['text'],lw=0.8)
            axes[0].legend(facecolor=C['surface0'],labelcolor=C['text'],fontsize=7)
        axes[0].set_title('Distribución P&L %',color=C['text'],fontsize=10,fontweight='bold')
        if 'P&L $' in df.columns:
            cum=df['P&L $'].astype(str).str.replace('+','',regex=False).astype(float).cumsum()
            axes[1].plot(cum.values,color=C['blue'],lw=1.4)
            axes[1].fill_between(range(len(cum)),cum.values,0,where=cum.values>=0,alpha=0.15,color=C['green'])
            axes[1].fill_between(range(len(cum)),cum.values,0,where=cum.values<0,alpha=0.15,color=C['red'])
            axes[1].axhline(0,color=C['surface1'],lw=0.6)
        axes[1].set_title('P&L Acumulado $',color=C['text'],fontsize=10,fontweight='bold')
        if 'Resultado' in df.columns:
            wn=df['Resultado'].str.contains('Win').sum(); ln=len(df)-wn
            if wn+ln>0:
                axes[2].pie([wn,ln],labels=[f'Win {wn}',f'Loss {ln}'],colors=[C['green'],C['red']],
                           autopct='%1.1f%%',textprops={'color':C['text'],'fontsize':8})
        axes[2].set_title('Win/Loss',color=C['text'],fontsize=10,fontweight='bold')
        if 'Apertura' in df.columns:
            try:
                m=pd.to_datetime(df['Apertura']).dt.to_period('M').value_counts().sort_index()
                axes[3].bar(range(len(m)),m.values,color=C['blue'],alpha=0.8)
                step=max(1,len(m)//5)
                axes[3].set_xticks(list(range(0,len(m),step)))
                axes[3].set_xticklabels([str(m.index[i]) for i in range(0,len(m),step)],rotation=30,fontsize=6,color=C['text'])
            except: pass
        axes[3].set_title('Trades por mes',color=C['text'],fontsize=10,fontweight='bold')
        fig.patch.set_facecolor(C['bg'])
        cv=getattr(self,'_cv3',None)
        if cv: cv.draw()

    def _plot_monte_carlo(self,r):
        fig=getattr(self,'_fig4',None)
        if fig is None: return
        fig.clear(); df=r['trades_df']
        if df is None or df.empty or 'P&L %' not in df.columns: return
        from src.core.optimizer import MonteCarloSimulator
        pnl=df['P&L %'].astype(float).tolist()
        if len(pnl)<3: return
        mc=MonteCarloSimulator(); res=mc.run(pnl,self.capital.value(),n_simulations=500)
        if not res: return
        gs=gridspec.GridSpec(1,2,figure=fig,wspace=0.3,left=0.06,right=0.97,top=0.92,bottom=0.1)
        ax1=fig.add_subplot(gs[0]); ax2=fig.add_subplot(gs[1])
        self._sa(ax1); self._sa(ax2)
        for path in res['equity_paths'][:100]: ax1.plot(path,color=C['blue'],alpha=0.04,lw=0.5)
        paths=res['equity_paths'][:500]
        if not paths: return
        ml = max(len(p) for p in paths)
        padded = np.array([np.pad(p, (0, ml - len(p)), constant_values=p[-1]) for p in paths])
        ax1.plot(np.percentile(padded,5,axis=0),color=C['red'],lw=1.5,label='P5')
        ax1.plot(np.percentile(padded,50,axis=0),color=C['yellow'],lw=1.5,label='P50')
        ax1.plot(np.percentile(padded,95,axis=0),color=C['green'],lw=1.5,label='P95')
        ax1.axhline(self.capital.value(),color=C['surface1'],lw=0.7,ls='--')
        ax1.legend(facecolor=C['surface0'],labelcolor=C['text'],fontsize=7)
        ax1.set_title('Monte Carlo — 500 sim.',color=C['text'],fontsize=10,fontweight='bold')
        ax1.yaxis.tick_right()
        fe=res['final_equities']
        ax2.hist(fe,bins=30,color=C['blue'],alpha=0.7)
        init=self.capital.value()
        ax2.axvline(init,color=C['surface1'],lw=1.0,ls='--',label='Capital inicial')
        ax2.axvline(res['q5_final'],color=C['red'],lw=1.2,label=f"P5 ${res['q5_final']:,.0f}")
        ax2.axvline(res['q50_final'],color=C['yellow'],lw=1.2,label=f"P50 ${res['q50_final']:,.0f}")
        ax2.axvline(res['q95_final'],color=C['green'],lw=1.2,label=f"P95 ${res['q95_final']:,.0f}")
        ax2.legend(facecolor=C['surface0'],labelcolor=C['text'],fontsize=7)
        ax2.set_title(f"Capital Final (Ruin: {res['prob_of_ruin']:.1f}%)",color=C['text'],fontsize=10,fontweight='bold')
        ax2.text(0.02,0.95,f"CAGR P5: {res['cagr_p5']:+.1f}%\nCAGR P50: {res['cagr_p50']:+.1f}%\nCAGR P95: {res['cagr_p95']:+.1f}%",
                 transform=ax2.transAxes,va='top',fontsize=8,color=C['text'],
                 bbox=dict(facecolor=C['surface0'],alpha=0.8))
        ax2.yaxis.tick_right()
        fig.patch.set_facecolor(C['bg'])
        cv=getattr(self,'_cv4',None)
        if cv: cv.draw()

    def _sa(self,ax):
        ax.set_facecolor(C['bg']); ax.tick_params(colors=C['text'],labelsize=7)
        ax.grid(color=C['surface0'],lw=0.4,alpha=0.5)
        for sp in ax.spines.values(): sp.set_color(C['surface1']); sp.set_lw(0.6)
        ax.yaxis.tick_right()
    def _xt(self,ax,x,dates,show=True):
        step=max(1,len(x)//8); ticks=list(range(0,len(x),step))
        ax.set_xticks(ticks)
        ax.set_xticklabels([dates[i] for i in ticks] if show else [],rotation=30,fontsize=7,color=C['text'])
        ax.set_xlim(-1,len(x))
    def get_result(self): return self._r
