"""Dynamic Sector Configuration Loader for Sovereign Industrial Operations.

Discovers and loads sector-specific configuration profiles from local JSON files.
Supports hot-loading of sector profiles for multi-industry deployment:
- Refinery (MRPL default)
- Manufacturing
- Utilities (power & water)
- Government (sovereign public sector)

Each sector defines:
- Equipment types and inspection standards
- Risk classification overrides
- Compliance frameworks (API 510, OISD, IS, etc.)
- Document templates and mandatory sections
- Default RBAC mappings
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CONFIGS_DIR = Path(__file__).resolve().parent


class SectorProfile:
    """Represents a loaded sector configuration profile."""

    def __init__(self, sector_id: str, config: Dict[str, Any]):
        self.sector_id = sector_id
        self.name = config.get("sector_name", sector_id)
        self.organization = config.get("organization", "Unknown")
        self.description = config.get("description", "")
        self.compliance_standards = config.get("compliance_standards", [])
        self.equipment_types = config.get("equipment_types", [])
        self.risk_overrides = config.get("risk_overrides", {})
        self.document_templates = config.get("document_templates", [])
        self.mandatory_sections = config.get("mandatory_sections", [])
        self.default_role_mappings = config.get("default_role_mappings", {})
        self.raw_config = config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sector_id": self.sector_id,
            "name": self.name,
            "organization": self.organization,
            "description": self.description,
            "compliance_standards": self.compliance_standards,
            "equipment_types": self.equipment_types,
            "document_templates": self.document_templates,
        }


class SectorLoader:
    """Discovers and loads sector profiles from the configs directory."""

    def __init__(self, configs_dir: Optional[Path] = None):
        self.configs_dir = configs_dir or CONFIGS_DIR
        self._profiles: Dict[str, SectorProfile] = {}
        self._discover_sectors()

    def _discover_sectors(self) -> None:
        """Auto-discovers sector config directories and loads their profiles."""
        if not self.configs_dir.exists():
            return

        for sector_dir in sorted(self.configs_dir.iterdir()):
            if not sector_dir.is_dir():
                continue
            config_file = sector_dir / "sector_config.json"
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    sector_id = sector_dir.name
                    self._profiles[sector_id] = SectorProfile(sector_id, config)
                except (json.JSONDecodeError, IOError):
                    pass

    def get_sector(self, sector_id: str) -> Optional[SectorProfile]:
        """Returns a loaded sector profile by ID."""
        return self._profiles.get(sector_id.lower())

    def list_sectors(self) -> List[Dict[str, Any]]:
        """Returns summary of all discovered sector profiles."""
        return [profile.to_dict() for profile in self._profiles.values()]

    def get_default_sector(self) -> SectorProfile:
        """Returns the refinery sector as default (MRPL primary)."""
        return self._profiles.get("refinery", SectorProfile("refinery", {
            "sector_name": "Petroleum Refinery",
            "organization": "MRPL",
        }))

    def get_compliance_standards(self, sector_id: str) -> List[str]:
        """Returns compliance standards for a given sector."""
        profile = self.get_sector(sector_id)
        return profile.compliance_standards if profile else []

    def get_equipment_types(self, sector_id: str) -> List[str]:
        """Returns equipment types for a given sector."""
        profile = self.get_sector(sector_id)
        return profile.equipment_types if profile else []


SECTOR_LOADER = SectorLoader()
