"""TradingLab Pro — Scanner Tab."""
import traceback, pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from src.core.scanner import MarketScanner, BUILT_IN_SCANS
from src.styles.theme import C as TC

C = TC

class ScanThread(QThread):
    progress=pyqtSignal(int,str); finished=pyqtSignal(object); error=pyqtSignal(str)
    def __init__(self,datasets,code): super().__init__(); self.ds=datasets;self.code=code
    def run(self):
        try: self.finished.emit(MarketScanner().run(self.ds,self.code,progress_cb=self.progress.emit))
        except Exception as e: self.error.emit(f"{e}\n\n{traceback.format_exc()}")

class ScannerTab(QWidget):
    status_msg=pyqtSignal(str)
    def __init__(self,dm):
        super().__init__(); self.dm=dm; self._syms=[]; self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        top=QHBoxLayout()
        top.addWidget(QLabel("Condición:"))
        self.preset=QComboBox(); self.preset.addItems(list(BUILT_IN_SCANS.keys()))
        self.preset.currentTextChanged.connect(self._load_preset); top.addWidget(self.preset)
        top.addStretch()
        self.run_btn=QPushButton("🔍  Escanear todo"); self.run_btn.setObjectName("primary")
        self.run_btn.setFixedHeight(40); self.run_btn.clicked.connect(self._run); top.addWidget(self.run_btn)
        L.addLayout(top)
        self.prog=QProgressBar(); self.prog.setVisible(False); L.addWidget(self.prog)
        sp=QSplitter(Qt.Orientation.Horizontal)
        eb=QGroupBox("Código"); el=QVBoxLayout(eb)
        from PyQt6.QtWidgets import QPlainTextEdit; from PyQt6.QtGui import QFont
        self.editor=QPlainTextEdit()
        self.editor.setFont(QFont("Cascadia Code,Consolas,Courier New",11))
        el.addWidget(self.editor)
        el.addWidget(QLabel("scan_condition(data) → True/False"))
        sp.addWidget(eb)
        rb=QGroupBox("Resultados"); rl=QVBoxLayout(rb)
        self.info=QLabel("Sin resultados."); self.info.setStyleSheet("color:#89b4fa;font-weight:bold;"); rl.addWidget(self.info)
        self.tbl=QTableWidget(); self.tbl.setAlternatingRowColors(True)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        rl.addWidget(self.tbl); sp.addWidget(rb)
        sp.setSizes([450,900]); L.addWidget(sp,1)
        self.log=QLabel(""); self.log.setStyleSheet("color:#6c7086;font-size:10px;"); L.addWidget(self.log)
        self._load_preset(self.preset.currentText())

    def update_symbols(self,syms): self._syms=syms

    def _load_preset(self,name):
        if name in BUILT_IN_SCANS: self.editor.setPlainText(BUILT_IN_SCANS[name].strip())

    def _run(self):
        if not self._syms: self.log.setText("❌ Sin símbolos"); return
        code=self.editor.toPlainText().strip()
        if not code: return
        datasets={s:self.dm.get_data(s) for s in self._syms}
        datasets={s:d for s,d in datasets.items() if d is not None and not d.empty}
        self.run_btn.setEnabled(False); self.prog.setVisible(True)
        self.log.setText(f"⏳ Escaneando {len(datasets)} símbolos...")
        self._t=ScanThread(datasets,code)
        self._t.progress.connect(lambda p,s: (self.prog.setValue(p),self.log.setText(f"🔍 {p}% — {s}")))
        self._t.finished.connect(self._done); self._t.error.connect(self._err); self._t.start()

    def _done(self,r):
        self.run_btn.setEnabled(True); self.prog.setVisible(False)
        if r is None or r.empty: self.info.setText("0 coincidencias"); self.log.setText("✅ Scan completado"); return
        n=len(r); self.info.setText(f"  ✅  {n} símbolo{'s' if n!=1 else ''} coinciden")
        self.log.setText(f"✅ Scan completado — {n} coincidencias")
        cols=list(r.columns); self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols); self.tbl.setRowCount(n)
        pct={'1D%','5D%','20D%'}
        for i,(_,row) in enumerate(r.iterrows()):
            for j,col in enumerate(cols):
                it=QTableWidgetItem(str(row[col]))
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if col in pct:
                    try: v=float(str(row[col]).replace('+','')); it.setForeground(QColor(C['green'] if v>0 else (C['red'] if v<0 else C['text'])))
                    except: pass
                elif col=='RSI':
                    try: v=float(str(row[col])); it.setForeground(QColor(C['green'] if v<30 else (C['red'] if v>70 else C['text'])))
                    except: pass
                self.tbl.setItem(i,j,it)

    def _err(self,e):
        self.run_btn.setEnabled(True); self.prog.setVisible(False); self.log.setText(f"❌ {e.split(chr(10))[0][:80]}")
