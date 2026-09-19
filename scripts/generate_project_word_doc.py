import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def build_project_doc():
    doc = docx.Document()

    # Define exact page margins (0.4 in) for compact, executive 2-page fit
    for section in doc.sections:
        section.top_margin = Inches(0.35)
        section.bottom_margin = Inches(0.35)
        section.left_margin = Inches(0.4)
        section.right_margin = Inches(0.4)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Color Palette Constants (Slate / Deep Navy / Tech Gold / White)
    COLOR_PRIMARY = RGBColor(15, 23, 42)      # #0f172a (Deep Slate / Charcoal)
    COLOR_ACCENT = RGBColor(14, 116, 144)    # #0e7490 (Cyan / Teal)
    COLOR_MUTED = RGBColor(71, 85, 105)      # #475569 (Slate Gray)
    COLOR_DARK = RGBColor(30, 41, 59)        # #1e293b (Body Text)
    HEX_BG_HEAD = "0F172A"                   # Table Header Dark Navy
    HEX_BG_ALT = "F8FAFC"                    # Subtle light gray
    HEX_BG_CARD = "F1F5F9"                   # Card gray
    HEX_BORDER = "CBD5E1"                    # Light border
    HEX_ACCENT_BG = "E0F2FE"                 # Light cyan banner

    def set_cell_bg(cell, hex_code):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_code}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'''
            <w:tcMar {nsdecls("w")}>
                <w:top w:w="{top}" w:type="dxa"/>
                <w:bottom w:w="{bottom}" w:type="dxa"/>
                <w:left w:w="{left}" w:type="dxa"/>
                <w:right w:w="{right}" w:type="dxa"/>
            </w:tcMar>
        ''')
        tcPr.append(tcMar)

    def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
        tblPr = table._tbl.tblPr
        tblBorders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:left w:val="none"/>
                <w:right w:val="none"/>
                <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        tblPr.append(tblBorders)

    # -------------------------------------------------------------
    # PAGE 1: EXECUTIVE BRIEF, ARCHITECTURE & 3D DIGITAL TWIN
    # -------------------------------------------------------------

    # Header Title Banner Table
    header_tbl = doc.add_table(rows=1, cols=2)
    header_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_tbl.autofit = False
    
    col0 = header_tbl.columns[0]
    col1 = header_tbl.columns[1]
    col0.width = Inches(5.6)
    col1.width = Inches(2.1)

    cell_l = header_tbl.cell(0, 0)
    cell_r = header_tbl.cell(0, 1)
    set_cell_bg(cell_l, "0F172A")
    set_cell_bg(cell_r, "0F172A")
    set_cell_margins(cell_l, top=100, bottom=100, left=140, right=100)
    set_cell_margins(cell_r, top=100, bottom=100, left=60, right=140)

    p_title = cell_l.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_t1 = p_title.add_run("SOVEREIGN INDUSTRIAL AI WORKBENCH\n")
    r_t1.bold = True
    r_t1.font.size = Pt(13.5)
    r_t1.font.name = "Arial"
    r_t1.font.color.rgb = RGBColor(248, 250, 252)

    r_t2 = p_title.add_run("Air-Gapped Multi-Model Operating System for Critical Refinery Infrastructure (MRPL SIH26117)")
    r_t2.font.size = Pt(8.5)
    r_t2.font.name = "Arial"
    r_t2.font.color.rgb = RGBColor(148, 163, 184)

    p_meta = cell_r.paragraphs[0]
    p_meta.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_meta.paragraph_format.space_before = Pt(4)
    p_meta.paragraph_format.space_after = Pt(0)
    r_m1 = p_meta.add_run("Author: ")
    r_m1.font.size = Pt(8.5)
    r_m1.font.color.rgb = RGBColor(148, 163, 184)
    r_m1_name = p_meta.add_run("Mukul Dhankhar\n")
    r_m1_name.bold = True
    r_m1_name.font.size = Pt(9.0)
    r_m1_name.font.color.rgb = RGBColor(56, 189, 248)

    r_m2 = p_meta.add_run("Lead AI/ML & System Architect\nStatus: Production / Air-Gapped")
    r_m2.font.size = Pt(8.0)
    r_m2.font.color.rgb = RGBColor(203, 213, 225)

    # Section 1: Executive Overview & Problem Statement
    p_sec1 = doc.add_paragraph()
    p_sec1.paragraph_format.space_before = Pt(6)
    p_sec1.paragraph_format.space_after = Pt(2)
    r_s1 = p_sec1.add_run("1. EXECUTIVE OVERVIEW & PROBLEM STATEMENT")
    r_s1.bold = True
    r_s1.font.size = Pt(9.5)
    r_s1.font.name = "Arial"
    r_s1.font.color.rgb = COLOR_PRIMARY

    p_body1 = doc.add_paragraph()
    p_body1.paragraph_format.space_before = Pt(0)
    p_body1.paragraph_format.space_after = Pt(4)
    p_body1.paragraph_format.line_spacing = 1.1
    r_b1 = p_body1.add_run(
        "Critical industrial infrastructure—such as petroleum refineries, thermal power stations, and petrochemical complexes—"
        "cannot rely on public cloud AI due to stringent zero-trust data sovereignty mandates, IP secrecy, and network air-gapping. "
        "The Sovereign Industrial AI Workbench provides a 100% self-hosted, air-gapped operating intelligence system. "
        "It unifies local SLM/LLM/VLM neural inference, real-time SCADA telemetry ingestion, 3D WebGL physics digital twins, "
        "and a cryptographically chained SHA-256 audit ledger—enforcing deterministic 4-tier RBAC safety interlocks with zero cloud egress."
    )
    r_b1.font.size = Pt(8.5)
    r_b1.font.name = "Arial"
    r_b1.font.color.rgb = COLOR_DARK

    # Section 2: Architecture & High-Resolution System Flowchart
    p_sec2 = doc.add_paragraph()
    p_sec2.paragraph_format.space_before = Pt(4)
    p_sec2.paragraph_format.space_after = Pt(2)
    r_s2 = p_sec2.add_run("2. SYSTEM ARCHITECTURE & NEURAL ORCHESTRATION PIPELINE")
    r_s2.bold = True
    r_s2.font.size = Pt(9.5)
    r_s2.font.name = "Arial"
    r_s2.font.color.rgb = COLOR_PRIMARY

    # Architecture Image Embedding
    arch_img_path = r"C:\Users\Mukul\.gemini\antigravity-ide\brain\262a87e8-1c37-4cd2-b911-19b6154abe88\workbench_architecture_diagram_1789316051347.jpg"
    if os.path.exists(arch_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(0)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.add_run().add_picture(arch_img_path, width=Inches(7.7))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(4)
        r_cap = p_cap.add_run("Figure 1: 4-Tier Sovereign Neural Architecture — Dynamic VRAM Scheduling, RBAC Gateway & Physical Interlocks")
        r_cap.font.size = Pt(7.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = COLOR_MUTED

    # Section 3: Core Technology Stack & Framework Matrix
    p_sec3 = doc.add_paragraph()
    p_sec3.paragraph_format.space_before = Pt(3)
    p_sec3.paragraph_format.space_after = Pt(2)
    r_s3 = p_sec3.add_run("3. INDUSTRIAL TECHNOLOGY STACK & FRAMEWORK SPECIFICATION")
    r_s3.bold = True
    r_s3.font.size = Pt(9.5)
    r_s3.font.name = "Arial"
    r_s3.font.color.rgb = COLOR_PRIMARY

    # Stack Table (5 Columns)
    tbl_stack = doc.add_table(rows=5, cols=4)
    tbl_stack.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_stack.autofit = False
    set_table_borders(tbl_stack)

    stack_widths = [Inches(1.5), Inches(2.2), Inches(2.3), Inches(1.7)]
    for row in tbl_stack.rows:
        for idx, width in enumerate(stack_widths):
            row.cells[idx].width = width

    headers = ["Layer / Subsystem", "Frameworks & Engines", "Key Technical Implementation", "Deployment Target"]
    for i, h in enumerate(headers):
        cell = tbl_stack.cell(0, i)
        set_cell_bg(cell, HEX_BG_HEAD)
        set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(8.0)
        r.font.name = "Arial"
        r.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Neural Engine & VLM", "llama.cpp, GGUF, CUDA 12, PyTorch", "500M Organizer + 3B Code + 3B Qwen2.5-VL Vision", "NVIDIA DGX / RTX VRAM"),
        ("SCADA & Automation Backend", "FastAPI (Python 3.11), Uvicorn, SQLite", "Asynchronous telemetry stream, REST & WebSocket", "Localhost / IPC Unix Socket"),
        ("3D Digital Twin & UI", "Electron, React, Vite, Three.js, Monaco", "60 FPS WebGL simulation (Plasma/Flames/Turbines)", "Cross-Platform Native Desktop"),
        ("Security & Safety Gate", "SHA-256 Ledger, 4-Tier RBAC, AST Parser", "Default-deny policy interlock, tamper-evident log", "Air-Gapped Hardware Security")
    ]

    for row_idx, row_data in enumerate(data, start=1):
        bg_col = HEX_BG_ALT if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            cell = tbl_stack.cell(row_idx, col_idx)
            set_cell_bg(cell, bg_col)
            set_cell_margins(cell, top=40, bottom=40, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.size = Pt(7.8)
            r.font.name = "Arial"
            if col_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_DARK

    # Page Break to enforce strictly 2 pages
    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 2: OPERATIONAL WORKFLOW, LIVE UI SCREENS & RESULTS
    # -------------------------------------------------------------

    # Section 4: Multimodal Workflow & Operational Methodology
    p_sec4 = doc.add_paragraph()
    p_sec4.paragraph_format.space_before = Pt(0)
    p_sec4.paragraph_format.space_after = Pt(2)
    r_s4 = p_sec4.add_run("4. OPERATIONAL METHODOLOGY & MULTIMODAL VERIFICATION WORKFLOW")
    r_s4.bold = True
    r_s4.font.size = Pt(9.5)
    r_s4.font.name = "Arial"
    r_s4.font.color.rgb = COLOR_PRIMARY

    # Methodology Diagram Embedding
    flow_img_path = r"C:\Users\Mukul\.gemini\antigravity-ide\brain\262a87e8-1c37-4cd2-b911-19b6154abe88\workflow_methodology_diagram.jpg"
    if os.path.exists(flow_img_path):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(0)
        p_img2.paragraph_format.space_after = Pt(2)
        p_img2.add_run().add_picture(flow_img_path, width=Inches(7.7))
        
        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_before = Pt(0)
        p_cap2.paragraph_format.space_after = Pt(4)
        r_cap2 = p_cap2.add_run("Figure 2: Closed-Loop Industrial Workflow — Blueprint OCR/Vision, SLM Reasoning, RBAC Validation & SCADA Actuation")
        r_cap2.font.size = Pt(7.5)
        r_cap2.font.italic = True
        r_cap2.font.color.rgb = COLOR_MUTED

    # Section 5: Live Workbench Application User Interface
    p_sec5 = doc.add_paragraph()
    p_sec5.paragraph_format.space_before = Pt(4)
    p_sec5.paragraph_format.space_after = Pt(2)
    r_s5 = p_sec5.add_run("5. PRODUCTION APPLICATION INTERFACE & LIVE OPERATIONS")
    r_s5.bold = True
    r_s5.font.size = Pt(9.5)
    r_s5.font.name = "Arial"
    r_s5.font.color.rgb = COLOR_PRIMARY

    # Dual UI Screenshot Table (Side-by-Side)
    ui_tbl = doc.add_table(rows=2, cols=2)
    ui_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ui_tbl.autofit = False
    
    col_w = Inches(3.8)
    ui_tbl.columns[0].width = col_w
    ui_tbl.columns[1].width = col_w

    ss1_path = r"C:\Users\Mukul\.gemini\antigravity-ide\brain\262a87e8-1c37-4cd2-b911-19b6154abe88\.user_uploaded\media_1789315959748.png"
    ss2_path = r"C:\Users\Mukul\.gemini\antigravity-ide\brain\262a87e8-1c37-4cd2-b911-19b6154abe88\.user_uploaded\media_1789321233671.png"

    # Row 0: Images
    cell_ss1 = ui_tbl.cell(0, 0)
    cell_ss2 = ui_tbl.cell(0, 1)
    set_cell_margins(cell_ss1, top=20, bottom=20, left=30, right=30)
    set_cell_margins(cell_ss2, top=20, bottom=20, left=30, right=30)

    p_s1 = cell_ss1.paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_s1.paragraph_format.space_before = Pt(0)
    p_s1.paragraph_format.space_after = Pt(0)
    if os.path.exists(ss1_path):
        p_s1.add_run().add_picture(ss1_path, width=Inches(3.7))

    p_s2 = cell_ss2.paragraphs[0]
    p_s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_s2.paragraph_format.space_before = Pt(0)
    p_s2.paragraph_format.space_after = Pt(0)
    if os.path.exists(ss2_path):
        p_s2.add_run().add_picture(ss2_path, width=Inches(3.7))

    # Row 1: Captions
    cell_c1 = ui_tbl.cell(1, 0)
    cell_c2 = ui_tbl.cell(1, 1)
    set_cell_margins(cell_c1, top=10, bottom=30, left=30, right=30)
    set_cell_margins(cell_c2, top=10, bottom=30, left=30, right=30)

    p_cap_s1 = cell_c1.paragraphs[0]
    p_cap_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_s1.paragraph_format.space_before = Pt(0)
    p_cap_s1.paragraph_format.space_after = Pt(0)
    r_cs1 = p_cap_s1.add_run("Screenshot A: Multi-Model Orchestration & Real-Time SCADA Console")
    r_cs1.font.size = Pt(7.2)
    r_cs1.font.bold = True
    r_cs1.font.color.rgb = COLOR_DARK

    p_cap_s2 = cell_c2.paragraphs[0]
    p_cap_s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_s2.paragraph_format.space_before = Pt(0)
    p_cap_s2.paragraph_format.space_after = Pt(0)
    r_cs2 = p_cap_s2.add_run("Screenshot B: Three.js 3D Digital Twin with Live Machinery Telemetry")
    r_cs2.font.size = Pt(7.2)
    r_cs2.font.bold = True
    r_cs2.font.color.rgb = COLOR_DARK

    # Section 6: Key Engineering Innovations & Verification Metrics
    p_sec6 = doc.add_paragraph()
    p_sec6.paragraph_format.space_before = Pt(4)
    p_sec6.paragraph_format.space_after = Pt(2)
    r_s6 = p_sec6.add_run("6. KEY ENGINEERING INNOVATIONS & VERIFICATION METRICS")
    r_s6.bold = True
    r_s6.font.size = Pt(9.5)
    r_s6.font.name = "Arial"
    r_s6.font.color.rgb = COLOR_PRIMARY

    # Metrics 4-Column Grid Table
    tbl_metrics = doc.add_table(rows=2, cols=4)
    tbl_metrics.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_metrics.autofit = False
    set_table_borders(tbl_metrics)

    m_widths = [Inches(1.92), Inches(1.92), Inches(1.92), Inches(1.94)]
    for row in tbl_metrics.rows:
        for idx, width in enumerate(m_widths):
            row.cells[idx].width = width

    innovations = [
        ("Zero Egress & Air-Gap", "100% Local Inference", "All model checkpoints (GGUF), embeddings, and audit trails reside in local hardware with zero external API calls."),
        ("Dynamic VRAM Budgeting", "< 8 GB VRAM Footprint", "Multi-model memory scheduler unloads dormant weights and loads active models in <400ms for DGX & workstation GPUs."),
        ("Tamper-Evident Ledger", "SHA-256 Chained Blocks", "Every operator command, voice actuation, and state change is cryptographically hashed with parent linkage."),
        ("Deterministic Safety Interlocks", "4-Tier RBAC Gateway", "Hardware trip lines and Python AST parser prevent unauthorized command execution with default-deny enforcement.")
    ]

    for idx, (title, stat, desc) in enumerate(innovations):
        cell_head = tbl_metrics.cell(0, idx)
        cell_desc = tbl_metrics.cell(1, idx)
        set_cell_bg(cell_head, HEX_BG_HEAD)
        set_cell_bg(cell_desc, HEX_BG_CARD)
        set_cell_margins(cell_head, top=40, bottom=40, left=50, right=50)
        set_cell_margins(cell_desc, top=40, bottom=40, left=50, right=50)

        p_h = cell_head.paragraphs[0]
        p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_h.paragraph_format.space_before = Pt(0)
        p_h.paragraph_format.space_after = Pt(0)
        r_th = p_h.add_run(f"{title}\n")
        r_th.bold = True
        r_th.font.size = Pt(7.8)
        r_th.font.color.rgb = RGBColor(255, 255, 255)
        
        r_st = p_h.add_run(stat)
        r_st.bold = True
        r_st.font.size = Pt(8.2)
        r_st.font.color.rgb = RGBColor(56, 189, 248)

        p_d = cell_desc.paragraphs[0]
        p_d.paragraph_format.space_before = Pt(0)
        p_d.paragraph_format.space_after = Pt(0)
        r_d = p_d.add_run(desc)
        r_d.font.size = Pt(7.2)
        r_d.font.color.rgb = COLOR_DARK

    # Bottom Sign-Off Footer
    p_foot = doc.add_paragraph()
    p_foot.paragraph_format.space_before = Pt(5)
    p_foot.paragraph_format.space_after = Pt(0)
    p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_ft = p_foot.add_run("Sovereign Industrial AI Workbench — Built & Documented by Mukul Dhankhar | Standalone DGX Spark & Windows Ready")
    r_ft.font.size = Pt(7.0)
    r_ft.font.italic = True
    r_ft.font.color.rgb = COLOR_MUTED

    # Save to Word Document
    target_path = "Sovereign_Industrial_AI_Workbench_Project_Brief.docx"
    doc.save(target_path)
    print(f"SUCCESSFULLY GENERATED 2-PAGE PROJECT WORD FILE: {target_path}")

if __name__ == "__main__":
    build_project_doc()
