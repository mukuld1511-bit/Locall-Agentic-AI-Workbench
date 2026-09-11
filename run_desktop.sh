#!/usr/bin/env bash
# Launcher for Sovereign Industrial AI Workbench (SIH26117)
# Runs the local desktop GUI application on the local workstation.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "Starting Sovereign Industrial AI Workbench (MRPL SIH26117)"
echo "Mode: Local Sovereign Runtime | Zero Cloud Egress"
echo "================================================================================"

# Initialize schema and seed data if database does not exist
if [ ! -f "data/workbench.db" ]; then
    echo "[*] Initializing local database..."
    python3 scripts/seed_data.py
fi

# Launch Desktop GUI
python3 desktop_gui/main.py "$@"
