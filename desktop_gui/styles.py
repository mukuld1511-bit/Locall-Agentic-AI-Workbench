"""Industrial Dark Qt StyleSheet (QSS) for Sovereign Air-Gapped Workstations.

Designed for high readability in control rooms and industrial field environments.
Complies with WCAG AA contrast standards; strictly uses local offline styling.
"""

QSS_INDUSTRIAL_DARK = """
QMainWindow, QWidget {
    background-color: #12161c;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #2d3748;
    background-color: #1a202c;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #12161c;
    color: #a0aec0;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #2d3748;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1a202c;
    color: #38bdf8;
    font-weight: bold;
    border-bottom: 2px solid #38bdf8;
}

QGroupBox {
    border: 1px solid #2d3748;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #94a3b8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: #12161c;
}

QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#DangerButton {
    background-color: #dc2626;
}

QPushButton#DangerButton:hover {
    background-color: #b91c1c;
}

QPushButton#SuccessButton {
    background-color: #16a34a;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 10px;
    color: #f8fafc;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #38bdf8;
}

QTableWidget, QTreeWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 4px;
    gridline-color: #1e293b;
    color: #f1f5f9;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QProgressBar {
    border: 1px solid #334155;
    border-radius: 4px;
    text-align: center;
    background-color: #0f172a;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #0284c7;
    border-radius: 3px;
}

QLabel#SecurityBadge {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}

QLabel#WarningBadge {
    background-color: #78350f;
    color: #fbbf24;
    border: 1px solid #d97706;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}
"""
