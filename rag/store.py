"""Local Sovereign Knowledge Base Store with Document Sensitivity & Role Classification.

Maintains indexed technical refinery SOPs, inspection manuals, and equipment standards.
Each document record tracks:
- Unique doc_id
- Title & SOP identifier
- Full text content & segmented chunks
- Security classification: PUBLIC_INTERNAL, ROLE_RESTRICTED, CONFIDENTIAL, HIGHLY_CONFIDENTIAL
- Department ownership
- SHA-256 integrity hash
Zero cloud database dependencies: fully local.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeDocument:
    doc_id: str
    title: str
    code: str
    classification: str  # PUBLIC_INTERNAL, ROLE_RESTRICTED, CONFIDENTIAL, HIGHLY_CONFIDENTIAL
    department: str
    content: str
    version: str = "1.0"
    chunks: List[str] = field(default_factory=list)
    sha256: str = ""


# Default Industrial Knowledge Base (MRPL & General Industrial Refinery)
REFINERY_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "doc_id": "doc_sop_hex_042",
        "title": "Standard Operating Procedure: Shell & Tube Heat Exchanger Inspection & Maintenance",
        "code": "MRPL-SOP-HEX-042",
        "classification": "PUBLIC_INTERNAL",
        "department": "Mechanical Maintenance",
        "content": (
            "1. PURPOSE: Outlines routine and turnaround ultrasonic thickness inspections for crude preheat heat exchangers (E-1100 series).\n"
            "2. APPLICABILITY: All carbon steel and 1.25Cr-0.5Mo heat exchangers operating in CDU/VDU units.\n"
            "3. THRESHOLDS: Retirement thickness (T_min) is calculated per API 510 formula: T_min = P*R / (S*E - 0.6*P). For E-1102, T_min = 6.5 mm.\n"
            "4. ACTIONS BY REMAINING LIFE:\n"
            "   - Clause 4.1: If remaining life > 5.0 years: Normal turnaround inspection interval (48 months).\n"
            "   - Clause 4.2: If remaining life between 2.0 and 5.0 years: Mandatory ultrasonic scan within 24 months.\n"
            "   - Clause 4.3: If remaining life < 2.0 years: Immediate engineering review for shell replacement or re-rating.\n"
            "5. REPORTING: Formal approval notes must be signed by Section Superintendent before restart."
        ),
    },
    {
        "doc_id": "doc_sop_api_510",
        "title": "API 510 Pressure Vessel Inspection Code - Refinery Application Guide",
        "code": "MRPL-STD-API-510",
        "classification": "ROLE_RESTRICTED",
        "department": "Inspection & Reliability",
        "content": (
            "API 510 10th Edition Summary:\n"
            "Corrosion Rate Calculation: CR = (T_initial - T_actual) / Years_in_service.\n"
            "Remaining Life Calculation: RL = (T_actual - T_required) / CR.\n"
            "Maximum inspection interval shall not exceed one-half of the remaining life or 10 years, whichever is less.\n"
            "For sour service or crude service with H2S > 10 ppm, maximum interval is capped at 3 years."
        ),
    },
    {
        "doc_id": "doc_pid_safety_08",
        "title": "P&ID Safety Interlock Matrix & Emergency Depressurization Manual",
        "code": "MRPL-SOP-PID-08",
        "classification": "CONFIDENTIAL",
        "department": "Process Safety",
        "content": (
            "CONFIDENTIAL PROCESS SAFETY MATRIX:\n"
            "Interlock I-101: Tripping flow control valve FCV-201 to FAIL_CLOSED when temperature TI-305 exceeds 310 deg C.\n"
            "Interlock I-102: Opening pressure relief PSV-104A to flare header when pressure PI-102 exceeds 32 barg.\n"
            "Any bypass of Interlock I-101 requires written approval from Chief Operating Officer (Grade 3 clearance)."
        ),
    },
    {
        "doc_id": "doc_chem_catalyst_secret",
        "title": "Proprietary Hydrocracker Catalyst Regeneration Formulation & Run Conditions",
        "code": "MRPL-TECH-HC-99",
        "classification": "HIGHLY_CONFIDENTIAL",
        "department": "Technology & Catalysis",
        "content": (
            "RESTRICTED FORMULATION: Active Zeolite Y-modified platinum-promoted catalyst matrix.\n"
            "Operating space velocity: 1.25 LHSV at 395 deg C and 145 bar H2 partial pressure.\n"
            "UNAUTHORIZED ACCESS WILL TRIGGER AUTOMATIC SECURITY AUDIT AND LEGAL PROSECUTION."
        ),
    },
]


class KnowledgeStore:
    def __init__(self):
        self.documents: Dict[str, KnowledgeDocument] = {}
        self._load_seed_documents()

    def _load_seed_documents(self) -> None:
        for item in REFINERY_KNOWLEDGE_BASE:
            text = item["content"]
            sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            # Split into chunks
            raw_chunks = [c.strip() for c in text.split("\n") if c.strip()]
            doc = KnowledgeDocument(
                doc_id=item["doc_id"],
                title=item["title"],
                code=item["code"],
                classification=item["classification"],
                department=item["department"],
                content=text,
                chunks=raw_chunks,
                sha256=sha,
            )
            self.documents[doc.doc_id] = doc

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        return self.documents.get(doc_id)

    def list_all_documents(self) -> List[Dict[str, Any]]:
        return [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "code": d.code,
                "classification": d.classification,
                "department": d.department,
                "chunk_count": len(d.chunks),
                "sha256": d.sha256[:16] + "...",
            }
            for d in self.documents.values()
        ]


KNOWLEDGE_STORE = KnowledgeStore()
