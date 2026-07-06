from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .jobs import job_dir, load_job


def _is_nifti(path: Path) -> bool:
    return path.name.endswith(".nii.gz") or path.suffix == ".nii"


def mask_key(path: Path) -> str:
    name = path.name
    if name.endswith(".nii.gz"):
        return name[:-7]
    if name.endswith(".nii"):
        return name[:-4]
    return path.stem


def segmentation_dir(job_id: str) -> Path:
    return job_dir(job_id) / "segmentations"


def input_nifti_path(job_id: str) -> Path:
    return job_dir(job_id) / "input.nii.gz"


@lru_cache(maxsize=4)
def _load_image(path_text: str) -> tuple[np.ndarray, tuple[float, ...]]:
    import SimpleITK as sitk

    image = sitk.ReadImage(path_text)
    array = sitk.GetArrayFromImage(image)
    spacing = tuple(float(v) for v in image.GetSpacing())
    return array, spacing


def load_ct(job_id: str) -> tuple[np.ndarray, tuple[float, ...]]:
    return _load_image(str(input_nifti_path(job_id)))


def list_mask_files(job_id: str) -> list[Path]:
    seg_dir = segmentation_dir(job_id)
    if not seg_dir.exists():
        return []
    return sorted(path for path in seg_dir.iterdir() if path.is_file() and _is_nifti(path))


def resolve_mask_file(job_id: str, key: str) -> Path:
    for path in list_mask_files(job_id):
        if mask_key(path) == key:
            return path
    raise FileNotFoundError(f"Mask not found: {key}")


def viewer_metadata(job_id: str) -> dict[str, Any]:
    job = load_job(job_id)
    ct, spacing = load_ct(job_id)
    masks = []
    for path in list_mask_files(job_id):
        item = {
            "key": mask_key(path),
            "file": path.name,
        }
        try:
            data, _ = _load_image(str(path))
            nonzero = np.where(np.any(data > 0, axis=(1, 2)))[0]
            if nonzero.size:
                item.update(
                    {
                        "first_slice": int(nonzero[0]),
                        "last_slice": int(nonzero[-1]),
                        "nonzero_slices": int(nonzero.size),
                    }
                )
            else:
                item.update({"first_slice": None, "last_slice": None, "nonzero_slices": 0})
        except Exception:
            item.update({"first_slice": None, "last_slice": None, "nonzero_slices": 0})
        masks.append(item)
    return {
        "job": job,
        "slices": int(ct.shape[0]),
        "height": int(ct.shape[1]),
        "width": int(ct.shape[2]),
        "spacing_xyz_mm": list(spacing),
        "masks": masks,
        "volumes": job.get("outputs", {}).get("volumes", []),
    }


def _window_ct(slice_data: np.ndarray, level: float, width: float) -> np.ndarray:
    low = level - width / 2.0
    high = level + width / 2.0
    clipped = np.clip(slice_data.astype(np.float32), low, high)
    scaled = (clipped - low) / max(high - low, 1.0)
    return (scaled * 255).astype(np.uint8)


def ct_slice_png(job_id: str, slice_index: int, level: float = -600, width: float = 1500) -> Image.Image:
    ct, _ = load_ct(job_id)
    index = max(0, min(int(slice_index), ct.shape[0] - 1))
    return Image.fromarray(_window_ct(ct[index], level, width), mode="L")


def mask_slice_png(job_id: str, mask: str, slice_index: int) -> Image.Image:
    path = resolve_mask_file(job_id, mask)
    data, _ = _load_image(str(path))
    index = max(0, min(int(slice_index), data.shape[0] - 1))
    binary = data[index] > 0
    image = np.zeros((binary.shape[0], binary.shape[1], 4), dtype=np.uint8)
    image[..., 0] = np.where(binary, 44, 12)
    image[..., 1] = np.where(binary, 190, 28)
    image[..., 2] = np.where(binary, 170, 36)
    image[..., 3] = 255
    return Image.fromarray(image, mode="RGBA")


def clear_viewer_cache() -> None:
    _load_image.cache_clear()
