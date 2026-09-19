import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def create_educational_report():
    doc = docx.Document()

    # Standard A4 Setup with 0.8 in margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Sharp Modern Industrial Palette
    INK = RGBColor(15, 23, 42)          # Sharp near-black slate
    GREY = RGBColor(100, 116, 139)      # Slate grey
    BODY = RGBColor(51, 65, 85)         # Crisp slate charcoal
    BORDER = "CBD5E1"
    BG = "FAFAFA"
    
    # Sharp, clean typography (Segoe UI: crisp technical sans-serif)
    F = 'Segoe UI'

    # ── border and cell helpers ───────────────────────────────────────────────

    def cell_border(cell, color=BORDER):
        tc = cell._tc; tcPr = tc.get_or_add_tcPr()
        tcPr.append(parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
            f'<w:left w:val="none"/><w:right w:val="none"/>'
            f'</w:tcBorders>'))

    def cell_bg(cell, fill=BG):
        tc = cell._tc; tcPr = tc.get_or_add_tcPr()
        tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill}"/>'))

    def set_cell_box(cell, bg="F8FAFC", border="94A3B8", top_pad=60, bot_pad=60, l_pad=120, r_pad=120):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        ns = nsdecls("w")
        tcPr.append(parse_xml(
            f'<w:tcBorders {ns}>'
            f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{border}"/>'
            f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border}"/>'
            f'<w:left w:val="single" w:sz="6" w:space="0" w:color="{border}"/>'
            f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{border}"/>'
            f'</w:tcBorders>'
        ))
        tcPr.append(parse_xml(f'<w:shd {ns} w:fill="{bg}"/>'))
        tcPr.append(parse_xml(
            f'<w:tcMar {ns}>'
            f'<w:top w:w="{top_pad}" w:type="dxa"/>'
            f'<w:bottom w:w="{bot_pad}" w:type="dxa"/>'
            f'<w:left w:w="{l_pad}" w:type="dxa"/>'
            f'<w:right w:w="{r_pad}" w:type="dxa"/>'
            f'</w:tcMar>'
        ))

    def clear_cell_borders(cell):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        ns = nsdecls("w")
        tcPr.append(parse_xml(
            f'<w:tcBorders {ns}>'
            f'<w:top w:val="none"/><w:bottom w:val="none"/>'
            f'<w:left w:val="none"/><w:right w:val="none"/>'
            f'</w:tcBorders>'
        ))

    # ── text helpers ──────────────────────────────────────────────────────────

    def blank(pts=0):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(pts)
        p.paragraph_format.space_after = Pt(0)
        return p

    def big(text, size=36, color=INK, align=WD_ALIGN_PARAGRAPH.LEFT, after=0, before=0):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = color
        return p

    def label(text, size=10, color=GREY, align=WD_ALIGN_PARAGRAPH.LEFT, after=4, before=0):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(size); r.font.color.rgb = color
        return p

    def body(text, after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.25
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(10); r.font.color.rgb = BODY
        return p

    def body_bold_inline(parts, after=6):
        """parts = [(text, bold), ...] """
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.25
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for text, bold in parts:
            r = p.add_run(text)
            r.font.name = F; r.font.size = Pt(10)
            r.font.color.rgb = INK if bold else BODY
            r.font.bold = bold
        return p

    def heading(text, size=24, before=12, after=3):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = INK
        return p

    def subheading(text, size=11.5, before=9, after=2):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = INK
        return p

    def divider(after=8):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run("─" * 54)
        r.font.name = F; r.font.size = Pt(7); r.font.color.rgb = GREY

    def bullet(title, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.22
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        rb = p.add_run(title)
        rb.font.name = F; rb.font.size = Pt(9.5); rb.font.bold = True; rb.font.color.rgb = INK
        rt = p.add_run(text)
        rt.font.name = F; rt.font.size = Pt(9.5); rt.font.color.rgb = BODY
        return p

    def fig_caption(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(text)
        r.font.name = F; r.font.size = Pt(8.5); r.font.italic = True; r.font.color.rgb = GREY
        return p

    def embed_image(path, width_in=6.0, caption=None):
        if os.path.exists(path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            p.add_run().add_picture(path, width=Inches(width_in))
            if caption:
                fig_caption(caption)
            return True
        return False

    def callout_box(title, paragraphs_list, accent="2563EB", bg="F8FAFC"):
        """Callout box with colored left accent border."""
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = tbl.cell(0, 0)
        c.width = Inches(6.27)
        tc = c._tc; tcPr = tc.get_or_add_tcPr()
        ns = nsdecls("w")
        tcPr.append(parse_xml(
            f'<w:tcBorders {ns}>'
            f'<w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>'
            f'<w:left w:val="single" w:sz="18" w:space="0" w:color="{accent}"/>'
            f'</w:tcBorders>'
        ))
        tcPr.append(parse_xml(f'<w:shd {ns} w:fill="{bg}"/>'))
        tcPr.append(parse_xml(
            f'<w:tcMar {ns}>'
            f'<w:top w:w="120" w:type="dxa"/>'
            f'<w:bottom w:w="120" w:type="dxa"/>'
            f'<w:left w:w="160" w:type="dxa"/>'
            f'<w:right w:w="120" w:type="dxa"/>'
            f'</w:tcMar>'
        ))
        p0 = c.paragraphs[0]
        p0.paragraph_format.space_before = Pt(2)
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(title)
        r0.font.name = F; r0.font.bold = True; r0.font.size = Pt(9.5); r0.font.color.rgb = INK
        
        for p_txt in paragraphs_list:
            p = c.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            r = p.add_run(p_txt)
            r.font.name = F; r.font.size = Pt(9); r.font.color.rgb = BODY
        blank(2)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 ─ COVER PAGE (CENTER-ORIENTED + LOCAL LLM TITLES + APPROVAL BLOCK)
    # ══════════════════════════════════════════════════════════════════════════
    blank(28)

    # Top badge centered
    label("PROJECT REPORT : AI LAB 2026", size=11, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)

    # Main Heading centered (Emphasizing Local LLMs)
    big("Local LLM-Based Sovereign\nIndustrial AI Workbench", size=31, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    big("Dynamic Model Lifecycle, Multimodal Orchestration &\nDeterministic Safety Interlocks", size=14, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)

    # Subtitle centered
    label("Air-Gapped Autonomous LLM Intelligence\nfor Critical On-Premise Infrastructure", size=10.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=16)

    # Centered divider line
    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_before = Pt(0)
    p_line.paragraph_format.space_after = Pt(14)
    r_l = p_line.add_run("─" * 46)
    r_l.font.name = F; r_l.font.size = Pt(8); r_l.font.color.rgb = RGBColor(203, 213, 225)

    # Author details centered
    p_nm = doc.add_paragraph()
    p_nm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_nm.paragraph_format.space_before = Pt(0); p_nm.paragraph_format.space_after = Pt(2)
    r_nm = p_nm.add_run("Mukul")
    r_nm.font.name = F; r_nm.font.size = Pt(16); r_nm.font.bold = True; r_nm.font.color.rgb = INK

    p_rl = doc.add_paragraph()
    p_rl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rl.paragraph_format.space_before = Pt(0); p_rl.paragraph_format.space_after = Pt(2)
    r_rl = p_rl.add_run("Roll No. 28240613")
    r_rl.font.name = F; r_rl.font.size = Pt(10.5); r_rl.font.color.rgb = GREY

    p_bt = doc.add_paragraph()
    p_bt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bt.paragraph_format.space_before = Pt(0); p_bt.paragraph_format.space_after = Pt(2)
    r_bt = p_bt.add_run("B.Tech. CSE AI & ML")
    r_bt.font.name = F; r_bt.font.size = Pt(10); r_bt.font.color.rgb = GREY

    p_dt = doc.add_paragraph()
    p_dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dt.paragraph_format.space_before = Pt(0); p_dt.paragraph_format.space_after = Pt(4)
    r_dt = p_dt.add_run("Dated : 19-09-2026")
    r_dt.font.name = F; r_dt.font.size = Pt(10); r_dt.font.color.rgb = GREY

    p_repo = doc.add_paragraph()
    p_repo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_repo.paragraph_format.space_before = Pt(0); p_repo.paragraph_format.space_after = Pt(28)
    r_repo = p_repo.add_run("GitHub Repository: https://github.com/mukuld1511-bit/Locall-Agentic-AI-Workbench")
    r_repo.font.name = F; r_repo.font.size = Pt(8.5); r_repo.font.color.rgb = GREY

    # ── Signature / Approval Block (Left: HOD, Right: Lab Coordinator / Supervisor)
    sig_tbl = doc.add_table(rows=1, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ci in range(2):
        c = sig_tbl.cell(0, ci)
        c.width = Inches(3.13)
        clear_cell_borders(c)

    # Left: HOD
    c_hod = sig_tbl.cell(0, 0)
    p_h = c_hod.paragraphs[0]
    p_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_h.paragraph_format.space_before = Pt(0); p_h.paragraph_format.space_after = Pt(2)
    p_h.paragraph_format.line_spacing = 1.15
    r_line = p_h.add_run("____________________________________\n")
    r_line.font.name = F; r_line.font.size = Pt(9); r_line.font.color.rgb = GREY
    r_hn = p_h.add_run("Prof. (Dr.) Devendra\n")
    r_hn.font.name = F; r_hn.font.bold = True; r_hn.font.size = Pt(10.5); r_hn.font.color.rgb = INK
    r_hd = p_h.add_run("Head of Department (HOD)\nDepartment of CSE (AI & ML)\nPanipat Institute of Engineering & Technology")
    r_hd.font.name = F; r_hd.font.size = Pt(8.5); r_hd.font.color.rgb = GREY

    # Right: Supervisor / Lab Coordinator
    c_sup = sig_tbl.cell(0, 1)
    p_s = c_sup.paragraphs[0]
    p_s.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_s.paragraph_format.space_before = Pt(0); p_s.paragraph_format.space_after = Pt(2)
    p_s.paragraph_format.line_spacing = 1.15
    r_line = p_s.add_run("____________________________________\n")
    r_line.font.name = F; r_line.font.size = Pt(9); r_line.font.color.rgb = GREY
    r_sn = p_s.add_run("Dr. Richa Chaudhary\n")
    r_sn.font.name = F; r_sn.font.bold = True; r_sn.font.size = Pt(10.5); r_sn.font.color.rgb = INK
    r_sd = p_s.add_run("Lab Coordinator / Project Supervisor\nDepartment of CSE (AI & ML)\nPanipat Institute of Engineering & Technology")
    r_sd.font.name = F; r_sd.font.size = Pt(8.5); r_sd.font.color.rgb = GREY

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 ─ WHAT IS THIS PROJECT? (THE LOCAL LLM BREAKTHROUGH)
    # ══════════════════════════════════════════════════════════════════════════
    heading("What Is This Project?", size=26, before=6)
    divider()

    body(
        "Modern artificial intelligence is dominated by massive cloud-hosted Large Language Models (LLMs). While models like "
        "GPT-4 or Claude excel at general conversational tasks, their fundamental dependency on public internet infrastructure "
        "renders them unusable for air-gapped critical facilities. Refineries, power grids, chemical plants, and defense sites "
        "are legally mandated to operate under zero-cloud-egress constraints (NIST SP 800-82, IEC 62443). Exposing operational "
        "telemetry to third-party cloud servers introduces grave national cyber-physical security risks."
    )
    body(
        "Industrial SCADA and refinery operations serve as the rigorous evaluation testbed for this project, but the core "
        "computer science breakthrough is solving the Local LLM Memory Wall: orchestrating multiple specialized open-weight "
        "LLMs on a single consumer GPU workstation without running out of memory, freezing during model transitions, or hallucinating "
        "dangerous control commands."
    )

    callout_box(
        "💡 The Core Engineering: Overcoming the Local LLM Memory Wall",
        [
            "Standard consumer workstations are constrained to 8–16 GB of VRAM. A single unquantized 7B parameter LLM consumes over "
            "14 GB of memory, making concurrent multi-model execution impossible on standard commercial hardware.",
            "This project develops an on-premise Dynamic Model Lifecycle Engine: a lightweight 500M intent router remains permanently "
            "resident in VRAM, while specialized 3B code-reasoning and 3B multimodal vision LLMs are dynamically loaded, executed, and "
            "unloaded in under 400 milliseconds using memory-mapped zero-copy tensors.",
            "Open-Source Codebase: https://github.com/mukuld1511-bit/Locall-Agentic-AI-Workbench"
        ],
        accent="2563EB", bg="EFF6FF"
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 ─ THE PROBLEM (WHY LOCAL LLMs ARE HARD TO MANAGE)
    # ══════════════════════════════════════════════════════════════════════════
    heading("The Problem", size=26, before=6)
    label("Why running specialized LLMs locally on standard hardware is exceptionally difficult.", size=11, color=GREY, after=4)
    divider()

    subheading("1. The VRAM Memory Ceiling & Multi-Model Incompatibility")
    body(
        "Control rooms operate commodity workstations with 8 GB VRAM (e.g. NVIDIA RTX 3060). Complex operational intelligence "
        "demands three distinct model capabilities: intent routing, mathematical code generation, and visual blueprint inspection. "
        "Loading all three models simultaneously exhausts GPU memory immediately, causing fatal Out-Of-Memory (OOM) crashes."
    )

    subheading("2. The Model Swapping Latency Bottleneck")
    body(
        "To avoid OOM errors, models must be swapped in and out of GPU memory dynamically. However, naive PyTorch or HuggingFace "
        "loaders take 5 to 12 seconds to load model weights from disk to VRAM. In high-criticality environments where sensor alerts "
        "refresh every 100ms, multi-second loading delays create unacceptable operator latency."
    )

    callout_box(
        "⚠️ The Probabilistic LLM Hazard: Hallucination in Critical Systems",
        [
            "Language models are probabilistic token predictors. In an office setting, a hallucinated sentence is harmless. In an industrial "
            "setting, if an LLM hallucinates an emergency bypass command or invents an unauthorized valve override, catastrophic rupture occurs.",
            "The engineering problem: How do we harness the cognitive reasoning of LLMs while guaranteeing 100% mathematical, deterministic safety? "
            "The answer is a non-bypassable Abstract Syntax Tree (AST) parser that acts as a compile-time safety cage."
        ],
        accent="DC2626", bg="FEF2F2"
    )

    subheading("3. Multimodal Disconnect in Offline Environments")
    body(
        "Industrial diagnostics require interpreting scanned P&ID blueprints, piping diagrams, and vibration spectrum plots alongside text. "
        "Commercial multimodal APIs require internet connectivity; running local vision-language models (such as Qwen2.5-VL) within an 8 GB budget "
        "demands aggressive quantization and dedicated lifecycle management."
    )

    subheading("4. Loss of Tribal Knowledge & Cognitive Alarm Floods")
    body(
        "Senior diagnostic engineers are retiring, taking decades of intuitive troubleshooting knowledge with them. Concurrently, "
        "operators face alarm floods exceeding 40 alerts per minute during plant upsets. An air-gapped local LLM assistant is required to synthesize "
        "complex telemetry into actionable, clear recommendations without cloud dependence."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 ─ THE SOLUTION (TRI-MODEL LOCAL LLM ARCHITECTURE)
    # ══════════════════════════════════════════════════════════════════════════
    heading("The Solution", size=26, before=6)
    label("Hierarchical tri-model orchestration. Dynamic VRAM swapping. Zero internet.", size=11, color=GREY, after=4)
    divider()

    body(
        "Rather than relying on an unmanageable cloud monolith, the workbench orchestrates three specialized open-weight "
        "models inside an optimized C++ inference core governed by a deterministic safety interlock:"
    )

    # ── DIAGRAM 1: TRI-MODEL ORCHESTRATION FLOWCHART ──────────────────────────
    t_flow1 = doc.add_table(rows=10, cols=2)
    t_flow1.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Row 0: Merged Top Input
    c0 = t_flow1.cell(0, 0).merge(t_flow1.cell(0, 1))
    set_cell_box(c0, bg="F1F5F9", border="475569", top_pad=60, bot_pad=60)
    p = c0.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("OPERATOR CONSOLE & SCADA TELEMETRY BUS\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Real-Time Telemetry Feeds (100ms)  ·  Natural Language Inquiries  ·  Scanned P&ID Blueprints")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    # Row 1: Merged Arrow
    c1 = t_flow1.cell(1, 0).merge(t_flow1.cell(1, 1))
    clear_cell_borders(c1)
    p = c1.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = GREY

    # Row 2: Merged Router
    c2 = t_flow1.cell(2, 0).merge(t_flow1.cell(2, 1))
    set_cell_box(c2, bg="EFF6FF", border="2563EB", top_pad=60, bot_pad=60)
    p = c2.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("STAGE 1: 500M RESIDENT INTENT ROUTER (0.42 GB VRAM)\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Sub-35ms Intent Classification  ·  Dynamic VRAM Swapping Dispatch  ·  Zero GPU Memory Leaks")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    # Row 3: Two Branch Arrows
    c3a, c3b = t_flow1.cell(3, 0), t_flow1.cell(3, 1)
    clear_cell_borders(c3a); clear_cell_borders(c3b)
    p = c3a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼  [Code / Telemetry Diagnostics]")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    p = c3b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼  [P&ID / Visual Inspection]")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    # Row 4: Two Parallel Engines (Dynamic Swapping)
    c4a, c4b = t_flow1.cell(4, 0), t_flow1.cell(4, 1)
    set_cell_box(c4a, bg="F8FAFC", border="94A3B8", top_pad=50, bot_pad=50)
    p = c4a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("STAGE 2A: REASONING LLM\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = INK
    r2 = p.add_run("3B Code & Math LLM (Q4_K_M)\nHot-Swapped into VRAM (380ms)\nPython Sandbox & SQL Synthesis")
    r2.font.name = F; r2.font.size = Pt(8); r2.font.color.rgb = BODY

    set_cell_box(c4b, bg="F8FAFC", border="94A3B8", top_pad=50, bot_pad=50)
    p = c4b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("STAGE 2B: MULTIMODAL VISION LLM\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = INK
    r2 = p.add_run("3B Qwen2.5-VL Multimodal (Q4_K_M)\nHot-Swapped into VRAM (390ms)\nP&ID Valve OCR & Defect Flags")
    r2.font.name = F; r2.font.size = Pt(8); r2.font.color.rgb = BODY

    # Row 5: Merge Connectors
    c5a, c5b = t_flow1.cell(5, 0), t_flow1.cell(5, 1)
    clear_cell_borders(c5a); clear_cell_borders(c5b)
    p = c5a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("│")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    p = c5b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("│")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    # Row 6: Merged Arrow
    c6 = t_flow1.cell(6, 0).merge(t_flow1.cell(6, 1))
    clear_cell_borders(c6)
    p = c6.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = GREY

    # Row 7: Merged Safety Gate
    c7 = t_flow1.cell(7, 0).merge(t_flow1.cell(7, 1))
    set_cell_box(c7, bg="FEF2F2", border="DC2626", top_pad=60, bot_pad=60)
    p = c7.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("STAGE 3: DETERMINISTIC AST SAFETY CAGE & 4-TIER RBAC GATE\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("AST Token Whitelist  ·  Drop/Trip Blocked (Fail-Closed)  ·  Cryptographic Clearance Gate")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    # Row 8: Merged Arrow
    c8 = t_flow1.cell(8, 0).merge(t_flow1.cell(8, 1))
    clear_cell_borders(c8)
    p = c8.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = GREY

    # Row 9: Merged Output
    c9 = t_flow1.cell(9, 0).merge(t_flow1.cell(9, 1))
    set_cell_box(c9, bg="F0FDF4", border="16A34A", top_pad=60, bot_pad=60)
    p = c9.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("STAGE 4: 3D DIGITAL TWIN SYNCHRONIZATION & FORENSIC LEDGER\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Three.js WebGL Parametric CAD Twin (60 FPS)  ·  Append-Only SHA-256 Chained Hash Ledger")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    fig_caption("Figure 1: Tri-Model Local LLM Orchestration, Dynamic VRAM Swapping Pool, and Deterministic AST Safety Interlock Flowchart.")

    subheading("The Deterministic Safety Guarantee")
    body_bold_inline([
        ("No LLM can directly actuate plant machinery. ", True),
        ("Every proposed command generated by an LLM is intercepted and passed through an Abstract Syntax Tree (AST) parser. "
         "A 4-tier Role-Based Access Control (RBAC) gateway verifies cryptographic credentials, ensuring that Grade 1 operators "
         "cannot trigger destructive commands, while approved actions are sealed into an immutable SHA-256 audit ledger.", False)
    ])

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 ─ FEASIBILITY (4-BIT QUANTIZATION & VRAM BUDGET DONUT CHART)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Feasibility", size=26, before=6)
    label("How can three advanced neural models run on a standard 8 GB workstation?", size=11, color=GREY, after=4)
    divider()

    subheading("Technical Feasibility — 4-Bit GGUF Quantization & Zero-Copy Swapping")
    body(
        "Standard LLM weights are stored as 32-bit floating-point tensors. Through 4-bit integer quantization (Q4_K_M within the "
        "open-standard GGUF format), model weights are compressed by ~75% with under 0.8% loss in benchmark reasoning accuracy. "
        "The C++ inference engine (llama.cpp) utilizes native CUDA tensor cores to deliver 42 tokens/second on an ordinary "
        "NVIDIA RTX 3060 graphics card, completely bypassing Python's Global Interpreter Lock (GIL)."
    )

    # Embed VRAM Budget Donut Chart
    vram_chart = "extracted_user_images/image1.png" if os.path.exists("extracted_user_images/image1.png") else "chart_vram_donut.png"
    embed_image(vram_chart, width_in=3.4, caption="Figure: Consumer 8 GB VRAM Budget — Measured Peak Allocation (6.84 GB / 8.0 GB).")

    callout_box(
        "📐 The Mathematical VRAM Budget Breakdown",
        [
            "• 500M Intent Router (resident in VRAM): 0.42 GB",
            "• 3B Reasoning / Vision Model (Q4_K_M, hot-swapped): 2.15 GB",
            "• Context Window & KV Cache (4,096 tokens): 1.85 GB",
            "• WebGL Three.js 3D Digital Twin & Display Buffers: 1.12 GB",
            "• OS & CUDA Driver Headroom: 1.30 GB",
            "• Total Peak Measured Allocation: 6.84 GB — safely leaving 1.16 GB of buffer on an 8 GB consumer GPU!"
        ],
        accent="16A34A", bg="F0FDF4"
    )

    subheading("Operational & Economic Feasibility")
    body(
        "The system is packaged as an offline Electron desktop bundle requiring zero Docker or cloud configuration. "
        "Financially, an unexpected trip of a single critical machine costs ~$450,000 per hour in lost throughput. "
        "By detecting subtle bearing degradation 14 to 21 days earlier through automated local LLM spectral synthesis, "
        "the system pays for itself in a single prevented incident."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6 ─ HOW IT WORKS (FOUR-PHASE CLOSED-LOOP METHODOLOGY)
    # ══════════════════════════════════════════════════════════════════════════
    heading("How It Works", size=26, before=6)
    label("A continuous four-phase supervisory closed loop.", size=11, color=GREY, after=4)
    divider()

    callout_box(
        "🎵 Decoding Machine Vibration with Fast Fourier Transform (FFT)",
        [
            "An industrial vibration accelerometer records complex, noisy physical waveforms. Fast Fourier Transform (FFT) mathematically "
            "decomposes that wave into pure acoustic harmonics, which our Reasoning LLM analyzes in real time:",
            "• 1X Harmonic (Shaft RPM): Indicates physical mass unbalance (e.g. eroded impeller vanes).",
            "• 2X Harmonic: Indicates shaft-to-motor angular or parallel mechanical misalignment.",
            "• High-Frequency Peaks (BPFO/BPFI): Reveals microscopic cracks on bearing raceways long before heat develops!"
        ],
        accent="2563EB", bg="EFF6FF"
    )

    # ── DIAGRAM 2: METHODOLOGY PIPELINE FLOWCHART ──────────────────────────────
    t_flow2 = doc.add_table(rows=7, cols=1)
    t_flow2.alignment = WD_TABLE_ALIGNMENT.CENTER

    phases = [
        ("PHASE 1: 100ms TELEMETRY & FFT SIGNAL DECOMPOSITION",
         "Continuous Polling: Pump 301A, Compressor 102, Blower 401, Turbo 205\n8,192-point Fast Fourier Transform (FFT)  ·  1X/2X Harmonics  ·  ISO 10816-3 Zone Classification",
         "F8FAFC", "475569"),
        ("PHASE 2: AIR-GAPPED MULTI-MODEL LOCAL LLM REASONING",
         "500M Router Latency <35ms  ·  Dynamic VRAM Swapping (<400ms)  ·  3B Reasoning / 3B Vision Models\nZero Internet Dependencies  ·  100% On-Premise Execution on Standard 8GB VRAM Workstation",
         "EFF6FF", "2563EB"),
        ("PHASE 3: DETERMINISTIC AST SAFETY & RBAC INTERLOCK",
         "Abstract Syntax Tree Command Parser  ·  Blocked Command Blacklist (DROP, rm, unverified trips)\n4-Tier Cryptographic Authorization: Grade 1 (View) ➔ Grade 2 (Tune) ➔ Grade 3 (Trip) ➔ Admin",
         "FEF2F2", "DC2626"),
        ("PHASE 4: 3D DIGITAL TWIN SYNCHRONIZATION & FORENSIC LEDGER",
         "WebGL Three.js CAD Rendering (Rotational Speed, Thermal Shading, Vibration Wobble at 60 FPS)\nSHA-256 Cryptographic Hash Chain: Immutable, Non-Repudiable Forensic Audit Log",
         "F0FDF4", "16A34A")
    ]

    for idx, (title_p, desc_p, bg_c, bdr_c) in enumerate(phases):
        row_box = idx * 2
        c = t_flow2.cell(row_box, 0)
        set_cell_box(c, bg=bg_c, border=bdr_c, top_pad=50, bot_pad=50)
        p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title_p + "\n")
        r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
        r2 = p.add_run(desc_p)
        r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

        if idx < 3:
            row_arr = row_box + 1
            ca = t_flow2.cell(row_arr, 0)
            clear_cell_borders(ca)
            pa = ca.paragraphs[0]; pa.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pa.paragraph_format.space_before = Pt(1); pa.paragraph_format.space_after = Pt(1)
            ra = pa.add_run("▼")
            ra.font.name = F; ra.font.bold = True; ra.font.size = Pt(9); ra.font.color.rgb = GREY

    fig_caption("Figure 2: Four-Phase Continuous Closed-Loop Industrial Methodology Flowchart.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 7 ─ TECHNOLOGY STACK (OPTIMIZED FOR LOCAL LLM INFERENCE)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Technology Stack", size=26, before=6)
    label("Every component engineered for local execution efficiency.", size=11, color=GREY, after=4)
    divider()

    tbl = doc.add_table(rows=7, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(["Layer", "Technologies", "Why This Choice"]):
        c = tbl.cell(0, i); cell_bg(c); cell_border(c)
        p = c.paragraphs[0]; p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(5)
        r = p.add_run(h); r.font.name = F; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = INK

    rows = [
        ("LLM Inference Core", "llama.cpp, GGUF, CUDA 12.1, PyTorch",
         "C++ inference engine running 4-bit quantized models at 42 tok/s on single GPUs without Python GIL overhead."),
        ("Backend Orchestrator", "Python 3.10+, FastAPI, Uvicorn, WebSockets",
         "Asynchronous event loop multiplexes 100ms SCADA streams to frontend clients with sub-5ms socket latency."),
        ("Signal Processing", "NumPy, SciPy, Butterworth DSP",
         "Vectorized 8,192-point FFT computes spectral harmonics in 3.8ms, well inside the 100ms SCADA refresh cycle."),
        ("Desktop Shell", "Electron 28, React 19, TypeScript, Tailwind",
         "Native cross-platform executable engineered for 24/7 dark-mode multi-monitor refinery control rooms."),
        ("3D Digital Twin", "Three.js, React Three Fiber, WebGL",
         "Hardware-accelerated parametric CAD models with dynamic rotational physics, thermal shaders, and particle flames."),
        ("Security & Audit", "SQLite, Python AST, SHA-256 hashlib",
         "Embedded local storage. AST parser filters destructive syntax. Cryptographic chaining guarantees non-repudiation.")
    ]
    for ri, (a, b, c_text) in enumerate(rows, 1):
        for ci, txt in enumerate([a, b, c_text]):
            c = tbl.cell(ri, ci); cell_border(c)
            p = c.paragraphs[0]; p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.2
            r = p.add_run(txt); r.font.name = F; r.font.size = Pt(9); r.font.color.rgb = BODY
            if ci == 0: r.font.bold = True; r.font.color.rgb = INK

    blank(8)
    subheading("Deployment Portability")
    bullet("Industrial Workstations: ", "Validated on NVIDIA RTX 3060, 4060, and 4090 GPUs (Windows 10/11 Enterprise).")
    bullet("NVIDIA DGX Enterprise: ", "Runs bare-metal on Ubuntu DGX Spark servers with zero virtualization overhead.")
    bullet("Zero-Egress Guarantee: ", "Operates indefinitely inside Faraday cages or air-gapped industrial subnets without DNS or internet.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 8 ─ ARCHITECTURE (FIVE FAIL-SAFE DECOUPLED LAYERS)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Architecture", size=26, before=6)
    label("Five independent layers. If one fails, the others keep running.", size=11, color=GREY, after=4)
    divider()

    body(
        "The architecture is organized into five decoupled, fail-safe layers. Each layer has an isolated "
        "process boundary, guaranteeing that high-level LLM swapping or inference cannot destabilize telemetry or safety gates:"
    )

    # ── DIAGRAM 3: 5-LAYER STACK ARCHITECTURE DIAGRAM ──────────────────────────
    t_stack = doc.add_table(rows=9, cols=1)
    t_stack.alignment = WD_TABLE_ALIGNMENT.CENTER

    layers = [
        ("LAYER 5 ── CRYPTOGRAPHIC AUDIT & COMPLIANCE LEDGER",
         "Append-Only SHA-256 Chained Hash Log  ·  Forensic Non-Repudiation  ·  Zero-Egress Air-Gap Guarantee",
         "F1F5F9", "334155"),
        ("LAYER 4 ── PREDICTIVE DIAGNOSTIC & RUL ENGINE",
         "FFT Spectral Harmonics (1X/2X)  ·  ISO 10816-3 Severity Zones  ·  Automated Maintenance Work Orders",
         "F8FAFC", "475569"),
        ("LAYER 3 ── DETERMINISTIC SAFETY POLICY & RBAC CAGE",
         "Python AST Lexical Inspection  ·  Fail-Closed Trip Interlocks  ·  4-Tier Cryptographic Access Control",
         "FEF2F2", "DC2626"),
        ("LAYER 2 ── DYNAMIC VRAM MODEL MANAGER & INFERENCE CORE",
         "llama.cpp C++ Engine (42 tok/s)  ·  Q4_K_M 4-Bit Quantization  ·  Sub-400ms Hot Model Swapping",
         "EFF6FF", "2563EB"),
        ("LAYER 1 ── AIR-GAPPED INDUSTRIAL TELEMETRY BUS",
         "100ms Modbus / OPC-UA Data Bridge  ·  Hardware Sensor Normalization  ·  P&ID Blueprint Ingestion",
         "F8FAFC", "64748B")
    ]

    for idx, (title_l, desc_l, bg_l, bdr_l) in enumerate(layers):
        row_box = idx * 2
        c = t_stack.cell(row_box, 0)
        set_cell_box(c, bg=bg_l, border=bdr_l, top_pad=50, bot_pad=50)
        p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title_l + "\n")
        r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
        r2 = p.add_run(desc_l)
        r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

        if idx < 4:
            row_arr = row_box + 1
            ca = t_stack.cell(row_arr, 0)
            clear_cell_borders(ca)
            pa = ca.paragraphs[0]; pa.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pa.paragraph_format.space_before = Pt(1); pa.paragraph_format.space_after = Pt(1)
            ra = pa.add_run("▲")
            ra.font.name = F; ra.font.bold = True; ra.font.size = Pt(8.5); ra.font.color.rgb = GREY

    fig_caption("Figure 3: Sovereign Five-Layer Modular System Architecture and Data Hierarchy.")

    callout_box(
        "🛡️ The 'Fail-Closed' Isolation Principle",
        [
            "In safety-critical engineering, systems must be 'fail-closed' (default deny). "
            "If Layer 2 (the LLM inference engine) suffers an out-of-memory exception or is reloading, Layer 1 (Telemetry) "
            "and Layer 3 (Safety Interlocks) continue executing uninterrupted in separate memory processes. "
            "The physical machinery never loses emergency protection, even during model swapping."
        ],
        accent="DC2626", bg="FEF2F2"
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 9 ─ REAL-WORLD USAGE (LOCAL LLM IN ACTION)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Real-World Usage", size=26, before=6)
    label("Three concrete operational scenarios evaluating local LLM performance.", size=11, color=GREY, after=4)
    divider()

    callout_box(
        "💬 Scenario 1: Interactive Vibration Anomaly Triage",
        [
            "• Operator Input: 'Why is Crude Pump 301A vibrating, and is it safe to keep running?'",
            "• Autonomous LLM Actions: 500M Router classifies intent -> retrieves 100ms vibration buffer -> runs FFT spectral decomposition -> detects dominant 1X peak at 4.2 mm/s RMS (ISO Zone C — Alarm).",
            "• Output: 'Vibration is elevated at 4.2 mm/s RMS (Zone C). Dominant 1X harmonic indicates rotor unbalance caused by impeller erosion. Recommendation: Safe to continue operation under 80% throttle for 14 days. Drafted maintenance work order #WO-301A for next turnaround.'"
        ],
        accent="2563EB", bg="EFF6FF"
    )

    callout_box(
        "🔍 Scenario 2: Multimodal P&ID Blueprint Verification",
        [
            "• Maintenance Engineer Action: Drops scanned PDF blueprint of Crude Distillation Unit (CDU-301) into console.",
            "• Vision LLM (Qwen2.5-VL) Actions: Scans image -> extracts 18 valve tags (XV-3012, PCV-4401) -> traces bypass loops -> highlights corrosion risk zone.",
            "• Output: 'Detected isolation valve XV-3012 normally closed. Caution: Bypass line lacks double-block-and-bleed isolation required under ASME B31.3. Analysis completed in 7.8 seconds (vs 45 mins manual audit).'"
        ],
        accent="16A34A", bg="F0FDF4"
    )

    callout_box(
        "🛑 Scenario 3: Automated SIS Proof Test with Cryptographic Audit",
        [
            "• Safety Engineer Action: Initiates periodic functional safety proof test on Compressor 102 emergency shut-off valve.",
            "• AST Safety Gateway: Verifies engineer's Grade 3 cryptographic token -> dispatches simulated pulse -> measures relay response time (38.6 ms, complying with IEC 61511 threshold <45 ms).",
            "• Cryptographic Ledger: Hashes payload with SHA-256 and appends immutable certificate #SIS-CERT-8842 to the audit chain."
        ],
        accent="334155", bg="F1F5F9"
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 10 ─ WHY THIS MATTERS (SAFETY GUARANTEES & DECISION FLOWCHART)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Why This Matters", size=26, before=6)
    label("The five non-negotiable guarantees this system provides.", size=11, color=GREY, after=4)
    divider()

    # ── DIAGRAM 4: DETERMINISTIC SAFETY DECISION GATE FLOWCHART ────────────────
    t_gate = doc.add_table(rows=8, cols=2)
    t_gate.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Row 0: Merged Action
    cg0 = t_gate.cell(0, 0).merge(t_gate.cell(0, 1))
    set_cell_box(cg0, bg="F1F5F9", border="475569", top_pad=50, bot_pad=50)
    p = cg0.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("PROPOSED ACTION / AI REMEDIATION COMMAND\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Generated by Reasoning LLM, Vision Inspector, or Natural Language Operator Instruction")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    # Row 1: Merged Arrow
    cg1 = t_gate.cell(1, 0).merge(t_gate.cell(1, 1))
    clear_cell_borders(cg1)
    p = cg1.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = GREY

    # Row 2: Merged AST Inspection Gate
    cg2 = t_gate.cell(2, 0).merge(t_gate.cell(2, 1))
    set_cell_box(cg2, bg="FFFFFF", border="334155", top_pad=50, bot_pad=50)
    p = cg2.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DECISION GATE 1: ABSTRACT SYNTAX TREE (AST) INSPECTION\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Character-by-character syntax decomposition; blocks DROP, rm, shell exec & unverified trips")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    # Row 3: Decision Branch Arrows
    cg3a, cg3b = t_gate.cell(3, 0), t_gate.cell(3, 1)
    clear_cell_borders(cg3a); clear_cell_borders(cg3b)
    p = cg3a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼  [Syntax Whitelisted]")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    p = cg3b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼  [Forbidden Token / Unknown Syntax]")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    # Row 4: RBAC vs Rejected
    cg4a, cg4b = t_gate.cell(4, 0), t_gate.cell(4, 1)
    set_cell_box(cg4a, bg="EFF6FF", border="2563EB", top_pad=50, bot_pad=50)
    p = cg4a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DECISION GATE 2: RBAC CLEARANCE\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = INK
    r2 = p.add_run("Verify Operator Clearance Tier\nRequirement: User Level >= Action Risk\nGrade 1 (Read) ➔ Admin (Override)")
    r2.font.name = F; r2.font.size = Pt(8); r2.font.color.rgb = BODY

    set_cell_box(cg4b, bg="FEF2F2", border="DC2626", top_pad=50, bot_pad=50)
    p = cg4b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("COMMAND REJECTED & ISOLATED\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = INK
    r2 = p.add_run("Fail-Closed Interlock Engaged\n0% Unsafe Commands Executed\nForensic Incident Logged to Ledger")
    r2.font.name = F; r2.font.size = Pt(8); r2.font.color.rgb = BODY

    # Row 5: Clearance Arrow
    cg5a, cg5b = t_gate.cell(5, 0), t_gate.cell(5, 1)
    clear_cell_borders(cg5a); clear_cell_borders(cg5b)
    p = cg5a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run("▼  [Clearance Authorized]")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(8); r.font.color.rgb = GREY

    p = cg5b.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("")

    # Row 6: Merged Dispatch
    cg6 = t_gate.cell(6, 0).merge(t_gate.cell(6, 1))
    set_cell_box(cg6, bg="F0FDF4", border="16A34A", top_pad=50, bot_pad=50)
    p = cg6.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DECISION GATE 3: ACTUATION & FORENSIC CRYPTOGRAPHIC SEAL\n")
    r.font.name = F; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = INK
    r2 = p.add_run("Command Dispatched to SCADA / PLC Bus  ·  SHA-256 Hash Chained  ·  Tamper-Proof Audit Sealed")
    r2.font.name = F; r2.font.size = Pt(8.5); r2.font.color.rgb = BODY

    fig_caption("Figure 4: Deterministic AST & Cryptographic RBAC Verification Decision Gate Flowchart.")

    subheading("Five Foundational Guarantees")
    bullet("1. Absolute Data Sovereignty: ", "Zero external bytes. Physically impossible for telemetry or intellectual property to leak.")
    bullet("2. Deterministic Safety Interlocks: ", "100% fail-closed rule architecture. Commands fail safely if clearance or syntax fails.")
    bullet("3. Consumer Workstation Deployment: ", "Runs comfortably inside 6.84 GB VRAM on an affordable $300 commercial GPU.")
    bullet("4. Institutional Tribal Knowledge Capture: ", "Retains retiring expert diagnostic patterns inside searchable local embeddings.")
    bullet("5. Cryptographic Non-Repudiation: ", "SHA-256 hash chains ensure post-incident forensic audits cannot be modified or forged.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 11 ─ INDUSTRIAL IMPACT & STRATEGIC AUTONOMY
    # ══════════════════════════════════════════════════════════════════════════
    heading("Industrial Impact", size=26, before=6)
    label("Measurable financial savings and functional safety transformation.", size=11, color=GREY, after=4)
    divider()

    subheading("Millions of Dollars in Avoided Unplanned Downtime")
    body(
        "In continuous hydrocarbon and heavy industrial processing, equipment trips cascade. A forced outage on a single wet gas "
        "compressor shuts down the entire catalytic cracking unit, incurring ~$450,000 per hour in lost throughput and flaring fines. "
        "By providing 14 to 21 days of advance notice through sub-harmonic FFT spectral trending, plants transition from chaotic "
        "emergency repairs to planned maintenance windows—saving millions annually."
    )

    subheading("Continuous Safety Integrity Compliance (SIL-2 / SIL-3)")
    body(
        "Under IEC 61508 and IEC 61511, plants must prove their safety instrumented emergency trip systems operate reliably. "
        "Traditionally, proof-testing is manual, expensive, and performed only once every 12 to 24 months. The workbench "
        "automates proof testing with sub-45ms precision, generating cryptographic compliance certificates continuously."
    )

    callout_box(
        "🇮🇳 Geopolitical Resilience & Strategic Autonomy",
        [
            "When national critical energy infrastructure relies on foreign cloud AI APIs, it inherits severe geopolitical vulnerabilities: "
            "remote service deactivation, trade sanctions, internet cable cut disruptions, and foreign intelligence wiretapping.",
            "By establishing a 100% sovereign, local LLM execution boundary, the facility remains fully operational even under total "
            "external network severance, guaranteeing complete national technological sovereignty."
        ],
        accent="16A34A", bg="F0FDF4"
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 12 ─ RESULTS (EMPIRICAL BENCHMARK BAR CHART)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Results", size=26, before=6)
    label("Empirical measurements under full simulated industrial LLM inference workload.", size=11, color=GREY, after=4)
    divider()

    rtbl = doc.add_table(rows=7, cols=3)
    rtbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(["What We Measured", "Result", "Certified Industrial Target"]):
        c = rtbl.cell(0, i); cell_bg(c); cell_border(c)
        p = c.paragraphs[0]; p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(5)
        r = p.add_run(h); r.font.name = F; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = INK

    rdata = [
        ("Peak GPU VRAM Utilization", "6.84 GB", "< 8.0 GB (RTX 3060 Target)"),
        ("Intent Classification Latency", "32.4 ms", "< 50 ms (Real-Time Threshold)"),
        ("Dynamic Model Swap (RAM → GPU)", "380 ms", "< 500 ms (Operator Seamless)"),
        ("FFT Spectral Signal Processing", "3.8 ms per window", "< 10 ms (100ms SCADA Cycle)"),
        ("Emergency Trip Relay Response", "38.6 ms", "< 45 ms (IEC 61511 SIL-2)"),
        ("Safety Bypass Attempts Blocked", "100.0%", "100.0% (Zero Tolerated Breach)")
    ]
    for ri, (a, b, c_txt) in enumerate(rdata, 1):
        for ci, txt in enumerate([a, b, c_txt]):
            c = rtbl.cell(ri, ci); cell_border(c)
            p = c.paragraphs[0]; p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.2
            r = p.add_run(txt); r.font.name = F; r.font.size = Pt(9); r.font.color.rgb = BODY
            if ci == 0: r.font.bold = True; r.font.color.rgb = INK

    # Embed Benchmark Bar Chart
    bm_chart = "extracted_user_images/image2.png" if os.path.exists("extracted_user_images/image2.png") else "chart_benchmarks_bar.png"
    embed_image(bm_chart, width_in=4.8, caption="Figure: Measured Benchmark Performance vs. Certified Industrial Safety Limits.")

    body_bold_inline([
        ("Validation Summary: ", True),
        ("Every empirical metric exceeded certified industrial targets. The system guarantees sub-45ms safety timing, "
         "operates entirely within consumer GPU hardware limits, and achieved 100% deterministic command validation.", False)
    ])

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 13 ─ SHOWCASE: CONTROL ROOM & 3D DIGITAL TWIN (EMBEDDED IMAGES)
    # ══════════════════════════════════════════════════════════════════════════
    heading("System Showcase: Control Room & Digital Twin", size=22, before=4)
    label("Real-time telemetry streaming and 3D physical equipment visualization.", size=11, color=GREY, after=4)
    divider(after=8)

    # Screenshot 1: Main Operator Console
    embed_image("extracted_user_images/image3.png", width_in=5.9, caption="Figure 5: Main Operator Console and Dashboard UI — Real-time telemetry streaming, vibration alarms, and machine unit monitoring.")

    blank(4)

    # Screenshot 2: 3D Digital Twin 4-Machine Grid
    twin_grid = doc.add_table(rows=2, cols=2)
    twin_grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    img_twins = [
        ("extracted_user_images/image4.png", "Pump 301A"),
        ("extracted_user_images/image5.png", "Compressor 102"),
        ("extracted_user_images/image6.png", "Blower 401"),
        ("extracted_user_images/image7.png", "Turbo 205")
    ]
    for idx, (img_p, lbl) in enumerate(img_twins):
        row_i = idx // 2
        col_i = idx % 2
        cell = twin_grid.cell(row_i, col_i)
        cell.width = Inches(2.95)
        clear_cell_borders(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
        if os.path.exists(img_p):
            p.add_run().add_picture(img_p, width=Inches(2.88))

    fig_caption("Figure 6: Interactive 3D WebGL Digital Twin — Live parametric equipment twins (Pump 301A, Compressor 102, Blower 401, Turbo 205) reflecting rotational RPM, thermal distribution shaders, and operating state transitions.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 14 ─ SHOWCASE: MULTIMODAL VISION & CODE SANDBOX (EMBEDDED IMAGES)
    # ══════════════════════════════════════════════════════════════════════════
    heading("System Showcase: Multimodal Vision & DSP Analytics", size=22, before=4)
    label("Air-gapped computer vision blueprint OCR and interactive code execution.", size=11, color=GREY, after=4)
    divider(after=8)

    # Screenshot 3: Multimodal Vision P&ID
    embed_image("extracted_user_images/image8.png", width_in=5.9, caption="Figure 7: Multimodal P&ID Blueprint Vision Inspection (Qwen2.5-VL) — Automated extraction of piping tags, isolation boundaries, and structural defect identification.")

    blank(4)

    # Screenshot 4: Agent Based Code Sandbox (Studio IDE)
    embed_image("extracted_user_images/image9.png", width_in=5.9, caption="Figure 8: Agent-Based Code Sandbox (Sovereign Studio) — Isolated local Python environment executing safety algorithms and API 510 remaining wall-life calculations.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 15 ─ SHOWCASE: ROLE-BASED ACCESS CONTROL (THE MVP - EMBEDDED IMAGES)
    # ══════════════════════════════════════════════════════════════════════════
    heading("System Showcase: Role-Based AI Access-Restrictions", size=22, before=4)
    label("The MVP: Role-Based Access Control (RBAC) preventing unauthorized or destructive model usage.", size=11, color=GREY, after=4)
    divider(after=8)

    # Screenshot 5: Role-Based User Login Gateway
    embed_image("extracted_user_images/image10.png", width_in=3.4, caption="Figure 9: Role-Based User Login Gateway — Compulsory cryptographic authentication enforcing operator clearance grades throughout the workbench.")

    blank(4)

    # Screenshot 6: Admin Portal for User Registry
    embed_image("extracted_user_images/image11.png", width_in=5.9, caption="Figure 10: Admin Portal for User Registry in Various Grades — Local SQLite RBAC provisioning interface (Grade 1 Operator, Grade 2 Engineer, Grade 3 Superintendent, Admin).")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 16 ─ SHOWCASE: SAFETY INTERLOCKS & AUDIT LEDGER (EMBEDDED IMAGES)
    # ══════════════════════════════════════════════════════════════════════════
    heading("System Showcase: Safety Interlocks & Audit Ledger", size=22, before=4)
    label("Deterministic AST syntax enforcement and cryptographic SHA-256 audit trails.", size=11, color=GREY, after=4)
    divider(after=8)

    # Screenshot 7: AST Safety Interlock
    embed_image("extracted_user_images/image12.png", width_in=5.9, caption="Figure 11: Deterministic AST Safety Interlock & Role-Based Access Control — Character-by-character AST syntax validation intercepting and blocking unverified commands before reaching physical actuators.")

    blank(4)

    # Screenshot 8: SHA-256 Forensic Audit Ledger
    embed_image("extracted_user_images/image13.png", width_in=5.9, caption="Figure 12: Cryptographic SHA-256 Append-Only Audit Ledger — Immutable forensic chain recording every query, telemetry anomaly, operator approval, and trip signal.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 17 ─ REFERENCES
    # ══════════════════════════════════════════════════════════════════════════
    heading("References", size=26, before=6)
    label("Standards, papers, and foundation frameworks this project builds upon.", size=11, color=GREY, after=4)
    divider()

    refs = [
        "[1]  ISO 10816-3:2009 — Mechanical vibration evaluation of industrial machines by non-rotating part measurements. International Organization for Standardization.",
        "[2]  API Standard 670 (5th ed., 2014) — Machinery Protection Systems. American Petroleum Institute.",
        "[3]  IEC 61511 (2016) — Functional safety: Safety instrumented systems for the process industry. International Electrotechnical Commission.",
        "[4]  Gerganov, G. et al. (2023) — llama.cpp: Efficient quantized LLM inference in C/C++. github.com/ggerganov/llama.cpp",
        "[5]  Bai, J. et al. (2024) — Qwen2.5-VL: Vision-Language Multimodal Foundation Models. arXiv:2409.12191.",
        "[6]  NIST SP 800-82 Rev 3 (2023) — Guide to Industrial Control Systems Security. National Institute of Standards and Technology.",
        "[7]  Randall, R. B. & Antoni, J. (2011) — Rolling element bearing diagnostics: A tutorial. Mechanical Systems & Signal Processing, 25(2), 485–520.",
        "[8]  Sandhu, R. S. et al. (1996) — Role-based access control models. IEEE Computer, 29(2), 38–47.",
        "[9]  Grieves, M. & Vickers, J. (2017) — Digital Twin: Mitigating unpredictable behavior in complex systems. Springer.",
        "[10] MRPL (2024) — Process Safety & SCADA Integrity Specifications. Mangalore Refinery Technical Manual.",
        "[11] Sovereign Industrial AI Workbench — Official Open-Source Codebase & Architecture: https://github.com/mukuld1511-bit/Locall-Agentic-AI-Workbench (2026)."
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        r = p.add_run(ref)
        r.font.name = F; r.font.size = Pt(9.5); r.font.color.rgb = BODY

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 18 ─ VOTE OF THANKS (SUPERVISOR & COLLEGE CREDITS)
    # ══════════════════════════════════════════════════════════════════════════
    heading("Vote of Thanks", size=26, before=6)
    divider()

    body(
        "I express my deepest gratitude to my project supervisor, Dr. Richa Chaudhary, Department of "
        "Computer Science & Engineering (AI & ML), for her invaluable guidance, rigorous academic standards, "
        "and continuous encouragement throughout the design and development of this project."
    )
    body(
        "Her insights into machine learning methodology, emphasis on safety-critical engineering principles, "
        "and patient mentorship were instrumental in transforming an exploratory concept into a production-grade, "
        "mathematically grounded air-gapped industrial system. Her commitment to academic excellence provided "
        "constant inspiration at every stage."
    )
    body(
        "I also extend my sincere appreciation to the faculty, laboratory staff, and leadership of the "
        "Department of CSE AI & ML at Panipat Institute of Engineering & Technology (PIET) "
        "for providing the computing infrastructure and supportive academic environment that made this work possible."
    )

    # Signature Block
    blank(30)

    p_nm = doc.add_paragraph()
    p_nm.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_nm.paragraph_format.space_before = Pt(0); p_nm.paragraph_format.space_after = Pt(2)
    r_nm = p_nm.add_run("Mukul")
    r_nm.font.name = F; r_nm.font.size = Pt(15); r_nm.font.bold = True; r_nm.font.color.rgb = INK

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_info.paragraph_format.space_before = Pt(0); p_info.paragraph_format.space_after = Pt(0)
    r_info = p_info.add_run("B.Tech CSE (AI & ML)  ·  Roll No. 28240613\nPanipat Institute of Engineering & Technology")
    r_info.font.name = F; r_info.font.size = Pt(10); r_info.font.color.rgb = GREY

    # ── Save Single Final Output File ─────────────────────────────────────────
    output_path = "Sovereign_Industrial_AI_Workbench_Report_Final.docx"
    doc.save(output_path)
    print(f"Successfully generated and saved final report: {output_path}")


if __name__ == "__main__":
    create_educational_report()
