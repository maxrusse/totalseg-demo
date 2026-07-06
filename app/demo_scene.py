from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


DEMO_SCENES = [
    {
        "id": "synthetic_torso",
        "label": "Synthetic torso",
        "modality": "Demo",
        "license": "public",
        "recommended": True,
        "supports_fast": True,
        "description": "Locally generated body, lungs, heart, liver, and spine volume.",
    }
]

_SPACING_XYZ_MM = (1.25, 1.25, 2.0)
_VOLUME_SHAPE_ZYX = (96, 160, 160)


def all_scenes() -> list[dict[str, object]]:
    return list(DEMO_SCENES)


def scene_exists(scene_id: str) -> bool:
    return any(scene["id"] == scene_id for scene in DEMO_SCENES)


def supports_fast(scene_id: str) -> bool:
    return scene_exists(scene_id)


def _ellipsoid(zn: np.ndarray, yn: np.ndarray, xn: np.ndarray, center: tuple[float, float, float], radii: tuple[float, float, float]) -> np.ndarray:
    cz, cy, cx = center
    rz, ry, rx = radii
    return ((zn - cz) / rz) ** 2 + ((yn - cy) / ry) ** 2 + ((xn - cx) / rx) ** 2 <= 1.0


def _normalized_grid(shape: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    z, y, x = np.indices(shape, dtype=np.float32)
    zn = (z - (shape[0] - 1) / 2.0) / ((shape[0] - 1) / 2.0)
    yn = (y - (shape[1] - 1) / 2.0) / ((shape[1] - 1) / 2.0)
    xn = (x - (shape[2] - 1) / 2.0) / ((shape[2] - 1) / 2.0)
    return zn, yn, xn


def _base_case(seed: int = 23) -> dict[str, Any]:
    shape = _VOLUME_SHAPE_ZYX
    zn, yn, xn = _normalized_grid(shape)
    rng = np.random.default_rng(seed)

    body = _ellipsoid(zn, yn, xn, center=(0.0, 0.0, 0.0), radii=(0.88, 0.76, 0.48))
    left_lung = _ellipsoid(zn, yn, xn, center=(-0.02, -0.08, -0.16), radii=(0.42, 0.25, 0.16))
    right_lung = _ellipsoid(zn, yn, xn, center=(-0.02, -0.08, 0.16), radii=(0.42, 0.25, 0.16))
    heart = _ellipsoid(zn, yn, xn, center=(0.05, -0.02, 0.04), radii=(0.18, 0.18, 0.14))
    liver = _ellipsoid(zn, yn, xn, center=(0.1, 0.14, 0.16), radii=(0.22, 0.18, 0.2))
    spine = (np.abs(xn) < 0.05) & (yn > 0.08) & (np.abs(zn) < 0.42)
    rib_band = (np.abs(yn) < 0.05) & body

    volume = np.full(shape, -1000.0, dtype=np.float32)
    volume[body] = -120.0
    volume[left_lung] = -790.0
    volume[right_lung] = -790.0
    volume[heart] = 120.0
    volume[liver] = 68.0
    volume[spine] = 660.0
    volume[rib_band] = np.maximum(volume[rib_band], 240.0)

    gradient = (zn * 80.0) + (yn * 35.0) + (xn * 18.0)
    noise = rng.normal(0.0, 14.0, size=shape).astype(np.float32)
    volume = np.clip(volume + gradient + noise, -1024.0, 900.0).astype(np.int16)

    masks = {
        "body": body,
        "left_lung": left_lung,
        "right_lung": right_lung,
        "heart": heart,
        "liver": liver,
        "spine": spine,
    }

    return {
        "volume": volume,
        "spacing_xyz_mm": _SPACING_XYZ_MM,
        "masks": masks,
    }


def save_scene(scene_id: str, input_path: Path, segmentation_dir: Path) -> dict[str, Any]:
    if not scene_exists(scene_id):
        raise ValueError(f"Unknown scene: {scene_id}")

    input_path.parent.mkdir(parents=True, exist_ok=True)
    segmentation_dir.mkdir(parents=True, exist_ok=True)

    scene = _base_case()
    volume = scene["volume"]
    spacing = np.array(scene["spacing_xyz_mm"], dtype=np.float32)

    np.savez_compressed(
        input_path,
        volume=volume,
        spacing=spacing,
        scene_id=scene_id,
        description="Synthetic CT-like demo volume generated locally.",
    )

    for mask_name, mask in scene["masks"].items():
        np.savez_compressed(
            segmentation_dir / f"{mask_name}.npz",
            mask=mask.astype(np.uint8),
            spacing=spacing,
            scene_id=scene_id,
            label=mask_name,
        )

    return {
        "scene_id": scene_id,
        "input_path": str(input_path),
        "segmentations_dir": str(segmentation_dir),
        "size_xyz": [int(volume.shape[2]), int(volume.shape[1]), int(volume.shape[0])],
        "spacing_xyz_mm": [float(v) for v in spacing],
        "mask_count": len(scene["masks"]),
    }
