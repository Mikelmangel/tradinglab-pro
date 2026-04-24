"""TradingLab Pro — Strategy Editor with syntax highlighting and 10 templates."""
import re
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import *

TEMPLATES = {
    'SMA Crossover': '''def generate_signals(data, fast_period=10, slow_period=30, **p):
    import pandas as pd, numpy as np
    close = data['Close']
    fast = close.rolling(fast_period).mean()
    slow = close.rolling(slow_period).mean()
    signals = pd.Series(0, index=data.index)
    signals[fast > slow] = 1
    signals[fast < slow] = -1
    # Only signal on crossover
    sig = signals.diff().fillna(0)
    signals = pd.Series(0, index=data.index)
    signals[sig > 0] = 1
    signals[sig < 0] = -1
    return signals
''',
    'EMA Crossover': '''def generate_signals(data, fast_period=9, slow_period=21, **p):
    import pandas as pd
    close = data['Close']
    fast = close.ewm(span=fast_period, adjust=False).mean()
    slow = close.ewm(span=slow_period, adjust=False).mean()
    signals = pd.Series(0, index=data.index)
    cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
    cross_dn = (fast < slow) & (fast.shift(1) >= slow.shift(1))
    signals[cross_up] = 1
    signals[cross_dn] = -1
    return signals
''',
    'RSI Reversión': '''def generate_signals(data, period=14, oversold=30, overbought=70, **p):
    import pandas as pd
    c = data['Close']
    d = c.diff()
    g = d.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    rsi = 100 - 100 / (1 + g / l.replace(0, float('nan')))
    signals = pd.Series(0, index=data.index)
    signals[(rsi < oversold) & (rsi.shift(1) >= oversold)] = 1
    signals[(rsi > overbought) & (rsi.shift(1) <= overbought)] = -1
    return signals
''',
    'MACD Crossover': '''def generate_signals(data, fast=12, slow=26, signal=9, **p):
    import pandas as pd
    c = data['Close']
    macd = c.ewm(span=fast, adjust=False).mean() - c.ewm(span=slow, adjust=False).mean()
    sig  = macd.ewm(span=signal, adjust=False).mean()
    signals = pd.Series(0, index=data.index)
    signals[(macd > sig) & (macd.shift(1) <= sig.shift(1))] = 1
    signals[(macd < sig) & (macd.shift(1) >= sig.shift(1))] = -1
    return signals
''',
    'Bollinger Bands': '''def generate_signals(data, period=20, std_dev=2.0, **p):
    import pandas as pd
    c = data['Close']
    mid = c.rolling(period).mean()
    std = c.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    signals = pd.Series(0, index=data.index)
    signals[(c < lower) & (c.shift(1) >= lower.shift(1))] = 1   # bounce lower band
    signals[(c > upper) & (c.shift(1) <= upper.shift(1))] = -1  # touch upper band
    return signals
''',
    'SuperTrend': '''def generate_signals(data, period=10, mult=3.0, **p):
    import pandas as pd, numpy as np
    h=data['High'];l=data['Low'];c=data['Close']
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(com=period-1,adjust=False).mean()
    hl2=(h+l)/2; ub=hl2+mult*atr; lb=hl2-mult*atr
    upper=ub.copy(); lower=lb.copy()
    for i in range(1,len(c)):
        upper.iloc[i]=min(ub.iloc[i],upper.iloc[i-1]) if c.iloc[i-1]<=upper.iloc[i-1] else ub.iloc[i]
        lower.iloc[i]=max(lb.iloc[i],lower.iloc[i-1]) if c.iloc[i-1]>=lower.iloc[i-1] else lb.iloc[i]
    trend=pd.Series(1,index=c.index)
    for i in range(1,len(c)):
        trend.iloc[i]=(1 if c.iloc[i]>upper.iloc[i] else (-1 if c.iloc[i]<lower.iloc[i] else trend.iloc[i-1]))
    signals=pd.Series(0,index=c.index)
    signals[(trend==1)&(trend.shift(1)==-1)]=1
    signals[(trend==-1)&(trend.shift(1)==1)]=-1
    return signals
''',
    'Donchian Breakout': '''def generate_signals(data, entry_period=20, exit_period=10, **p):
    import pandas as pd
    h=data['High']; l=data['Low']; c=data['Close']
    upper_entry = h.rolling(entry_period).max().shift(1)
    lower_exit  = l.rolling(exit_period).min().shift(1)
    signals = pd.Series(0, index=data.index)
    signals[c >= upper_entry] = 1
    signals[c <= lower_exit]  = -1
    return signals
''',
    'Mean Reversion Z-Score': '''def generate_signals(data, period=20, z_entry=2.0, z_exit=0.5, **p):
    import pandas as pd
    c = data['Close']
    mu = c.rolling(period).mean()
    std = c.rolling(period).std()
    z = (c - mu) / std.replace(0, float('nan'))
    signals = pd.Series(0, index=data.index)
    signals[z < -z_entry] = 1    # oversold
    signals[z > z_entry]  = -1   # overbought
    signals[(z > -z_exit) & (z.shift(1) <= -z_exit)] = -1  # mean reversion exit
    return signals
''',
    'ADX Trend Filter': '''def generate_signals(data, adx_period=14, ma_period=20, adx_threshold=25, **p):
    import pandas as pd, numpy as np
    h=data['High'];l=data['Low'];c=data['Close']
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    pdm=(h-h.shift(1)).clip(lower=0);ndm=(l.shift(1)-l).clip(lower=0)
    pdm=pdm.where(pdm>ndm,0);ndm=ndm.where(ndm>pdm,0)
    atr=tr.ewm(com=adx_period-1,adjust=False).mean()
    pdi=100*pdm.ewm(com=adx_period-1,adjust=False).mean()/atr.replace(0,float('nan'))
    ndi=100*ndm.ewm(com=adx_period-1,adjust=False).mean()/atr.replace(0,float('nan'))
    dx=100*(pdi-ndi).abs()/(pdi+ndi).replace(0,float('nan'))
    adx=dx.ewm(com=adx_period-1,adjust=False).mean()
    ma=c.ewm(span=ma_period,adjust=False).mean()
    strong=adx>adx_threshold
    signals=pd.Series(0,index=c.index)
    signals[strong & (c>ma) & (c.shift(1)<=ma.shift(1))]=1
    signals[strong & (c<ma) & (c.shift(1)>=ma.shift(1))]=-1
    return signals
''',
    'Personalizada': '''def generate_signals(data, period=20, **params):
    """
    Escribe tu estrategia aquí.
    data: DataFrame con Open, High, Low, Close, Volume
    Retorna: Series con 1=compra, -1=venta, 0=mantener
    """
    import pandas as pd, numpy as np
    signals = pd.Series(0, index=data.index)
    # Tu lógica aquí
    return signals
''',
}

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor); self.editor = editor
    def sizeHint(self): return QSize(self.editor._line_number_width(), 0)
    def paintEvent(self, e): self.editor._paint_line_numbers(e)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self._line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_width)
        self.updateRequest.connect(self._update_line_area)
        self._update_width(0)
        self.setFont(QFont("Cascadia Code,Consolas,Fira Code,Courier New", 12))
        self.setTabStopDistance(28)

    def _line_number_width(self):
        d=max(1,len(str(self.blockCount()))); return 12 + self.fontMetrics().horizontalAdvance('9')*d

    def _update_width(self,_):
        self.setViewportMargins(self._line_number_width(),0,0,0)

    def _update_line_area(self,rect,dy):
        if dy: self._line_area.scroll(0,dy)
        else: self._line_area.update(0,rect.y(),self._line_area.width(),rect.height())
        if rect.contains(self.viewport().rect()): self._update_width(0)

    def resizeEvent(self,e):
        super().resizeEvent(e)
        cr=self.contentsRect()
        self._line_area.setGeometry(QRect(cr.left(),cr.top(),self._line_number_width(),cr.height()))

    def _paint_line_numbers(self,e):
        p=QPainter(self._line_area)
        p.fillRect(e.rect(),QColor("#181825"))
        block=self.firstVisibleBlock(); bn=block.blockNumber()
        top=round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bot=top+round(self.blockBoundingRect(block).height())
        while block.isValid() and top<=e.rect().bottom():
            if block.isVisible() and bot>=e.rect().top():
                p.setPen(QColor("#45475a"))
                p.setFont(QFont("Consolas",9))
                p.drawText(0,top,self._line_area.width()-4,self.fontMetrics().height(),Qt.AlignmentFlag.AlignRight,str(bn+1))
            block=block.next(); top=bot; bot=top+round(self.blockBoundingRect(block).height()); bn+=1

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self,parent):
        super().__init__(parent)
        kw_fmt=QTextCharFormat(); kw_fmt.setForeground(QColor("#cba6f7")); kw_fmt.setFontWeight(QFont.Weight.Bold)
        fn_fmt=QTextCharFormat(); fn_fmt.setForeground(QColor("#89b4fa")); fn_fmt.setFontWeight(QFont.Weight.Bold)
        str_fmt=QTextCharFormat(); str_fmt.setForeground(QColor("#a6e3a1"))
        num_fmt=QTextCharFormat(); num_fmt.setForeground(QColor("#fab387"))
        cmt_fmt=QTextCharFormat(); cmt_fmt.setForeground(QColor("#6c7086")); cmt_fmt.setFontItalic(True)
        dec_fmt=QTextCharFormat(); dec_fmt.setForeground(QColor("#f9e2af"))
        bi_fmt=QTextCharFormat(); bi_fmt.setForeground(QColor("#94e2d5"))
        kws=r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'
        bis=r'\b(abs|all|any|bin|bool|dict|dir|enumerate|filter|float|format|getattr|hasattr|int|isinstance|len|list|map|max|min|next|open|print|range|round|set|setattr|sorted|str|sum|tuple|type|zip)\b'
        self._rules=[
            (re.compile(kws),kw_fmt),(re.compile(r'\bdef\s+(\w+)'),fn_fmt),
            (re.compile(r'@\w+'),dec_fmt),(re.compile(bis),bi_fmt),
            (re.compile(r'\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\"[^\"]*\"|\'[^\']*\''),str_fmt),
            (re.compile(r'\b\d+\.?\d*([eE][+-]?\d+)?\b'),num_fmt),
        ]
        self._cmt=re.compile(r'#.*'); self._cmt_fmt=cmt_fmt

    def highlightBlock(self,text):
        for pat,fmt in self._rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(),m.end()-m.start(),fmt)
        m=self._cmt.search(text)
        if m: self.setFormat(m.start(),len(text)-m.start(),self._cmt_fmt)

class StrategyTab(QWidget):
    def __init__(self):
        super().__init__(); self._name='SMA Crossover'; self._setup_ui()

    def _setup_ui(self):
        L=QVBoxLayout(self); L.setContentsMargins(6,6,6,6)
        top=QHBoxLayout()
        top.addWidget(QLabel("Plantilla:"))
        self.tmpl=QComboBox(); self.tmpl.addItems(list(TEMPLATES.keys()))
        self.tmpl.currentTextChanged.connect(self._load_template); top.addWidget(self.tmpl)
        top.addWidget(QLabel("Nombre:"))
        self.name_edit=QLineEdit("Mi Estrategia"); top.addWidget(self.name_edit)
        top.addStretch()
        L.addLayout(top)
        self.editor=CodeEditor()
        PythonHighlighter(self.editor.document())
        L.addWidget(self.editor,1)
        doc=QLabel(
            "API: def generate_signals(data, param1=10, param2=30, **params) → pd.Series  |  "
            "1 = Comprar · -1 = Vender · 0 = Mantener  |  "
            "data: Open, High, Low, Close, Volume")
        doc.setStyleSheet("color:#6c7086;font-size:9px;padding:2px 4px;")
        L.addWidget(doc)
        self._load_template(self.tmpl.currentText())

    def _load_template(self,name):
        if name in TEMPLATES:
            self.editor.setPlainText(TEMPLATES[name].strip())
            self._name=name; self.name_edit.setText(name)

    def get_code(self): return self.editor.toPlainText()
    def get_name(self): return self.name_edit.text() or self._name
    def set_code(self,code): self.editor.setPlainText(code)
