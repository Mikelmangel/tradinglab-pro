"""TradingLab Pro — Data Tab."""
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QColor, QFont
from src.styles.theme import C

class DownloadThread(QThread):
    done=pyqtSignal(str,object); progress=pyqtSignal(str)
    def __init__(self,dm,sym,start_date,end_date,interval):
        super().__init__(); self.dm=dm;self.sym=sym;self.start_date=start_date;self.end_date=end_date;self.interval=interval
    def run(self):
        self.progress.emit(f"Descargando {self.sym}...")
        df=self.dm.download(self.sym,self.start_date,self.end_date,self.interval)
        self.done.emit(self.sym,df)

class DataTab(QWidget):
    data_loaded=pyqtSignal(str)
    status_msg=pyqtSignal(str)
    def __init__(self,dm):
        super().__init__(); self.dm=dm; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        top=QSplitter(Qt.Orientation.Horizontal)
        # Download panel
        dp=QGroupBox("Descargar Datos"); dl=QVBoxLayout(dp)
        fr=QHBoxLayout(); fr.addWidget(QLabel("Símbolo:"))
        self.sym=QLineEdit("AAPL"); self.sym.setMaximumWidth(100); fr.addWidget(self.sym)
        fr.addWidget(QLabel("Inicio:"))
        self.start=QDateEdit(); self.start.setDate(QDate(2015,1,1)); self.start.setCalendarPopup(True); fr.addWidget(self.start)
        fr.addWidget(QLabel("Fin:"))
        self.end=QDateEdit(); self.end.setDate(QDate.currentDate()); self.end.setCalendarPopup(True); fr.addWidget(self.end)
        fr.addWidget(QLabel("Intervalo:"))
        self.interval=QComboBox(); self.interval.addItems(['1d','1wk','1mo','1h','15m','5m','1m']); fr.addWidget(self.interval)
        self.dl_btn=QPushButton("📥 Descargar"); self.dl_btn.setObjectName("primary")
        self.dl_btn.clicked.connect(self._download); fr.addWidget(self.dl_btn)
        dl.addLayout(fr)
        self.prog=QProgressBar(); self.prog.setVisible(False); dl.addWidget(self.prog)
        # Symbol list
        self.sym_table=QTableWidget(); self.sym_table.setColumnCount(4)
        self.sym_table.setHorizontalHeaderLabels(["Símbolo","Intervalo","Barras","Actualizado"])
        self.sym_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sym_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sym_table.setAlternatingRowColors(True)
        del_btn=QPushButton("🗑️ Eliminar selección"); del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_sym)
        dl.addWidget(self.sym_table); dl.addWidget(del_btn)
        top.addWidget(dp)
        # Watchlists
        wp=QGroupBox("Watchlists"); wl=QVBoxLayout(wp)
        wr=QHBoxLayout()
        self.wl_name=QLineEdit(); self.wl_name.setPlaceholderText("Nombre watchlist")
        add_wl=QPushButton("➕"); add_wl.clicked.connect(self._add_wl); add_wl.setMaximumWidth(35)
        del_wl=QPushButton("🗑️"); del_wl.clicked.connect(self._del_wl); del_wl.setMaximumWidth(35)
        wr.addWidget(self.wl_name); wr.addWidget(add_wl); wr.addWidget(del_wl); wl.addLayout(wr)
        self.wl_list=QListWidget(); self.wl_list.currentTextChanged.connect(self._wl_selected); wl.addWidget(self.wl_list)
        wl.addWidget(QLabel("Símbolos:")); self.wl_syms=QListWidget()
        as_=QPushButton("➕ Añadir símbolo"); as_.clicked.connect(self._add_sym_to_wl)
        rs_=QPushButton("➖ Quitar símbolo"); rs_.clicked.connect(self._remove_sym_from_wl)
        wl.addWidget(self.wl_syms); wl.addWidget(as_); wl.addWidget(rs_)
        top.addWidget(wp)
        top.setSizes([900,350])
        L.addWidget(top)
        # Preview
        prev=QGroupBox("Vista previa")
        pl=QVBoxLayout(prev)
        self.prev_table=QTableWidget(); self.prev_table.setAlternatingRowColors(True)
        self.prev_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.prev_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pl.addWidget(self.prev_table)
        L.addWidget(prev,1)
        self.status=QLabel(""); self.status.setStyleSheet("color:#6c7086;font-size:10px;")
        L.addWidget(self.status)
        self._refresh_sym_table(); self._refresh_wl()
    def _download(self):
        sym=self.sym.text().strip().upper()
        if not sym: return
        self.dl_btn.setEnabled(False); self.prog.setVisible(True); self.prog.setRange(0,0)
        self._thread=DownloadThread(
            dm=self.dm,
            sym=sym,
            start_date=self.start.date().toString("yyyy-MM-dd"),
            end_date=self.end.date().toString("yyyy-MM-dd"),
            interval=self.interval.currentText())
        self._thread.progress.connect(lambda m: self.status.setText(m))
        self._thread.done.connect(self._on_done)
        self._thread.start()
    def _on_done(self,sym,df):
        self.dl_btn.setEnabled(True); self.prog.setVisible(False)
        if df is None: self.status.setText(f"❌ Error descargando {sym}"); return
        self.status.setText(f"✅ {sym}: {len(df)} barras descargadas")
        self._refresh_sym_table(); self._preview(sym,df); self.data_loaded.emit(sym)
        self.status_msg.emit(f"{sym} listo ({len(df)} barras)")
    def _refresh_sym_table(self):
        c=self.dm.conn.execute("SELECT s.symbol,s.interval,COUNT(o.date),s.last_update FROM symbols s LEFT JOIN ohlcv o ON s.symbol=o.symbol AND s.interval=o.interval GROUP BY s.symbol,s.interval ORDER BY s.symbol")
        rows=c.fetchall()
        self.sym_table.setRowCount(len(rows))
        for i,(sym,iv,n,upd) in enumerate(rows):
            for j,v in enumerate([sym,iv,str(n),str(upd)[:16]]):
                it=QTableWidgetItem(v); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sym_table.setItem(i,j,it)
    def _delete_sym(self):
        row=self.sym_table.currentRow()
        if row<0: return
        sym=self.sym_table.item(row,0).text(); iv=self.sym_table.item(row,1).text()
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar {sym} ({iv})?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            self.dm.delete_symbol(sym,iv); self._refresh_sym_table()
    def _preview(self,sym,df):
        df2=df.tail(300)
        self.prev_table.setColumnCount(len(df2.columns))
        self.prev_table.setHorizontalHeaderLabels([str(c) for c in df2.columns])
        self.prev_table.setRowCount(len(df2))
        for i,(idx,row) in enumerate(df2.iterrows()):
            for j,v in enumerate(row):
                self.prev_table.setItem(i,j,QTableWidgetItem(f"{v:.4f}" if isinstance(v,float) else str(v)))
    def _refresh_wl(self):
        self.wl_list.clear()
        for w in self.dm.get_watchlists(): self.wl_list.addItem(w)
    def _add_wl(self):
        name=self.wl_name.text().strip()
        if name: self.dm.create_watchlist(name); self._refresh_wl(); self.wl_name.clear()
    def _del_wl(self):
        cur=self.wl_list.currentItem()
        if cur: self.dm.delete_watchlist(cur.text()); self._refresh_wl(); self.wl_syms.clear()
    def _wl_selected(self,name):
        self.wl_syms.clear()
        if name:
            for s in self.dm.get_watchlist_symbols(name): self.wl_syms.addItem(s)
    def _add_sym_to_wl(self):
        wl=self.wl_list.currentItem()
        if not wl: return
        sym,ok=QInputDialog.getText(self,"Añadir símbolo","Símbolo:")
        if ok and sym: self.dm.add_to_watchlist(wl.text(),sym.upper()); self._wl_selected(wl.text())
    def _remove_sym_from_wl(self):
        wl=self.wl_list.currentItem(); sym=self.wl_syms.currentItem()
        if wl and sym: self.dm.remove_from_watchlist(wl.text(),sym.text()); self._wl_selected(wl.text())
