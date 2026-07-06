from __future__ import annotations

import io
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import (
    DEFAULT_DICOM_ROOT,
    STATIC_DIR,
    local_python,
    local_totalsegmentator,
    ensure_runtime_dirs,
)
from .dicom_io import scan_dicom_series
from .jobs import create_job, list_jobs, load_job, read_log
from .segmentation import run_segmentation_job
from .tasks import all_tasks, task_exists
from .viewer import ct_slice_png, mask_slice_png, viewer_metadata


class SegmentRequest(BaseModel):
    dicom_path: str
    task: str = "lung_nodules"
    fast: bool = True
    device: str = Field(default="cpu", pattern="^(cpu|gpu|gpu:[0-9]+)$")
    roi_subset: list[str] = Field(default_factory=list)


app = FastAPI(title="TotalSegmentator Local Tool")
ensure_runtime_dirs()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict[str, Any]:
    exe = local_totalsegmentator()
    python = local_python()
    torch_status: dict[str, Any] = {
        "torch_available": False,
        "cuda_available": False,
        "cuda_device": "",
    }
    try:
        import torch

        torch_status["torch_available"] = True
        torch_status["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            torch_status["cuda_device"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        torch_status["torch_error"] = str(exc)
    return {
        "default_dicom_root": str(DEFAULT_DICOM_ROOT),
        "local_python": str(python),
        "local_python_exists": python.exists(),
        "totalsegmentator": str(exe) if exe else "",
        "totalsegmentator_exists": exe is not None,
        **torch_status,
    }


@app.get("/api/tasks")
def tasks() -> list[dict[str, object]]:
    return all_tasks()


@app.get("/api/fs/list")
def list_directories(path: str | None = Query(default=None)) -> dict[str, Any]:
    root = Path(path or DEFAULT_DICOM_ROOT).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {root}")
    dirs = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if child.is_dir():
            dirs.append({"name": child.name, "path": str(child)})
    return {
        "path": str(root),
        "parent": str(root.parent) if root.parent != root else "",
        "dirs": dirs,
    }


@app.get("/api/dicom/scan")
def dicom_scan(path: str, max_files: int = 25000) -> dict[str, Any]:
    try:
        series = scan_dicom_series(path, max_files=max_files)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": str(Path(path).expanduser().resolve()), "series": series}


@app.post("/api/jobs")
def start_job(request: SegmentRequest) -> dict[str, Any]:
    dicom_path = Path(request.dicom_path).expanduser().resolve()
    if not dicom_path.exists():
        raise HTTPException(status_code=404, detail=f"DICOM path not found: {dicom_path}")
    if not task_exists(request.task):
        raise HTTPException(status_code=400, detail=f"Unknown task: {request.task}")
    job = create_job({**request.model_dump(), "dicom_path": str(dicom_path)})
    thread = threading.Thread(target=run_segmentation_job, args=(job["id"],), daemon=True)
    thread.start()
    return job


@app.get("/api/jobs")
def jobs() -> list[dict[str, Any]]:
    return list_jobs()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    try:
        job = load_job(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    job["log_tail"] = read_log(job_id, tail=80)
    return job


@app.get("/api/jobs/{job_id}/log")
def get_log(job_id: str) -> PlainTextResponse:
    return PlainTextResponse(read_log(job_id))


@app.get("/api/jobs/{job_id}/viewer")
def get_viewer(job_id: str) -> dict[str, Any]:
    try:
        return viewer_metadata(job_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _png_response(image) -> Response:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(buffer.getvalue(), media_type="image/png")


@app.get("/api/jobs/{job_id}/ct/{slice_index}.png")
def ct_png(
    job_id: str,
    slice_index: int,
    level: float = Query(default=-600),
    width: float = Query(default=1500),
) -> Response:
    try:
        return _png_response(ct_slice_png(job_id, slice_index, level=level, width=width))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/mask/{mask_name}/{slice_index}.png")
def mask_png(job_id: str, mask_name: str, slice_index: int) -> Response:
    try:
        return _png_response(mask_slice_png(job_id, mask_name, slice_index))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/volumes.txt")
def volumes_txt(job_id: str) -> FileResponse:
    path = Path(load_job(job_id).get("outputs", {}).get("volumes_txt", ""))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Volume report not available.")
    return FileResponse(path, media_type="text/plain", filename=f"{job_id}_volumes.txt")
