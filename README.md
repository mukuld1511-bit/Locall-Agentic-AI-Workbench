# Sovereign Industrial AI Workbench
> **SIH26117** · Air-Gapped Sovereign Industrial Agentic Intelligence System

A mission-critical desktop workbench engineered for oil refineries, chemical plants, and high-consequence industrial infrastructure. Operates 100% on-premise with zero cloud egress, central Role-Based Access Control (RBAC), deterministic safety policy interception, and real-time SCADA 3D Digital Twins.

---

## Key Pillars & Architecture

- **Sovereign & Air-Gapped**: 100% local model inference (GGUF / Ollama / vLLM) with hard zero-egress network policies.
- **Fail-Closed Policy Engine**: Deterministic RBAC enforcement (Grade 1 Operator to Admin) intercepting unsafe commands (`DROP DATABASE`, unauthorized emergency trips, unprivileged script execution).
- **SCADA 3D Digital Twin**: High-fidelity WebGL Three.js interactive models (`PUMP_301A`, `COMPRESSOR_102`, `FURNACE_BLOWER_401`, `EXPANDER_TURBINE_205`) with physics-coupled thermodynamics and live actuator tuning.
- **ISO 10816-3 & API 670 Diagnostics**: Real-time spectral FFT harmonic decomposition (1X, 2X, 3X, bearing pass) and Remaining Useful Life (RUL) projections.
- **Safety Instrumented System (SIS Proof Testing)**: Certified proof-testing with <45ms relay response validation recorded in an immutable SHA-256 ledger.
- **Autonomous CMMS Work Orders**: Automated generation of SAP/Maximo work orders with spare parts requisitioning.
- **Sovereign Studio IDE**: Integrated Monaco editor with multi-language compiler sandboxes (Python, C, C++, JavaScript, TypeScript, SQL, Bash).
- **Multimodal Vision Inspection**: Local P&ID diagram analysis, weld defect identification, and ASME corrosion evaluation.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Windows 10/11 or Enterprise Linux

### Launching the Workbench
```bash
# Start both Backend & Electron Desktop Shell
.\start_electron.bat
```

Or launch individual services:
```bash
# 1. Start Sovereign Backend API (Port 8088)
.\.venv\Scripts\python.exe backend\api_server.py

# 2. Start Frontend Dev Server (Port 3000)
npm run dev

# 3. Launch Electron Shell
npm run electron
```

---

## Role-Based Access Clearance (RBAC)

| Role Tier | Clearance | Authorized Capabilities |
|---|---|---|
| **GRADE 1** | Plant Operator | Read-only telemetry, SOP search, basic voice queries. Destructive queries blocked. |
| **GRADE 2** | Maintenance Engineer | Parameter tuning, auxiliary actuators (Lube, Coolant, Purge), compiler sandbox execution. |
| **GRADE 3** | Plant Superintendent | High-risk overrides, 205 Turbine E-Stop, Plant-wide ESD approval. |
| **ADMIN** | System Administrator | Employee registry, policy engine configuration, tamper-evident SHA-256 audit ledger inspection. |

---

## Repository Structure

```
├── backend/            # FastAPI Sovereign API Server & Industrial Engines
│   └── app/            # Policy Engine, RBAC, SIS Verification, Workflows
├── src/                # Modern React 19 + TypeScript + TailwindCSS Workbench
│   ├── components/     # ThreeMachineCanvas 3D Viewport & Industrial UI
│   └── App.tsx         # Central SCADA & Sovereign Workbench Workspace
├── electron/           # Electron Desktop Shell & Native IPC Gateways
├── public/             # Architecture, Neural Routing & Workflow Diagrams
└── data/               # Local Demo SQLite DBs & Tamper-Evident Ledgers
```
