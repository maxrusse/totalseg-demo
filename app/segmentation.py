from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from .demo_scene import save_scene
from .jobs import append_log, job_dir, load_job, update_job
from .tasks import supports_fast
from .viewer import clear_viewer_cache, mask_key


def _mask_files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix == ".npz")


def compute_volumes(seg_dir: Path) -> list[dict[str, Any]]:
    volumes: list[dict[str, Any]] = []
    for mask_path in _mask_files(seg_dir):
        with np.load(mask_path, allow_pickle=False) as data:
            mask = np.asarray(data["mask"])
            spacing = np.asarray(data["spacing"], dtype=float)
        voxel_volume_mm3 = float(np.prod(np.abs(spacing)))
        voxel_count = int(np.count_nonzero(mask > 0))
        volume_mm3 = voxel_count * voxel_volume_mm3
        volumes.append(
            {
                "name": mask_key(mask_path),
                "file": mask_path.name,
                "voxels": voxel_count,
                "volume_mm3": volume_mm3,
                "volume_ml": volume_mm3 / 1000.0,
            }
        )
    volumes.sort(key=lambda item: item["name"])
    return volumes


def write_volume_exports(job_id: str, volumes: list[dict[str, Any]]) -> dict[str, str]:
    folder = job_dir(job_id)
    json_path = folder / "volumes.json"
    txt_path = folder / "volumes.txt"
    json_path.write_text(json.dumps(volumes, indent=2), encoding="utf-8")
    lines = [
        "Synthetic demo volume report",
        f"Job: {job_id}",
        "",
        f"{'Mask':40} {'Voxels':>12} {'mm3':>14} {'ml':>12}",
        "-" * 82,
    ]
    for item in volumes:
        lines.append(
            f"{item['name'][:40]:40} {item['voxels']:12d} "
            f"{item['volume_mm3']:14.2f} {item['volume_ml']:12.3f}"
        )
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"volumes_json": str(json_path), "volumes_txt": str(txt_path)}


def run_segmentation_job(job_id: str) -> None:
    job = load_job(job_id)
    folder = job_dir(job_id)
    input_npz = folder / "input.npz"
    output_dir = folder / "segmentations"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        scene_id = str(job["input"].get("scene_id", "synthetic_torso"))
        if not supports_fast(scene_id):
            raise RuntimeError(f"Unsupported demo scene: {scene_id}")

        append_log(job_id, f"Generating synthetic demo scene: {scene_id}")
        update_job(job_id, state="preprocessing", progress=5, stage="Preparing demo scene")
        time.sleep(0.1)
        update_job(job_id, progress=18, stage="Synthesizing volume")
        time.sleep(0.1)
        update_job(job_id, progress=34, stage="Writing masks")
        preprocess = save_scene(scene_id, input_npz, output_dir)
        update_job(job_id, preprocess=preprocess, progress=68)
        append_log(job_id, f"Wrote demo input: {input_npz}")

        update_job(job_id, state="postprocessing", progress=84, stage="Computing volumes")
        volumes = compute_volumes(output_dir)
        if not volumes:
            raise RuntimeError("Demo generation finished, but no masks were created.")
        exports = write_volume_exports(job_id, volumes)
        clear_viewer_cache()
        update_job(
            job_id,
            state="completed",
            progress=100,
            stage="Completed",
            outputs={
                "segmentations_dir": str(output_dir),
                "volumes": volumes,
                **exports,
            },
        )
        append_log(job_id, "Completed.")
    except Exception as exc:
        append_log(job_id, f"ERROR: {exc}")
        update_job(job_id, state="failed", progress=100, stage="Failed", error=str(exc))
