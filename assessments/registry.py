from __future__ import annotations
import os
import yaml
from typing import Dict, Any, List
from .runtime import Assessment, Cutoff, SafetyRule

REGISTRY: Dict[str, Assessment] = {}

def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_pack(base_dir: str, pack_id: str, lang: str = "sk") -> Assessment:
    pack_dir = os.path.join(base_dir, "assessments", "packs", pack_id)
    meta = _load_yaml(os.path.join(pack_dir, "meta.yaml"))
    items = _load_yaml(os.path.join(pack_dir, f"items.{lang}.yaml"))["items"]

    cutoffs = [
        Cutoff(lo=c["range"][0], hi=c["range"][1], level=c["level"], advice=c["advice"])
        for c in meta.get("cutoffs", [])
    ]
    safety_rules = []
    for r in meta.get("safety_rules", []):
        safety_rules.append(
            SafetyRule(
                id=r["id"],
                item_id=r["when"]["item_id"],
                min_score=r["when"]["min_score"],
                message=r["message"],
            )
        )

    return Assessment(
        id=meta["id"],
        name=meta["name"],
        version=meta.get("version", "1.0.0"),
        recall=meta["recall"],
        scale_labels=meta["scale"]["labels"],
        scale_scores=meta["scale"]["scores"],
        impairment_scale=meta.get("impairment_scale", []),
        max_score=meta["max_score"],
        items=items,
        cutoffs=cutoffs,
        safety_rules=safety_rules,
    )

def load_all(base_dir: str, lang: str = "sk") -> Dict[str, Assessment]:
    packs_root = os.path.join(base_dir, "assessments", "packs")
    for pack_id in os.listdir(packs_root):
        pack_path = os.path.join(packs_root, pack_id)
        if os.path.isdir(pack_path):
            a = load_pack(base_dir, pack_id, lang=lang)
            REGISTRY[a.id] = a
    return REGISTRY
