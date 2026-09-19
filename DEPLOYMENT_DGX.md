# 🚀 Sovereign Industrial AI Workbench — DGX & Linux Native Execution Guide

**Mangalore Refinery and Petrochemicals Limited (MRPL) | SIH26117**  
*Pure Native Bare-Metal / Conda / Virtualenv Setup • Zero Cloud Egress • 100% Local Inference*

---

## 🖥️ 1. Running on NVIDIA DGX Spark / Linux (Native, No Docker)

### Step 1: Extract Archive
```bash
unzip Sovereign-Industrial-AI-Workbench-DGX.zip -d sovereign_workbench
cd sovereign_workbench
```

### Step 2: Set up Python Environment & Node.js
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install PyTorch with CUDA & requirements
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 3. Install Node.js frontend dependencies and build
npm install
npm run build
```

### Step 3: Run One-Click Startup Script
```bash
chmod +x start_workbench.sh
./start_workbench.sh
```

- **Dashboard UI**: `http://localhost:3000` (or `http://<DGX_IP>:3000`)
- **Backend API & Swagger**: `http://localhost:8088/docs`

---

## 🪟 2. Running on Windows PC

1. Extract the zip to any local folder (e.g. `C:\AI\Workbench`).
2. Run `start_electron.bat` (or `./start_workbench.sh` in Git Bash / WSL).

---

## 🔐 3. Preset RBAC Clearance Logins

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `Admin@MRPL2026!` | Root clearance, user creation, policy engine management |
| **Plant Superintendent** | `superintendent_303` | `Super@789!` | Machinery override, emergency shutdown, full SCADA access |
| **Maintenance Engineer** | `engineer_202` | `Engineer@456!` | Diagnostics, vibration analysis, work order management |
| **Plant Operator** | `operator_101` | `Operator@123!` | SCADA monitoring, parameter review, read-only clearance |
