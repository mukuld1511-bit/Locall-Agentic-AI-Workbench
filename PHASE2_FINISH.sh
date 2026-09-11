#!/usr/bin/env bash
set +e

ROOT="$(pwd)"
LOG="$ROOT/PHASE2_FINISH.log"

exec > >(tee -a "$LOG") 2>&1

echo "============================================================"
echo "PHASE 2 — RAG + GUI + SECURITY + PACKAGING"
echo "============================================================"
echo "Started: $(date)"

mkdir -p .phase2_backup

backup() {
    f="$1"
    if [ -f "$f" ]; then
        b=".phase2_backup/$(echo "$f" | tr '/' '_').bak"
        [ -f "$b" ] || cp "$f" "$b"
    fi
}

for f in \
    backend/app/workflows/workflow_engine.py \
    backend/app/organizer/organizer_service.py \
    model_manager/manager.py \
    model_manager/registry.py \
    model_manager/adapters/base.py \
    model_manager/adapters/llama_cpp_adapter.py \
    model_manager/adapters/transformers_organizer_adapter.py \
    rag/engine.py \
    rag/store.py \
    desktop_gui/main.py \
    desktop_gui/styles.py \
    tools/gateway.py \
    tools/registry.py \
    README.md \
    .gitignore \
    run_desktop.sh \
    .env.example \
    metadata.json \
    package.json
do
    backup "$f"
done

# ============================================================
# 1. BASELINE
# ============================================================

echo
echo "===== BASELINE TEST ====="
python3 run_tests.py
BASE_RC=$?

# ============================================================
# 2. REPOSITORY INVENTORY
# ============================================================

echo
echo "===== REPOSITORY INVENTORY ====="

find backend model_manager rag tools desktop_gui tests \
    -type f \
    -not -path "*/__pycache__/*" \
    | sort

# ============================================================
# 3. RAG DEEP INSPECTION
# ============================================================

echo
echo "===== RAG SOURCE ====="

[ -f rag/engine.py ] && sed -n '1,360p' rag/engine.py
echo
[ -f rag/store.py ] && sed -n '1,360p' rag/store.py

echo
echo "===== RAG REFERENCES ====="

grep -RniE \
"rag_search|retrieve|retrieval|chunk|embedding|vector|document_id|metadata" \
backend rag tools tests 2>/dev/null \
| grep -v "__pycache__" \
| head -500

# ============================================================
# 4. DOCUMENT INGESTION INVENTORY
# ============================================================

echo
echo "===== DOCUMENT / OCR ====="

grep -RniE \
"OCR|PyMuPDF|pymupdf|fitz|docx|pdf|extract.*text|parse.*document" \
backend tools rag 2>/dev/null \
| grep -v "__pycache__" \
| head -500

# ============================================================
# 5. MAKE LOCAL RAG TEST DIRECTORY
# ============================================================

mkdir -p data/rag_documents
mkdir -p data/rag_index

echo
echo "===== RAG DIRECTORY ====="
ls -lah data/rag_documents
ls -lah data/rag_index

# ============================================================
# 6. RAG SECURITY CHECK
# ============================================================

echo
echo "===== RAG SECURITY ====="

grep -RniE \
"ignore previous|system message|developer message|execute command|sudo|delete database|command_exec" \
rag backend tools tests 2>/dev/null \
| grep -v "__pycache__" \
| head -300 || true

# ============================================================
# 7. GUI SOURCE
# ============================================================

echo
echo "===== DESKTOP GUI SOURCE ====="

find desktop_gui \
    -type f \
    -not -path "*/__pycache__/*" \
    -print

echo
[ -f desktop_gui/main.py ] && sed -n '1,500p' desktop_gui/main.py
echo
[ -f desktop_gui/styles.py ] && sed -n '1,360p' desktop_gui/styles.py

# ============================================================
# 8. GUI DEPENDENCY CHECK
# ============================================================

echo
echo "===== GUI IMPORT ====="

python3 - <<'PY'
try:
    import PySide6
    print("PySide6:", PySide6.__version__)
    print("[OK] Native Qt available")
except Exception as e:
    print("[FAIL]", e)
PY

# ============================================================
# 9. GUI STATIC CHECK
# ============================================================

echo
echo "===== GUI BACKEND CONNECTIONS ====="

grep -RniE \
"ModelManager|WORKFLOW_ENGINE|execute_workflow|Authentication|RBAC|POLICY|AUDIT|ToolGateway|QApplication|QMainWindow" \
desktop_gui 2>/dev/null \
| grep -v "__pycache__" \
| head -500

# ============================================================
# 10. MODEL MANAGER SOURCE REVIEW
# ============================================================

echo
echo "===== MODEL MANAGER ====="

sed -n '1,340p' model_manager/manager.py
echo
sed -n '1,260p' model_manager/registry.py

# ============================================================
# 11. MODEL PATH VALIDATION
# ============================================================

echo
echo "===== MODEL PATH VALIDATION ====="

python3 - <<'PY'
from pathlib import Path

paths = {
    "organizer":
        "/home/piet/sih-workbench/organizer/models/organizer-final",
    "general":
        "/home/piet/sih-workbench/models/qwen2.5-3b/qwen2.5-3b-instruct-q4_k_m.gguf",
    "coding":
        "/home/piet/sih-workbench/models/starcoder2-3b/starcoder2-3b-instruct.Q4_K_M.gguf",
    "vision":
        "/home/piet/sih-workbench/models/Qwen2.5-VL-3B-Instruct-GGUF/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf",
    "vision_mmproj":
        "/home/piet/sih-workbench/models/Qwen2.5-VL-3B-Instruct-GGUF/mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf",
}

for name, path in paths.items():
    p = Path(path)
    print(f"{name:20s} {'OK' if p.exists() else 'MISSING'} :: {path}")
PY

# ============================================================
# 12. LOCAL MODEL HEALTH
# ============================================================

echo
echo "===== MODEL MANAGER HEALTH ====="

python3 - <<'PY'
from model_manager.manager import ModelManager

mm = ModelManager()

for worker in [
    "organizer",
    "general",
    "coding",
    "vision",
    "document",
]:
    try:
        print(worker, "STATE =", mm.get_model_state(worker))
    except Exception as e:
        print(worker, "ERROR =", e)

try:
    print("\nSYSTEM:")
    print(mm.get_system_status())
except Exception as e:
    print("SYSTEM ERROR:", e)
PY

# ============================================================
# 13. REAL MODEL SMOKE TESTS
# ============================================================

echo
echo "===== ORGANIZER ====="

python3 - <<'PY'
from model_manager.manager import ModelManager

mm = ModelManager()

r = mm.run_worker(
    "organizer",
    """
Create a JSON workflow plan for:
Audit a refinery heat exchanger inspection report.

Allowed workers:
general
coding
vision
document

Never use arbitrary shell commands.
Never bypass policy.
""",
    max_tokens=300,
)

print("STATUS:", r.status)
print("TOKENS:", r.tokens_generated)
print("LATENCY:", r.latency_ms)
print(r.content)
PY

echo
echo "===== GENERAL ====="

python3 - <<'PY'
from model_manager.manager import ModelManager

mm = ModelManager()

r = mm.run_worker(
    "general",
    "Explain three ways local RAG improves refinery inspection workflows.",
    max_tokens=150,
)

print("STATUS:", r.status)
print("TOKENS:", r.tokens_generated)
print("LATENCY:", r.latency_ms)
print(r.content)
PY

echo
echo "===== CODING ====="

python3 - <<'PY'
from model_manager.manager import ModelManager

mm = ModelManager()

r = mm.run_worker(
    "coding",
    "Write Python code to calculate remaining life from thickness and corrosion rate.",
    max_tokens=180,
)

print("STATUS:", r.status)
print("TOKENS:", r.tokens_generated)
print("LATENCY:", r.latency_ms)
print(r.content)
PY

echo
echo "===== VISION ====="

if [ -f /home/piet/vision-media/test.png ]; then
python3 - <<'PY'
from model_manager.manager import ModelManager

mm = ModelManager()

r = mm.run_worker(
    "vision",
    "Identify the main object, visible text, and any engineering-relevant features.",
    image_path="/home/piet/vision-media/test.png",
    max_tokens=150,
)

print("STATUS:", r.status)
print("TOKENS:", r.tokens_generated)
print("LATENCY:", r.latency_ms)
print("ERROR:", r.error_message)
print(r.content)
PY
fi

# ============================================================
# 14. WORKFLOW E2E
# ============================================================

echo
echo "===== LIVE E-1102 WORKFLOW ====="

python3 - <<'PY'
from backend.app.workflows.workflow_engine import WORKFLOW_ENGINE

task = (
    "Audit scanned ultrasonic thickness inspection report for "
    "crude preheat heat exchanger E-1102 and generate official "
    "approval note."
)

state = WORKFLOW_ENGINE.execute_workflow(
    task_description=task,
    user_id="usr_eng202",
    role="GRADE_2",
    session_id="phase2_e1102",
)

print("STATUS:", state.status)
print("COMPLETED:", state.completed_steps)
print("FAILED:", state.failed_steps)
print("ARTIFACTS:", state.generated_artifacts)
print("VERIFICATION:", state.verification_summary)
print("FINAL:", state.final_response)
print("ERROR:", getattr(state, "error_message", None))

if state.generated_artifacts:
    print("\nARTIFACT DETAILS:")
    for x in state.generated_artifacts:
        print(x)
PY

# ============================================================
# 15. ARTIFACT VERIFICATION
# ============================================================

echo
echo "===== ARTIFACT VERIFICATION ====="

find data/artifacts \
    -maxdepth 1 \
    -type f \
    -printf "%TY-%Tm-%Td %TH:%TM:%TS %s bytes %p\n" \
    2>/dev/null \
    | sort | tail -100

python3 - <<'PY'
from pathlib import Path

for p in Path("data/artifacts").glob("*"):
    if p.is_file():
        print(p.name, p.stat().st_size, "bytes")
PY

# ============================================================
# 16. OFFICE LIBRARY STRUCTURAL CHECK
# ============================================================

echo
echo "===== OFFICE LIBRARIES ====="

python3 - <<'PY'
from pathlib import Path

checks = [
    ("docx", "python-docx"),
    ("xlsx", "openpyxl"),
    ("pptx", "python-pptx"),
]

for module, label in checks:
    try:
        __import__(module)
        print("[OK]", label)
    except Exception as e:
        print("[FAIL]", label, e)

for p in Path("data/artifacts").glob("*.docx"):
    try:
        import docx
        d = docx.Document(p)
        text = "\n".join(x.text for x in d.paragraphs)
        print("[DOCX]", p.name, "paragraphs=", len(d.paragraphs))
        print("  MRPL:", "MRPL" in text)
        print("  Inspection:", "Inspection" in text)
        print("  Approval:", "Approval" in text)
    except Exception as e:
        print("[DOCX FAIL]", p, e)
PY

# ============================================================
# 17. AUTH / RBAC / POLICY TESTS
# ============================================================

echo
echo "===== SECURITY TESTS ====="

python3 -m unittest \
    tests.test_auth \
    tests.test_rbac_policy \
    tests.test_prompt_injection \
    tests.test_rag_security \
    tests.test_tool_gateway \
    tests.test_human_approval \
    -v

SECURITY_RC=$?

# ============================================================
# 18. MODEL MANAGER TESTS
# ============================================================

echo
echo "===== MODEL MANAGER TESTS ====="

python3 -m unittest \
    tests.test_model_manager \
    -v

MM_RC=$?

# ============================================================
# 19. VERIFICATION TESTS
# ============================================================

echo
echo "===== VERIFICATION TESTS ====="

python3 -m unittest \
    tests.test_verification_engine \
    -v

VERIF_RC=$?

# ============================================================
# 20. E2E TESTS
# ============================================================

echo
echo "===== E2E TESTS ====="

python3 -m unittest \
    tests.test_e2e_workflows \
    -v

E2E_RC=$?

# ============================================================
# 21. FULL REGRESSION
# ============================================================

echo
echo "============================================================"
echo "FULL 55+ TEST REGRESSION"
echo "============================================================"

python3 run_tests.py
FULL_RC=$?

# ============================================================
# 22. COMPILE
# ============================================================

echo
echo "===== COMPILE ====="

python3 -m compileall -q \
    backend \
    model_manager \
    rag \
    tools \
    desktop_gui \
    tests

COMPILE_RC=$?

# ============================================================
# 23. NETWORK / EGRESS REVIEW
# ============================================================

echo
echo "===== NETWORK / EGRESS REVIEW ====="

grep -RniE \
"requests\.|urllib\.request|httpx|aiohttp|socket\.|subprocess.*curl|wget|https://|http://" \
backend model_manager rag tools desktop_gui 2>/dev/null \
| grep -v "__pycache__" \
| head -400 || true

echo
echo "Local model ports:"
ss -ltnp 2>/dev/null \
    | grep -E ":(8091|8092|8093|8094)\b" \
    || true

# ============================================================
# 24. PROCESS LEAK CHECK
# ============================================================

echo
echo "===== LLAMA PROCESS CHECK ====="

pgrep -af llama-server || true

# ============================================================
# 25. GUI PYTHON COMPILE
# ============================================================

echo
echo "===== GUI COMPILE ====="

python3 -m py_compile \
    desktop_gui/main.py \
    desktop_gui/styles.py

GUI_COMPILE_RC=$?

# ============================================================
# 26. GUI HEADLESS IMPORT TEST
# ============================================================

echo
echo "===== GUI IMPORT TEST ====="

python3 - <<'PY'
try:
    import desktop_gui.main
    print("[OK] desktop_gui.main imports")
except Exception as e:
    print("[FAIL]", repr(e))
PY

# ============================================================
# 27. DOCUMENTATION CHECK
# ============================================================

echo
echo "===== DOCUMENTATION ====="

grep -nEi \
"sovereign|local|Organizer|Model Manager|RBAC|policy|audit|RAG|Vision|Coding|GUI|installation|testing" \
README.md 2>/dev/null \
| head -200

# ============================================================
# 28. REMOVE STALE AI STUDIO / GEMINI REFERENCES
# ============================================================

echo
echo "===== STALE CLOUD REFERENCES ====="

grep -RniE \
"AI Studio|ai\.studio|GEMINI_API_KEY|Gemini|google.*AI|generativelanguage" \
--exclude-dir=.git \
--exclude-dir=node_modules \
--exclude-dir=.venv \
--exclude-dir=__pycache__ \
. 2>/dev/null \
| head -300 || true

# ============================================================
# 29. GITIGNORE HARDENING
# ============================================================

cat >> .gitignore <<'EOF'

# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Runtime state
data/*.db
data/*.sqlite
data/*.sqlite3
data/artifacts/
data/rag_index/

# Logs
*.log

# Local model binaries
models/
*.gguf
*.safetensors
*.pt
*.pth

# Temporary engineering backups
.phase2_backup/

# Phase logs
PHASE2_FINISH.log
EOF

# ============================================================
# 30. CLEAN GENERATED CACHES
# ============================================================

echo
echo "===== CACHE CLEANUP ====="

find . \
    -type d \
    -name "__pycache__" \
    -prune \
    -exec rm -rf {} + \
    2>/dev/null || true

find . \
    -type f \
    -name "*.pyc" \
    -delete \
    2>/dev/null || true

# ============================================================
# 31. GIT TRACKING CLEANUP
# ============================================================

echo
echo "===== GIT TRACKING CLEANUP ====="

git rm -r --cached --ignore-unmatch \
    .venv \
    __pycache__ \
    backend/**/__pycache__ \
    model_manager/**/__pycache__ \
    rag/**/__pycache__ \
    tools/**/__pycache__ \
    desktop_gui/__pycache__ \
    tests/__pycache__ \
    data/workbench.db \
    data/artifacts \
    2>/dev/null || true

# ============================================================
# 32. FINAL REGRESSION AFTER CLEANUP
# ============================================================

echo
echo "===== FINAL REGRESSION ====="

python3 run_tests.py
FINAL_RC=$?

# ============================================================
# 33. FINAL SOURCE STATUS
# ============================================================

echo
echo "============================================================"
echo "FINAL SOURCE STATUS"
echo "============================================================"

git status --short

echo
echo "============================================================"
echo "FINAL DIFF STAT"
echo "============================================================"

git diff --stat

# ============================================================
# 34. REPORT
# ============================================================

cat > PHASE2_REPORT.md <<EOF
# Phase 2 Workbench Report

Generated:
$(date)

## Results

Baseline:
$BASE_RC

Security:
$SECURITY_RC

Model Manager:
$MM_RC

Verification:
$VERIF_RC

E2E:
$E2E_RC

Compile:
$COMPILE_RC

GUI compile:
$GUI_COMPILE_RC

Final regression:
$FINAL_RC

## Model Integration

Organizer:
local Transformers / safetensors

General:
Qwen2.5-3B GGUF

Coding:
StarCoder2-3B GGUF

Vision:
Qwen2.5-VL-3B GGUF + mmproj

## Primary Architecture

Authentication
→ RBAC
→ Organizer
→ Workflow Engine
→ Policy
→ Tool Gateway
→ Specialist Workers
→ Verification
→ Human Approval where required
→ Audit
→ Artifacts
→ Final Response

## Git Status

\`\`\`
$(git status --short)
\`\`\`

## Diff

\`\`\`
$(git diff --stat)
\`\`\`
EOF

echo
echo "============================================================"
echo "PHASE 2 FINISHED"
echo "============================================================"
echo "Baseline RC : $BASE_RC"
echo "Security RC : $SECURITY_RC"
echo "Model RC    : $MM_RC"
echo "Verify RC   : $VERIF_RC"
echo "E2E RC      : $E2E_RC"
echo "Compile RC  : $COMPILE_RC"
echo "GUI RC      : $GUI_COMPILE_RC"
echo "Final RC    : $FINAL_RC"
echo
echo "Report:"
echo "$ROOT/PHASE2_REPORT.md"
echo
echo "Log:"
echo "$LOG"
echo "============================================================"
