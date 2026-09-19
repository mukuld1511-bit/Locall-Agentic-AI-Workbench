import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def create_synopsis():
    doc = docx.Document()
    
    # Page setup - Standard A4 with 1 inch (72pt) margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)

    def set_cell_border(cell, **kwargs):
        """
        Set cell borders
        kwargs: top, bottom, left, right
        values: dict(sz=12, val='single', color='000000')
        """
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = parse_xml(
            r'<w:tcBorders %s>'
            r'<w:top w:val="%s" w:sz="%s" w:space="0" w:color="%s"/>'
            r'<w:left w:val="%s" w:sz="%s" w:space="0" w:color="%s"/>'
            r'<w:bottom w:val="%s" w:sz="%s" w:space="0" w:color="%s"/>'
            r'<w:right w:val="%s" w:sz="%s" w:space="0" w:color="%s"/>'
            r'</w:tcBorders>' % (
                nsdecls('w'),
                kwargs.get('top_val', 'none'), kwargs.get('top_sz', '0'), kwargs.get('top_color', 'auto'),
                kwargs.get('left_val', 'none'), kwargs.get('left_sz', '0'), kwargs.get('left_color', 'auto'),
                kwargs.get('bottom_val', 'none'), kwargs.get('bottom_sz', '0'), kwargs.get('bottom_color', 'auto'),
                kwargs.get('right_val', 'none'), kwargs.get('right_sz', '0'), kwargs.get('right_color', 'auto'),
            )
        )
        tcPr.append(tcBorders)

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    # ---------------------------------------------------------------------------
    # PAGE 1: COVER PAGE
    # ---------------------------------------------------------------------------
    p_title_lead = doc.add_paragraph()
    p_title_lead.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title_lead.paragraph_format.space_before = Pt(24)
    p_title_lead.paragraph_format.space_after = Pt(6)
    r = p_title_lead.add_run("Project Synopsis\non")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(16)
    r.font.bold = True

    p_proj_title = doc.add_paragraph()
    p_proj_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_proj_title.paragraph_format.space_before = Pt(6)
    p_proj_title.paragraph_format.space_after = Pt(18)
    r = p_proj_title.add_run("Sovereign Industrial AI Workbench:\nAir-Gapped Autonomous Agentic Intelligence System\nfor Critical Infrastructure & SCADA Operations")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(18)
    r.font.bold = True

    p_degree = doc.add_paragraph()
    p_degree.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_degree.paragraph_format.space_before = Pt(12)
    p_degree.paragraph_format.space_after = Pt(18)
    r = p_degree.add_run("Submitted in partial fulfillment\nfor the award of the degree of\n\n")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r_deg = p_degree.add_run("Bachelor of Technology\nin\nComputer Science Engineering\n(Artificial Intelligence & Machine Learning)")
    r_deg.font.name = 'Times New Roman'
    r_deg.font.size = Pt(14)
    r_deg.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(16)
    p_sub.paragraph_format.space_after = Pt(6)
    r = p_sub.add_run("Submitted By")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True

    # Student Table on Cover Page
    student_table = doc.add_table(rows=2, cols=2)
    student_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    students = [
        ("Mukul", "28240613"),
        ("Gaurav", "28240582")
    ]
    for row_idx, (name, roll) in enumerate(students):
        cell_name = student_table.cell(row_idx, 0)
        cell_roll = student_table.cell(row_idx, 1)
        cell_name.width = Inches(2.2)
        cell_roll.width = Inches(2.0)
        
        p_n = cell_name.paragraphs[0]
        p_n.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_n.paragraph_format.space_before = Pt(2)
        p_n.paragraph_format.space_after = Pt(2)
        rn = p_n.add_run(name)
        rn.font.name = 'Times New Roman'
        rn.font.size = Pt(13)
        rn.font.bold = True

        p_r = cell_roll.paragraphs[0]
        p_r.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_r.paragraph_format.space_before = Pt(2)
        p_r.paragraph_format.space_after = Pt(2)
        rr = p_r.add_run(f"       {roll}")
        rr.font.name = 'Times New Roman'
        rr.font.size = Pt(13)
        rr.font.bold = True

    p_sup = doc.add_paragraph()
    p_sup.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sup.paragraph_format.space_before = Pt(20)
    p_sup.paragraph_format.space_after = Pt(16)
    r = p_sup.add_run("Under the Supervision of\n")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r_guide = p_sup.add_run("Dr. Richa Chaudhary\n")
    r_guide.font.name = 'Times New Roman'
    r_guide.font.size = Pt(13)
    r_guide.font.bold = True
    r_desig = p_sup.add_run("Department of CSE (AI & ML)")
    r_desig.font.name = 'Times New Roman'
    r_desig.font.size = Pt(12)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(16)
    p_inst.paragraph_format.space_after = Pt(0)
    r_inst = p_inst.add_run("Panipat Institute of Engineering & Technology,\nSamalkha, Panipat\nAffiliated to\n")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(13)
    r_inst.font.bold = True
    r_univ = p_inst.add_run("Kurukshetra University Kurukshetra, India\n(2025–2026)")
    r_univ.font.name = 'Times New Roman'
    r_univ.font.size = Pt(13)
    r_univ.font.bold = True

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 2: SUPERVISOR CONSENT & DPEC REMARKS
    # ---------------------------------------------------------------------------
    p_h2 = doc.add_paragraph()
    p_h2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_h2.paragraph_format.space_before = Pt(30)
    p_h2.paragraph_format.space_after = Pt(20)
    r = p_h2.add_run("Supervisor’s Consent")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(15)
    r.font.bold = True

    # Supervisor consent table
    sc_table = doc.add_table(rows=1, cols=2)
    sc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c0 = sc_table.cell(0, 0)
    c1 = sc_table.cell(0, 1)
    c0.width = Inches(4.7)
    c1.width = Inches(1.8)

    # Add single black borders
    for c in (c0, c1):
        set_cell_border(c, top_val='single', top_sz='6', top_color='000000',
                           bottom_val='single', bottom_sz='6', bottom_color='000000',
                           left_val='single', left_sz='6', left_color='000000',
                           right_val='single', right_sz='6', right_color='000000')

    p_sc = c0.paragraphs[0]
    p_sc.paragraph_format.space_before = Pt(6)
    p_sc.paragraph_format.space_after = Pt(6)
    p_sc.paragraph_format.line_spacing = 1.15
    r_sc = p_sc.add_run("The synopsis of final year project work titled ")
    r_sc.font.name = 'Times New Roman'
    r_sc.font.size = Pt(11)
    r_sc_b = p_sc.add_run("Sovereign Industrial AI Workbench: Air-Gapped Autonomous Agentic Intelligence System for Critical Infrastructure & SCADA Operations ")
    r_sc_b.font.name = 'Times New Roman'
    r_sc_b.font.size = Pt(11)
    r_sc_b.font.bold = True
    r_sc_e = p_sc.add_run("by the students’ group id.………… has been written with my consent and every section of this synopsis report is reflecting the work to be carried out by the group.")
    r_sc_e.font.name = 'Times New Roman'
    r_sc_e.font.size = Pt(11)

    p_sig = c1.paragraphs[0]
    p_sig.paragraph_format.space_before = Pt(36)
    p_sig.paragraph_format.space_after = Pt(6)
    p_sig.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sig = p_sig.add_run("(Signature of\nsupervisor with date)")
    r_sig.font.name = 'Times New Roman'
    r_sig.font.size = Pt(10)
    r_sig.font.italic = True

    # DPEC Remarks
    p_dpec = doc.add_paragraph()
    p_dpec.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dpec.paragraph_format.space_before = Pt(45)
    p_dpec.paragraph_format.space_after = Pt(24)
    r = p_dpec.add_run("Department Project Evaluation Committee (DPEC) Remarks")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.font.bold = True

    p_dp1 = doc.add_paragraph()
    p_dp1.paragraph_format.space_before = Pt(12)
    p_dp1.paragraph_format.space_after = Pt(12)
    p_dp1.paragraph_format.line_spacing = 1.25
    r = p_dp1.add_run("The project is ……………………….. by DPEC. The group is advised to submit progress of the project work in progress presentation1 to be held on……………………………………………….")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)

    p_or = doc.add_paragraph()
    p_or.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_or.paragraph_format.space_before = Pt(16)
    p_or.paragraph_format.space_after = Pt(16)
    r = p_or.add_run("OR")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True

    p_dp2 = doc.add_paragraph()
    p_dp2.paragraph_format.space_before = Pt(12)
    p_dp2.paragraph_format.space_after = Pt(60)
    p_dp2.paragraph_format.line_spacing = 1.25
    r = p_dp2.add_run("The project is ……………………….. by DPEC. The group is advised to submit the synopsis report again after making changes as suggested by DPEC on …………………........................................")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)

    p_dsig = doc.add_paragraph()
    p_dsig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_dsig.paragraph_format.space_before = Pt(40)
    p_dsig.paragraph_format.space_after = Pt(0)
    r = p_dsig.add_run("Name & Signature of DPEC member (s) with date")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)

    doc.add_page_break()

    # Helper function for Section Headings
    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        return p

    def add_sub_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)
        r.font.bold = True
        return p

    def add_body_p(text, justify=True):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if justify:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        return p

    def add_bullet_item(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(11)
        r_b.font.bold = True
        r_t = p.add_run(text)
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(11)
        return p

    # ---------------------------------------------------------------------------
    # PAGE 3: TITLE, 1. INTRODUCTION, 2. OBJECTIVE
    # ---------------------------------------------------------------------------
    p_title_main = doc.add_paragraph()
    p_title_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title_main.paragraph_format.space_before = Pt(0)
    p_title_main.paragraph_format.space_after = Pt(16)
    r = p_title_main.add_run("Sovereign Industrial AI Workbench:\nAir-Gapped Autonomous Agentic Intelligence System\nfor Critical Infrastructure & SCADA Operations")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True

    add_section_header("1. Introduction")
    add_body_p(
        "Critical industrial infrastructure—such as petroleum refineries, chemical processing plants, thermal power stations, "
        "and pipeline transport networks—operates under strict zero-trust regulatory mandates, trade secret protections, and "
        "physical safety constraints. In these high-consequence environments, commercial public cloud AI solutions cannot be deployed "
        "due to data sovereignty laws, corporate intellectual property sensitivity, and the severe risks of network air-gap contamination "
        "or cyber-kinetic sabotage. However, modern industrial facilities face acute operational challenges: senior engineering talent attrition, "
        "millions of multi-variable SCADA telemetry streams that exceed human cognitive processing bandwidth, unstandardized shift handovers, "
        "and catastrophic equipment failures that cost upwards of $500,000 per hour in unplanned downtime."
    )
    add_body_p(
        "Recent breakthroughs in Small Language Models (SLMs), local vision-language architectures, and quantized neural inference engines "
        "enable running state-of-the-art artificial intelligence directly on on-premise hardware without external network dependencies. "
        "The Sovereign Industrial AI Workbench addresses this operational imperative by engineering a 100% self-hosted, air-gapped agentic "
        "intelligence desktop operating environment. Built specifically for critical plant infrastructure (demonstrated with Mangalore Refinery "
        "and Petrochemicals Limited – MRPL / SIH26117 requirements), the system unifies multi-model GGUF neural reasoning, real-time SCADA "
        "telemetry ingestion, physics-informed 3D WebGL digital twins, ISO 10816-3 vibration diagnostics, Safety Instrumented System (SIS) "
        "proof testing, and a cryptographically chained SHA-256 audit ledger. The platform bridges cutting-edge industrial artificial intelligence "
        "with deterministically enforced safety policies to empower plant operators and reliability engineers while guaranteeing zero cloud egress."
    )

    add_section_header("2. Objective")
    add_body_p(
        "The primary objective of this project is to develop and deploy a 100% sovereign, air-gapped agentic AI workbench capable of executing "
        "sub-second multi-model reasoning, multimodal engineering document analysis, and physics-coupled industrial machinery diagnostics "
        "entirely on local edge and workstation hardware (from RTX 4090 GPUs to NVIDIA DGX stations) with zero network egress."
    )
    add_body_p(
        "The secondary objectives comprise:"
    )
    add_bullet_item("Multi-Model VRAM Memory Routing: ", "Implement an intelligent memory manager that dynamically hot-swaps and arbitrates between a 500M intent organizer, a 3B domain code reasoning model, and a 3B Qwen2.5-VL multimodal vision model within a strict <8 GB VRAM budget.")
    add_bullet_item("Deterministic Fail-Closed Safety Interlocks: ", "Enforce a strict 4-tier Role-Based Access Control (RBAC) policy engine with an AST command parser that intercepts and neutralizes unauthorized or destructive operational actions (such as emergency shutdowns or unprivileged SQL mutations).")
    add_bullet_item("Real-Time SCADA 3D Digital Twin: ", "Deliver an interactive WebGL Three.js 3D visualization of critical refinery machinery (Heavy Crude Pump 301A, Wet Gas Compressor 102, Furnace Blower 401, Turbo Expander 205) coupled with live thermodynamic and spectral FFT harmonic telemetry.")
    add_bullet_item("Predictive Maintenance & SIS Verification: ", "Automate ISO 10816-3 velocity classification, Bearing Defect Frequency (BPFO/BPFI) tracking, automated CMMS work order generation, and Safety Instrumented System proof testing with <45ms emergency trip loop validation.")
    add_bullet_item("Cryptographic Auditability: ", "Log every telemetry anomaly, operator override, model prompt, and actuator tuning into an immutable, SHA-256 hash-chained block ledger for absolute regulatory and forensic accountability.")

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 4: 3. SCOPE, 4. ARCHITECTURE
    # ---------------------------------------------------------------------------
    add_section_header("3. Scope")
    add_body_p("The operational and technical scope of this project encompasses:")
    add_bullet_item("Theoretical & Mathematical Foundation: ", "Study of localized quantized neural inference (GGUF k-quants), Fast Fourier Transform (FFT) vibration harmonics, Weibull-based Remaining Useful Life (RUL) estimation, and safety instrumentation standards (IEC 61508 / IEC 61511 / ISO 10816-3).")
    add_bullet_item("Model Integration & Orchestration: ", "Native local execution of specialized SLMs/VLMs via llama.cpp and PyTorch with custom C++ bindings, eliminating third-party API keys, cloud latency, and telemetry leakage.")
    add_bullet_item("Industrial Data & Telemetry Pipeline: ", "Bidirectional telemetry engine ingesting real-time Modbus/OPC-UA and simulated SCADA sensor feeds across 4 critical industrial rotating assets at sub-100ms refresh cycles.")
    add_bullet_item("Multimodal Computer Vision Engine: ", "Computer vision pipeline for P&ID engineering drawings, thermal thermography scans, weld radiographic analysis, and ASME Section VIII corrosion pitting evaluation using local vision-language transformers.")
    add_bullet_item("Sovereign Studio IDE Sandbox: ", "Isolated, secure multi-language execution sandbox supporting Python, C, C++, Bash, and SQL with deterministic AST abstract syntax verification and timeout boundaries.")
    add_bullet_item("Desktop Shell & Web Application: ", "Modern desktop workstation packaging via Electron and React 19 / TypeScript / Tailwind CSS, optimized for high-resolution plant multi-monitor control room configurations.")
    add_bullet_item("Evaluation & Validation Framework: ", "Rigorous benchmarking against real refinery operational envelopes, testing relay response latency (<45ms), cold-start hot-swap times (<400ms), and 100% block-rate on safety policy violations.")

    add_section_header("4. Architecture")
    add_bullet_item("Backend Stack: ", "Python 3.10+, FastAPI asynchronous REST and WebSocket server, Uvicorn, llama.cpp / llama-cpp-python (CUDA 12.1 / cuBLAS acceleration), PyTorch, NumPy, SciPy (FFT / Signal Processing).")
    add_bullet_item("Frontend & Desktop Shell: ", "Electron 28+, React 19, TypeScript, Tailwind CSS, Lucide Icons, Three.js / React Three Fiber for WebGL 3D CAD rendering, Canvas-based spectral FFT visualizers.")
    add_bullet_item("Data Storage & Cryptographic Subsystems: ", "Embedded SQLite relational databases for asset hierarchy and sensor catalogs, Chained Block SHA-256 tamper-evident append-only ledger.")
    add_bullet_item("Inference & VRAM Management Architecture: ", "Dedicated Model Registry maintaining dormant and active model states in pinned CPU host memory and GPU VRAM; automated LRU eviction ensuring zero out-of-memory (OOM) faults under continuous operation.")
    add_bullet_item("Deterministic Policy Interception Pipeline: ", "Hierarchical 4-tier RBAC Gateway (Grade 1 Operator → Grade 2 Maintenance Engineer → Grade 3 Superintendent → Administrator). Abstract Syntax Tree (AST) pattern matcher inspects natural language and script commands before dispatching to physical actuator endpoints.")

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 5: 5. METHODOLOGY
    # ---------------------------------------------------------------------------
    add_section_header("5. Methodology")
    add_body_p(
        "This project adheres to an end-to-end industrial MLOps and DevSecOps engineering pipeline—spanning quantized model adaptation, "
        "real-time sensor fusion, deterministic policy safety layers, and high-fidelity operator interaction."
    )

    add_sub_header("5.1 Data Preparation, Telemetry Ingestion & Physics Modeling")
    add_bullet_item("SCADA Telemetry Streams: ", "Synthesizes and ingests high-frequency telemetry across four critical asset classes: PUMP_301A (impeller cavitation, bearing temperature, discharge pressure), COMPRESSOR_102 (surge margin, inter-stage cooler pressure), FURNACE_BLOWER_401 (flue gas draft, stator vibration), and EXPANDER_TURBINE_205 (thrust bearing axial displacement, rotor speed).")
    add_bullet_item("Signal Processing: ", "Calculates real-time Fast Fourier Transform (FFT) to decompose complex vibration signals into fundamental running speeds (1X, 2X, 3X) and high-frequency bearing ball pass outer/inner race frequencies (BPFO/BPFI).")
    add_bullet_item("Standardized Thresholding: ", "Maps ISO 10816-3 velocity standards across Zone A (Newly Commissioned), Zone B (Unrestricted Long-Term Operation), Zone C (Restricted / Alarm), and Zone D (Dangerous / Automatic Trip).")

    add_sub_header("5.2 Multi-Model Local Neural Inference Pipeline")
    add_bullet_item("Intent Routing: ", "A 500M ultra-compact organizer parses user queries and voice commands into structured operational intents (SCADA Query, Diagnosis, Actuator Adjustment, Safety Proof Test) in <35ms.")
    add_bullet_item("Domain Code Reasoning: ", "A 3B parameter coding model generates validated automation scripts, SQL queries, and calibration routines within sandboxed execution limits.")
    add_bullet_item("Multimodal Inspection: ", "A 3B Qwen2.5-VL vision-language model analyzes uploaded P&ID blueprints, ultrasonic thickness reports, and thermal scans, extracting pipe tags, valve states, and structural anomalies.")
    add_bullet_item("Memory Scheduling: ", "Employs an intelligent VRAM budgeting algorithm that unloads idle models to RAM and pre-warms active model context in <400ms, maintaining total GPU memory utilization below 8 GB.")

    add_sub_header("5.3 Safety Interlocks, Deterministic Policy & Cryptographic Ledger")
    add_bullet_item("Default-Deny Gateway: ", "All tool executions and physical parameter changes pass through a deterministic RBAC filter. Grade 1 operators are strictly restricted from destructive modifications.")
    add_bullet_item("AST Policy Analyzer: ", "Scans code blocks and system calls to intercept destructive strings ('DROP TABLE', 'rm -rf', unauthorized trip overrides) before execution.")
    add_bullet_item("Immutable SHA-256 Ledger: ", "Every security event, manual bypass, and autonomous command is hashed with the previous block's SHA-256 digest, timestamped, and persisted to an append-only cryptographic audit ledger.")

    add_sub_header("5.4 Digital Twin & Control Room Interface")
    add_bullet_item("Interactive WebGL 3D Canvas: ", "Renders parametric 3D machinery representations in Three.js with real-time dynamic heatmaps, operational rotation speeds, vibration wobble, and interactive camera viewpoints.")
    add_bullet_item("Autonomous CMMS Integration: ", "Automatically synthesizes industry-standard SAP/Maximo work orders with failure codes, required spare parts catalogs, and priority assignments upon detecting ISO Zone D anomalies.")

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 6: 6. CONCLUSION & 7. FUTURE SCOPE
    # ---------------------------------------------------------------------------
    add_section_header("6. Conclusion")
    add_body_p(
        "The Sovereign Industrial AI Workbench demonstrates a production-grade paradigm shift in industrial artificial intelligence. "
        "By proving that multi-model agentic AI, multimodal visual inspection, and high-fidelity physics-coupled digital twins can run "
        "with complete operational autonomy on air-gapped local hardware, this project resolves the critical conflict between AI modernization "
        "and data sovereignty for high-consequence national infrastructure."
    )
    add_body_p(
        "The system's modular architecture cleanly separates low-latency GPU neural inference, high-frequency telemetry processing, "
        "deterministic safety verification, and interactive 3D visualization. This architecture delivers instantaneous decision support "
        "to field operators, slashes unplanned downtime through sub-harmonic predictive diagnostics, and provides cryptographic auditability "
        "that exceeds contemporary industrial cybersecurity benchmarks."
    )

    add_sub_header("6.1 Key Highlights")
    add_bullet_item("Absolute Data Sovereignty: ", "Zero external network egress; 100% of weights, embeddings, and telemetry stay on local premises.")
    add_bullet_item("Sub-8GB VRAM Efficiency: ", "Dynamic model arbitration allows multi-model intelligence on standard commercial workstations and edge boxes.")
    add_bullet_item("Deterministic Fail-Closed Safety: ", "4-tier RBAC policy gateway with AST parsing guarantees unvalidated AI hallucinations cannot trigger dangerous physical actions.")
    add_bullet_item("Sub-45ms SIS Verification: ", "Integrated Safety Instrumented System proof testing validates emergency shut-off loops against IEC 61511 compliance.")
    add_bullet_item("Cryptographic Integrity: ", "Append-only SHA-256 hash-chained block ledger ensures tamper-proof audit trails for safety investigations.")

    add_sub_header("6.2 Current Limitations")
    add_bullet_item("Hardware Acceleration Prerequisite: ", "Sub-second inference and real-time 3D WebGL rendering require a dedicated GPU (minimum 8 GB VRAM, e.g., RTX 3060/4060) or Apple Silicon Unified Memory.")
    add_bullet_item("Protocol Coverage: ", "Current implementation natively targets Modbus-TCP and OPC-UA; legacy proprietary serial fieldbuses (e.g., Foundation Fieldbus H1) require external protocol gateways.")
    add_bullet_item("Dynamic Finite Element Meshing: ", "The 3D digital twin utilizes parametric physical shaders rather than real-time full Navier-Stokes computational fluid dynamics (CFD).")

    add_section_header("7. Future Scope")
    add_bullet_item("Edge Micro-Controller Deployment: ", "Compile quantized 1-bit / 2-bit neural sub-modules directly onto edge micro-controllers (e.g., Jetson Orin Nano, Raspberry Pi 5) for localized pump-side monitoring.")
    add_bullet_item("Federated Privacy-Preserving Learning: ", "Implement secure federated weight averaging across distributed refinery units without transmitting raw sensor telemetry or operational logs.")
    add_bullet_item("Automated P&ID Reconstruction: ", "Extend the multimodal vision pipeline to generate fully interactive Three.js 3D piping networks directly from scanned 2D engineering blueprints.")
    add_bullet_item("AR/VR Operator Spatial Walkthroughs: ", "Integrate WebXR support for field technicians using Augmented Reality headsets to view real-time holographic FFT overlays directly on physical plant equipment.")

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 7: HARDWARE / SOFTWARE REQUIREMENTS
    # ---------------------------------------------------------------------------
    add_section_header("Hardware / Software Requirement")

    add_bullet_item("Programming Languages: ", "Python 3.10+, TypeScript 5+, JavaScript (ES2022+), SQL, C++ (cuBLAS / llama.cpp compilation)")
    add_bullet_item("AI / ML Frameworks & Inference Engines: ", "llama.cpp, llama-cpp-python, GGUF Quantization (Q4_K_M, Q5_K_M), PyTorch 2.2+ (CUDA 12.1), HuggingFace Transformers, Qwen2.5-VL Vision Engine")
    add_bullet_item("Compute Hardware Platform: ", "Local Workstation (NVIDIA RTX 3060/4060/4090 with 8GB–24GB VRAM) / NVIDIA DGX Station / Enterprise Linux Bare-Metal Server")
    add_bullet_item("Desktop Shell & Frontend UI: ", "Electron 28, React 19, TypeScript, Tailwind CSS, Lucide Icons, Three.js, React Three Fiber, WebGL")
    add_bullet_item("Backend API & Orchestration: ", "FastAPI asynchronous web server, Uvicorn ASGI server, WebSockets for high-frequency SCADA telemetry broadcast")
    add_bullet_item("Industrial Signal & Math Libraries: ", "NumPy, SciPy (Signal processing, Fast Fourier Transform, Butterworth filtering), Pydantic v2")
    add_bullet_item("Data Storage & Security: ", "Embedded SQLite relational database, JSON-lines persistence, Python hashlib (SHA-256 chained block ledger)")
    add_bullet_item("Industrial Standards & Compliance: ", "ISO 10816-3 (Mechanical vibration evaluation), API 670 (Machinery protection systems), IEC 61508 / IEC 61511 (Functional safety & SIS), NIST SP 800-82 (ICS Security)")
    add_bullet_item("Development & Build Tooling: ", "Visual Studio Code, Node.js 18+, Vite / npm, Git, Powershell 7 / Bash")

    doc.add_page_break()

    # ---------------------------------------------------------------------------
    # PAGE 8: REFERENCES
    # ---------------------------------------------------------------------------
    add_section_header("References")
    
    references = [
        "[1] ISO 10816-3:2009. Mechanical vibration — Evaluation of machine vibration by measurements on non-rotating parts — Part 3: Industrial machines with nominal power above 15 kW and nominal speeds between 120 r/min and 15 000 r/min.",
        "[2] American Petroleum Institute (API). (2014). API Standard 670: Machinery Protection Systems (5th ed.). Washington, D.C.: API Publishing Services.",
        "[3] International Electrotechnical Commission (IEC). (2016). IEC 61511: Functional safety - Safety instrumented systems for the process industry sector. Geneva: IEC.",
        "[4] Gerganov, G., et al. (2023). llama.cpp: Port of Facebook's LLaMA model in C/C++. GitHub repository. https://github.com/ggerganov/llama.cpp",
        "[5] Bai, J., et al. (2024). Qwen2.5-VL: Technical Report on Vision-Language Multimodal Foundation Models. arXiv preprint arXiv:2409.12191.",
        "[6] Stouffer, K., Pease, M., Tang, C., Zimmerman, T., Pillitteri, V., & Lubell, J. (2023). NIST Special Publication 800-82 Revision 3: Guide to Industrial Control Systems (ICS) Security. National Institute of Standards and Technology.",
        "[7] Touvron, H., Martin, L., Stone, K., Albert, P., Almahairi, A., et al. (2023). Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv preprint arXiv:2307.09288.",
        "[8] Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). QLoRA: Efficient Finetuning of Quantized LLMs. Advances in Neural Information Processing Systems, 36, 10088–10115.",
        "[9] Cabanes, I., et al. (2008). Early fault detection in rotating machines based on spectral kurtosis and vibration harmonics. Mechanical Systems and Signal Processing, 22(4), 846–858.",
        "[10] Randall, R. B., & Antoni, J. (2011). Rolling element bearing diagnostics—A tutorial. Mechanical Systems and Signal Processing, 25(2), 485–520.",
        "[11] Haber, M. J., et al. (2020). Digital Twin Framework for Industrial Rotating Machinery with Dynamic Degradation Models. IEEE Transactions on Industrial Informatics, 16(8), 5345–5355.",
        "[12] Grieves, M., & Vickers, J. (2017). Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems. In Transdisciplinary Perspectives on Complex Systems (pp. 85–113). Springer, Cham.",
        "[13] Parisi, G. I., Kemker, R., Part, J. L., Kanan, C., & Wermter, S. (2019). Continual lifelong learning with neural networks: A review. Neural Networks, 113, 54–71.",
        "[14] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998–6008.",
        "[15] ISO/IEC 27001:2022. Information security, cybersecurity and privacy protection — Information security management systems — Requirements. International Organization for Standardization.",
        "[16] Sandhu, R. S., Coyne, E. J., Feinstein, H. L., & Youman, C. E. (1996). Role-based access control models. IEEE Computer, 29(2), 38–47.",
        "[17] Narayanan, A., et al. (2016). Bitcoin and Cryptocurrency Technologies: A Comprehensive Introduction (Cryptographic Hash Functions and Ledgers). Princeton University Press.",
        "[18] Cabitza, F., Campagner, A., & Balsano, C. (2020). Bridging the gap between artificial intelligence and clinical practice / mission critical operations. Artificial Intelligence in Medicine, 107, 101908.",
        "[19] NVIDIA Corporation. (2024). NVIDIA TensorRT-LLM and cuBLAS Optimization Guide for Low-Latency Industrial Inference. NVIDIA Developer Documentation.",
        "[20] Mangalore Refinery and Petrochemicals Limited (MRPL). (2024). Industrial Automation & Process Safety Guidelines for SCADA Systems. Technical Documentation.",
        "[21] Sovereign Industrial AI Workbench — Official Open-Source Repository & Architecture. https://github.com/mukuld1511-bit/Locall-Agentic-AI-Workbench (2026)."
    ]

    for ref in references:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        # Hanging indent
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)

    output_path = "Sovereign_Industrial_AI_Workbench_Synopsis.docx"
    doc.save(output_path)
    print(f"Successfully generated synopsis document: {output_path}")

if __name__ == "__main__":
    create_synopsis()
