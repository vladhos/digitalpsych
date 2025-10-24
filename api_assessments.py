from __future__ import annotations
import os
from typing import Dict, List, Literal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from assessments.registry import load_all, REGISTRY

router = APIRouter(prefix="/assessments", tags=["assessments"])
templates = Jinja2Templates(directory="templates")

# načítaj registry pri importe (jazyk 'sk')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_all(BASE_DIR, lang="sk")

@router.get("/list")
def list_assessments():
    return [{"id": a.id, "name": a.name, "version": a.version} for a in REGISTRY.values()]

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def page(request: Request):
    return templates.TemplateResponse("assessments.html", {"request": request})

@router.get("/{assess_id}/schema")
def schema(assess_id: str):
    a = REGISTRY.get(assess_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": a.id,
        "title": a.name,
        "recall": a.recall,
        "scale": a.scale_labels,
        "impairment_scale": a.impairment_scale,
        "items": a.items,
        "max_score": a.max_score,
        "version": a.version,
    }

class Answer(BaseModel):
    item_id: str
    label: str

class SubmitPayload(BaseModel):
    answers: List[Answer] = Field(..., min_items=1)
    impairment: Literal["Žiadny", "Mierny", "Výrazný", "Extrémny"] | None = None

@router.post("/{assess_id}/score")
def score(assess_id: str, payload: SubmitPayload):
    a = REGISTRY.get(assess_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # zoradenie odpovedí podľa poradia otázok
    item_index = {it["id"]: i for i, it in enumerate(a.items)}
    responses = [None] * len(a.items)
    for ans in payload.answers:
        if ans.item_id not in item_index:
            raise HTTPException(status_code=400, detail=f"Unknown item_id: {ans.item_id}")
        responses[item_index[ans.item_id]] = ans.label
    if any(r is None for r in responses):
        raise HTTPException(status_code=400, detail="Missing answers")

    total = a.score_total(responses)
    level, advice = a.interpret(total)
    safety_msgs = a.apply_safety({ans.item_id: ans.label for ans in payload.answers})

    out: Dict = {
        "assessment": a.id,
        "version": a.version,
        "total": total,
        "max_score": a.max_score,
        "severity": level,
        "advice": advice,
        "impairment": payload.impairment,
    }
    if safety_msgs:
        out["safety_flag"] = True
        out["safety_msgs"] = safety_msgs
    return out
