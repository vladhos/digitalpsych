# main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Tuple
from db import init_db, get_session
from models import ResponseGDT

app = FastAPI(title="DigitalPsych – MVP GDT")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    init_db()


# 1) Formulár
@app.get("/gdt/start", response_class=HTMLResponse)
def gdt_start(request: Request, client: str = "anon"):
    scale_labels: List[str] = ["nikdy", "zriedkavo", "niekedy", "často", "veľmi často"]
    # pošleme do šablóny už spárované (index, label), aby šablóna nemusela používať enumerate
    scale: List[Tuple[int, str]] = list(enumerate(scale_labels))
    items = [
        ("GDT_1", "Mal/a som problém s kontrolovaním svojho hrania."),
        ("GDT_2", "Uprednostňoval/a som hranie pred inými záujmami a dennými aktivitami."),
        ("GDT_3", "Pokračoval/a som v hraní aj napriek jeho negatívnym dôsledkom."),
        ("GDT_4", "Mal/a som závažné životné problémy v dôsledku hrania."),
    ]
    return templates.TemplateResponse(
        "gdt_form.html",
        {
            "request": request,
            "client": client,
            "scale": scale,
            "items": items,
            "title": "GDT – Gaming Disorder Test",
        },
    )


# 2) Submit
@app.post("/gdt/submit")
def gdt_submit(
    client: str = Form(...),
    GDT_1: int = Form(...),
    GDT_2: int = Form(...),
    GDT_3: int = Form(...),
    GDT_4: int = Form(...),
):
    answers: Dict[str, int] = {
        "GDT_1": int(GDT_1),
        "GDT_2": int(GDT_2),
        "GDT_3": int(GDT_3),
        "GDT_4": int(GDT_4),
    }
    raw_total = sum(answers.values())  # 0–16

    with get_session() as session:
        rec = ResponseGDT(client_code=client, answers=answers, raw_total=raw_total)
        session.add(rec)
        session.commit()
        session.refresh(rec)

    return RedirectResponse(url=f"/gdt/result/{rec.id}", status_code=303)


# 3) Výsledok
@app.get("/gdt/result/{response_id}", response_class=HTMLResponse)
def gdt_result(request: Request, response_id: int):
    with get_session() as session:
        rec = session.get(ResponseGDT, response_id)
        if not rec:
            return HTMLResponse("Záznam nenájdený", status_code=404)

    interp = interpret_gdt(rec.raw_total, rec.answers)
    return templates.TemplateResponse(
        "gdt_result.html",
        {
            "request": request,
            "rec": rec,
            "interp": interp,
            "title": "GDT – Výsledok",
        },
    )


# --- Pomocná interpretácia (skríning, nie diagnostika) ---
def interpret_gdt(raw_total: int, answers: Dict[str, int]) -> str:
    high_count = sum(1 for v in answers.values() if v >= 3)  # často/veľmi často
    if raw_total <= 4 and high_count == 0:
        return (
            "Výsledok naznačuje nízku mieru ťažkostí spojených s hraním hier. "
            "Odporúčame priebežné sledovanie a rozhovor o vyváženosti aktivít."
        )
    if high_count >= 2 or raw_total >= 10:
        return (
            "Výsledok naznačuje zvýšenú frekvenciu problémového hrania. "
            "Odporúča sa podrobnejšie posúdenie psychológom a dohodnutie cieľov na úpravu návykov."
        )
    return (
        "Výsledok je v strednom pásme. Odporúčame venovať pozornosť návykom "
        "a v prípade pretrvávania ťažkostí konzultovať s odborníkom."
    )
