# Sovereign Industrial AI Workbench - Full Upgrade Plan

The user requested a massive, cohesive transformation across both frontend and backend for their upcoming hackathon presentation:
1. **Attachments (Image + Files + DB)**: Attach images, documents (PDF, DOCX, TXT), spreadsheets (XLSX, CSV), and SQLite databases (`.db`) directly into chat with visual preview chip and multimodal vision / document / DB analysis.
2. **IDE Upgrade**:
   - Rename Antigravity IDE to a clean, minimal, sovereign name: **"SOVEREIGN STUDIO"** (or **"INDUSTRIAL AGENTIC IDE"**).
   - Light theme, minimal premium UI matching the Aurora glass aesthetic (clean whites, `#f8fafc` editor themes, subtle borders).
   - Real terminal execution access with command running, output stream, and kill/clear.
   - File creation & folder navigation: Ability to create new files (`+ New File` modal/input), create folders, save, edit, and delete files directly in the IDE workspace.
   - Code language switching (Python, JavaScript/TypeScript, SQL, C++, HTML/CSS, JSON).
3. **Sandbox Upgrade**:
   - Turn Sandbox into an interactive **Programmiz / Online-Compiler** style runtime!
   - Multi-language support: Python, JavaScript/Node, SQL (in-memory/demo DB), Bash/Shell.
   - Split layout: Editor on top/left, interactive Run button, input/stdin box, execution timer, output window with STDOUT, STDERR, exit status, and memory/time metrics.
   - Reset sandbox, sample templates for instant compilation.
4. **Role & Grade-Based Access Control (RBAC & Central Policy Engine)**:
   - Connect the central policy engine and role checks (`GRADE_1`, `GRADE_2`, `GRADE_3`, `ADMIN`).
   - Grade level command authorization:
     - Grade 1 (Operator/Technician): Chat, Read-only documents, cannot run unapproved scripts or drop databases.
     - Grade 2 (Engineer): Sandbox execution, spreadsheet analysis, P&ID inspection, file generation.
     - Grade 3 (Superintendent/CTO): Privileged workflows, confidential documents, equipment override approvals.
     - Admin: Full governance, user creation, policy management, audit trail inspection.
   - **Protection Against Scary Commands**: Explicitly block dangerous commands like "drop database", "delete whole db", "rm -rf /", "TRUNCATE", "DROP TABLE" with policy warning: *"Scary command blocked! Policy Engine prevented database deletion (GRADE_1/Operator cannot drop production database)."*
5. **Sample Industrial Presentation Database (`industrial_demo.db`)**:
   - Expose `/api/db/demo/query`, `/api/db/demo/schema`, `/api/db/demo/tables`, and `/api/db/demo/analytics` in the backend.
   - Add a dedicated **Database & Analytics Explorer** tab or panel where the presenter can click:
     - "Analyze Equipment Health"
     - "Query Corrosion & Sensor Readings"
     - "View Active Work Orders & Employees"
     - Run safe SELECT queries with live data table presentation for hackathon judges!
6. **Employee Registry & Login System**:
   - Full login system modal / user switcher: Switch between `admin` (Admin), `operator_101` (Grade 1), `engineer_202` (Grade 2), `superintendent_303` (Grade 3), or custom login.
   - Real Employee Management page: Register new employee with full name, department, role, password, and view live active directory table synced with `backend/app/database/db.py`.
7. **Intent Resolver & Semantic Organizer Integration**:
   - Wire `desktop_gui/intent_resolver.py` and `desktop_gui/semantic_organizer.py` into the backend `/api/chat` flow so attachments (image, document, db, code) trigger specialized workers (vision, document, coding, db analysis).
   - Enable same-file editing and file generation artifacts directly from chat.
8. **Home UI / Dashboard**:
   - Make the Home / Overview UI rich, filled, aesthetic, and minimal with quick-launch cards:
     - Sovereign Kernel Status & VRAM Budget meter
     - Quick Action Cards: "Run P&ID Vision Analysis", "Analyze Refinery Database", "Launch Safe Python Sandbox", "Generate API-510 Inspection Report"
     - Active Role & Clearance badge
     - Recent chats & recent audit events ticker

---

## User Review Required
> [!IMPORTANT]
> The app will switch from the default dev user to an interactive session model where the user can either stay logged in as `admin` or toggle active employee clearance (`GRADE_1`, `GRADE_2`, `GRADE_3`, `ADMIN`) right from the top title bar to immediately demonstrate security controls to judges!

## Proposed Changes

### Backend (`backend/api_server.py`)
- Import and connect `AUTH`, `DB`, `POLICY`, `RBAC`, `AUDIT` from `backend.app`.
- Add endpoints:
  - `POST /api/auth/login` and `POST /api/auth/logout` and `GET /api/auth/me`
  - `GET /api/employees` and `POST /api/employees/create`
  - `POST /api/chat` with attachment support (`image`, `document`, `database`), policy evaluation, intent resolution, and DB-drop protection.
  - `POST /api/chat/upload` (multipart or base64 file upload storing into `data/uploads`)
  - `POST /api/files/create` (create new file in workspace)
  - `POST /api/files/delete` (delete file with policy check)
  - `POST /api/terminal/run` (safe terminal command runner via `safe_tools.py` / `safe_command`)
  - `GET /api/db/demo/schema` and `POST /api/db/demo/query` (query `industrial_demo.db` for hackathon presentation)
  - `GET /api/audit/logs` (retrieve tamper-evident audit logs)

### Frontend (`src/App.tsx` & `src/index.css`)
- **Header**:
  - Add Role Clearance selector dropdown (`ADMIN`, `GRADE_3 Superintendent`, `GRADE_2 Engineer`, `GRADE_1 Operator`) and Login/Logout profile pill.
  - Minimal, light-themed, refined glass aesthetic.
- **Chat**:
  - Attachment button (+ Image, + File, + Sample DB) with preview thumbnail chips.
  - Multi-modal question answering (Vision analysis for images, schema/data analysis for attached DB).
  - Safety alert banners if a prompt attempts unauthorized or dangerous operations.
- **Studio (IDE)**:
  - Renamed to "Sovereign Studio".
  - Premium light theme (Monaco `vs` or custom light editor, sleek slate borders).
  - Top action bar with New File, Save, Run, Language select, Terminal toggle.
  - File tree with "+ New File" and "+ Refresh".
  - Integrated live terminal tab with command execution prompt and clear button.
- **Programmiz-style Sandbox**:
  - Top bar with language switcher (Python, JavaScript, SQLite, Bash), Run button with hotkey, Clear, Template chooser.
  - Code editor + Stdin input box + Execution Output panel with timing stats and status badges.
- **Database Explorer Tab**:
  - Dedicated view for presentation: inspect `industrial_demo.db` tables (`employees`, `equipment`, `inspections`, `sensor_readings`, `work_orders`), pre-built analytics buttons, and SQL query runner.
- **Employees Tab**:
  - Full Employee registration form and searchable table.
- **Audit Tab**:
  - Live audit trail table showing cryptographic event hashes, user, role, and policy decisions.
