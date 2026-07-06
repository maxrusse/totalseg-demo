from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any


DICOM_TAGS = [
    "PatientID",
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "StudyDescription",
    "SeriesDescription",
    "Modality",
    "Manufacturer",
    "Rows",
    "Columns",
    "SliceThickness",
    "PixelSpacing",
    "InstanceNumber",
]


def _coerce_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float_list(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw = value
    else:
        try:
            raw = list(value)
        except TypeError:
            raw = [value]
    result: list[float] = []
    for item in raw:
        try:
            result.append(float(item))
        except (TypeError, ValueError):
            pass
    return result


def _common_parent(paths: list[Path]) -> Path:
    if not paths:
        raise ValueError("No DICOM files found.")
    parents = [str(path.parent) for path in paths]
    return Path(os.path.commonpath(parents))


def scan_dicom_series(root: str | Path, max_files: int = 25000) -> list[dict[str, Any]]:
    """Read DICOM headers below root and group files by SeriesInstanceUID."""
    import pydicom

    root_path = _coerce_path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"DICOM path does not exist: {root_path}")
    files = sorted(root_path.rglob("*.dcm")) if root_path.is_dir() else [root_path]
    groups: dict[str, dict[str, Any]] = {}
    group_files: dict[str, list[Path]] = defaultdict(list)
    skipped = 0

    for index, file_path in enumerate(files):
        if index >= max_files:
            break
        try:
            ds = pydicom.dcmread(
                str(file_path),
                stop_before_pixels=True,
                force=True,
                specific_tags=DICOM_TAGS,
            )
        except Exception:
            skipped += 1
            continue
        series_uid = _safe_text(getattr(ds, "SeriesInstanceUID", "")) or str(file_path.parent)
        group_files[series_uid].append(file_path)
        if series_uid not in groups:
            pixel_spacing = _safe_float_list(getattr(ds, "PixelSpacing", None))
            groups[series_uid] = {
                "series_uid": series_uid,
                "patient_id": _safe_text(getattr(ds, "PatientID", "")),
                "study_uid": _safe_text(getattr(ds, "StudyInstanceUID", "")),
                "study_description": _safe_text(getattr(ds, "StudyDescription", "")),
                "series_description": _safe_text(getattr(ds, "SeriesDescription", "")),
                "modality": _safe_text(getattr(ds, "Modality", "")),
                "manufacturer": _safe_text(getattr(ds, "Manufacturer", "")),
                "rows": int(getattr(ds, "Rows", 0) or 0),
                "columns": int(getattr(ds, "Columns", 0) or 0),
                "slice_thickness_mm": float(getattr(ds, "SliceThickness", 0) or 0),
                "pixel_spacing_mm": pixel_spacing,
            }

    summaries: list[dict[str, Any]] = []
    for series_uid, header in groups.items():
        paths = group_files[series_uid]
        parent = _common_parent(paths)
        item = dict(header)
        item.update(
            {
                "path": str(parent),
                "file_count": len(paths),
                "skipped_files": skipped,
            }
        )
        summaries.append(item)

    summaries.sort(
        key=lambda item: (
            item.get("modality") != "CT",
            str(item.get("patient_id") or ""),
            -int(item.get("file_count") or 0),
        )
    )
    return summaries


def first_ct_series(root: str | Path) -> dict[str, Any]:
    series = scan_dicom_series(root)
    for item in series:
        if item.get("modality") == "CT":
            return item
    if series:
        return series[0]
    raise ValueError(f"No DICOM series found below {root}")


def preprocess_dicom_to_nifti(dicom_dir: str | Path, output_file: str | Path) -> dict[str, Any]:
    """Convert a selected DICOM series folder to NIfTI with SimpleITK."""
    import SimpleITK as sitk

    source = _coerce_path(dicom_dir)
    output = Path(output_file).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(source))
    if not series_ids:
        # If a patient/study folder was selected, choose the largest CT series below it.
        selected = first_ct_series(source)
        source = Path(selected["path"])
        series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(source))
    if not series_ids:
        raise ValueError(f"No readable DICOM series found in {source}")

    best_files: list[str] = []
    best_series_id = series_ids[0]
    for series_id in series_ids:
        files = list(sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(source), series_id))
        if len(files) > len(best_files):
            best_files = files
            best_series_id = series_id
    if not best_files:
        raise ValueError(f"No DICOM files found for series in {source}")

    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(best_files)
    image = reader.Execute()
    sitk.WriteImage(image, str(output))
    size = image.GetSize()
    spacing = image.GetSpacing()
    return {
        "source_dir": str(source),
        "series_id": str(best_series_id),
        "input_files": len(best_files),
        "nifti_path": str(output),
        "size_xyz": [int(v) for v in size],
        "spacing_xyz_mm": [float(v) for v in spacing],
    }
