from __future__ import annotations

import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = PROJECT_ROOT / "data"
JOBS_DIR = DATA_DIR / "jobs"
SMOKE_DIR = DATA_DIR / "smoke"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
CONDA_ENV_DIR = RUNTIME_DIR / "conda-env"
TOTALSEG_HOME_DIR = RUNTIME_DIR / "totalsegmentator_home"
DEFAULT_DICOM_ROOT = Path(r"C:\Users\Max\code\work\TCIA_LIDC-IDRI\lidc_idri")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7865


def ensure_runtime_dirs() -> None:
    for path in (DATA_DIR, JOBS_DIR, SMOKE_DIR, RUNTIME_DIR, TOTALSEG_HOME_DIR):
        path.mkdir(parents=True, exist_ok=True)


def local_python() -> Path:
    return CONDA_ENV_DIR / ("python.exe" if os.name == "nt" else "bin/python")


def scripts_dir() -> Path:
    return CONDA_ENV_DIR / ("Scripts" if os.name == "nt" else "bin")


def local_totalsegmentator() -> Path | None:
    for name in ("TotalSegmentator.exe", "TotalSegmentator"):
        candidate = scripts_dir() / name
        if candidate.exists():
            return candidate
    found = shutil.which("TotalSegmentator")
    return Path(found) if found else None


def local_weight_downloader() -> Path | None:
    for name in ("totalseg_download_weights.exe", "totalseg_download_weights"):
        candidate = scripts_dir() / name
        if candidate.exists():
            return candidate
    found = shutil.which("totalseg_download_weights")
    return Path(found) if found else None


def runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env["TOTALSEG_HOME_DIR"] = str(TOTALSEG_HOME_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    return env
