from __future__ import annotations

import io
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import STATIC_DIR, ensure_runtime_dirs, local_python
from .jobs import create_job, list_jobs, load_job, read_log
from .segmentation import run_segmentation_job
from .tasks import all_tasks, task_exists
from .viewer import ct_slice_png, mask_slice_png, viewer_metadata


class SegmentRequest(BaseModel):
    scene_id: str = "synthetic_torso"
    fast: bool = True


app = FastAPI(title="Codex Windows Demo")
ensure_runtime_dirs()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict[str, Any]:
    python = local_python()
    return {
        "demo_mode": True,
        "local_python": str(python),
        "local_python_exists": python.exists(),
        "scene_count": len(all_tasks()),
    }


@app.get("/api/tasks")
def tasks() -> list[dict[str, object]]:
    return all_tasks()


@app.get("/api/scenes")
def scenes() -> list[dict[str, object]]:
    return all_tasks()


@app.post("/api/jobs")
def start_job(request: SegmentRequest) -> dict[str, Any]:
    if not task_exists(request.scene_id):
        raise HTTPException(status_code=400, detail=f"Unknown scene: {request.scene_id}")
    job = create_job(request.model_dump())
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
    path = load_job(job_id).get("outputs", {}).get("volumes_txt", "")
    if not path:
        raise HTTPException(status_code=404, detail="Volume report not available.")
    report = FileResponse(path, media_type="text/plain", filename=f"{job_id}_volumes.txt")
    return report
