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

    -- Indices for ultra-fast querying & joins
    CREATE INDEX idx_sensor_equipment ON sensor_readings(equipment_id);
    CREATE INDEX idx_sensor_timestamp ON sensor_readings(timestamp);
    CREATE INDEX idx_inspection_equipment ON inspections(equipment_id);
    CREATE INDEX idx_inspection_date ON inspections(inspection_date);
    CREATE INDEX idx_work_order_status ON work_orders(status);
    CREATE INDEX idx_work_order_priority ON work_orders(priority);
    CREATE INDEX idx_equipment_unit ON equipment(unit);
    CREATE INDEX idx_equipment_status ON equipment(status);
    CREATE INDEX idx_safety_severity ON safety_incidents(severity);
    """)

    # --- Seed Plant Units (8 Realistic Units across the Refinery Complex) ---
    units = [
        (1, "CDU-1", "Crude Distillation Unit I", "Sector A (North Complex)", "PESO-REF-2024-001", 150000, 2012, "Vikram Rao"),
        (2, "VDU-1", "Vacuum Distillation Unit I", "Sector A (North Complex)", "PESO-REF-2024-002", 90000, 2012, "Neha Sharma"),
        (3, "HGU-2", "Hydrogen Generation Unit II", "Sector B (Gas Hub)", "PESO-REF-2024-009", 70000, 2018, "Arun Kumar"),
        (4, "FCCU-1", "Fluidized Catalytic Cracker", "Sector C (Conversion)", "PESO-REF-2024-015", 110000, 2015, "Priya Menon"),
        (5, "UTL-1", "Central Utilities & High-Pressure Steam", "Sector D (Utilities)", "PESO-REF-2024-022", 50000, 2010, "Suresh Hegde"),
        (6, "DHDS-1", "Diesel Hydro-Desulfurization Unit", "Sector B (Gas Hub)", "PESO-REF-2024-028", 85000, 2019, "Rajesh Gowda"),
        (7, "SRU-1", "Sulfur Recovery Unit (Claus Process)", "Sector E (Environmental)", "PESO-REF-2024-033", 35000, 2016, "Kavita Shenoy"),
        (8, "ETP-1", "Effluent Treatment & Water Reclaim", "Sector E (Environmental)", "PESO-REF-2024-041", 40000, 2011, "Manoj Kumble"),
    ]
    cur.executemany(
        """
        INSERT INTO plant_units (unit_id, unit_code, unit_name, refinery_zone, operating_license, capacity_bpsd, commissioned_year, lead_engineer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        units
    )

    # --- Seed Employees & Inspectors (12 Certified Personnel) ---
    employees = [
        ("MRPL-001", "Arun Kumar", "Inspection & Integrity", "G3", "Senior Lead Inspector", "API 510 / API 570 / NDT L-III", 14, 1),
        ("MRPL-002", "Neha Sharma", "Process Engineering", "G2", "Process Engineer", "Energy Auditor / Chemical PE", 8, 1),
        ("MRPL-003", "Vikram Rao", "Mechanical Maintenance", "G3", "Superintendent", "CMRP Reliability Professional", 16, 1),
        ("MRPL-004", "Priya Menon", "HSE & Process Safety", "G2", "Safety Inspector", "NEBOSH Diploma / OSHA Certified", 9, 1),
        ("MRPL-005", "System Admin", "Digital Systems & SCADA", "ADMIN", "Administrator", "ISA/IEC 62443 Cybersecurity", 12, 1),
        ("MRPL-006", "Rajesh Gowda", "Electrical & Drives", "G2", "Electrical Engineer", "IEEE High-Voltage Certified", 7, 1),
        ("MRPL-007", "Kavita Shenoy", "Laboratory & Quality Assurance", "G1", "QA Chemist", "ISO 17025 Lead Auditor", 5, 1),
        ("MRPL-008", "Manoj Kumble", "Rotating Equipment", "G2", "Vibration Analyst", "ISO 18436 Vibration Cat III", 11, 1),
        ("MRPL-009", "Deepak Verma", "Instrumentation & Controls", "G2", "Lead Instrument Tech", "TUV Rheinland Functional Safety", 10, 1),
        ("MRPL-010", "Ananya Deshmukh", "Corrosion & Metallurgical", "G3", "Corrosion Specialist", "NACE Senior Internal Corrosion Tech", 13, 1),
        ("MRPL-011", "Rohan Sen", "Turnaround & Planning", "G2", "Turnaround Planner", "PMP / Primavera P6 Specialist", 6, 1),
        ("MRPL-012", "Suresh Hegde", "Utilities & Power Plant", "G3", "Chief Boiler Engineer", "National Board BOI Inspector", 19, 1),
    ]
    cur.executemany(
        """
        INSERT INTO employees (employee_code, name, department, grade, role, certification, years_experience, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        employees
    )

    # --- Seed Monitored Equipment (24 Realistic Refinery Tagged Assets) ---
    equipment = [
        # CDU-1
        ("E-1102", "Atmospheric Column Vessel", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 18.5, 380.0, 16.2, 362.0, "ASTM A516 Gr 70", "2012-04-15"),
        ("P-2201A", "Heavy Gas Oil Charge Pump", "Crude Distillation Unit I", 1, "OPERATIONAL", "HIGH", 35.0, 240.0, 31.5, 225.0, "ASTM A216 WCB", "2013-08-20"),
        ("P-2201B", "Heavy Gas Oil Pump (Standby)", "Crude Distillation Unit I", 1, "STANDBY", "HIGH", 35.0, 240.0, 0.0, 45.0, "ASTM A216 WCB", "2013-08-20"),
        ("HX-1209", "Crude Pre-Flash Condenser", "Crude Distillation Unit I", 1, "OPERATIONAL", "MEDIUM", 22.0, 210.0, 19.8, 195.0, "Titanium Gr 2 / Carbon Shell", "2016-10-02"),
        ("V-4407", "Emergency Shutdown Valve (ESD)", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 45.0, 410.0, 42.0, 395.0, "Stellite-Faced Super Duplex", "2017-09-14"),
        ("F-101", "Crude Atmospheric Radiant Furnace", "Crude Distillation Unit I", 1, "OPERATIONAL", "CRITICAL", 25.0, 850.0, 21.0, 780.0, "Centrifugally Cast HP-40 Nb", "2012-05-19"),

        # VDU-1
        ("VDU-T-01", "Vacuum Tower Flash Zone Separator", "Vacuum Distillation Unit I", 2, "OPERATIONAL", "CRITICAL", 4.5, 415.0, 3.8, 390.0, "AISI 317L Clad Carbon Steel", "2012-11-05"),
        ("P-2302A", "Vacuum Bottom Slurry Pump A", "Vacuum Distillation Unit I", 2, "OPERATIONAL", "HIGH", 28.0, 375.0, 24.5, 360.0, "High-Chrome Iron A532", "2013-03-10"),
        ("EJ-201", "3-Stage Steam Ejector Vacuum System", "Vacuum Distillation Unit I", 2, "OPERATIONAL", "HIGH", 12.0, 260.0, 10.4, 245.0, "Hastelloy C-276 Nozzles", "2014-06-22"),

        # HGU-2
        ("HX-3304", "Reactor Feed/Effluent Exchanger", "Hydrogen Generation Unit II", 3, "MAINTENANCE", "CRITICAL", 75.0, 480.0, 68.0, 465.0, "Alloy 800H / 1.25Cr-0.5Mo", "2018-02-10"),
        ("K-201A", "High-Pressure Hydrogen Recycled Compressor", "Hydrogen Generation Unit II", 3, "OPERATIONAL", "CRITICAL", 120.0, 160.0, 112.0, 148.0, "Forged Ni-Cr-Mo Steel", "2018-05-12"),
        ("RV-108", "Safety Pressure Relief Valve", "Hydrogen Generation Unit II", 3, "OPERATIONAL", "CRITICAL", 82.0, 450.0, 68.0, 420.0, "Inconel 625 Bellows", "2019-04-11"),
        ("R-301", "Steam Methane Reforming Catalyst Bed", "Hydrogen Generation Unit II", 3, "OPERATIONAL", "CRITICAL", 35.0, 920.0, 32.4, 885.0, "Micro-alloyed Incoloy 800HT", "2018-03-15"),

        # FCCU-1
        ("C-101", "FCC Catalyst Regenerator Column", "Fluidized Catalytic Cracker", 4, "OPERATIONAL", "CRITICAL", 8.5, 720.0, 7.8, 695.0, "SA-387 Gr 11 Cl 2 Refractory", "2015-06-30"),
        ("P-4102", "FCC Slurry Settler Bottom Pump", "Fluidized Catalytic Cracker", 4, "WARNING", "HIGH", 28.0, 360.0, 26.2, 345.0, "High-Chrome White Iron", "2015-11-28"),
        ("RG-402", "Flue Gas Power Recovery Expander", "Fluidized Catalytic Cracker", 4, "OPERATIONAL", "CRITICAL", 6.0, 680.0, 5.2, 650.0, "Waspaloy Rotor / Inconel 718", "2016-04-18"),

        # UTL-1
        ("B-901", "High-Pressure Utility Steam Boiler", "Central Utilities & High-Pressure Steam", 5, "OPERATIONAL", "HIGH", 85.0, 510.0, 82.5, 498.0, "ASME SA-213 T22", "2010-03-22"),
        ("E-5022", "Deaerator Pressure Storage Drum", "Central Utilities & High-Pressure Steam", 5, "OPERATIONAL", "HIGH", 14.0, 185.0, 12.2, 172.0, "SA-516 Gr 70 Normalised", "2011-07-09"),
        ("TG-101", "Turbine Generator Co-generation Set", "Central Utilities & High-Pressure Steam", 5, "OPERATIONAL", "CRITICAL", 90.0, 480.0, 84.0, 470.0, "Forged Cr-Mo-V Alloy", "2010-08-14"),

        # DHDS-1
        ("R-601", "Trickle-Bed Hydrotreater Reactor", "Diesel Hydro-Desulfurization Unit", 6, "OPERATIONAL", "CRITICAL", 95.0, 420.0, 88.0, 395.0, "2.25Cr-1Mo-0.25V Vanadium Mod", "2019-02-14"),
        ("C-602", "High-Pressure Stripper Tower", "Diesel Hydro-Desulfurization Unit", 6, "OPERATIONAL", "HIGH", 38.0, 260.0, 34.2, 245.0, "316L Stainless Clad", "2019-05-18"),

        # SRU-1
        ("WHB-701", "Waste Heat Claus Reaction Boiler", "Sulfur Recovery Unit (Claus Process)", 7, "OPERATIONAL", "HIGH", 42.0, 1350.0, 38.5, 1280.0, "Refractory Alumina / SA-516", "2016-08-20"),
        ("SR-702", "Liquid Sulfur Degassing Pit Tank", "Sulfur Recovery Unit (Claus Process)", 7, "OPERATIONAL", "MEDIUM", 2.0, 160.0, 1.2, 145.0, "Steam-Jacketed Carbon Steel", "2016-11-04"),

        # ETP-1
        ("DAF-801", "Dissolved Air Flotation Clarifier", "Effluent Treatment & Water Reclaim", 8, "OPERATIONAL", "MEDIUM", 6.0, 50.0, 4.8, 38.0, "Duplex 2205 Stainless", "2011-10-12"),
    ]
    cur.executemany(
        """
        INSERT INTO equipment (tag, equipment_type, unit, unit_id, status, criticality, design_pressure, design_temperature, operating_pressure, operating_temperature, metallurgy, installation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        equipment
    )

    # --- Seed Inspections (20 Detailed NDT Records across API 510/570/653 Standards) ---
    inspections = [
        (1, 1, "2026-08-12", "UT_ULTRASONIC", 17.8, 20.0, 0.18, 14.2, "PASS", "API 510", "Shell thickness stable, zero pitting detected across circumferential welds."),
        (2, 3, "2026-08-15", "VIBRATION_FFT", 8.9, 10.0, 0.31, 4.1, "REVIEW", "ISO 10816", "Peak harmonic at 2x running speed. Seal flush API Plan 53B pressure normal."),
        (3, 1, "2026-08-20", "VISUAL_NDT", 12.1, 12.5, 0.12, 10.2, "PASS", "API 570", "External insulation jacket intact, no corrosion under insulation (CUI)."),
        (4, 4, "2026-08-22", "EDDY_CURRENT", 15.4, 18.0, 0.42, 3.8, "WARNING", "ASME SEC V", "Tube wall loss at baffle plate #4 exceeds 20% limit. Hydrotest requested."),
        (5, 1, "2026-08-28", "FUNCTIONAL_STROKE", 22.0, 22.0, 0.05, 18.5, "PASS", "IEC 61511", "Full stroke closure verified within 2.8 seconds. SIL-3 ESD response verified."),
        (6, 4, "2026-09-02", "RADIOGRAPHIC_RT", 28.5, 30.0, 0.22, 12.0, "PASS", "API 510", "Plenum cyclone weld RT completed. Zero planar linear indications found."),
        (7, 3, "2026-09-05", "OIL_SPECTROMETRY", 14.2, 15.0, 0.15, 9.5, "PASS", "ASTM D5185", "Lube oil ISO code 16/14/11. Trace iron wear particles within allowable limits."),
        (8, 2, "2026-09-07", "UT_PHASED_ARRAY", 11.2, 14.0, 0.28, 6.4, "PASS", "API 510", "Flash zone cladding thickness verified. Nominal 3.0mm 317L clad remaining."),
        (9, 1, "2026-09-09", "MAGNETIC_PARTICLE", 19.5, 21.0, 0.11, 15.1, "PASS", "ASME SEC VIII", "Mud drum knuckle radii MT inspection complete. No thermal fatigue cracks."),
        (10, 4, "2026-09-10", "ACOUSTIC_EMISSION", 9.8, 10.0, 0.08, 22.0, "PASS", "API 653", "Atmospheric storage floor AE sensors indicate zero annular ring leakage."),
        (11, 1, "2026-09-11", "THERMOGRAPHY_FLIR", 14.0, 14.0, 0.19, 8.9, "PASS", "ISO 18434", "Pre-flash condenser skin temp balance confirmed with FLIR infrared scans."),
        (12, 10, "2026-09-12", "ULTRASONIC_AURA", 6.8, 9.5, 0.58, 2.3, "CRITICAL", "API 570", "Impeller casing cavitation erosion accelerated. High wear rate (>0.5mm/yr)!"),
        (13, 1, "2026-09-01", "POPPING_TEST", 18.0, 18.0, 0.06, 16.0, "PASS", "API 527", "Seat tightness confirmed at 90% set pressure. Pop tolerance within +/- 3%."),
        (14, 12, "2026-08-18", "ULTRASONIC_SHEAR", 24.2, 25.0, 0.14, 11.8, "PASS", "ASME SEC I", "Superheater outlet header weld scanning shows zero creep cavitation micro-voids."),
        (15, 10, "2026-09-03", "METALLOGRAPHY_REPLICA", 52.0, 54.0, 0.20, 13.5, "PASS", "API 941", "Nelson curve evaluation: In-situ replica confirms ferrite-pearlite stability without HTHA."),
        (16, 9, "2026-08-30", "BOROSCOPE_OPTICAL", 8.2, 8.5, 0.09, 14.0, "PASS", "API 612", "Steam turbine blade leading edges clean. Minor scale deposition removed."),
        (17, 10, "2026-09-04", "HYDROGEN_PERMEATION", 44.0, 45.0, 0.16, 15.2, "PASS", "NACE TM0284", "Barnacle cell hydrogen flux measured < 0.02 uA/cm2. HIC resistance validated."),
        (18, 4, "2026-08-25", "HARDNESS_TEST_EQUOTIP", 16.5, 17.0, 0.13, 12.4, "PASS", "NACE MR0175", "Weld heat-affected zone (HAZ) hardness verified below 22 HRC ceiling."),
        (19, 12, "2026-09-06", "CORROSION_COUPON", 12.8, 13.0, 0.24, 7.8, "REVIEW", "ASTM G4", "30-day desalter water return coupon logged 0.24 mm/yr. Filming amine dosage adjusted."),
        (20, 1, "2026-09-08", "INFRARED_PYROMETRY", 9.4, 9.8, 0.17, 9.1, "PASS", "API 560", "Fired heater radiant coil skin temp measured 812°C, well below design limit 860°C."),
    ]
    cur.executemany(
        """
        INSERT INTO inspections (equipment_id, inspector_id, inspection_date, inspection_type, thickness_mm, nominal_thickness_mm, corrosion_rate_mm_year, remaining_life_years, status, governing_code, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        inspections
    )

    # --- Seed Sensor Telemetry (48 historical time steps per equipment = 1152 records) ---
    base = datetime(2026, 9, 11, 0, 0, 0)
    readings = []
    for eq_id in range(1, 25):
        for h in range(48):
            ts = (base + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S")
            # Base ranges dependent on machine type
            is_high_temp = eq_id in (1, 6, 10, 13, 14, 16, 20, 22)
            temp = round(random.uniform(320.0, 480.0) if is_high_temp else random.uniform(45.0, 185.0), 2)
            pres = round(random.uniform(25.0, 115.0) if eq_id in (10, 11, 12, 17, 19, 20) else random.uniform(3.5, 32.0), 2)
            flow = round(random.uniform(180.0, 960.0), 2)
            vib = round(random.uniform(3.2, 5.8) if eq_id == 15 else random.uniform(0.5, 2.4), 2)
            eff = round(random.uniform(72.0, 84.0) if eq_id == 15 else random.uniform(88.5, 99.2), 2)
            readings.append((
                eq_id,
                ts,
                temp,
                pres,
                flow,
                vib,
                eff,
            ))
    cur.executemany(
        """
        INSERT INTO sensor_readings (equipment_id, timestamp, temperature_c, pressure_bar, flow_m3_h, vibration_mm_s, efficiency_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        readings
    )

    # --- Seed Work Orders (14 Realistic Industrial Work Orders) ---
    work_orders = [
        ("WO-2026-0911", 15, 3, "2026-09-11 08:30:00", "2026-09-15", "CRITICAL", "ROTATING", "Inspect cavitation wear on P-4102 bottom impeller casing per NDT finding.", "OPEN", 16.0),
        ("WO-2026-0902", 10, 2, "2026-09-02 10:00:00", "2026-09-18", "HIGH", "HEAT_TRANSFER", "Hydrotest & pull tube bundle on HX-3304 to isolate thinned baffle zones.", "IN_PROGRESS", 36.0),
        ("WO-2026-0829", 1, 1, "2026-08-29 14:15:00", "2026-09-20", "MEDIUM", "VESSEL", "Calibrate high-temperature differential pressure transmitter on E-1102.", "OPEN", 8.0),
        ("WO-2026-0820", 5, 4, "2026-08-20 09:00:00", "2026-08-25", "HIGH", "INSTRUMENTATION", "Annual stroke testing & pneumatic seat leakage test on Emergency Shutdown Valve.", "CLOSED", 6.0),
        ("WO-2026-0908", 11, 8, "2026-09-08 11:30:00", "2026-09-22", "MEDIUM", "COMPRESSOR", "Replace suction dampener seal ring and top-up synthetic ester lube.", "IN_PROGRESS", 12.0),
        ("WO-2026-0815", 17, 6, "2026-08-15 07:45:00", "2026-08-18", "LOW", "ELECTRICAL", "Inspect 6.6kV motor terminal box insulation resistance for B-901 draft fan.", "CLOSED", 4.0),
        ("WO-2026-0912", 12, 1, "2026-09-12 13:00:00", "2026-09-14", "CRITICAL", "SAFETY_VALVE", "Verify pop pressure on RV-108 bench test stand prior to unit restart.", "OPEN", 8.0),
        ("WO-2026-0904", 6, 2, "2026-09-04 16:00:00", "2026-09-30", "MEDIUM", "FIRED_HEATER", "Conduct optical pyrometry on radiant tube skin thermocouples on F-101.", "OPEN", 10.0),
        ("WO-2026-0910", 20, 10, "2026-09-10 11:00:00", "2026-09-25", "HIGH", "CATALYST", "Inspect gas distribution grid and catalyst bed differential pressure on R-601.", "OPEN", 24.0),
        ("WO-2026-0818", 22, 12, "2026-08-18 08:30:00", "2026-08-22", "LOW", "BOILER", "Perform acoustic soot blower cycle inspection on WHB-701 boiler banks.", "CLOSED", 6.0),
        ("WO-2026-0905", 16, 9, "2026-09-05 14:00:00", "2026-09-28", "MEDIUM", "TURBINE", "Calibrate speed governor electro-hydraulic valve actuator on RG-402 expander.", "IN_PROGRESS", 18.0),
        ("WO-2026-0824", 19, 6, "2026-08-24 10:30:00", "2026-08-27", "LOW", "ELECTRICAL", "Perform thermographic scan on 11kV busbar duct connections for TG-101.", "CLOSED", 4.0),
        ("WO-2026-0913", 8, 8, "2026-09-13 09:15:00", "2026-09-17", "HIGH", "ROTATING", "Inspect mechanical seal face wear and flush barrier fluid on P-2302A.", "OPEN", 14.0),
        ("WO-2026-0909", 24, 8, "2026-09-09 13:45:00", "2026-09-24", "LOW", "ENVIRONMENTAL", "Calibrate dissolved oxygen sensor probe and scraper drive speed on DAF-801.", "OPEN", 5.0),
    ]
    cur.executemany(
        """
        INSERT INTO work_orders (wo_number, equipment_id, assigned_to, created_at, due_date, priority, category, description, status, estimated_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        work_orders
    )

    # --- Seed Safety Incidents (8 Realistic refinery incident reports) ---
    incidents = [
        ("INC-2026-001", 15, "Fluidized Catalytic Cracker", "2026-09-10", "MEDIUM", "VIBRATION_TRIP", "High vibration alarm triggered on slurry bottom pump P-4102.", "Cavitation induced by high liquid viscosity during heavy feedstock swing.", "Adjusted inlet suction strainer and scheduled impeller inspection.", "RESOLVED", 3),
        ("INC-2026-002", 10, "Hydrogen Generation Unit II", "2026-08-27", "LOW", "MINOR_FLANGE_WEEP", "Trace hydrocarbon weeping observed at flange gasket G-14 during thermal ramp-up.", "Torque relaxation on B7 stud bolts after emergency shutdown cycle.", "Hot torqued flange bolts per ASME PCC-1 procedure. Leak ceased.", "CLOSED", 1),
        ("INC-2026-003", 5, "Crude Distillation Unit I", "2026-07-19", "HIGH", "ESD_SPURIOUS_ALERT", "ESD logic card flagged communication interruption with DCS field bus.", "Optical fiber bend radius exceeded in field junction cabinet J-104.", "Re-routed fiber optic patch cord with armored sleeve protection.", "CLOSED", 4),
        ("INC-2026-004", 6, "Crude Distillation Unit I", "2026-06-05", "MEDIUM", "FLAME_STABILITY_DRIFT", "Furnace F-101 burner #3 flame detector logged momentary signal loss.", "Secondary air register blockage from airborne seasonal dust accumulation.", "Cleaned burner plenum and re-aligned UV scanner optical lens.", "CLOSED", 2),
        ("INC-2026-005", 12, "Hydrogen Generation Unit II", "2026-09-12", "HIGH", "PRV_SEAT_LEAK", "Safety relief valve RV-108 acoustic monitor detected sub-critical weeping.", "Particulate scale deposition on nozzle seat ring during upstream surge.", "Scheduled bypass alignment and bench testing work order WO-2026-0912.", "INVESTIGATING", 10),
        ("INC-2026-006", 11, "Hydrogen Generation Unit II", "2026-05-14", "CRITICAL", "LUBE_OIL_PRESSURE_DROP", "Recycle compressor K-201A auxiliary lube pump tripped on low discharge head.", "Suction strainer differential pressure high due to resin particulate ingress.", "Auto-transferred to standby pump; replaced duplex filter element.", "CLOSED", 1),
        ("INC-2026-007", 22, "Sulfur Recovery Unit (Claus Process)", "2026-08-02", "LOW", "SO2_SENSOR_SPIKE", "Claus tail gas analyzer recorded brief SO2 rise to 180 ppm.", "Air-to-acid gas ratio controller hunting during feedstock density transient.", "Retuned PID loop derivative time constant in DCS console.", "CLOSED", 7),
        ("INC-2026-008", 20, "Diesel Hydro-Desulfurization Unit", "2026-09-07", "MEDIUM", "HYDROGEN_SULFIDE_ALARM", "H2S fixed electrochemical sensor logged 8.5 ppm in sampling shelter.", "Sample loop needle valve packing gland slightly loose.", "Isolated sample bomb, replaced PTFE packing, leak checked with soap solution.", "RESOLVED", 4),
    ]
    cur.executemany(
        """
        INSERT INTO safety_incidents (incident_code, equipment_id, unit, incident_date, severity, incident_type, description, root_cause, corrective_action, status, reported_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        incidents
    )

    # --- Seed Chemical & Process Fluid Inventory (10 Refinery Essential Chemicals) ---
    chemicals = [
        ("Amine MDEA (Methyl Diethanolamine)", "105-59-9", "Acid Gas Removal Unit", "TK-801A", 145.5, 40.0, "NFPA Class 1 Flammable / Skin Irritant", "SDS-MDEA-2026-V3", "2026-09-01"),
        ("Sulfiding Agent (DMDS)", "624-92-0", "Hydrotreater Catalyst Activation", "TK-804", 28.2, 10.0, "DOT Class 3 Flammable Liquid / Toxic", "SDS-DMDS-2025-V2", "2026-09-05"),
        ("Corrosion Inhibitor (Filming Amine)", "68603-42-9", "Crude Overhead System", "TK-812B", 18.4, 5.0, "Corrosive Liquid Class 8", "SDS-CI-441-2026", "2026-09-08"),
        ("Boiler Oxygen Scavenger (Carbohydrazide)", "497-18-7", "Central Utilities & High-Pressure Steam", "TK-902", 12.8, 3.0, "Hazardous Non-Toxic White Solid", "SDS-O2SCAV-99", "2026-08-25"),
        ("Demulsifier Polymer Compound", "9003-11-6", "Crude Desalter Unit", "TK-815", 34.0, 12.0, "Combustible Liquid Class III-A", "SDS-DEMULS-301", "2026-09-10"),
        ("Caustic Soda 50% (Sodium Hydroxide)", "1310-73-2", "Merox Treating Unit", "TK-820A", 82.5, 25.0, "Class 8 Corrosive Liquid", "SDS-NAOH-50-V4", "2026-09-02"),
        ("Sulfuric Acid 98% (H2SO4)", "7664-93-9", "Alkylation / Water Treatment", "TK-822", 64.0, 20.0, "Class 8 Corrosive / Water Reactive", "SDS-H2SO4-98-V2", "2026-09-06"),
        ("FCC Equilibrium Catalyst (Zeolite)", "1318-02-1", "Fluidized Catalytic Cracker", "SILO-401", 120.0, 30.0, "Particulate Dust / Inhalation Precaution", "SDS-ZEOLITE-2026", "2026-09-09"),
        ("Phosphoric Acid Neutralizer", "7664-38-2", "Utilities Water Pretreatment", "TK-905", 22.5, 6.0, "Class 8 Corrosive", "SDS-H3PO4-2025", "2026-08-28"),
        ("Biocide / Algaecide (Isothiazolinone)", "26172-55-4", "Cooling Water Towers", "DRUM-BAY-3", 8.6, 2.5, "Class 6.1 Toxic / Environmental Hazard", "SDS-BIOCIDE-77", "2026-09-04"),
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
