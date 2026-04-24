"""TradingLab Pro v2.0 — Entry Point"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from PyQt6.QtWidgets import QApplication, QSplashScreen
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
    from PyQt6.QtCore import Qt, QTimer

    app = QApplication(sys.argv)
    app.setApplicationName("TradingLab Pro")
    app.setApplicationVersion("2.0")

    from src.styles.theme import THEME, apply_palette
    app.setStyleSheet(THEME); apply_palette(app)

    # Splash screen
    px = QPixmap(520, 280); px.fill(QColor("#1e1e2e"))
    p = QPainter(px)
    p.setPen(QColor("#89b4fa")); p.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
    p.drawText(0, 80, 520, 60, Qt.AlignmentFlag.AlignHCenter, "📊 TradingLab Pro")
    p.setPen(QColor("#cba6f7")); p.setFont(QFont("Segoe UI", 13))
    p.drawText(0, 130, 520, 30, Qt.AlignmentFlag.AlignHCenter, "v2.0  —  Bar-by-Bar · MTF · Fundamentales · IA")
    p.setPen(QColor("#a6e3a1")); p.setFont(QFont("Segoe UI", 10))
    p.drawText(0, 175, 520, 25, Qt.AlignmentFlag.AlignHCenter, "🕯️ Motor bar-by-bar  ·  🤖 IA integrada  ·  📊 Fundamentales")
    p.drawText(0, 200, 520, 25, Qt.AlignmentFlag.AlignHCenter, "⚙️ Genetic Optimizer  ·  🎲 Monte Carlo  ·  📅 Heatmap")
    p.setPen(QColor("#45475a")); p.setFont(QFont("Segoe UI", 9))
    p.drawText(0, 245, 520, 25, Qt.AlignmentFlag.AlignHCenter, "Python · PyQt6 · yfinance · Anthropic Claude")
    p.end()

    splash = QSplashScreen(px)
    splash.show(); app.processEvents()

    from src.core.data_manager import DataManager
    dm = DataManager()

    from src.ui.main_window import MainWindow
    win = MainWindow(dm)

    def show_main():
        win.show(); splash.finish(win)

    QTimer.singleShot(1800, show_main)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
