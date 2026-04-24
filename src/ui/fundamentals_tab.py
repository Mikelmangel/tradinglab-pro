"""TradingLab Pro — Fundamentals Tab."""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from src.core.fundamentals import get_fundamentals, get_financials, fundamental_score

class FundThread(QThread):
    done=pyqtSignal(object,object,str)
    def __init__(self,sym): super().__init__(); self.sym=sym
    def run(self):
        info=get_fundamentals(self.sym); fin=get_financials(self.sym)
        score_text=""
        try:
            import yfinance as yf
            raw=yf.Ticker(self.sym).info
            s,t=fundamental_score(raw); score_text=t
        except: pass
        self.done.emit(info,fin,score_text)

class FundamentalsTab(QWidget):
    status_msg=pyqtSignal(str)
    def __init__(self,dm):
        super().__init__(); self.dm=dm; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        top=QHBoxLayout()
        top.addWidget(QLabel("Símbolo:"))
        self.sym=QLineEdit(); self.sym.setPlaceholderText("AAPL, MSFT, etc."); self.sym.setMaximumWidth(120); top.addWidget(self.sym)
        btn=QPushButton("🔍  Analizar"); btn.setObjectName("primary"); btn.clicked.connect(self._load); top.addWidget(btn)
        self.score_lbl=QLabel(""); self.score_lbl.setFont(QFont("Segoe UI",11,QFont.Weight.Bold)); top.addWidget(self.score_lbl)
        top.addStretch(); L.addLayout(top)
        self.prog=QProgressBar(); self.prog.setRange(0,0); self.prog.setVisible(False); L.addWidget(self.prog)
        tabs=QTabWidget()
        # Fundamental cards
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True)
        self.cards_w=QWidget(); self.cards_l=QVBoxLayout(self.cards_w)
        self.cards_l.setAlignment(Qt.AlignmentFlag.AlignTop); self.scroll.setWidget(self.cards_w)
        tabs.addTab(self.scroll,"📊 Métricas Fundamentales")
        # Income statement
        self.income_table=QTableWidget(); self.income_table.setAlternatingRowColors(True)
        self.income_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabs.addTab(self.income_table,"📈 P&L Anual")
        # Balance
        self.balance_table=QTableWidget(); self.balance_table.setAlternatingRowColors(True)
        self.balance_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabs.addTab(self.balance_table,"🏦 Balance")
        # Cash flow
        self.cf_table=QTableWidget(); self.cf_table.setAlternatingRowColors(True)
        self.cf_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabs.addTab(self.cf_table,"💰 Cash Flow")
        L.addWidget(tabs,1)
        self.log=QLabel(""); self.log.setStyleSheet("color:#6c7086;font-size:10px;"); L.addWidget(self.log)

    def _load(self):
        sym=self.sym.text().strip().upper()
        if not sym: return
        self.prog.setVisible(True); self.log.setText(f"⏳ Cargando fundamentales de {sym}...")
        self._t=FundThread(sym); self._t.done.connect(self._on_done); self._t.start()

    def _on_done(self,info,fin,score_text):
        self.prog.setVisible(False)
        if not info: self.log.setText("❌ No se encontraron datos"); return
        self._fill_cards(info)
        self.score_lbl.setText(score_text.split('\n')[0] if score_text else "")
        for attr,key,title in [('income_table','income','P&L'),('balance_table','balance','Balance'),('cf_table','cashflow','Cash Flow')]:
            df=fin.get(key)
            if df is not None: self._fill_financial_table(getattr(self,attr),df)
        self.log.setText("✅ Datos fundamentales cargados")
        self.status_msg.emit(f"Fundamentales: {self.sym.text().strip().upper()}")

    def _fill_cards(self,info):
        while self.cards_l.count(): 
            w=self.cards_l.takeAt(0).widget()
            if w: w.deleteLater()
        for cat,fields in info.items():
            if cat=='Error': continue
            gb=QGroupBox(cat); gl=QGridLayout(gb); gb.setFont(QFont("Segoe UI",10,QFont.Weight.Bold))
            col=0; row=0
            for name,val in fields.items():
                if name=='Descripción' and len(str(val))>100:
                    desc=QLabel(str(val)[:500]); desc.setWordWrap(True)
                    desc.setStyleSheet("color:#a6adc8;font-size:10px;padding:4px;")
                    gl.addWidget(QLabel(f"<b>{name}</b>"),row,0); gl.addWidget(desc,row,1,1,3); row+=1; col=0
                    continue
                lbl=QLabel(f"{name}:"); lbl.setStyleSheet("color:#89b4fa;font-weight:bold;font-size:10px;")
                vl=QLabel(str(val)); vl.setStyleSheet("color:#cdd6f4;font-size:11px;font-weight:bold;")
                if str(val)!='N/A':
                    try:
                        v=float(str(val).replace('%','').replace('$','').replace(',','').replace('T','').replace('B','').replace('M',''))
                        if v>0: vl.setStyleSheet("color:#a6e3a1;font-size:11px;font-weight:bold;")
                        elif v<0: vl.setStyleSheet("color:#f38ba8;font-size:11px;font-weight:bold;")
                    except: pass
                gl.addWidget(lbl,row,col*2); gl.addWidget(vl,row,col*2+1)
                col+=1
                if col>=3: col=0; row+=1
            self.cards_l.addWidget(gb)

    def _fill_financial_table(self,table,df):
        if df is None or df.empty: return
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c)[:10] for c in df.columns])
        table.setRowCount(len(df))
        table.setVerticalHeaderLabels([str(r)[:40] for r in df.index])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i,row in enumerate(df.itertuples()):
            for j,v in enumerate(row[1:]):
                try: fmt=f"${float(v)/1e9:.2f}B" if abs(float(v))>=1e9 else (f"${float(v)/1e6:.2f}M" if abs(float(v))>=1e6 else f"${float(v):,.0f}")
                except: fmt=str(v)
                it=QTableWidget.item if False else QTableWidgetItem(fmt)
                it=QTableWidgetItem(fmt)
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                try:
                    fv=float(str(v))
                    it.setForeground(QColor("#a6e3a1") if fv>0 else QColor("#f38ba8"))
                except: pass
                table.setItem(i,j,it)
