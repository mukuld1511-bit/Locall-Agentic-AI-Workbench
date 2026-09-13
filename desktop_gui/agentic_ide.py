from __future__ import annotations

import difflib
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QKeySequence,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


ROOT = Path(__file__).resolve().parents[1]


class CodeEditor(QTextEdit):

    file_changed = Signal()

    def __init__(self):
        super().__init__()

        self.setFont(
            QFont("JetBrains Mono", 11)
        )

        self.setAcceptRichText(False)

        self.setTabStopDistance(
            4 * self.fontMetrics().horizontalAdvance(" ")
        )

        self.document().modificationChanged.connect(
            self._modified
        )

    def _modified(self, changed):
        if changed:
            self.file_changed.emit()

    def keyPressEvent(self, event):

        # Ctrl+S
        if event.matches(
            QKeySequence.StandardKey.Save
        ):
            window = self.window()

            if hasattr(
                window,
                "save_current_file",
            ):
                window.save_current_file()

            return

        # Ctrl+F
        if event.matches(
            QKeySequence.StandardKey.Find
        ):
            window = self.window()

            if hasattr(
                window,
                "focus_search",
            ):
                window.focus_search()

            return

        super().keyPressEvent(event)


class AgenticIDE(QMainWindow):

    def __init__(
        self,
        user=None,
    ):
        super().__init__()

        self.user = user or {
            "username": "local",
            "role": "ADMIN",
        }

        self.current_file = None
        self.file_tabs = {}

        self.setWindowTitle(
            "Sovereign Agentic IDE"
        )

        self.resize(
            1550,
            950,
        )

        self._build_ui()
        self._build_actions()

        self.refresh_explorer()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        central = QWidget()
        self.setCentralWidget(
            central
        )

        root = QVBoxLayout(
            central
        )

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        # ----------------------------------------------------
        # TOP BAR
        # ----------------------------------------------------

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        root.addWidget(
            self.toolbar
        )

        self.brand = QLabel(
            "  SOVEREIGN IDE"
        )

        self.brand.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 700;
                padding: 8px 14px;
            }
            """
        )

        self.toolbar.addWidget(
            self.brand
        )

        self.toolbar.addSeparator()

        self.run_button = QPushButton(
            "▶ Run"
        )

        self.run_button.clicked.connect(
            self.run_current
        )

        self.toolbar.addWidget(
            self.run_button
        )

        self.sandbox_button = QPushButton(
            "Sandbox"
        )

        self.sandbox_button.clicked.connect(
            self.run_sandbox
        )

        self.toolbar.addWidget(
            self.sandbox_button
        )

        self.toolbar.addSeparator()

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search in file..."
        )

        self.search.setMaximumWidth(
            280
        )

        self.search.returnPressed.connect(
            self.search_current
        )

        self.toolbar.addWidget(
            self.search
        )

        self.toolbar.addSeparator()

        self.language = QComboBox()

        self.language.addItems([
            "Auto",
            "Python",
            "JavaScript",
            "HTML",
            "CSS",
            "JSON",
            "Shell",
        ])

        self.toolbar.addWidget(
            self.language
        )

        # ----------------------------------------------------
        # MAIN SPLITTER
        # ----------------------------------------------------

        self.main_splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        root.addWidget(
            self.main_splitter,
            1,
        )

        # ----------------------------------------------------
        # EXPLORER
        # ----------------------------------------------------

        explorer = QWidget()

        explorer_layout = QVBoxLayout(
            explorer
        )

        explorer_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        title = QLabel(
            "EXPLORER"
        )

        explorer_layout.addWidget(
            title
        )

        self.file_tree = QListWidget()

        self.file_tree.itemDoubleClicked.connect(
            self.open_explorer_item
        )

        explorer_layout.addWidget(
            self.file_tree,
            1,
        )

        buttons = QHBoxLayout()

        for text, callback in (
            ("＋", self.create_file),
            ("↻", self.refresh_explorer),
            ("⌕", self.focus_search),
        ):

            button = QPushButton(
                text
            )

            button.clicked.connect(
                callback
            )

            buttons.addWidget(
                button
            )

        explorer_layout.addLayout(
            buttons
        )

        self.main_splitter.addWidget(
            explorer
        )

        # ----------------------------------------------------
        # CENTER EDITOR
        # ----------------------------------------------------

        center = QWidget()

        center_layout = QVBoxLayout(
            center
        )

        center_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.tabs = QTabWidget()

        self.tabs.setTabsClosable(
            True
        )

        self.tabs.tabCloseRequested.connect(
            self.close_tab
        )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

        center_layout.addWidget(
            self.tabs,
            1,
        )

        self.main_splitter.addWidget(
            center
        )

        # ----------------------------------------------------
        # AGENT PANEL
        # ----------------------------------------------------

        agent = QWidget()

        agent_layout = QVBoxLayout(
            agent
        )

        agent_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        agent_title = QLabel(
            "AGENT"
        )

        agent_title.setStyleSheet(
            "font-weight:700;"
        )

        agent_layout.addWidget(
            agent_title
        )

        self.agent_status = QLabel(
            "Ready"
        )

        agent_layout.addWidget(
            self.agent_status
        )

        self.agent_input = QTextEdit()

        self.agent_input.setPlaceholderText(
            "Ask the local agent to explain, edit, "
            "create or refactor code..."
        )

        self.agent_input.setMaximumHeight(
            120
        )

        agent_layout.addWidget(
            self.agent_input
        )

        self.agent_send = QPushButton(
            "Ask Agent"
        )

        self.agent_send.clicked.connect(
            self.agent_request
        )

        agent_layout.addWidget(
            self.agent_send
        )

        self.agent_output = QTextEdit()

        self.agent_output.setReadOnly(
            True
        )

        agent_layout.addWidget(
            self.agent_output,
            1,
        )

        self.main_splitter.addWidget(
            agent
        )

        self.main_splitter.setSizes([
            240,
            850,
            360,
        ])

        # ----------------------------------------------------
        # BOTTOM PANEL
        # ----------------------------------------------------

        self.bottom_tabs = QTabWidget()

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(
            True
        )

        self.output = QTextEdit()
        self.output.setReadOnly(
            True
        )

        self.problems = QListWidget()

        self.preview = QTextEdit()
        self.preview.setReadOnly(
            True
        )

        self.bottom_tabs.addTab(
            self.terminal,
            "Terminal",
        )

        self.bottom_tabs.addTab(
            self.output,
            "Output",
        )

        self.bottom_tabs.addTab(
            self.problems,
            "Problems",
        )

        self.bottom_tabs.addTab(
            self.preview,
            "Preview",
        )

        root.addWidget(
            self.bottom_tabs
        )

    # ========================================================
    # ACTIONS
    # ========================================================

    def _build_actions(self):

        action = QAction(
            "Save",
            self,
        )

        action.setShortcut(
            QKeySequence.StandardKey.Save
        )

        action.triggered.connect(
            self.save_current_file
        )

        self.addAction(
            action
        )

        action = QAction(
            "Search",
            self,
        )

        action.setShortcut(
            QKeySequence.StandardKey.Find
        )

        action.triggered.connect(
            self.focus_search
        )

        self.addAction(
            action
        )

        action = QAction(
            "Command Palette",
            self,
        )

        action.setShortcut(
            "Ctrl+Shift+P"
        )

        action.triggered.connect(
            self.command_palette
        )

        self.addAction(
            action
        )

    # ========================================================
    # EXPLORER
    # ========================================================

    def refresh_explorer(self):

        self.file_tree.clear()

        allowed = (
            ROOT / "backend",
            ROOT / "desktop_gui",
            ROOT / "tools",
            ROOT / "rag",
            ROOT / "model_manager",
        )

        for base in allowed:

            if not base.exists():
                continue

            parent = QListWidgetItem(
                f"📁 {base.name}"
            )

            parent.setData(
                Qt.ItemDataRole.UserRole,
                str(base),
            )

            self.file_tree.addItem(
                parent
            )

            for path in sorted(
                base.rglob("*")
            ):

                if not path.is_file():
                    continue

                if "__pycache__" in path.parts:
                    continue

                if path.suffix.lower() not in {
                    ".py",
                    ".js",
                    ".html",
                    ".css",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".md",
                    ".txt",
                    ".sh",
                }:
                    continue

                item = QListWidgetItem(
                    "  "
                    + str(
                        path.relative_to(
                            ROOT
                        )
                    )
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    str(path),
                )

                self.file_tree.addItem(
                    item
                )

    def open_explorer_item(self, item):

        path = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not path:
            return

        path = Path(path)

        if path.is_file():
            self.open_file(
                path
            )

    # ========================================================
    # FILES
    # ========================================================

    def open_file(self, path):

        path = Path(
            path
        ).expanduser().resolve()

        if not path.exists():
            return

        if path in self.file_tabs:
            self.tabs.setCurrentWidget(
                self.file_tabs[path]
            )
            return

        try:

            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Open failed",
                str(exc),
            )

            return

        editor = CodeEditor()

        editor.setPlainText(
            text
        )

        editor.document().setModified(
            False
        )

        index = self.tabs.addTab(
            editor,
            path.name,
        )

        self.tabs.setCurrentIndex(
            index
        )

        self.file_tabs[
            path
        ] = editor

        editor.file_changed.connect(
            lambda: self.update_tab_title(editor, path)
        )

        self.current_file = path

        self.preview_if_html(
            path,
            text,
        )

    def update_tab_title(
        self,
        editor,
        path,
    ):

        index = self.tabs.indexOf(
            editor
        )

        if index < 0:
            return

        name = path.name

        if editor.document().isModified():
            name += " ●"

        self.tabs.setTabText(
            index,
            name,
        )

    def tab_changed(self, index):

        widget = self.tabs.widget(
            index
        )

        if widget is None:
            return

        for path, editor in self.file_tabs.items():

            if editor is widget:

                self.current_file = path

                self.preview_if_html(
                    path,
                    editor.toPlainText(),
                )

                break

    def save_current_file(self):

        editor = self.tabs.currentWidget()

        if editor is None:
            return

        if not isinstance(
            editor,
            CodeEditor,
        ):
            return

        path = None

        for p, e in self.file_tabs.items():

            if e is editor:
                path = p
                break

        if path is None:

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save file",
                str(ROOT),
                "Source files (*)",
            )

            if not path:
                return

            path = Path(path).resolve()

            self.file_tabs[
                path
            ] = editor

        try:

            editor.setDocument(
                editor.document()
            )

            path.write_text(
                editor.toPlainText(),
                encoding="utf-8",
            )

            editor.document().setModified(
                False
            )

            self.current_file = path

            self.refresh_explorer()

            self.output.append(
                f"[saved] {path}"
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Save failed",
                str(exc),
            )

    def create_file(self):

        name, _ = QFileDialog.getSaveFileName(
            self,
            "Create source file",
            str(ROOT),
            "Source files (*)",
        )

        if not name:
            return

        path = Path(
            name
        ).expanduser().resolve()

        try:
            path.write_text(
                "",
                encoding="utf-8",
            )

            self.open_file(
                path
            )

            self.refresh_explorer()

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Create failed",
                str(exc),
            )

    def close_tab(self, index):

        widget = self.tabs.widget(
            index
        )

        if isinstance(
            widget,
            CodeEditor,
        ) and widget.document().isModified():

            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save changes before closing?",
            )

            if answer == QMessageBox.StandardButton.Yes:

                self.tabs.setCurrentIndex(
                    index
                )

                self.save_current_file()

        self.tabs.removeTab(
            index
        )

        for path, editor in list(
            self.file_tabs.items()
        ):

            if editor is widget:
                del self.file_tabs[path]
                break

    # ========================================================
    # SEARCH
    # ========================================================

    def focus_search(self):

        self.search.setFocus()
        self.search.selectAll()

    def search_current(self):

        text = self.search.text()

        if not text:
            return

        editor = self.tabs.currentWidget()

        if editor is None:
            return

        cursor = editor.document().find(
            text,
            editor.textCursor(),
        )

        if not cursor.isNull():
            editor.setTextCursor(
                cursor
            )

    # ========================================================
    # RUN
    # ========================================================

    def run_current(self):

        if not self.current_file:
            return

        path = Path(
            self.current_file
        )

        if path.suffix.lower() == ".py":

            self.output.append(
                f"[run] {path}"
            )

            process = subprocess.run(
                [
                    sys.executable,
                    str(path),
                ],
                cwd=str(path.parent),
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.output.append(
                process.stdout
            )

            if process.stderr:
                self.problems.addItem(
                    process.stderr
                )

        elif path.suffix.lower() == ".html":

            self.preview_if_html(
                path,
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ),
            )

            self.bottom_tabs.setCurrentIndex(
                3
            )

    # ========================================================
    # SANDBOX
    # ========================================================

    def run_sandbox(self):

        editor = self.tabs.currentWidget()

        if editor is None:
            return

        if not isinstance(
            editor,
            CodeEditor,
        ):
            return

        code = editor.toPlainText()

        sandbox = (
            ROOT
            / "runtime"
            / "sandbox"
        )

        sandbox.mkdir(
            parents=True,
            exist_ok=True,
        )

        script = (
            sandbox / "ide_run.py"
        )

        script.write_text(
            code,
            encoding="utf-8",
        )

        self.bottom_tabs.setCurrentIndex(
            1
        )

        self.output.append(
            "[sandbox] running..."
        )

        try:

            process = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(script),
                ],
                cwd=str(sandbox),
                capture_output=True,
                text=True,
                timeout=30,
                env={
                    "PATH": os.environ.get(
                        "PATH",
                        "",
                    ),
                    "HOME": str(
                        sandbox
                    ),
                    "TMPDIR": str(
                        sandbox
                    ),
                    "PYTHONUNBUFFERED": "1",
                },
            )

            self.output.append(
                process.stdout
            )

            if process.stderr:
                self.output.append(
                    process.stderr
                )

            self.output.append(
                f"[sandbox] exit={process.returncode}"
            )

        except subprocess.TimeoutExpired:

            self.output.append(
                "[sandbox] timeout"
            )

    # ========================================================
    # HTML PREVIEW
    # ========================================================

    def preview_if_html(
        self,
        path,
        text,
    ):

        if Path(
            path
        ).suffix.lower() != ".html":
            return

        self.preview.setPlainText(
            text
        )

    # ========================================================
    # AGENT
    # ========================================================

    def agent_request(self):

        request = self.agent_input.toPlainText().strip()

        if not request:
            return

        editor = self.tabs.currentWidget()

        selected = ""

        if editor is not None:
            selected = editor.textCursor().selectedText()

        file_content = ""

        if editor is not None:
            file_content = editor.toPlainText()

        self.agent_status.setText(
            "Working…"
        )

        self.agent_output.append(
            f"> {request}"
        )

        # Leave actual model invocation to the existing
        # Workbench ModelManager integration. The IDE prepares
        # a clean agent context here.

        self.agent_output.append(
            "\nAgent context prepared:"
            f"\nFile: {self.current_file}"
            f"\nSelected code: {len(selected)} chars"
            f"\nFile content: {len(file_content)} chars"
            "\n\nConnect this request to the Workbench "
            "Coding/General model through ModelManager."
        )

        self.agent_status.setText(
            "Ready"
        )

    # ========================================================
    # COMMAND PALETTE
    # ========================================================

    def command_palette(self):

        commands = [
            "Open File",
            "Save File",
            "Run",
            "Run in Sandbox",
            "Refresh Explorer",
            "Search",
        ]

        from PySide6.QtWidgets import QInputDialog

        value, ok = QInputDialog.getItem(
            self,
            "Command Palette",
            "Command:",
            commands,
            0,
            False,
        )

        if not ok:
            return

        if value == "Open File":

            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open",
                str(ROOT),
            )

            if path:
                self.open_file(
                    Path(path)
                )

        elif value == "Save File":
            self.save_current_file()

        elif value == "Run":
            self.run_current()

        elif value == "Run in Sandbox":
            self.run_sandbox()

        elif value == "Refresh Explorer":
            self.refresh_explorer()

        elif value == "Search":
            self.focus_search()


def open_agentic_ide(user=None):

    app = QApplication.instance()

    owns_app = False

    if app is None:
        app = QApplication([])
        owns_app = True

    window = AgenticIDE(
        user
    )

    window.show()

    if owns_app:
        return app.exec()

    return window


def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    window = AgenticIDE()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
