from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import SMOKE_DIR, ensure_runtime_dirs  # noqa: E402
from app.dicom_io import first_ct_series, preprocess_dicom_to_nifti  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dicom-root", required=True)
    args = parser.parse_args()

    ensure_runtime_dirs()
    series = first_ct_series(args.dicom_root)
    out = SMOKE_DIR / "smoke_input.nii.gz"
    meta = preprocess_dicom_to_nifti(series["path"], out)

    print("Selected CT series:")
    print(f"  patient: {series.get('patient_id')}")
    print(f"  path:    {series.get('path')}")
    print(f"  slices:  {series.get('file_count')}")
    print("Preprocessed NIfTI:")
    print(f"  output:  {meta['nifti_path']}")
    print(f"  size:    {meta['size_xyz']}")
    print(f"  spacing: {meta['spacing_xyz_mm']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
