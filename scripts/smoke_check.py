from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.jobs import create_job, load_job  # noqa: E402
from app.segmentation import run_segmentation_job  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    job = create_job({"scene_id": "synthetic_torso", "fast": True})
    run_segmentation_job(job["id"])
    result = load_job(job["id"])
    if result.get("state") != "completed":
        raise SystemExit(f"Smoke test failed: {result.get('state')}")
    volumes = result.get("outputs", {}).get("volumes", [])
    if not volumes:
        raise SystemExit("Smoke test failed: no volumes were produced")

    print("Synthetic demo smoke test passed.")
    print(f"  job: {job['id']}")
    print(f"  volumes: {len(volumes)}")
    print(f"  report: {result.get('outputs', {}).get('volumes_txt', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
