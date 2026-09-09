
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

BG = "#f5f7fa"
PANEL = "#ffffff"
PANEL_ALT = "#fbfcfe"
BORDER = "#e4e8ee"
TEXT = "#17202a"
MUTED = "#77818d"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
ACCENT_SOFT = "#edf4ff"
GOOD = "#16875a"
BAD = "#c43d49"

def apply_app_style(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont("DejaVu Sans", 10))
    app.setStyleSheet(f"""
    QWidget {{ background:{BG}; color:{TEXT}; }}
    QMainWindow, QDialog {{ background:{BG}; }}
    QFrame#panel {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:12px; }}
    QLabel#title {{ color:{TEXT}; font-size:22px; font-weight:650; }}
    QLabel#subtitle {{ color:{MUTED}; font-size:11px; }}
    QLabel#section {{ color:{MUTED}; font-size:10px; font-weight:700; }}
    QLineEdit,QPlainTextEdit,QTextBrowser,QTableWidget,QListWidget,QComboBox {{
        background:{PANEL_ALT}; color:{TEXT}; border:1px solid {BORDER};
        border-radius:10px; padding:9px 10px;
    }}
    QLineEdit:focus,QPlainTextEdit:focus,QComboBox:focus {{
        border:1px solid {ACCENT}; background:{PANEL};
    }}
    QPushButton {{
        background:{PANEL}; color:{TEXT}; border:1px solid {BORDER};
        border-radius:9px; padding:8px 14px; font-weight:600;
    }}
    QPushButton:hover {{ border-color:#bfd1f5; background:{ACCENT_SOFT}; }}
    QPushButton#primary {{
        background:{ACCENT}; color:white; border:0; min-height:36px;
        padding:8px 18px;
    }}
    QPushButton#primary:hover {{ background:{ACCENT_HOVER}; }}
    QPushButton#nav {{
        text-align:left; padding:11px 12px; border:0; border-radius:8px;
        background:transparent; color:{MUTED};
    }}
    QPushButton#nav:hover {{ background:{PANEL_ALT}; color:{TEXT}; }}
    QPushButton#nav[active="true"] {{
        background:{ACCENT_SOFT}; color:{ACCENT}; border:1px solid #d4e3fd;
    }}
    QHeaderView::section {{
        background:{PANEL_ALT}; color:{MUTED}; border:0;
        border-bottom:1px solid {BORDER}; padding:8px; font-size:10px;
        font-weight:700;
    }}
    QTableWidget {{ gridline-color:{BORDER}; }}
    QScrollBar:vertical {{ width:10px; background:transparent; }}
    QScrollBar::handle:vertical {{ background:#ccd4dd; border-radius:5px; min-height:30px; }}
    """)

