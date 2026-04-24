"""TradingLab Pro — Dark Theme (Catppuccin Mocha)"""
from PyQt6.QtGui import QPalette, QColor

C = {
    'bg':'#1e1e2e','base':'#1e1e2e','mantle':'#181825','crust':'#11111b',
    'surface0':'#313244','surface1':'#45475a','surface2':'#585b70',
    'overlay0':'#6c7086','overlay1':'#7f849c','text':'#cdd6f4',
    'subtext0':'#a6adc8','blue':'#89b4fa','sapphire':'#74c7ec',
    'sky':'#89dceb','teal':'#94e2d5','green':'#a6e3a1',
    'yellow':'#f9e2af','peach':'#fab387','red':'#f38ba8',
    'mauve':'#cba6f7','pink':'#f5c2e7','lavender':'#b4befe',
}

THEME = f"""
QMainWindow,QWidget,QDialog{{background:{C['base']};color:{C['text']};font-family:'Segoe UI','Ubuntu',sans-serif;}}
QFrame{{background:transparent;border:none;}}
QTabWidget::pane{{border:1px solid {C['surface1']};background:{C['base']};border-radius:0 4px 4px 4px;}}
QTabBar::tab{{background:{C['mantle']};color:{C['overlay1']};padding:9px 18px;border:1px solid {C['surface0']};border-bottom:none;border-radius:5px 5px 0 0;font-size:11px;font-weight:500;}}
QTabBar::tab:selected{{background:{C['blue']};color:{C['crust']};font-weight:bold;border-color:{C['blue']};}}
QTabBar::tab:hover:!selected{{background:{C['surface0']};color:{C['text']};}}
QGroupBox{{border:1px solid {C['surface0']};border-radius:6px;margin-top:16px;padding-top:8px;color:{C['blue']};font-weight:bold;font-size:11px;}}
QGroupBox::title{{subcontrol-origin:margin;left:12px;padding:0 6px;background:{C['base']};}}
QPushButton{{background:{C['surface0']};color:{C['text']};border:1px solid {C['surface1']};border-radius:5px;padding:6px 14px;font-size:11px;}}
QPushButton:hover{{background:{C['surface1']};border-color:{C['blue']};}}
QPushButton:pressed{{background:{C['blue']};color:{C['crust']};}}
QPushButton:disabled{{background:{C['mantle']};color:{C['surface2']};border-color:{C['surface0']};}}
QPushButton#primary{{background:{C['blue']};color:{C['crust']};font-weight:bold;border:none;}}
QPushButton#primary:hover{{background:{C['sapphire']};}}
QPushButton#success{{background:{C['green']};color:{C['crust']};font-weight:bold;border:none;}}
QPushButton#success:hover{{background:{C['teal']};}}
QPushButton#danger{{background:{C['red']};color:{C['crust']};font-weight:bold;border:none;}}
QPushButton#warning{{background:{C['yellow']};color:{C['crust']};font-weight:bold;border:none;}}
QPushButton#warning:hover{{background:{C['peach']};}}
QPushButton#ai{{background:{C['mauve']};color:{C['crust']};font-weight:bold;border:none;}}
QPushButton#ai:hover{{background:{C['lavender']};}}
QLineEdit,QDateEdit,QDoubleSpinBox,QSpinBox,QComboBox,QTimeEdit{{background:{C['surface0']};color:{C['text']};border:1px solid {C['surface1']};border-radius:4px;padding:5px 8px;font-size:11px;selection-background-color:{C['blue']};selection-color:{C['crust']};}}
QLineEdit:focus,QDateEdit:focus,QDoubleSpinBox:focus,QSpinBox:focus,QComboBox:focus{{border-color:{C['blue']};background:{C['mantle']};}}
QComboBox::drop-down{{border:none;background:{C['surface1']};width:22px;border-radius:0 4px 4px 0;}}
QComboBox QAbstractItemView{{background:{C['surface0']};color:{C['text']};selection-background-color:{C['blue']};selection-color:{C['crust']};border:1px solid {C['surface1']};}}
QSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::up-button,QDoubleSpinBox::down-button{{background:{C['surface1']};border:none;width:16px;}}
QTableWidget,QTableView{{background:{C['base']};color:{C['text']};gridline-color:{C['surface0']};border:1px solid {C['surface1']};border-radius:4px;font-size:11px;alternate-background-color:{C['mantle']};selection-background-color:{C['surface1']};}}
QTableWidget::item,QTableView::item{{padding:4px 6px;border:none;}}
QHeaderView::section{{background:{C['mantle']};color:{C['blue']};border:none;border-bottom:2px solid {C['blue']};border-right:1px solid {C['surface0']};padding:7px 8px;font-weight:bold;font-size:11px;}}
QHeaderView::section:hover{{background:{C['surface0']};}}
QProgressBar{{background:{C['surface0']};border:1px solid {C['surface1']};border-radius:4px;text-align:center;color:{C['text']};font-size:10px;height:14px;}}
QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C['blue']},stop:1 {C['mauve']});border-radius:3px;}}
QSplitter::handle{{background:{C['surface0']};width:3px;height:3px;}}
QSplitter::handle:hover{{background:{C['blue']};}}
QScrollBar:vertical,QScrollBar:horizontal{{background:{C['mantle']};border:none;width:10px;height:10px;}}
QScrollBar::handle:vertical,QScrollBar::handle:horizontal{{background:{C['surface1']};border-radius:5px;min-height:24px;min-width:24px;}}
QScrollBar::handle:vertical:hover,QScrollBar::handle:horizontal:hover{{background:{C['blue']};}}
QScrollBar::add-line,QScrollBar::sub-line{{background:none;border:none;}}
QMenuBar{{background:{C['mantle']};color:{C['text']};border-bottom:1px solid {C['surface0']};font-size:11px;padding:2px;}}
QMenuBar::item{{padding:4px 12px;border-radius:4px;}}
QMenuBar::item:selected{{background:{C['surface0']};color:{C['blue']};}}
QMenu{{background:{C['surface0']};color:{C['text']};border:1px solid {C['surface1']};border-radius:6px;padding:4px;}}
QMenu::item{{padding:6px 24px;border-radius:4px;}}
QMenu::item:selected{{background:{C['blue']};color:{C['crust']};}}
QMenu::separator{{background:{C['surface1']};height:1px;margin:4px 8px;}}
QStatusBar{{background:{C['mantle']};color:{C['overlay0']};border-top:1px solid {C['surface0']};font-size:10px;padding:2px 8px;}}
QLabel{{color:{C['text']};font-size:11px;background:transparent;}}
QCheckBox{{color:{C['text']};spacing:6px;font-size:11px;}}
QCheckBox::indicator{{width:16px;height:16px;border:1px solid {C['surface1']};border-radius:3px;background:{C['surface0']};}}
QCheckBox::indicator:checked{{background:{C['blue']};border-color:{C['blue']};}}
QToolTip{{background:{C['surface0']};color:{C['text']};border:1px solid {C['blue']};border-radius:4px;padding:4px 8px;font-size:10px;}}
QPlainTextEdit,QTextEdit{{background:{C['mantle']};color:{C['text']};border:1px solid {C['surface1']};selection-background-color:{C['surface1']};font-family:'Cascadia Code','Consolas','Fira Code','Courier New',monospace;font-size:12px;}}
"""

def apply_palette(app):
    p = QPalette()
    q = lambda c: QColor(c)
    p.setColor(QPalette.ColorRole.Window,          q(C['base']))
    p.setColor(QPalette.ColorRole.WindowText,      q(C['text']))
    p.setColor(QPalette.ColorRole.Base,            q(C['mantle']))
    p.setColor(QPalette.ColorRole.AlternateBase,   q(C['base']))
    p.setColor(QPalette.ColorRole.Text,            q(C['text']))
    p.setColor(QPalette.ColorRole.Button,          q(C['surface0']))
    p.setColor(QPalette.ColorRole.ButtonText,      q(C['text']))
    p.setColor(QPalette.ColorRole.Highlight,       q(C['blue']))
    p.setColor(QPalette.ColorRole.HighlightedText, q(C['crust']))
    p.setColor(QPalette.ColorRole.Link,            q(C['blue']))
    app.setPalette(p)
