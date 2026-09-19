#!/usr/bin/env bash
# ==============================================================================
# Sovereign Industrial AI Workbench - DGX Spark / Linux Startup Script
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo "   Sovereign Industrial AI Workbench (Air-Gapped / DGX Edition)      "
echo "   Mangalore Refinery and Petrochemicals Limited (MRPL)              "
echo "======================================================================"

# 1. Check Python Environment
if [ -d ".venv" ]; then
    echo "[*] Activating local virtual environment (.venv)..."
    source .venv/bin/activate
elif command -v python3 &>/dev/null; then
    echo "[*] Using system Python 3: $(python3 --version)"
else
    echo "[-] Error: Python 3 not found. Please install Python 3.10+."
    exit 1
fi

# 2. Check GPU & CUDA
if command -v nvidia-smi &>/dev/null; then
    echo "[*] NVIDIA GPU Detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
    echo "[!] Notice: No NVIDIA GPU detected. Running in CPU / Emulated Mode."
fi

# 3. Initialize Demo Database if not present
if [ ! -f "data/demo_db/industrial_demo.db" ]; then
    echo "[*] Generating Enriched Industrial Demo Database..."
    python3 desktop_gui/create_demo_db.py
fi

# 4. Kill any orphan process listening on port 8088 or 3000
echo "[*] Clearing listening ports (8088, 3000)..."
fuser -k 8088/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

# 5. Start Backend API Daemon
echo "[*] Starting Sovereign FastAPI Backend on http://0.0.0.0:8088..."
python3 backend/api_server.py &
BACKEND_PID=$!

# Wait for backend to report healthy
echo "[*] Waiting for backend initialization..."
for i in {1..15}; do
    if curl -s http://127.0.0.1:8088/docs >/dev/null 2>&1; then
        echo "[+] Backend API is online and responding (PID: $BACKEND_PID)!"
        break
    fi
    sleep 1
done

# 6. Start Web / Electron Frontend
if [ -f "dist/index.html" ]; then
    echo "[*] Starting production frontend preview on port 3000..."
    npx vite preview --port 3000 --host 0.0.0.0 &
    FRONTEND_PID=$!
else
    echo "[*] Starting Vite development server on port 3000..."
    npm run dev -- --port 3000 --host 0.0.0.0 &
    FRONTEND_PID=$!
fi

echo "======================================================================"
echo "  Sovereign Industrial AI Workbench is LIVE!                          "
echo "  - Web Dashboard:    http://localhost:3000                           "
echo "  - Backend API:      http://localhost:8088                           "
echo "  - API Swagger Docs: http://localhost:8088/docs                      "
echo "======================================================================"

# Trap termination signals
trap "echo '[*] Shutting down Sovereign Workbench...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM

wait
