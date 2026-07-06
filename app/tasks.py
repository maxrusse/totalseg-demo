from __future__ import annotations


OPEN_TASKS = [
    {
        "id": "total",
        "label": "total",
        "modality": "CT",
        "license": "open",
        "recommended": True,
        "supports_fast": True,
        "description": "Default CT model with the main body classes.",
    },
    {
        "id": "lung_nodules",
        "label": "lung_nodules",
        "modality": "CT",
        "license": "open",
        "recommended": True,
        "supports_fast": False,
        "description": "Lung and lung nodule model; useful for LIDC-IDRI CT scans.",
    },
    {
        "id": "lung_vessels",
        "label": "lung_vessels",
        "modality": "CT",
        "license": "open",
        "recommended": True,
        "supports_fast": True,
        "description": "Lung arteries, veins, airways, and airway wall.",
    },
    {
        "id": "body",
        "label": "body",
        "modality": "CT",
        "license": "open",
        "recommended": True,
        "supports_fast": True,
        "description": "Body, trunk, extremities, and skin.",
    },
    {
        "id": "kidney_cysts",
        "label": "kidney_cysts",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Kidney cyst masks.",
    },
    {
        "id": "liver_vessels",
        "label": "liver_vessels",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Liver vessels and liver tumor.",
    },
    {
        "id": "liver_segments",
        "label": "liver_segments",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Couinaud liver segments.",
    },
    {
        "id": "pleural_pericard_effusion",
        "label": "pleural_pericard_effusion",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Pleural and pericardial effusion.",
    },
    {
        "id": "head_glands_cavities",
        "label": "head_glands_cavities",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Head glands and cavity structures.",
    },
    {
        "id": "head_muscles",
        "label": "head_muscles",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Head muscle structures.",
    },
    {
        "id": "headneck_bones_vessels",
        "label": "headneck_bones_vessels",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Head and neck bones and vessels.",
    },
    {
        "id": "headneck_muscles",
        "label": "headneck_muscles",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Head and neck muscles.",
    },
    {
        "id": "craniofacial_structures",
        "label": "craniofacial_structures",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Mandible, skull, teeth, and sinus classes.",
    },
    {
        "id": "abdominal_muscles",
        "label": "abdominal_muscles",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Abdominal and paraspinal muscle groups.",
    },
    {
        "id": "trunk_cavities",
        "label": "trunk_cavities",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Thoracic and abdominal cavity regions.",
    },
    {
        "id": "ventricle_parts",
        "label": "ventricle_parts",
        "modality": "CT",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Detailed brain ventricle parts.",
    },
    {
        "id": "total_mr",
        "label": "total_mr",
        "modality": "MR",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "Default MR model; included for completeness.",
    },
    {
        "id": "body_mr",
        "label": "body_mr",
        "modality": "MR",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "MR body mask.",
    },
    {
        "id": "vertebrae_mr",
        "label": "vertebrae_mr",
        "modality": "MR",
        "license": "open",
        "recommended": False,
        "supports_fast": True,
        "description": "MR vertebrae classes.",
    },
]


LICENSED_TASKS = [
    "heartchambers_highres",
    "appendicular_bones",
    "tissue_types",
    "tissue_4_types",
    "brain_structures",
    "vertebrae_body",
    "face",
    "coronary_arteries",
    "aortic_sinuses",
]


def all_tasks() -> list[dict[str, object]]:
    licensed = [
        {
            "id": task,
            "label": task,
            "modality": "CT/MR",
            "license": "requires_license",
            "recommended": False,
            "supports_fast": True,
            "description": "Requires a TotalSegmentator license.",
        }
        for task in LICENSED_TASKS
    ]
    return OPEN_TASKS + licensed


def task_exists(task_id: str) -> bool:
    return any(task["id"] == task_id for task in all_tasks())


def supports_fast(task_id: str) -> bool:
    for task in all_tasks():
        if task["id"] == task_id:
            return bool(task.get("supports_fast", True))
    return True
