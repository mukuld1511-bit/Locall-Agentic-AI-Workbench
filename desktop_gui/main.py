
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit,
    QTextBrowser, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QFormLayout
)

from .styles import apply_app_style, MUTED, GOOD, BAD, ACCENT

try:
    from backend.app.auth.auth_service import AuthService
except Exception:
    AuthService = None

try:
    from backend.app.database.db import DB
except Exception:
    DB = None

try:
    from backend.app.workflows.workflow_engine import WORKFLOW_ENGINE
except Exception:
    WORKFLOW_ENGINE = None

try:
    from backend.app.audit.audit_service import AUDIT
except Exception:
    AUDIT = None

try:
    from model_manager.manager import MODEL_MGR
except Exception:
    MODEL_MGR = None


def ensure_schema():
    if DB is not None:
        try:
            DB.init_schema()
        except Exception:
            pass


def open_local_file(path: str):
    try:
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        pass


def esc(text: str) -> str:
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace("\n", "<br>")
    )


class ChatInput(QPlainTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                if self.toPlainText().strip():
                    self.send_requested.emit()
            return
        super().keyPressEvent(event)


class WorkflowWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, task, user_id, role, session_id):
        super().__init__()
        self.task = task
        self.user_id = user_id
        self.role = role
        self.session_id = session_id

    def run(self):
        try:
            if WORKFLOW_ENGINE is None:
                raise RuntimeError("Workflow Engine unavailable.")
            state = WORKFLOW_ENGINE.execute_workflow(
                task_description=self.task,
                user_id=self.user_id,
                role=self.role,
                session_id=self.session_id,
            )
            self.finished.emit(state)
        except Exception as exc:
            self.failed.emit(str(exc))


class LoginWidget(QWidget):
    authenticated = Signal(dict)

    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self)
        root.setContentsMargins(70, 55, 70, 55)
        root.setSpacing(24)

        left = QFrame()
        left.setObjectName("panel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(34, 34, 34, 34)

        brand = QLabel("SOVEREIGN\nINDUSTRIAL AI")
        brand.setStyleSheet(f"font-size:30px;font-weight:700;color:{ACCENT};")
        ll.addWidget(brand)

        sub = QLabel("Local intelligence for confidential industrial operations")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{MUTED};font-size:12px;")
        ll.addWidget(sub)
        ll.addStretch()

        for text in ("● LOCAL RUNTIME", "● SECURE SESSION", "NO CLOUD DATA PATH"):
            lab = QLabel(text)
            lab.setStyleSheet(
                f"color:{GOOD if '●' in text else MUTED};font-weight:700;"
                if '●' in text else f"color:{MUTED};font-size:10px;"
            )
            ll.addWidget(lab)

        right = QFrame()
        right.setObjectName("panel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(34, 34, 34, 34)

        title = QLabel("Welcome back")
        title.setObjectName("title")
        rl.addWidget(title)

        hint = QLabel("Sign in to your local workbench.")
        hint.setStyleSheet(f"color:{MUTED};")
        rl.addWidget(hint)
        rl.addSpacing(18)

        rl.addWidget(QLabel("USERNAME"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("mukul")
        rl.addWidget(self.username)

        rl.addSpacing(8)
        rl.addWidget(QLabel("PASSWORD"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        rl.addWidget(self.password)

        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet(f"color:{BAD};")
        rl.addWidget(self.error)

        button = QPushButton("SIGN IN")
        button.setObjectName("primary")
        button.clicked.connect(self.login)
        rl.addSpacing(6)
        rl.addWidget(button)
        rl.addStretch()

        root.addWidget(left, 1)
        root.addWidget(right, 1)

    def login(self):
        ensure_schema()
        if not self.username.text().strip() or not self.password.text():
            self.error.setText("Enter username and password.")
            return

        if AuthService is None:
            self.error.setText("Authentication service unavailable.")
            return

        try:
            result = AuthService().login(
                self.username.text().strip(),
                self.password.text(),
            )
            if result.get("success"):
                self.authenticated.emit(result)
            else:
                self.error.setText(result.get("error", "Invalid credentials"))
        except Exception as exc:
            self.error.setText(str(exc))


class SovereignWorkbenchGUI(QMainWindow):
    def __init__(self, user: Optional[dict] = None):
        super().__init__()
        self.user = user or {
            "user_id": "usr_local",
            "username": "local",
            "role": "GRADE_2",
        }
        self.current_state = None
        self.attached_file = None

        self.setWindowTitle("Sovereign Industrial AI Workbench")
        self.resize(1360, 820)
        self.setMinimumSize(1050, 680)
        self._build()
        self._refresh_all()

    def panel(self):
        frame = QFrame()
        frame.setObjectName("panel")
        return frame

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(12, 12, 12, 10)
        shell.setSpacing(10)

        shell.addWidget(self._header())

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self._sidebar())

        self.pages = QStackedWidget()
        self.pages.addWidget(self._chat_page())
        self.pages.addWidget(self._files_page())
        self.pages.addWidget(self._workflow_page())
        self.pages.addWidget(self._models_page())
        self.pages.addWidget(self._audit_page())
        body.addWidget(self.pages, 1)

        shell.addLayout(body, 1)

        footer = self.panel()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 6, 12, 6)

        self.status = QLabel("● LOCAL • READY")
        self.status.setStyleSheet(f"color:{GOOD};font-weight:700;")
        fl.addWidget(self.status)
        fl.addStretch()

        self.resource = QLabel()
        self.resource.setStyleSheet(
            f"color:{MUTED};font-family:monospace;font-size:10px;"
        )
        fl.addWidget(self.resource)
        shell.addWidget(footer)

    def _header(self):
        frame = self.panel()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 9, 14, 9)

        title = QLabel("SOVEREIGN INDUSTRIAL AI WORKBENCH")
        title.setStyleSheet("font-size:14px;font-weight:700;")
        layout.addWidget(title)

        local = QLabel("LOCAL")
        local.setStyleSheet(
            f"color:{ACCENT};background:#edf4ff;padding:4px 8px;"
            "border-radius:6px;font-weight:700;"
        )
        layout.addWidget(local)
        layout.addStretch()

        name = self.user.get("username", self.user.get("user_id", "local"))
        role = self.user.get("role", "UNKNOWN")
        who = QLabel(f"{name}  •  {role}")
        who.setStyleSheet(f"color:{MUTED};font-family:monospace;")
        layout.addWidget(who)
        return frame

    def _sidebar(self):
        frame = self.panel()
        frame.setFixedWidth(170)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 12, 8, 12)

        section = QLabel("WORKBENCH")
        section.setObjectName("section")
        layout.addWidget(section)
        layout.addSpacing(5)

        self.nav_buttons = []
        for text, index in [
            ("Chat", 0), ("Files", 1), ("Workflow", 2),
            ("Models", 3), ("Audit", 4)
        ]:
            button = QPushButton(text)
            button.setObjectName("nav")
            button.setProperty("active", index == 0)
            button.clicked.connect(
                lambda _, i=index, b=button: self._switch(i, b)
            )
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()

        note = QLabel("LOCAL ONLY\nBackend authorization\nAudit protected")
        note.setStyleSheet(f"color:{MUTED};font-size:10px;padding:7px;")
        layout.addWidget(note)

        return frame

    def _switch(self, index, button):
        self.pages.setCurrentIndex(index)
        for b in self.nav_buttons:
            b.setProperty("active", b is button)
            b.style().unpolish(b)
            b.style().polish(b)
        self._refresh_all()

    def _chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        box = QVBoxLayout()
        title = QLabel("Chat")
        title.setObjectName("title")
        box.addWidget(title)
        subtitle = QLabel("Local AI workspace · your data stays on this machine")
        subtitle.setObjectName("subtitle")
        box.addWidget(subtitle)
        top.addLayout(box)
        top.addStretch()

        self.mode = QComboBox()
        self.mode.addItems(["Workflow", "General"])
        self.mode.setFixedWidth(120)
        top.addWidget(self.mode)

        local = QLabel("● LOCAL")
        local.setStyleSheet(f"color:{GOOD};font-weight:700;padding-left:6px;")
        top.addWidget(local)
        layout.addLayout(top)

        history = self.panel()
        hl = QVBoxLayout(history)
        hl.setContentsMargins(8, 8, 8, 8)

        self.output = QTextBrowser()
        self.output.setOpenExternalLinks(False)
        self.output.setPlaceholderText("Start a conversation…")
        self.output.setStyleSheet("QTextBrowser { border:0; background:transparent; }")
        hl.addWidget(self.output, 1)
        layout.addWidget(history, 1)

        composer = self.panel()
        cl = QVBoxLayout(composer)
        cl.setContentsMargins(10, 10, 10, 10)

        self.task_input = ChatInput()
        self.task_input.setPlaceholderText(
            "Message your local AI…   Enter to send · Shift+Enter for new line"
        )
        self.task_input.setFixedHeight(90)
        self.task_input.send_requested.connect(self._run)
        cl.addWidget(self.task_input)

        row = QHBoxLayout()
        attach = QPushButton("＋ Attach")
        attach.clicked.connect(self._attach)
        row.addWidget(attach)

        self.file_label = QLabel("No file attached")
        self.file_label.setStyleSheet(f"color:{MUTED};font-size:10px;")
        row.addWidget(self.file_label)
        row.addStretch()

        hint = QLabel("Enter ↵")
        hint.setStyleSheet(f"color:{MUTED};font-size:10px;")
        row.addWidget(hint)

        self.run_button = QPushButton("Send")
        self.run_button.setObjectName("primary")
        self.run_button.setMinimumWidth(88)
        self.run_button.clicked.connect(self._run)
        row.addWidget(self.run_button)

        cl.addLayout(row)
        layout.addWidget(composer)
        return page

    def _attach(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach local file", str(Path.home()),
            "Documents (*.pdf *.docx *.xlsx *.pptx *.txt);;Images (*.png *.jpg *.jpeg *.webp);;All files (*)"
        )
        if path:
            self.attached_file = path
            self.file_label.setText(Path(path).name)

    def _run(self):
        text = self.task_input.toPlainText().strip()
        if not text:
            return

        user_text = esc(text)
        task = text
        if self.attached_file:
            task += f"\n\nAttached local file: {self.attached_file}"

        self.output.append(
            f'<div style="margin:12px 8px 8px 110px; padding:12px;'
            f'background:#edf4ff; border:1px solid #d4e3fd; border-radius:12px;">'
            f'<b style="color:{ACCENT};font-size:10px;">YOU</b>'
            f'<div style="margin-top:6px;">{user_text}</div></div>'
        )
        self.task_input.clear()
        self.run_button.setEnabled(False)
        self.status.setText("● THINKING")

        uid = self.user.get("user_id", self.user.get("username", "usr_local"))
        role = self.user.get("role", "GRADE_2")
        sid = self.user.get("session_id", f"gui_{uuid.uuid4().hex[:10]}")

        if self.mode.currentText() == "General":
            try:
                result = MODEL_MGR.run_worker(
                    "general", task, request_id=sid, max_tokens=512
                )
                content = esc(getattr(result, "content", ""))
                self.output.append(
                    f'<div style="margin:8px 110px 14px 8px; padding:12px;'
                    f'background:white; border:1px solid #e4e8ee; border-radius:12px;">'
                    f'<b style="color:{MUTED};font-size:10px;">LOCAL AI · GENERAL</b>'
                    f'<div style="margin-top:6px;">{content}</div></div>'
                )
            except Exception as exc:
                self.output.append(
                    f'<div style="margin:8px 110px 14px 8px; padding:12px;'
                    f'background:#fff0f2; border:1px solid #f3cbd0; border-radius:12px;">'
                    f'<b style="color:{BAD};">ERROR</b><div>{esc(exc)}</div></div>'
                )
            self.run_button.setEnabled(True)
            self.status.setText("● LOCAL • READY")
            return

        self.output.append(
            f'<div style="margin:8px 110px 8px 8px; padding:10px 12px;'
            f'background:#fbfcfe; border:1px solid #e4e8ee; border-radius:10px;'
            f'color:{MUTED};">Running local workflow…</div>'
        )

        self.thread = QThread()
        self.worker = WorkflowWorker(task, uid, role, sid)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._workflow_done)
        self.worker.failed.connect(self._workflow_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(lambda: self.run_button.setEnabled(True))
        self.thread.start()

    def _workflow_failed(self, message):
        self.output.append(
            f'<div style="margin:8px 110px 14px 8px; padding:12px;'
            f'background:#fff0f2; border:1px solid #f3cbd0; border-radius:12px;">'
            f'<b style="color:{BAD};">WORKFLOW FAILED</b>'
            f'<div style="margin-top:5px;">{esc(message)}</div></div>'
        )
        self.status.setText("● LOCAL • ERROR")
        self._refresh_all()

    def _workflow_done(self, state):
        self.current_state = state

        status = getattr(state, "status", "UNKNOWN")
        completed = getattr(state, "completed_steps", [])
        failed = getattr(state, "failed_steps", [])
        verification = getattr(state, "verification_summary", {})
        final = getattr(state, "final_response", "")
        artifacts = getattr(state, "generated_artifacts", [])

        color = GOOD if str(status).upper() == "COMPLETED" else BAD

        self.output.append(
            f'<div style="margin:8px 110px 14px 8px; padding:14px;'
            f'background:white; border:1px solid #e4e8ee; border-radius:12px;">'
            f'<b style="color:{color};font-size:10px;">WORKFLOW · {esc(status)}</b>'
            f'<div style="margin-top:8px;line-height:1.5;">{esc(final)}</div>'
            f'<div style="margin-top:10px;padding-top:9px;border-top:1px solid #edf0f3;'
            f'color:{MUTED};font-size:10px;">'
            f'Steps: {completed} · Verification: {verification.get("overall_status","UNKNOWN")}'
            f'</div></div>'
        )

        if artifacts:
            self.output.append(
                f'<div style="margin:0 110px 14px 8px; padding:12px 14px;'
                f'background:#eaf8f1; border:1px solid #c9ead9; border-radius:10px;'
                f'color:{GOOD};"><b>Artifacts generated</b><br>'
                f'{"<br>".join(esc(a) for a in map(str, artifacts))}</div>'
            )

        self.status.setText("● LOCAL • READY")
        self._refresh_all()

    def _files_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Files")
        title.setObjectName("title")
        layout.addWidget(title)
        sub = QLabel("Generated local artifacts.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        self.files = QListWidget()
        self.files.itemDoubleClicked.connect(
            lambda item: open_local_file(item.data(Qt.UserRole))
        )
        layout.addWidget(self.files, 1)
        return page

    def _refresh_files(self):
        if not hasattr(self, "files"):
            return
        self.files.clear()
        root = Path("data/artifacts")
        if not root.exists():
            return
        for p in sorted(root.iterdir()):
            if p.is_file():
                item = QListWidgetItem(
                    f"{p.name}    ·    {p.stat().st_size:,} bytes"
                )
                item.setData(Qt.UserRole, str(p.resolve()))
                self.files.addItem(item)

    def _workflow_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Workflow")
        title.setObjectName("title")
        layout.addWidget(title)

        self.workflow_info = QLabel("No workflow executed.")
        self.workflow_info.setStyleSheet(f"color:{MUTED};")
        layout.addWidget(self.workflow_info)

        self.workflow_table = QTableWidget(0, 2)
        self.workflow_table.setHorizontalHeaderLabels(["STEP", "STATUS"])
        self.workflow_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.workflow_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.workflow_table, 1)
        return page

    def _refresh_workflow(self):
        if not hasattr(self, "workflow_table"):
            return
        self.workflow_table.setRowCount(0)
        if self.current_state is None:
            self.workflow_info.setText("No workflow executed.")
            return

        state = self.current_state
        status = getattr(state, "status", "UNKNOWN")
        completed = getattr(state, "completed_steps", [])
        failed = getattr(state, "failed_steps", [])

        self.workflow_info.setText(
            f"STATUS {status}  ·  COMPLETED {completed}  ·  FAILED {failed}"
        )

        for n in completed:
            r = self.workflow_table.rowCount()
            self.workflow_table.insertRow(r)
            self.workflow_table.setItem(r, 0, QTableWidgetItem(str(n)))
            self.workflow_table.setItem(r, 1, QTableWidgetItem("COMPLETED"))

        for n in failed:
            r = self.workflow_table.rowCount()
            self.workflow_table.insertRow(r)
            self.workflow_table.setItem(r, 0, QTableWidgetItem(str(n)))
            self.workflow_table.setItem(r, 1, QTableWidgetItem("FAILED"))

    def _models_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Models")
        title.setObjectName("title")
        layout.addWidget(title)
        sub = QLabel("Local worker state and active model.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        self.models = QTableWidget(0, 3)
        self.models.setHorizontalHeaderLabels(["WORKER", "STATE", "MODEL"])
        self.models.setEditTriggers(QTableWidget.NoEditTriggers)
        self.models.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.models, 1)
        return page

    def _refresh_models(self):
        if not hasattr(self, "models"):
            return

        self.models.setRowCount(0)

        for name in ["organizer", "general", "coding", "vision", "document"]:
            state = "UNKNOWN"
            model = ""
            try:
                if MODEL_MGR:
                    state = MODEL_MGR.get_model_state(name)
                    worker = MODEL_MGR.registry.get_worker(name)
                    model = getattr(worker, "model_name", "") if worker else ""
            except Exception as exc:
                model = str(exc)

            row = self.models.rowCount()
            self.models.insertRow(row)
            for c, value in enumerate(
                [name.upper(), str(state), str(model)]
            ):
                self.models.setItem(row, c, QTableWidgetItem(value))

    def _audit_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Audit")
        title.setObjectName("title")
        layout.addWidget(title)

        self.audit = QListWidget()
        layout.addWidget(self.audit, 1)

        self.audit_status = QLabel()
        self.audit_status.setStyleSheet(
            f"color:{GOOD};font-family:monospace;font-size:10px;"
        )
        layout.addWidget(self.audit_status)
        return page

    def _refresh_audit(self):
        if not hasattr(self, "audit"):
            return

        self.audit.clear()
        if AUDIT is None:
            self.audit.addItem("Audit service unavailable.")
            return

        try:
            result = AUDIT.verify_integrity()
            self.audit_status.setText(
                f"CHAIN: {'VALID' if result.get('chain_valid') else 'INVALID'}"
                f"   ·   RECORDS: {result.get('total_records_checked', 0)}"
            )
        except Exception as exc:
            self.audit_status.setText(f"AUDIT CHECK ERROR: {exc}")

    def _refresh_all(self):
        self._refresh_files()
        self._refresh_workflow()
        self._refresh_models()
        self._refresh_audit()

        if MODEL_MGR is not None:
            try:
                status = MODEL_MGR.get_system_status()
                self.resource.setText(
                    f"ACTIVE {len(status.get('active_workers', []))}"
                    f"  ·  {status.get('vram_current_used_mb', 0)} MB USED"
                    f"  ·  {status.get('vram_headroom_mb', 0)} MB HEADROOM"
                )
            except Exception:
                pass


def run_app():
    ensure_schema()
    app = QApplication(sys.argv)
    apply_app_style(app)

    login = LoginWidget()
    host = QMainWindow()
    host.setWindowTitle("Sovereign Industrial AI Workbench")
    host.resize(860, 600)
    host.setMinimumSize(760, 520)
    host.setCentralWidget(login)
    host.show()

    def authenticated(user):
        main = SovereignWorkbenchGUI(user)
        main.show()
        host.hide()
        app.main_window = main

    login.authenticated.connect(authenticated)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_app())
