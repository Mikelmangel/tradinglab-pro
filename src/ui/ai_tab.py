"""TradingLab Pro — AI Assistant Tab."""
import re
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
from src.core.ai_assistant import AIAssistant

QUICK_PROMPTS = [
    "Analiza mi estrategia y sugiere mejoras",
    "¿Por qué el Sharpe es bajo?",
    "Genera una estrategia de momentum",
    "Genera una estrategia de mean reversion",
    "Genera una estrategia con filtro de tendencia ADX",
    "¿Cómo mejorar el Max Drawdown?",
    "Explica el resultado del Walk-Forward",
    "¿Hay señales de overfitting?",
    "¿Cuál es el mejor position sizing para esta estrategia?",
    "Dame una estrategia para mercados laterales",
]

class ChatThread(QThread):
    response=pyqtSignal(str); error=pyqtSignal(str)
    def __init__(self,assistant,msg):
        super().__init__(); self.ai=assistant; self.msg=msg
    def run(self):
        try: self.response.emit(self.ai.chat(self.msg))
        except Exception as e: self.error.emit(str(e))

class AITab(QWidget):
    status_msg=pyqtSignal(str)
    code_requested=pyqtSignal(str)  # send generated code to strategy editor
    def __init__(self):
        super().__init__()
        self.ai=AIAssistant()
        self._setup_ui()
    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        # API key row
        key_row=QHBoxLayout()
        key_row.addWidget(QLabel("API Key Anthropic:"))
        self.key_input=QLineEdit(); self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-ant-api03-...  (obténla en console.anthropic.com)")
        self.key_input.textChanged.connect(lambda t: self.ai.set_api_key(t))
        key_row.addWidget(self.key_input)
        clr=QPushButton("🗑️ Limpiar historial"); clr.clicked.connect(self._clear)
        key_row.addWidget(clr)
        L.addLayout(key_row)
        # Quick prompts
        qp_row=QHBoxLayout()
        qp_row.addWidget(QLabel("Rápido:"))
        self.quick=QComboBox(); self.quick.addItems(QUICK_PROMPTS)
        qp_btn=QPushButton("↗"); qp_btn.setMaximumWidth(32); qp_btn.clicked.connect(self._quick_send)
        qp_row.addWidget(self.quick); qp_row.addWidget(qp_btn)
        qp_row.addStretch(); L.addLayout(qp_row)
        # Chat display
        self.chat=QTextEdit(); self.chat.setReadOnly(True)
        self.chat.setFont(QFont("Segoe UI",11)); L.addWidget(self.chat,1)
        # Input
        inp_row=QHBoxLayout()
        self.inp=QLineEdit(); self.inp.setPlaceholderText("Escribe tu pregunta o pide una estrategia...")
        self.inp.setFont(QFont("Segoe UI",12)); self.inp.returnPressed.connect(self._send)
        send_btn=QPushButton("➤ Enviar"); send_btn.setObjectName("ai"); send_btn.setFixedHeight(40)
        send_btn.clicked.connect(self._send)
        inp_row.addWidget(self.inp,1); inp_row.addWidget(send_btn); L.addLayout(inp_row)
        self.status=QLabel("Asistente IA listo. Configura tu API key para comenzar.")
        self.status.setStyleSheet("color:#6c7086;font-size:10px;"); L.addWidget(self.status)
        self._add_msg("TradingLab AI","👋 ¡Hola! Soy tu asistente de trading IA. Puedo analizar estrategias, generar código, e interpretar resultados de backtest.\n\n💡 Cuando hagas un backtest, inyectaré automáticamente el contexto para darte análisis precisos.\n\n🔑 Configura tu API key de Anthropic arriba para comenzar.","ai")

    def _quick_send(self):
        self.inp.setText(self.quick.currentText()); self._send()

    def _send(self):
        msg=self.inp.text().strip()
        if not msg: return
        self._add_msg("Tú",msg,"user")
        self.inp.clear()
        self.status.setText("⏳ TradingLab AI está pensando...")
        self._t=ChatThread(self.ai,msg)
        self._t.response.connect(self._on_response)
        self._t.error.connect(lambda e: self.status.setText(f"❌ {e}"))
        self._t.start()

    def _on_response(self,text):
        self._add_msg("TradingLab AI",text,"ai")
        self.status.setText("✅ Respuesta recibida")
        code=self.ai.extract_code(text)
        if code:
            use_btn=QPushButton("📋 Usar este código en el Editor")
            use_btn.setObjectName("success")
            use_btn.clicked.connect(lambda: self.code_requested.emit(code))
            w=QWidget(); wl=QHBoxLayout(w); wl.setContentsMargins(0,4,0,0)
            wl.addWidget(use_btn); wl.addStretch()
            self.chat.textCursor().insertHtml("<br>")

    def _add_msg(self,sender,text,role):
        color={"user":"#89b4fa","ai":"#a6e3a1","system":"#fab387"}.get(role,"#cdd6f4")
        bg={"user":"#313244","ai":"#1e1e2e","system":"#181825"}.get(role,"#1e1e2e")
        text_escaped=text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        # Handle code blocks
        text_escaped=re.sub(r'```python(.*?)```',
            r'<pre style="background:#181825;color:#a6e3a1;padding:8px;border-radius:4px;font-family:monospace;font-size:10px;">\1</pre>',
            text_escaped,flags=re.DOTALL)
        text_escaped=re.sub(r'`([^`]+)`',r'<code style="background:#313244;color:#89b4fa;padding:1px 4px;border-radius:3px;">\1</code>',text_escaped)
        html=f'<div style="margin:8px 0;padding:10px;background:{bg};border-radius:8px;border-left:3px solid {color};">'
        html+=f'<b style="color:{color};font-size:11px;">{sender}</b><br>'
        html+=f'<span style="color:#cdd6f4;font-size:11px;line-height:1.5;">{text_escaped}</span></div>'
        self.chat.append(html)
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def _clear(self):
        self.ai.clear_history(); self.chat.clear()
        self._add_msg("TradingLab AI","Historial limpiado. ¿En qué puedo ayudarte?","ai")

    def inject_context(self,metrics=None,annual=None,code=""):
        self.ai.set_context(metrics,annual,code)
        self.status.setText("✅ Contexto del backtest inyectado — el asistente está al día")
