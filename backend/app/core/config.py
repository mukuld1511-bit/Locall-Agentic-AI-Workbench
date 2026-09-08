"""Configuration module for Sovereign Industrial AI Workbench."""

import os
from dataclasses import dataclass
from pathlib import Path


from backend.app.core.hardware import AUTO_HARDWARE


@dataclass
class WorkbenchConfig:
    # Environment & Sovereign Constraints
    AIR_GAPPED: bool = True
    SECTOR: str = "refinery"
    ORGANIZATION: str = "Mangalore Refinery and Petrochemicals Limited (MRPL)"
    PROJECT_ID: str = "SIH26117"
    
    # Auto-detected Local Hardware Specifications (No manual configuration needed)
    TARGET_DEVICE: str = AUTO_HARDWARE.device_name
    VRAM_BUDGET_MB: int = AUTO_HARDWARE.total_vram_mb
    SYSTEM_RAM_BUDGET_MB: int = AUTO_HARDWARE.system_ram_mb
    VRAM_RESERVE_MB: int = 1024  # generic safety reserve
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    DOCS_STORAGE_DIR: Path = BASE_DIR / "data" / "documents"
    ARTIFACTS_DIR: Path = BASE_DIR / "data" / "artifacts"
    DATABASE_PATH: Path = BASE_DIR / "data" / "workbench.db"
    AUDIT_LOG_PATH: Path = BASE_DIR / "data" / "audit.log"
    CONFIGS_DIR: Path = BASE_DIR / "configs"
    
    # Security Policies
    DEFAULT_DENY: bool = True
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    SESSION_EXPIRY_HOURS: int = 8
    SANDBOX_NETWORK: bool = False
    SANDBOX_TIMEOUT_SECONDS: int = 10
    MAX_FILE_SIZE_MB: int = 25
    
    # Network / Serving
    LOCAL_HOST: str = "127.0.0.1"
    LOCAL_PORT: int = 8088
    ORGANIZER_ENDPOINT: str = "http://127.0.0.1:8080/v1"

    @classmethod
    def load_from_env(cls) -> "WorkbenchConfig":
        config = cls()
        config.AIR_GAPPED = os.getenv("AIR_GAPPED", "true").lower() == "true"
        config.SECTOR = os.getenv("SECTOR", "refinery")
        # Hardware is automatically detected, falling back to auto-detected hardware values
        config.TARGET_DEVICE = AUTO_HARDWARE.device_name
        config.VRAM_BUDGET_MB = AUTO_HARDWARE.total_vram_mb
        config.SYSTEM_RAM_BUDGET_MB = AUTO_HARDWARE.system_ram_mb
        
        # Ensure directories exist
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.DOCS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        return config


# Global singleton
GLOBAL_CONFIG = WorkbenchConfig.load_from_env()
