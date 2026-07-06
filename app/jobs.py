from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import JOBS_DIR, ensure_runtime_dirs


_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def status_path(job_id: str) -> Path:
    return job_dir(job_id) / "status.json"


def log_path(job_id: str) -> Path:
    return job_dir(job_id) / "log.txt"


def create_job(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_runtime_dirs()
    job_id = new_job_id()
    folder = job_dir(job_id)
    folder.mkdir(parents=True, exist_ok=False)
    job = {
        "id": job_id,
        "created_at": _now(),
        "updated_at": _now(),
        "state": "queued",
        "progress": 0,
        "stage": "Queued",
        "input": payload,
        "preprocess": {},
        "outputs": {},
        "error": "",
    }
    save_job(job)
    log_path(job_id).write_text("", encoding="utf-8")
    return job


def save_job(job: dict[str, Any]) -> None:
    with _LOCK:
        job["updated_at"] = _now()
        path = status_path(job["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name("status.tmp")
        tmp.write_text(json.dumps(job, indent=2), encoding="utf-8")
        tmp.replace(path)


def load_job(job_id: str) -> dict[str, Any]:
    path = status_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"Job not found: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    with _LOCK:
        job = load_job(job_id)
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(job.get(key), dict):
                merged = dict(job[key])
                merged.update(value)
                job[key] = merged
            else:
                job[key] = value
        save_job(job)
        return job


def append_log(job_id: str, line: str) -> None:
    text = line.rstrip("\r\n")
    with _LOCK:
        with log_path(job_id).open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def read_log(job_id: str, tail: int | None = None) -> str:
    path = log_path(job_id)
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if tail is None:
        return text
    lines = text.splitlines()
    return "\n".join(lines[-tail:])


def list_jobs() -> list[dict[str, Any]]:
    ensure_runtime_dirs()
    jobs: list[dict[str, Any]] = []
    for path in sorted(JOBS_DIR.glob("*/status.json"), reverse=True):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return jobs

