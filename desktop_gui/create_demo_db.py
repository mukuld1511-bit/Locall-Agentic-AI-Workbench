from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "demo_db" / "industrial_demo.db"


def create_db():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass

    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    cur.executescript("""
    PRAGMA foreign_keys = ON;

    -- 1. Plant Units / Refinery Sectors
    CREATE TABLE plant_units (
        unit_id INTEGER PRIMARY KEY,
        unit_code TEXT UNIQUE NOT NULL,
        unit_name TEXT NOT NULL,
        refinery_zone TEXT NOT NULL,
        operating_license TEXT NOT NULL,
        capacity_bpsd INTEGER NOT NULL,
        commissioned_year INTEGER NOT NULL,
        lead_engineer TEXT NOT NULL
    );

    -- 2. Employees & Certifications
    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        employee_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        grade TEXT NOT NULL,
        role TEXT NOT NULL,
        certification TEXT,
        years_experience INTEGER DEFAULT 5,
        active INTEGER NOT NULL DEFAULT 1
    );

    -- 3. Monitored Equipment Registry
    CREATE TABLE equipment (
        equipment_id INTEGER PRIMARY KEY,
        tag TEXT UNIQUE NOT NULL,
        equipment_type TEXT NOT NULL,
        unit TEXT NOT NULL,
        unit_id INTEGER,
        status TEXT NOT NULL,
        criticality TEXT NOT NULL DEFAULT 'HIGH',
        design_pressure REAL,
        design_temperature REAL,
        operating_pressure REAL,
        operating_temperature REAL,
        metallurgy TEXT NOT NULL DEFAULT 'Carbon Steel A106-B',
        installation_date TEXT NOT NULL,
        FOREIGN KEY(unit_id) REFERENCES plant_units(unit_id)
    );

    -- 4. Ultrasonic & Non-Destructive Inspections (NDT)
    CREATE TABLE inspections (
        inspection_id INTEGER PRIMARY KEY,
        equipment_id INTEGER NOT NULL,
        inspector_id INTEGER NOT NULL,
        inspection_date TEXT NOT NULL,
        inspection_type TEXT NOT NULL,
        thickness_mm REAL,
        nominal_thickness_mm REAL,
        corrosion_rate_mm_year REAL,
        remaining_life_years REAL,
        status TEXT NOT NULL,
        governing_code TEXT NOT NULL DEFAULT 'API 510',
        notes TEXT,
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id),
        FOREIGN KEY(inspector_id) REFERENCES employees(employee_id)
    );

    -- 5. Real-Time Telemetry & Sensor Readings
    CREATE TABLE sensor_readings (
        reading_id INTEGER PRIMARY KEY,
        equipment_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        temperature_c REAL,
        pressure_bar REAL,
        flow_m3_h REAL,
        vibration_mm_s REAL,
        efficiency_pct REAL,
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id)
    );

    -- 6. Corrective & Preventative Work Orders
    CREATE TABLE work_orders (
        work_order_id INTEGER PRIMARY KEY,
        wo_number TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        assigned_to INTEGER,
        created_at TEXT NOT NULL,
        due_date TEXT NOT NULL,
        priority TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'MECHANICAL',
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        estimated_hours REAL,
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id),
        FOREIGN KEY(assigned_to) REFERENCES employees(employee_id)
    );

    -- 7. Safety Incidents & Near-Miss Log
    CREATE TABLE safety_incidents (
        incident_id INTEGER PRIMARY KEY,
        incident_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER,
        unit TEXT NOT NULL,
        incident_date TEXT NOT NULL,
        severity TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
        incident_type TEXT NOT NULL,
        description TEXT NOT NULL,
        root_cause TEXT,
        corrective_action TEXT,
        status TEXT NOT NULL DEFAULT 'CLOSED',
        reported_by INTEGER,
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id),
        FOREIGN KEY(reported_by) REFERENCES employees(employee_id)
    );

    -- 8. Chemical & Process Fluid Inventory
    CREATE TABLE chemical_inventory (
        chemical_id INTEGER PRIMARY KEY,
        chemical_name TEXT NOT NULL,
        cas_number TEXT NOT NULL,
        unit TEXT NOT NULL,
        storage_tank TEXT NOT NULL,
        quantity_metric_tons REAL NOT NULL,
        reorder_threshold_tons REAL NOT NULL,
        hazard_classification TEXT NOT NULL,
        sds_reference TEXT NOT NULL,
        last_inspected TEXT NOT NULL
    );

    -- Indices for fast querying
    CREATE INDEX idx_sensor_equipment ON sensor_readings(equipment_id);
    CREATE INDEX idx_inspection_equipment ON inspections(equipment_id);
    CREATE INDEX idx_work_order_status ON work_orders(status);
    CREATE INDEX idx_equipment_unit ON equipment(unit);
    CREATE INDEX idx_safety_severity ON safety_incidents(severity);
    """)

    # --- Seed Plant Units ---
    units = [
        (1, "CDU-1", "Crude Distillation Unit I", "Sector A (North Complex)", "PESO-REF-2024-001", 150000, 2012, "Vikram Rao"),
        (2, "VDU-1", "Vacuum Distillation Unit I", "Sector A (North Complex)", "PESO-REF-2024-002", 90000, 2012, "Neha Sharma"),
        (3, "HGU-2", "Hydrogen Generation Unit II", "Sector B (Gas Hub)", "PESO-REF-2024-009", 70000, 2018, "Arun Kumar"),
        (4, "FCCU-1", "Fluidized Catalytic Cracker", "Sector C (Conversion)", "PESO-REF-2024-015", 110000, 2015, "Priya Menon"),
        (5, "UTL-1", "Central Utilities & Steam Boiler", "Sector D (Utilities)", "PESO-REF-2024-022", 50000, 2010, "Suresh Hegde"),
    ]
    cur.executemany(
        """
        INSERT INTO plant_units (unit_id, unit_code, unit_name, refinery_zone, operating_license, capacity_bpsd, commissioned_year, lead_engineer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        units
    )

    # --- Seed Employees ---
    employees = [
        ("MRPL-001", "Arun Kumar", "Inspection & Integrity", "G3", "Senior Lead Inspector", "API 510 / API 570 Certified", 14, 1),
        ("MRPL-002", "Neha Sharma", "Process Engineering", "G2", "Process Engineer", "Energy Auditor / Chemical PE", 8, 1),
        ("MRPL-003", "Vikram Rao", "Mechanical Maintenance", "G3", "Superintendent", "CMRP Reliability Professional", 16, 1),
        ("MRPL-004", "Priya Menon", "HSE & Process Safety", "G2", "Safety Inspector", "NEBOSH Diploma / OSHA Certified", 9, 1),
        ("MRPL-005", "System Admin", "Digital Systems & SCADA", "ADMIN", "Administrator", "ISA/IEC 62443 Cybersecurity", 12, 1),
        ("MRPL-006", "Rajesh Gowda", "Electrical & Drives", "G2", "Electrical Engineer", "IEEE High-Voltage Certified", 7, 1),
        ("MRPL-007", "Kavita Shenoy", "Laboratory & Quality Assurance", "G1", "QA Chemist", "ISO 17025 Lead Auditor", 5, 1),
        ("MRPL-008", "Manoj Kumble", "Rotating Equipment", "G2", "Vibration Analyst", "ISO 18436 Vibration Cat III", 11, 1),
    ]
    cur.executemany(
        """
        INSERT INTO employees (employee_code, name, department, grade, role, certification, years_experience, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        employees
    )

    # --- Seed Equipment (16 realistic refinery units) ---
    equipment = [
        ("E-1102", "Atmospheric Column Vessel", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 18.5, 380.0, 16.2, 362.0, "ASTM A516 Gr 70", "2012-04-15"),
        ("P-2201A", "Heavy Gas Oil Charge Pump", "Crude Distillation Unit I", 1, "OPERATIONAL", "HIGH", 35.0, 240.0, 31.5, 225.0, "ASTM A216 WCB", "2013-08-20"),
        ("P-2201B", "Heavy Gas Oil Pump (Standby)", "Crude Distillation Unit I", 1, "STANDBY", "HIGH", 35.0, 240.0, 0.0, 45.0, "ASTM A216 WCB", "2013-08-20"),
        ("HX-3304", "Reactor Feed/Effluent Exchanger", "Hydrogen Generation Unit II", 3, "MAINTENANCE", "CRITICAL", 75.0, 480.0, 68.0, 465.0, "Alloy 800H / 1.25Cr-0.5Mo", "2018-02-10"),
        ("V-4407", "Emergency Shutdown Valve (ESD)", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 45.0, 410.0, 42.0, 395.0, "Stellite-Faced Super Duplex", "2017-09-14"),
        ("C-101", "FCC Catalyst Regenerator Column", "Fluidized Catalytic Cracker", 4, "OPERATIONAL", "CRITICAL", 8.5, 720.0, 7.8, 695.0, "SA-387 Gr 11 Cl 2 Refractory", "2015-06-30"),
        ("K-201A", "High-Pressure Hydrogen Recycled Compressor", "Hydrogen Generation Unit II", 3, "OPERATIONAL", "CRITICAL", 120.0, 160.0, 112.0, 148.0, "Forged Ni-Cr-Mo Steel", "2018-05-12"),
        ("VDU-T-01", "Vacuum Tower Flash Zone Separator", "Vacuum Distillation Unit I", 2, "OPERATIONAL", "CRITICAL", 4.5, 415.0, 3.8, 390.0, "AISI 317L Clad Carbon Steel", "2012-11-05"),
        ("B-901", "High-Pressure Utility Steam Boiler", "Central Utilities & Steam Boiler", 5, "OPERATIONAL", "HIGH", 85.0, 510.0, 82.5, 498.0, "ASME SA-213 T22", "2010-03-22"),
        ("T-501", "Motor Spirit Storage Tank", "Sector D (Utilities)", 5, "OPERATIONAL", "MEDIUM", 0.05, 50.0, 0.02, 32.0, "API 650 Welded Steel", "2014-01-18"),
        ("HX-1209", "Crude Pre-Flash Condenser", "Crude Distillation Unit I", 1, "OPERATIONAL", "MEDIUM", 22.0, 210.0, 19.8, 195.0, "Titanium Gr 2 / Carbon Shell", "2016-10-02"),
        ("P-4102", "FCC Slurry Settler Bottom Pump", "Fluidized Catalytic Cracker", 4, "WARNING", "HIGH", 28.0, 360.0, 26.2, 345.0, "High-Chrome White Iron", "2015-11-28"),
        ("RV-108", "Safety Pressure Relief Valve", "Hydrogen Generation Unit II", 3, "OPERATIONAL", "CRITICAL", 82.0, 450.0, 68.0, 420.0, "Inconel 625 Bellows", "2019-04-11"),
        ("E-5022", "Deaerator Pressure Storage Drum", "Central Utilities & Steam Boiler", 5, "OPERATIONAL", "HIGH", 14.0, 185.0, 12.2, 172.0, "SA-516 Gr 70 Normalised", "2011-07-09"),
        ("V-9901", "Fuel Gas Knockout Drum", "Sector A (North Complex)", 1, "OPERATIONAL", "MEDIUM", 16.0, 120.0, 14.5, 95.0, "ASTM A106 Gr B", "2013-04-18"),
        ("F-101", "Crude Atmospheric Radiant Furnace", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 25.0, 850.0, 21.0, 780.0, "Centrifugally Cast HP-40 Nb", "2012-05-19"),
    ]
    cur.executemany(
        """
        INSERT INTO equipment (tag, equipment_type, unit, unit_id, status, criticality, design_pressure, design_temperature, operating_pressure, operating_temperature, metallurgy, installation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        equipment
    )

    # --- Seed Inspections (NDT Records with API standards) ---
    inspections = [
        (1, 1, "2026-08-12", "UT_ULTRASONIC", 17.8, 20.0, 0.18, 14.2, "PASS", "API 510", "Shell thickness stable, zero pitting detected across welds."),
        (2, 3, "2026-08-15", "VIBRATION_FFT", 8.9, 10.0, 0.31, 4.1, "REVIEW", "ISO 10816", "Peak harmonic at 2x running speed. Seal flush pressure normal."),
        (3, 1, "2026-08-20", "VISUAL_NDT", 12.1, 12.5, 0.12, 10.2, "PASS", "API 570", "External insulation jacket intact, no corrosion under insulation (CUI)."),
        (4, 4, "2026-08-22", "EDDY_CURRENT", 15.4, 18.0, 0.42, 3.8, "WARNING", "ASME SEC V", "Tube wall loss at baffle plate #4 exceeds 20% limit. Action requested."),
        (5, 1, "2026-08-28", "FUNCTIONAL_STROKE", 22.0, 22.0, 0.05, 18.5, "PASS", "IEC 61511", "Full stroke closure within 2.8 seconds. SIL-3 response verified."),
        (6, 4, "2026-09-02", "RADIOGRAPHIC_RT", 28.5, 30.0, 0.22, 12.0, "PASS", "API 510", "Regenerator plenum weld RT completed. Zero linear indications."),
        (7, 3, "2026-09-05", "OIL_SPECTROMETRY", 14.2, 15.0, 0.15, 9.5, "PASS", "ASTM D5185", "Lube oil ISO code 16/14/11. Trace iron within acceptable limits."),
        (8, 2, "2026-09-07", "UT_PHASED_ARRAY", 11.2, 14.0, 0.28, 6.4, "PASS", "API 510", "Flash zone cladding thickness verified. Nominal 3.0mm 317L clad remaining."),
        (9, 1, "2026-09-09", "MAGNETIC_PARTICLE", 19.5, 21.0, 0.11, 15.1, "PASS", "ASME SEC VIII", "Mud drum knuckle radii MT complete. No stress-cracking."),
        (10, 4, "2026-09-10", "ACOUSTIC_EMISSION", 9.8, 10.0, 0.08, 22.0, "PASS", "API 653", "Atmospheric storage floor AE test indicates no bottom plate leakage."),
        (11, 1, "2026-09-11", "THERMOGRAPHY_FLIR", 14.0, 14.0, 0.19, 8.9, "PASS", "ISO 18434", "Pre-flash heat flux balance verified with FLIR infrared imaging."),
        (12, 3, "2026-09-12", "ULTRASONIC_AURA", 6.8, 9.5, 0.58, 2.3, "CRITICAL", "API 570", "Impeller casing cavitation erosion accelerated. High wear rate!"),
    ]
    cur.executemany(
        """
        INSERT INTO inspections (equipment_id, inspector_id, inspection_date, inspection_type, thickness_mm, nominal_thickness_mm, corrosion_rate_mm_year, remaining_life_years, status, governing_code, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        inspections
    )

    # --- Seed Sensor Telemetry (48 historical time steps per equipment) ---
    base = datetime(2026, 9, 11, 0, 0, 0)
    readings = []
    for eq_id in range(1, 17):
        for h in range(48):
            ts = (base + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S")
            readings.append((
                eq_id,
                ts,
                round(random.uniform(95.0, 365.0), 2),
                round(random.uniform(3.5, 42.0), 2),
                round(random.uniform(120.0, 950.0), 2),
                round(random.uniform(0.4, 4.2), 2),
                round(random.uniform(78.5, 99.1), 2),
            ))
    cur.executemany(
        """
        INSERT INTO sensor_readings (equipment_id, timestamp, temperature_c, pressure_bar, flow_m3_h, vibration_mm_s, efficiency_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        readings
    )

    # --- Seed Work Orders ---
    work_orders = [
        ("WO-2026-0911", 12, 3, "2026-09-11 08:30:00", "2026-09-15", "CRITICAL", "ROTATING", "Inspect cavitation wear on P-4102 bottom impeller casing per NDT finding.", "OPEN", 16.0),
        ("WO-2026-0902", 4, 2, "2026-09-02 10:00:00", "2026-09-18", "HIGH", "HEAT_TRANSFER", "Hydrotest & pull tube bundle on HX-3304 to isolate thinned baffle zones.", "IN_PROGRESS", 36.0),
        ("WO-2026-0829", 1, 1, "2026-08-29 14:15:00", "2026-09-20", "MEDIUM", "VESSEL", "Calibrate high-temperature differential pressure transmitter on E-1102.", "OPEN", 8.0),
        ("WO-2026-0820", 5, 4, "2026-08-20 09:00:00", "2026-08-25", "HIGH", "INSTRUMENTATION", "Annual stroke testing & pneumatic seat leakage test on Emergency Shutdown Valve.", "CLOSED", 6.0),
        ("WO-2026-0908", 7, 8, "2026-09-08 11:30:00", "2026-09-22", "MEDIUM", "COMPRESSOR", "Replace suction dampener seal ring and top-up synthetic ester lube.", "IN_PROGRESS", 12.0),
        ("WO-2026-0815", 9, 6, "2026-08-15 07:45:00", "2026-08-18", "LOW", "ELECTRICAL", "Inspect 6.6kV motor terminal box insulation resistance for B-901 draft fan.", "CLOSED", 4.0),
        ("WO-2026-0912", 13, 1, "2026-09-12 13:00:00", "2026-09-14", "CRITICAL", "SAFETY_VALVE", "Verify pop pressure on RV-108 bench test stand prior to unit restart.", "OPEN", 8.0),
        ("WO-2026-0904", 16, 2, "2026-09-04 16:00:00", "2026-09-30", "MEDIUM", "FIRED_HEATER", "Conduct optical pyrometry on radiant tube skin thermocouples on F-101.", "OPEN", 10.0),
    ]
    cur.executemany(
        """
        INSERT INTO work_orders (wo_number, equipment_id, assigned_to, created_at, due_date, priority, category, description, status, estimated_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        work_orders
    )

    # --- Seed Safety Incidents ---
    incidents = [
        ("INC-2026-001", 12, "Fluidized Catalytic Cracker", "2026-09-10", "MEDIUM", "VIBRATION_TRIP", "High vibration alarm triggered on slurry bottom pump P-4102.", "Cavitation induced by high liquid viscosity during startup.", "Adjusted inlet suction strainer and scheduled impeller inspection.", "RESOLVED", 3),
        ("INC-2026-002", 4, "Hydrogen Generation Unit II", "2026-08-27", "LOW", "MINOR_FLANGE_WEEP", "Trace hydrocarbon weeping observed at flange gasket G-14 during thermal ramp-up.", "Torque relaxation on B7 stud bolts after shutdown.", "Hot torqued flange bolts per ASME PCC-1 procedure. Leak ceased.", "CLOSED", 1),
        ("INC-2026-003", 5, "Crude Distillation Unit I", "2026-07-19", "HIGH", "ESD_SPURIOUS_ALERT", "ESD logic card flagged communication interruption with DCS field bus.", "Optical fiber bend radius exceeded in field junction cabinet.", "Re-routed fiber optic patch cord with armored sleeve.", "CLOSED", 4),
        ("INC-2026-004", 16, "Crude Distillation Unit I", "2026-06-05", "MEDIUM", "FLAME_STABILITY_DRIFT", "Furnace F-101 burner #3 flame detector logged momentary signal loss.", "Secondary air register blockage from airborne dust.", "Cleaned burner plenum and re-aligned UV scanner optics.", "CLOSED", 2),
    ]
    cur.executemany(
        """
        INSERT INTO safety_incidents (incident_code, equipment_id, unit, incident_date, severity, incident_type, description, root_cause, corrective_action, status, reported_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        incidents
    )

    # --- Seed Chemical Inventory ---
    chemicals = [
        ("Amine MDEA (Methyl Diethanolamine)", "105-59-9", "Acid Gas Removal Unit", "TK-801A", 145.5, 40.0, "NFPA Class 1 Flammable / Skin Irritant", "SDS-MDEA-2026-V3", "2026-09-01"),
        ("Sulfiding Agent (DMDS)", "624-92-0", "Hydrotreater Catalyst Activation", "TK-804", 28.2, 10.0, "DOT Class 3 Flammable Liquid / Toxic", "SDS-DMDS-2025-V2", "2026-09-05"),
        ("Corrosion Inhibitor (Filming Amine)", "68603-42-9", "Crude Overhead System", "TK-812B", 18.4, 5.0, "Corrosive Liquid Class 8", "SDS-CI-441-2026", "2026-09-08"),
        ("Boiler Oxygen Scavenger (Carbohydrazide)", "497-18-7", "Central Utilities & Steam Boiler", "TK-902", 12.8, 3.0, "Hazardous Non-Toxic White Solid", "SDS-O2SCAV-99", "2026-08-25"),
        ("Demulsifier Polymer Compound", "9003-11-6", "Crude Desalter Unit", "TK-815", 34.0, 12.0, "Combustible Liquid Class III-A", "SDS-DEMULS-301", "2026-09-10"),
    ]
    cur.executemany(
        """
        INSERT INTO chemical_inventory (chemical_name, cas_number, unit, storage_tank, quantity_metric_tons, reorder_threshold_tons, hazard_classification, sds_reference, last_inspected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        chemicals
    )

    db.commit()
    db.close()
    print("ENRICHED INDUSTRIAL DEMO DATABASE CREATED AT:", DB_PATH)


if __name__ == "__main__":
    create_db()
