from __future__ import annotations


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


def all_tasks() -> list[dict[str, object]]:
    return list(DEMO_SCENES)


def task_exists(task_id: str) -> bool:
    return any(scene["id"] == task_id for scene in DEMO_SCENES)


def supports_fast(task_id: str) -> bool:
    return task_exists(task_id)
