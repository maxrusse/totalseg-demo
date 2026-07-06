from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = PROJECT_ROOT / "data"
JOBS_DIR = DATA_DIR / "jobs"
SMOKE_DIR = DATA_DIR / "smoke"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
VENV_DIR = RUNTIME_DIR / "venv"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7865


def ensure_runtime_dirs() -> None:
    for path in (DATA_DIR, JOBS_DIR, SMOKE_DIR, RUNTIME_DIR):
        path.mkdir(parents=True, exist_ok=True)


def local_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return env
