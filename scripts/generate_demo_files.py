import os
import math
import csv
from PIL import Image, ImageDraw, ImageFont

DATA_DIR = r"c:\AI\Locall-Agentic-AI-Workbench\data"
SHOWCASE_DIR = os.path.join(DATA_DIR, "demo_showcase")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(SHOWCASE_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ==============================================================================
# 1. P&ID BLUEPRINT: Crude Distillation Overhead Stabilizer Loop (CDU-301)
# ==============================================================================
def generate_pid_blueprint():
    width, height = 1920, 1080
    bg_color = (13, 20, 36) # Deep blueprint navy
    grid_color = (22, 34, 60)
    line_cyan = (38, 198, 218)
    line_yellow = (255, 213, 79)
    line_red = (255, 82, 82)
    text_white = (240, 246, 252)
    text_dim = (144, 164, 174)
    alert_bg = (60, 15, 20)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Grid background
    grid_step = 40
    for x in range(0, width, grid_step):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, grid_step):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Outer border & Title Block (ASME Y14 standard engineering border)
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(56, 90, 138), width=3)
    draw.rectangle([(25, 25), (width - 25, height - 25)], outline=(30, 50, 80), width=1)

    # Title block bottom right
    tb_w, tb_h = 560, 140
    tb_x1, tb_y1 = width - 20 - tb_w, height - 20 - tb_h
    draw.rectangle([(tb_x1, tb_y1), (width - 20, height - 20)], fill=(16, 28, 50), outline=(56, 90, 138), width=2)
    draw.line([(tb_x1, tb_y1 + 40), (width - 20, tb_y1 + 40)], fill=(56, 90, 138), width=1)
    draw.line([(tb_x1, tb_y1 + 80), (width - 20, tb_y1 + 80)], fill=(56, 90, 138), width=1)
    draw.line([(tb_x1 + 280, tb_y1 + 40), (tb_x1 + 280, height - 20)], fill=(56, 90, 138), width=1)

    draw.text((tb_x1 + 15, tb_y1 + 10), "SOVEREIGN APEX ENERGY - UNIT 300 CRUDE REFINERY", fill=text_white)
    draw.text((tb_x1 + 15, tb_y1 + 50), "DWG: PID-CDU-301-REV4  |  ZONE: 01-HAZARDOUS", fill=line_cyan)
    draw.text((tb_x1 + 15, tb_y1 + 95), "PROCESS FLUID: SOUR CRUDE / H2S VAPOR (18.4 BAR)", fill=text_dim)
    draw.text((tb_x1 + 295, tb_y1 + 50), "SAFETY INTEGRITY LEVEL: SIL-3", fill=line_yellow)
    draw.text((tb_x1 + 295, tb_y1 + 95), "INSPECTION CODE: ASME B31.3 / API 570", fill=text_dim)

    # Top Header Banner
    draw.rectangle([(30, 30), (750, 95)], fill=(18, 32, 58), outline=line_cyan, width=1)
    draw.text((45, 40), "PIPING & INSTRUMENTATION DIAGRAM (P&ID)", fill=(255, 255, 255))
    draw.text((45, 65), "CDU-301 OVERHEAD CONDENSER & CRITICAL REFLUX STABILIZER PUMP TRAIN", fill=line_cyan)

    # Helper function: Draw Process Line
    def draw_pipe(pts, color=line_cyan, w=4, label=""):
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=w)
        if label and len(pts) >= 2:
            mid_x = (pts[0][0] + pts[1][0]) // 2
            mid_y = (pts[0][1] + pts[1][1]) // 2
            draw.rectangle([(mid_x - 45, mid_y - 12), (mid_x + 45, mid_y + 12)], fill=(13, 20, 36))
            draw.text((mid_x - 40, mid_y - 8), label, fill=line_cyan)

    # Helper function: Draw Instrument Bubble (ISA 5.1 tag)
    def draw_inst_tag(center, tag, subtag, alert=False):
        cx, cy = center
        r = 26
        fill_col = alert_bg if alert else (16, 28, 52)
        border_col = line_red if alert else line_cyan
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=fill_col, outline=border_col, width=2)
        draw.line([(cx - r, cy), (cx + r, cy)], fill=border_col, width=1)
        draw.text((cx - 16, cy - 18), tag, fill=(255, 82, 82) if alert else text_white)
        draw.text((cx - 16, cy + 3), subtag, fill=(255, 82, 82) if alert else line_cyan)

    # Helper function: Draw Valve
    def draw_gate_valve(center, horiz=True, esd=False):
        cx, cy = center
        s = 14
        col = line_red if esd else text_white
        if horiz:
            draw.polygon([(cx - s, cy - s), (cx + s, cy + s), (cx - s, cy + s), (cx + s, cy - s)], outline=col, width=2)
            draw.line([(cx, cy), (cx, cy - 22)], fill=col, width=2)
            draw.ellipse([(cx - 7, cy - 26), (cx + 7, cy - 16)], outline=col, width=2)
        if esd:
            draw.rectangle([(cx - 18, cy - 45), (cx + 18, cy - 27)], fill=(120, 20, 20), outline=line_red, width=1)
            draw.text((cx - 14, cy - 42), "XV", fill=(255, 255, 255))

    # Helper function: Draw Centrifugal Pump
    def draw_centrifugal_pump(center, pump_id="P-301A"):
        cx, cy = center
        r = 45
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=line_cyan, width=3, fill=(20, 36, 65))
        draw.polygon([(cx - 20, cy - r), (cx + 45, cy), (cx - 20, cy + r)], outline=line_cyan, fill=(30, 56, 95), width=2)
        draw.text((cx - 28, cy - 7), pump_id, fill=(255, 255, 255))

    # 1. Distillation Column V-301 (Vessel on the Left)
    draw.rounded_rectangle([(100, 180), (320, 860)], radius=35, outline=line_cyan, width=4, fill=(18, 30, 54))
    draw.text((140, 210), "PRIMARY COLUMN", fill=text_dim)
    draw.text((160, 235), "V-301", fill=(255, 255, 255))
    draw.text((130, 260), "P: 18.2 BAR  T: 342°C", fill=line_yellow)
    # Internal Trays representation
    for y_tray in range(320, 820, 45):
        draw.line([(115, y_tray), (305, y_tray)], fill=(40, 65, 105), width=2)

    # 2. Overhead Vapor Line (from top of V-301 to Condenser E-301)
    pipe_overhead = [(210, 180), (210, 130), (520, 130), (520, 230)]
    draw_pipe(pipe_overhead, color=line_cyan, w=5, label="14\"-HC-30101")
    draw_inst_tag((360, 95), "PT", "301A")
    draw.line([(360, 121), (360, 130)], fill=line_cyan, width=1)
    draw_inst_tag((440, 95), "TT", "301A")
    draw.line([(440, 121), (440, 130)], fill=line_cyan, width=1)

    # 3. Heat Exchanger / Condenser E-301
    draw.rectangle([(480, 230), (680, 350)], outline=line_cyan, width=3, fill=(20, 40, 70))
    draw.ellipse([(450, 230), (510, 350)], outline=line_cyan, width=2)
    draw.ellipse([(650, 230), (710, 350)], outline=line_cyan, width=2)
    draw.text((530, 275), "CONDENSER", fill=text_dim)
    draw.text((545, 295), "E-301", fill=(255, 255, 255))

    # Cooling Water Supply / Return on E-301
    draw_pipe([(580, 170), (580, 230)], color=(66, 165, 245), w=3, label="CWS")
    draw_pipe([(630, 230), (630, 170)], color=(41, 121, 255), w=3, label="CWR")

    # 4. Condensate down to Reflux Drum V-302
    draw_pipe([(580, 350), (580, 440), (840, 440), (840, 490)], color=line_cyan, w=4, label="8\"-L-30102")

    # Reflux Drum V-302 (Horizontal Vessel)
    draw.rounded_rectangle([(780, 490), (1080, 620)], radius=30, outline=line_cyan, width=3, fill=(18, 30, 54))
    draw.text((880, 525), "REFLUX DRUM V-302", fill=(255, 255, 255))
    draw.text((880, 550), "BOOT LEVEL: 64.2%", fill=line_cyan)
    draw.text((880, 575), "HYDROCARBON / H2O SEPARATION", fill=text_dim)
    draw_inst_tag((950, 435), "LT", "302A")
    draw.line([(950, 461), (950, 490)], fill=line_cyan, width=1)

    # 5. Bottom Suction Lines to Pumps P-301A and P-301B (Dual Redundant)
    draw_pipe([(930, 620), (930, 720)], color=line_cyan, w=4)
    # Branch to Pump A
    draw_pipe([(930, 720), (750, 720), (750, 780)], color=line_cyan, w=4)
    draw_gate_valve((840, 720), horiz=True, esd=True)
    draw_centrifugal_pump((750, 830), "P-301A")

    # Branch to Pump B (Standby)
    draw_pipe([(930, 720), (1110, 720), (1110, 780)], color=line_cyan, w=4)
    draw_gate_valve((1020, 720), horiz=True, esd=False)
    draw_centrifugal_pump((1110, 830), "P-301B")

    # Discharge lines
    draw_pipe([(750, 875), (750, 940), (930, 940)], color=line_cyan, w=4)
    draw_pipe([(1110, 875), (1110, 940), (930, 940)], color=line_cyan, w=4)
    draw_gate_valve((750, 915), horiz=False)
    draw_gate_valve((1110, 915), horiz=False)

    # Recirculation back to V-301 Column (Reflux Loop)
    draw_pipe([(930, 940), (930, 980), (380, 980), (380, 350), (320, 350)], color=line_yellow, w=4, label="REFLUX RETURN")
    draw_inst_tag((380, 520), "FT", "301B")
    draw_gate_valve((380, 430), horiz=False)

    # 6. CRITICAL ANOMALY ALERT CALLOUT (Vibration / Cavitation on P-301A Discharge Elbow)
    alert_box = [(600, 780), (710, 780), (710, 880), (600, 880)]
    draw.rectangle([(550, 680), (720, 760)], fill=(50, 15, 20), outline=line_red, width=2)
    draw.text((560, 690), "[!] ASME ANOMALY DETECTED", fill=(255, 82, 82))
    draw.text((560, 712), "ELBOW CORROSION & 7.8 mm/s VIB", fill=(255, 200, 200))
    draw.text((560, 734), "T_wall: 2.1mm (T_min: 3.2mm) CRITICAL", fill=line_yellow)
    # Pointer line to pump P-301A
    draw.line([(680, 760), (730, 810)], fill=line_red, width=2)
    draw.ellipse([(725, 805), (735, 815)], fill=line_red)

    # 7. Pressure Safety Relief System (PSV-301A/B to Flare Header)
    draw_pipe([(1020, 490), (1020, 380), (1250, 380)], color=line_red, w=3, label="RELIEF LINE")
    draw_inst_tag((1120, 335), "PSV", "301A", alert=False)
    draw.line([(1120, 361), (1120, 380)], fill=line_red, width=1)
    # Flare Header Discharge
    draw_pipe([(1250, 380), (1250, 200), (1350, 200)], color=line_red, w=4, label="TO HIGH PRESSURE FLARE")
    draw.polygon([(1350, 190), (1380, 200), (1350, 210)], fill=line_red)

    # Save P&ID image
    pid_path_showcase = os.path.join(SHOWCASE_DIR, "pid_crude_cdu301_blueprint.png")
    pid_path_uploads = os.path.join(UPLOADS_DIR, "pid_crude_cdu301_blueprint.png")
    img.save(pid_path_showcase, "PNG")
    img.save(pid_path_uploads, "PNG")
    print(f"[OK] Generated P&ID Blueprint: {pid_path_showcase}")


# ==============================================================================
# 2. CORROSION & NDT ULTRASONIC SURVEY (ASME B31G & API 570) - CSV
# ==============================================================================
def generate_ndt_corrosion_survey():
    rows = [
        ["circuit_id", "equipment_tag", "service_fluid", "pipe_spec", "nominal_wt_mm", "min_allowable_tmin_mm", "measured_thickness_mm", "corrosion_rate_mpy", "inspection_method", "calc_remaining_life_yrs", "asme_b31g_status", "recommended_action"],
        ["CKT-301-01", "PUMP_301A_DISCH", "Heavy Sour Naphtha", "A106-B / 8\" Sch 40", 8.18, 3.20, 2.15, 18.4, "UT Phased Array", 0.0, "CRITICAL_FAILURE", "IMMEDIATE TRIP & B31G CLAMP REPAIR"],
        ["CKT-301-02", "PUMP_301B_DISCH", "Heavy Sour Naphtha", "A106-B / 8\" Sch 40", 8.18, 3.20, 6.42, 3.1, "UT Grid 100mm", 10.4, "ACCEPTABLE", "Routine monitoring at 24mo cycle"],
        ["CKT-301-03", "V-301_OVERHEAD", "H2S / Hydrocarbon Vapor", "A333-Gr6 / 14\" Sch 40", 11.13, 4.50, 8.20, 5.2, "Digital Radiography", 7.1, "MONITOR", "Inspect at next turnaround Q3 2027"],
        ["CKT-301-04", "E-301_COND_OUT", "Wet Sour Distillate", "316L SS / 8\" Sch 10S", 3.76, 1.80, 2.95, 1.8, "PEC Pulsed Eddy", 6.4, "ACCEPTABLE", "Baseline re-verify in 18mo"],
        ["CKT-301-05", "V-302_BOOT_DRAIN", "Sour Sour Water / H2S", "A106-B / 4\" Sch 80", 8.56, 3.80, 3.42, 22.8, "UT Spot Wall", 0.0, "RETIREMENT_REACHED", "Replace circuit spools with Inconel 625"],
        ["CKT-301-06", "C-102_SUCTION_KOD", "Hydrogen Rich Gas 45BAR", "A516-Gr70 / Vessel Shell", 28.50, 14.00, 24.10, 2.4, "UT Phased Array", 42.1, "ACCEPTABLE", "Clean integrity clearance"],
        ["CKT-301-07", "C-102_1ST_STAGE_OUT", "Hydrogen Gas 110BAR", "A335-P11 / 6\" Sch 160", 18.26, 8.90, 16.40, 1.9, "Time of Flight Diff (TOFD)", 39.5, "ACCEPTABLE", "Optimal condition"],
        ["CKT-301-08", "C-102_INTERCOOLER_TB", "Treated Demin Water", "Titanium Gr2 Tubes", 1.65, 0.70, 0.74, 4.2, "Internal Rotary Inspection (IRIS)", 0.9, "ACTION_REQUIRED", "Plug 14 leaking tubes during outage"],
        ["CKT-301-09", "F-201_FURNACE_COIL_5", "Atmospheric Residue 380C", "A335-P9 / 4\" Sch 120", 11.10, 4.20, 5.10, 8.7, "Laser Profilometry", 1.0, "HIGH_RISK", "Schedule decoking and smart pigging"],
        ["CKT-301-10", "T-401_CRUDE_CHARGE", "Desalted Crude Oil", "API 5L-X52 / 24\" Sch 20", 9.53, 3.50, 7.80, 2.5, "Magnetic Flux Leakage (MFL)", 17.2, "ACCEPTABLE", "Next pigging run in 36mo"],
        ["CKT-301-11", "R-101_HYDROTREATER_BED", "Hydrotreated Diesel / H2", "2.25Cr-1Mo-V Forged", 145.00, 95.00, 141.20, 0.6, "Automated PAUT + TOFD", 77.0, "ACCEPTABLE", "Zero high-temperature hydrogen attack (HTHA)"],
        ["CKT-301-12", "REFLUX_LINE_BENT_ELB", "Sour Naphtha 60C", "A106-B / 6\" LR 90 Elbow", 7.11, 2.80, 2.75, 14.5, "UT Phased Array B-Scan", 0.0, "CRITICAL_FAILURE", "Immediate composite sleeve or spool replacement"]
    ]

    csv_path_showcase = os.path.join(SHOWCASE_DIR, "refinery_corrosion_ndt_survey.csv")
    csv_path_uploads = os.path.join(UPLOADS_DIR, "refinery_corrosion_ndt_survey.csv")
    for target in [csv_path_showcase, csv_path_uploads]:
        with open(target, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    print(f"[OK] Generated NDT Survey CSV: {csv_path_showcase}")


# ==============================================================================
# 3. HIGH-SPEED VIBRATION & BEARING SPECTRAL FFT DATA - CSV
# ==============================================================================
def generate_vibration_telemetry_csv():
    # 200 samples showing normal baseline transitioning into severe BPFO (Ball Pass Frequency Outer) defect
    rows = [["timestamp_ms", "machine_id", "sensor_axis", "rpm", "overall_rms_velocity_mms", "peak_acceleration_g", "bearing_crest_factor", "1x_unbalance_amp", "2x_misalignment_amp", "bpfo_fault_energy", "iso_10816_zone", "alarm_state"]]
    
    base_time = 1726248000000
    for i in range(120):
        t = base_time + (i * 50)
        # First 60 samples: mild vibration; Last 60 samples: runaway cavitation + outer race bearing defect
        if i < 50:
            rpm = 2980 + (i % 5)
            rms = round(1.8 + 0.02 * (i % 7), 2)
            pk_g = round(0.45 + 0.01 * (i % 4), 2)
            cf = round(2.8 + 0.1 * (i % 3), 1)
            amp1x = round(0.42, 2)
            amp2x = round(0.18, 2)
            bpfo = 0.02
            zone = "ZONE_A_NEW"
            alarm = "NORMAL"
        elif i < 85:
            rpm = 2965 - (i % 8)
            rms = round(3.8 + 0.08 * (i - 50), 2)
            pk_g = round(1.2 + 0.05 * (i - 50), 2)
            cf = round(4.2 + 0.1 * (i - 50), 1)
            amp1x = round(0.95 + 0.02 * (i - 50), 2)
            amp2x = round(0.75 + 0.03 * (i - 50), 2)
            bpfo = round(0.15 + 0.02 * (i - 50), 2)
            zone = "ZONE_C_RESTRICTED"
            alarm = "WARNING_HIGH_VIB"
        else:
            rpm = 2890 - (i % 15)
            rms = round(7.9 + 0.12 * (i - 85), 2)
            pk_g = round(4.8 + 0.15 * (i - 85), 2)
            cf = round(7.8 + 0.2 * (i - 85), 1)
            amp1x = round(2.45 + 0.05 * (i - 85), 2)
            amp2x = round(3.10 + 0.04 * (i - 85), 2)
            bpfo = round(1.85 + 0.08 * (i - 85), 2)
            zone = "ZONE_D_CRITICAL_TRIP"
            alarm = "EMERGENCY_TRIP_REQUIRED"

        rows.append([t, "PUMP_301A", "RADIAL_DRIVE_END", rpm, rms, pk_g, cf, amp1x, amp2x, bpfo, zone, alarm])

    vib_path_showcase = os.path.join(SHOWCASE_DIR, "pump301a_vibration_accelerometer_stream.csv")
    vib_path_uploads = os.path.join(UPLOADS_DIR, "pump301a_vibration_accelerometer_stream.csv")
    for target in [vib_path_showcase, vib_path_uploads]:
        with open(target, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    print(f"[OK] Generated Vibration Telemetry CSV: {vib_path_showcase}")


# ==============================================================================
# 4. OSHA 1910 PSM ROOT CAUSE FORENSIC DOSSIER - MARKDOWN / TEXT REPORT
# ==============================================================================
def generate_forensic_incident_report():
    report_content = """================================================================================
CRITICAL SAFETY & PROCESS SAFETY MANAGEMENT (PSM) INCIDENT REPORT
REGULATORY AUDIT REF: OSHA 1910.119 / API RP 754 TIER-1 PREVENTION DOSSIER
================================================================================
FACILITY: SOVEREIGN CONTINUOUS CATALYTIC CRACKER & CDU-300 COMPLEX
UNIT CODE: CDU-301 / STABILIZER OVERHEAD TRAIN
EQUIPMENT TAG: PUMP-301A (SOUR NAPHTHA CHARGE PUMP)
DATE / TIME OF FLAGGED ANOMALY: 2026-09-13 22:14:08 UTC
CLASSIFICATION: TIER 1 PROCESS SAFETY EVENT PREVENTED VIA AUTONOMOUS TRIP
INVESTIGATION STATUS: ROOT CAUSE ANALYSIS (RCA) - SOVEREIGN AI WORKBENCH

1. EXECUTIVE SUMMARY & ANOMALY CHAIN
--------------------------------------------------------------------------------
During steady-state operation at 342°C and 18.2 bar column overhead pressure, 
primary charge pump P-301A registered progressive mechanical degradation over 
a 4-hour monitoring window:
  - Bearing Radial Vibration escalated from 1.8 mm/s to 8.4 mm/s RMS (ISO 10816 Zone D).
  - High-frequency ultrasonic demodulation revealed outer raceway spalling (BPFO = 108.4 Hz).
  - Phased Array Ultrasonic Testing (PAUT) along discharge bend CKT-301-01 indicated 
    severe localized thinning down to 2.15 mm against an ASME B31.3 T-min allowable of 3.20 mm.
  - Calculated burst pressure under Barlow equation reduced factor of safety to 0.94 (FAILURE IMMINENT).

2. QUANTITATIVE INTEGRITY METRICS
--------------------------------------------------------------------------------
Parametric Check        | Measured Value | Nominal Design | Threshold Limit | Compliance Standard
------------------------|----------------|----------------|-----------------|--------------------
Discharge Wall (T_act)  | 2.15 mm        | 8.18 mm        | 3.20 mm (T_min) | ASME B31.3 / B31G [FAIL]
Radial Vibration        | 8.42 mm/s RMS  | 1.80 mm/s RMS  | 4.50 mm/s RMS   | ISO 10816-3 Class II [FAIL]
Shaft Orbital Excursion | 82.4 microns   | 18.0 microns   | 45.0 microns    | API 610 12th Ed. [FAIL]
Bearing Temp (DE)       | 104.2 °C       | 68.0 °C        | 92.0 °C TRIP    | API 670 Machinery Prot. [FAIL]
SIL Safety Loop Status  | 1-oo-2 VOTED   | Redundant      | Auto Trip Ready | IEC 61508 / SIL-3 [ARMED]

3. AUTONOMOUS AIR-GAPPED MITIGATION EXECUTED
--------------------------------------------------------------------------------
Under the Sovereign Agentic Safety Matrix, the autonomous system executed the following:
  Step 1 [22:14:12] -> Initiated SIL-3 trip command to actuated motor contactor P-301A-ESD.
  Step 2 [22:14:14] -> Commanded auto-start and soft-ramp of 100% standby pump P-301B.
  Step 3 [22:14:18] -> Modulated XV-30101 emergency isolation valve to isolate compromised spool.
  Step 4 [22:14:22] -> Dispatched SAP Plant Maintenance Emergency Work Order (WO-99482)
                       with P&ID markup coordinates and pre-kitted mechanical seals.

4. REQUIRED ACTIONS FOR TURNAROUND SQUAD
--------------------------------------------------------------------------------
1. Isolate and lock-out/tag-out (LOTO) breaker 52-P301A at 4.16 kV Switchgear Bus 1B.
2. Cold-cut and extract 8" A106-GrB Schedule 40 elbow (Spool S-301-E04).
3. Install shop-fabricated 316L clad spool piece rated for 25 bar design pressure.
4. Replace SKF 7314 BECBM angular contact bearings on DE and NDE bearing housings.
5. Perform 100% radiographic weld testing before de-isolation.

ENGINEERING SIGN-OFF:
Lead Rotating Machinery Specialist: DR. A. RAMAN, PE (CHEVRON / SOVEREIGN AUDIT)
Chief Process Safety Officer: M. VERMA, CEng FIChemE
"""
    rep_path_showcase = os.path.join(SHOWCASE_DIR, "osha_psm_critical_incident_investigation.txt")
    rep_path_uploads = os.path.join(UPLOADS_DIR, "osha_psm_critical_incident_investigation.txt")
    for target in [rep_path_showcase, rep_path_uploads]:
        with open(target, mode="w", encoding="utf-8") as f:
            f.write(report_content)
    print(f"[OK] Generated Incident Report: {rep_path_showcase}")


if __name__ == "__main__":
    generate_pid_blueprint()
    generate_ndt_corrosion_survey()
    generate_vibration_telemetry_csv()
    generate_forensic_incident_report()
    print("\nALL DEMO SHOWCASE ARTIFACTS GENERATED SUCCESSFULLY!")
