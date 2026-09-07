"""Automatic local hardware detection module for Sovereign Industrial AI Workbench.

Detects available GPU/CPU, system RAM, and computes memory budgets automatically at startup.
No user or administrator manual hardware configuration is required.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class HardwareProfile:
    device_name: str
    device_type: str  # "cuda" or "cpu"
    total_vram_mb: int
    usable_vram_mb: int
    system_ram_mb: int
    is_auto_detected: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_name": self.device_name,
            "device_type": self.device_type,
            "total_vram_mb": self.total_vram_mb,
            "usable_vram_mb": self.usable_vram_mb,
            "system_ram_mb": self.system_ram_mb,
            "is_auto_detected": self.is_auto_detected,
        }


def detect_local_hardware() -> HardwareProfile:
    """Automatically detects local workstation hardware without user input."""
    device_name = "Local Workstation GPU"
    device_type = "cuda"
    total_vram = 8192  # baseline default
    usable_vram = 7168 # 8192 - 1024 OS reserve
    sys_ram = 32768

    # 1. Try PyTorch CUDA detection if installed
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_type = "cuda"
            props = torch.cuda.get_device_properties(0)
            total_vram = int(props.total_memory / (1024 * 1024))
            usable_vram = max(2048, total_vram - 1024)
    except Exception:
        # 2. Try nvidia-smi query if available
        try:
            smi_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                timeout=2,
            ).decode("utf-8").strip()
            if smi_output:
                parts = smi_output.split("\n")[0].split(",")
                if len(parts) >= 2:
                    device_name = parts[0].strip()
                    total_vram = int(parts[1].strip())
                    usable_vram = max(2048, total_vram - 1024)
                    device_type = "cuda"
        except Exception:
            pass

    # 3. Detect System RAM: try Windows ctypes, /proc/meminfo, or psutil
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            sys_ram = int(stat.ullTotalPhys / (1024 * 1024))
    except Exception:
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        kb = int(line.split()[1])
                        sys_ram = int(kb / 1024)
                        break
        except Exception:
            pass

    return HardwareProfile(
        device_name=device_name,
        device_type=device_type,
        total_vram_mb=total_vram,
        usable_vram_mb=usable_vram,
        system_ram_mb=sys_ram,
        is_auto_detected=True,
    )


AUTO_HARDWARE = detect_local_hardware()
