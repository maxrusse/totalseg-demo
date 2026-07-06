from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from .config import local_totalsegmentator, runtime_env
from .dicom_io import preprocess_dicom_to_nifti
from .jobs import append_log, job_dir, load_job, update_job
from .tasks import supports_fast
from .viewer import clear_viewer_cache, mask_key


def _nifti_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and (path.name.endswith(".nii.gz") or path.suffix == ".nii")
    )


def _build_command(job: dict[str, Any], input_nii: Path, output_dir: Path) -> list[str]:
    exe = local_totalsegmentator()
    if exe is None:
        raise RuntimeError("TotalSegmentator was not found. Run install.ps1 first.")
    request = job["input"]
    command = [
        str(exe),
        "-i",
        str(input_nii),
        "-o",
        str(output_dir),
        "--task",
        str(request.get("task", "total")),
        "--device",
        str(request.get("device", "cpu")),
    ]
    task = str(request.get("task", "total"))
    if request.get("fast", True) and supports_fast(task):
        command.append("--fast")
    roi_subset = request.get("roi_subset") or []
    if roi_subset:
        command.append("--roi_subset")
        command.extend(str(item) for item in roi_subset)
    return command


def _line_progress(line: str, current: int) -> int:
    text = line.lower()
    if "download" in text:
        return max(current, 30)
    if "preprocess" in text or "resampl" in text:
        return max(current, 36)
    if "predict" in text or "nnunet" in text:
        return max(current, 55)
    if "saving" in text or "postprocess" in text:
        return max(current, 82)
    return min(84, current + 1)


def compute_volumes(seg_dir: Path) -> list[dict[str, Any]]:
    import SimpleITK as sitk

    volumes: list[dict[str, Any]] = []
    for mask_path in _nifti_files(seg_dir):
        image = sitk.ReadImage(str(mask_path))
        spacing = image.GetSpacing()
        voxel_volume_mm3 = float(np.prod(np.abs(spacing)))
        data = sitk.GetArrayFromImage(image)
        voxel_count = int(np.count_nonzero(data > 0))
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
        "TotalSegmentator volume report",
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
    input_nii = folder / "input.nii.gz"
    output_dir = folder / "segmentations"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        update_job(job_id, state="preprocessing", progress=5, stage="Preprocessing DICOM")
        append_log(job_id, "Preprocessing DICOM series to NIfTI.")
        preprocess = preprocess_dicom_to_nifti(job["input"]["dicom_path"], input_nii)
        update_job(job_id, preprocess=preprocess, progress=18)
        append_log(job_id, f"Wrote input NIfTI: {input_nii}")

        command = _build_command(job, input_nii, output_dir)
        append_log(job_id, "Running: " + " ".join(f'"{part}"' if " " in part else part for part in command))
        update_job(job_id, state="running", progress=25, stage="Running TotalSegmentator")

        process = subprocess.Popen(
            command,
            cwd=str(folder),
            env=runtime_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        progress = 25
        assert process.stdout is not None
        for raw_line in process.stdout:
            append_log(job_id, raw_line)
            progress = _line_progress(raw_line, progress)
            update_job(job_id, progress=progress)
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"TotalSegmentator exited with code {return_code}. See log.txt.")

        update_job(job_id, state="postprocessing", progress=90, stage="Computing volumes")
        volumes = compute_volumes(output_dir)
        if not volumes:
            raise RuntimeError("TotalSegmentator finished, but no NIfTI masks were created.")
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
