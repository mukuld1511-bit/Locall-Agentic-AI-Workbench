# Sovereign Industrial Agentic AI Workbench
> **SIH26117** · Air-Gapped Sovereign Industrial Agentic Intelligence System for Critical Infrastructure & SCADA Operations

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Electron 28](https://img.shields.io/badge/Electron-28-47848F.svg)](https://www.electronjs.org/)
[![Three.js WebGL](https://img.shields.io/badge/Three.js-WebGL_3D-black.svg)](https://threejs.org/)
[![Air-Gapped Certified](https://img.shields.io/badge/Network-100%25_Air--Gapped-green.svg)](#)
[![Deterministic Safety](https://img.shields.io/badge/Safety-AST_Fail--Closed-red.svg)](#)

---

## Overview

The **Sovereign Industrial Agentic AI Workbench** is an on-premise, zero-cloud artificial intelligence operating system engineered specifically for petroleum refineries, chemical processing units, and mission-critical SCADA environments. 

Operating under strict national air-gap regulations (ISA/IEC 62443, NIST SP 800-82), the system eliminates external telemetry beacons and cloud API dependencies. It runs an intelligent **Tri-Model Multi-Agent Architecture** within an accessible **6.84 GB VRAM budget** on standard commercial workstation GPUs (such as an NVIDIA RTX 3060), combining real-time spectral signal processing, computer vision blueprint OCR, deterministic Abstract Syntax Tree (AST) safety gating, and hardware-accelerated 3D WebGL digital twins.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│  OPERATOR CONSOLE & AIR-GAPPED SCADA TELEMETRY BUS                     │
│  Live Sensor Feeds (100ms)  ·  Natural Language Inquiries  ·  P&ID Scans│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: 500M ORGANIZING INTENT ROUTER (Sub-35ms Dispatch)            │
│  Intent Classification  ·  Dynamic VRAM Model Swapper  ·  Context Prep │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
        (Telemetry / Code Queries)         (P&ID / Inspection Scans)
                    ▼                                ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│  STAGE 2A: REASONING ENGINE     │  │  STAGE 2B: VISION INSPECTOR     │
│  3B Code & Math LLM             │  │  3B Qwen2.5-VL Multimodal       │
│  SQL Generation · FFT Spectrum  │  │  P&ID Valve Tag OCR             │
│  Sandboxed Python Diagnostics   │  │  Corrosion & Hotspot Detection  │
└───────────────────┬─────────────┘  └───────────────┬─────────────────┘
                    │                                │
                    └───────────────┬────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: DETERMINISTIC AST SAFETY CAGE & 4-TIER RBAC                  │
│  Abstract Syntax Tree Whitelist  ·  Fail-Closed Physical Interlocks    │
│  Role Clearance: Grade 1 (Read) ➔ Grade 2 ➔ Grade 3 ➔ Admin (Override) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: PLANT DIGITAL TWIN & FORENSIC AUDIT LEDGER                   │
│  Three.js WebGL 3D Visualization (60 FPS)  ·  SHA-256 Chained Hash Log │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Key Capabilities

1. **Tri-Model Neural Orchestration**:
   - **500M Router**: Sub-35ms intent classification dispatching tasks without lag.
   - **3B Reasoning & Math LLM**: Sandboxed SQL/Python generation and ISO 10816-3 mechanical diagnostics.
   - **3B Qwen2.5-VL Multimodal Vision**: P&ID engineering blueprint OCR (extracting tags like `XV-3012`, `PCV-4401`) and thermal corrosion inspection.
2. **Fast Fourier Transform (FFT) Spectral Analytics**:
   - Real-time 8,192-point FFT signal decomposition computed in 3.8ms across 4 critical machines (*Heavy Crude Pump 301A, Wet Gas Compressor 102, Furnace Blower 401, Turbo Expander 205*).
   - Identifies 1X unbalance, 2X misalignment harmonics, and high-frequency BPFO/BPFI bearing defect frequencies.
3. **Deterministic AST Safety Interlock**:
   - Every AI-suggested command passes through an Abstract Syntax Tree (AST) lexical parser that strips dangerous keywords (`DROP`, `rm`, unverified emergency trips).
   - 100% fail-closed default-deny policy interlock.
4. **4-Tier Role-Based Access Control (RBAC)**:
   - **Grade 1 (Operator)**: Read telemetry, view alarms, query documentation.
   - **Grade 2 (Maintenance Engineer)**: Tune auxiliary loops (cooling, lube), execute sandboxed diagnostics.
   - **Grade 3 (Superintendent)**: Authorize high-risk overrides, bypasses, and emergency shutdowns.
   - **Admin (System Administrator)**: Configure safety policy rules and inspect audit chains.
5. **Interactive 3D WebGL Digital Twin**:
   - Parametric CAD models rendered at 60 FPS in Three.js with real-time rotational speed, temperature heat gradient shaders, and simulated combustion blower flame intensity.
6. **Cryptographic SHA-256 Audit Ledger**:
   - Append-only, tamper-evident Merkle-style event ledger recording every query, telemetry anomaly, operator approval, and trip signal.

---

## Hardware & System Requirements

| Specification | Minimum Requirement | Recommended Production Target |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 (64-bit) or Ubuntu Linux 22.04+ | Windows 11 Pro Enterprise or DGX Linux |
| **GPU** | NVIDIA GPU with 8 GB VRAM (RTX 3060 / 4060) | NVIDIA RTX 4090 (24 GB) or NVIDIA DGX |
| **System RAM** | 16 GB DDR4/DDR5 | 32 GB DDR5 |
| **Processor** | Intel Core i5 / AMD Ryzen 5 (6+ cores) | Intel Core i7 / i9 or AMD Ryzen 7 / 9 |
| **Disk Space** | 10 GB free storage (SSD recommended) | 50 GB NVMe PCIe 4.0 |
| **Network** | **Zero Internet Required** (100% Air-Gapped) | Air-gapped isolated SCADA subnet |

---

## Step-by-Step Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/mukuld1511-bit/Locall-Agentic-AI-Workbench.git
cd Locall-Agentic-AI-Workbench
```

### 2. Environment Configuration
Copy the example environment configuration:
```bash
copy .env.example .env
```
*(On Linux/macOS: `cp .env.example .env`)*

### 3. Backend Setup (Python Virtual Environment)
Create and activate an isolated Python 3.10+ virtual environment:

**Windows (PowerShell / Command Prompt):**
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / DGX Station:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Frontend & Electron Desktop Setup (Node.js)
Ensure **Node.js (v18+)** and **npm** are installed:
```bash
npm install
```

### 5. Local Model Weights (Air-Gapped Setup)
Place your quantized GGUF models into the `models/` directory:
- `models/organizer-500m.Q4_K_M.gguf` (Intent Router)
- `models/reasoning-3b.Q4_K_M.gguf` (Math & Code Engine)
- `models/qwen2.5-vl-3b.Q4_K_M.gguf` (Multimodal Vision Engine)

*(Note: The system includes a built-in mock telemetry simulator that allows full functional testing of all UI, 3D WebGL models, AST safety gates, and analytics even before downloading neural weights).*

---

## Launching the Workbench

### Option A: One-Click Desktop Launch (Recommended)
Double-click or execute the automated Windows launch script:
```bash
.\start_electron.bat
```
This script automatically:
1. Spawns the FastAPI asynchronous SCADA backend server on `http://127.0.0.1:8088`.
2. Starts the Vite React 19 development server on `http://localhost:3000`.
3. Opens the native Electron 28 desktop application window.

### Option B: Manual Service Launch

**Terminal 1 — Backend API:**
```bash
.\.venv\Scripts\python.exe backend\api_server.py
```

**Terminal 2 — Frontend Dev Server:**
```bash
npm run dev
```

**Terminal 3 — Electron Shell:**
```bash
npm run electron
```

### Option C: Linux / DGX Spark Native Deployment
```bash
chmod +x start_workbench.sh
./start_workbench.sh
```

---

## Repository Structure

```
Locall-Agentic-AI-Workbench/
├── backend/
│   ├── api_server.py                 # Central FastAPI Server & WebSocket Gateway
│   └── app/
│       ├── policy/                   # AST Lexical Parser & Safety Rule Interlock
│       ├── rbac/                     # 4-Tier Role-Based Access Control Engine
│       ├── telemetry/                # Modbus / OPC-UA Simulated Signal Bus
│       └── diagnostics/              # 8,192-point FFT & ISO 10816-3 Evaluator
├── src/
│   ├── components/
│   │   ├── ThreeMachineCanvas.tsx    # Hardware-Accelerated 3D WebGL Digital Twin
│   │   ├── ScadaTelemetryCards.tsx   # Live Sensor Metric Visualizers
│   │   └── AstSecurityModal.tsx      # Fail-Closed Safety Interlock Dialog
│   ├── App.tsx                       # Main Control Room UI & Viewport Routing
│   └── index.css                     # Industrial Dark-Mode Theme Styles
├── electron/
│   ├── main.cjs                      # Electron Main Desktop Process
│   └── preload.cjs                   # Secure Context Isolation IPC Bridge
├── data/
│   ├── demo_showcase/                # P&ID Blueprint Scans & Inspection Media
│   └── sovereign_ledger.db           # SQLite Immutable SHA-256 Event Chain
├── scripts/
│   ├── generate_project_report.py    # Generates 17-Page Academic Project Report
│   └── generate_synopsis.py          # Generates 8-Page Formal Academic Synopsis
├── Sovereign_Industrial_AI_Workbench_Report_Final.docx  # Academic Project Report
├── Sovereign_Industrial_AI_Workbench_Synopsis.docx      # Academic Synopsis Document
├── start_electron.bat                # One-Click Windows Launch Script
├── start_workbench.sh                # Linux / DGX Spark Shell Script
└── README.md                         # Repository Documentation
```

---

## Academic Documentation & Reports

This repository contains fully formatted, publication-grade academic and technical documentation:

- **[Project Report (DOCX)](./Sovereign_Industrial_AI_Workbench_Report_Final.docx)**: Comprehensive 17-page technical project report featuring:
  - Center-oriented title page with Supervisor & HOD approval columns.
  - Native Word-based flowcharts (Tri-model orchestration, closed-loop methodology, 5-layer stack, safety decision gates).
  - Empirical benchmark charts and detailed mathematical VRAM budget analysis.
  - 6 dedicated visual showcase slots with complete feature captions.
  - References and formal Vote of Thanks to **Dr. Richa Chaudhary** (PIET).
- **[Project Synopsis (DOCX)](./Sovereign_Industrial_AI_Workbench_Synopsis.docx)**: Official 8-page academic synopsis document.
- **Report Generator Code**: Run `python generate_project_report.py` to regenerate the DOCX document anytime.

---

## Author & Academic Acknowledgments

- **Lead Engineer & Author:** Mukul (`Roll No. 28240613`)
- **Department:** Department of Computer Science & Engineering (AI & ML)
- **Institution:** Panipat Institute of Engineering & Technology (PIET)
- **Project Supervisor:** Dr. Richa Chaudhary, Department of CSE (AI & ML)
- **Head of Department:** Prof. (Dr.) Devendra, Department of CSE (AI & ML)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Built for critical industrial automation, research, and functional safety engineering.
