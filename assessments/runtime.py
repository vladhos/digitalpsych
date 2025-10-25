from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

@dataclass
class Cutoff:
    lo: int
    hi: int
    level: str
    advice: str

@dataclass
class SafetyRule:
    id: str
    item_id: str
    min_score: int
    message: str

@dataclass
class Assessment:
    id: str
    name: str
    version: str
    recall: str
    scale_labels: List[str]
    scale_scores: List[int]                 # mapovanie indexu labelu -> skóre
    impairment_scale: List[str]
    max_score: int
    items: List[Dict[str, str]]             # [{id, text}]
    cutoffs: List[Cutoff]
    safety_rules: List[SafetyRule]

    def score_total(self, answers: List[str]) -> int:
        label2score = {lbl: self.scale_scores[i] for i, lbl in enumerate(self.scale_labels)}
        return sum(label2score[a] for a in answers)

    def interpret(self, total: int) -> Tuple[str, str]:
        for c in self.cutoffs:
            if c.lo <= total <= c.hi:
                return c.level, c.advice
        # fallback
        return "Neznáme", "Bez interpretácie."

    def apply_safety(self, answers: Dict[str, str]) -> List[str]:
        # pre safety pravidlá potrebujeme skóre z labelov
        label2score = {lbl: self.scale_scores[i] for i, lbl in enumerate(self.scale_labels)}
        messages = []
        for r in self.safety_rules:
            if r.item_id in answers:
                if label2score.get(answers[r.item_id], 0) >= r.min_score:
                    messages.append(r.message)
        return messages


# --- 3.1: Generické vyhodnocovanie podľa meta.yaml bands ---

def compute_sum_score(answers: Dict[str, int | str], label2score: Dict[str, int] | None = None) -> int:
    """
    Sumuje hodnoty odpovedí.
    - Ak je label2score zadaný, premapuje textové labely na skóre.
    - Inak predpokladá, že answers obsahuje číselné hodnoty.
    answers: { item_id: value_or_label }
    """
    total = 0
    if label2score:
        for v in answers.values():
            total += int(label2score.get(str(v), 0))
    else:
        for v in answers.values():
            total += int(v)
    return total


def band_from_score(meta: Dict[str, Any], score: int) -> Optional[Dict[str, Any]]:
    """
    Nájde príslušné pásmo (band) podľa skóre. Podporuje:
    - meta["bands"] alebo
    - meta["scale"]["bands"]
    Band by mal mať kľúče: label, min, max.
    """
    bands = meta.get("bands") or meta.get("scale", {}).get("bands") or []
    for b in bands:
        if int(b["min"]) <= score <= int(b["max"]):
            return b
    return None
