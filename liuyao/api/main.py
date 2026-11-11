# -*- coding: utf-8 -*-
"""FastAPI 后端：识卦 → 确认 → 断卦（后台任务+轮询）→ 追问。
启动：uvicorn liuyao.api.main:app --port 8046"""
import asyncio
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..agents import orchestrator
from ..agents.vision import recognize
from ..core.facts import build_facts, facts_to_text
from ..core.palace import NAME_TABLE

app = FastAPI(title="六爻多Agent断卦平台")
WEB = Path(__file__).parent.parent.parent / "web"


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/api/guaming")
def guaming():
    """64卦名列表（前端下拉修正用）。"""
    return sorted(NAME_TABLE.keys())


@app.post("/api/recognize")
async def api_recognize(image: UploadFile = File(...)):
    data = await image.read()
    mime = image.content_type or "image/png"
    try:
        r = await asyncio.to_thread(recognize, data, mime)
        return r
    except Exception as e:
        return JSONResponse({"data": None, "warnings": [f"识别失败: {e}"], "raw": None},
                            status_code=200)


class Confirmed(BaseModel):
    question: str
    category: str = "其他"
    ganzhi: dict
    bengua_name: str
    dong: list


@app.post("/api/preview")
def api_preview(c: Confirmed):
    """确认后先预览事实表（不耗LLM），前端展示供最后核对。"""
    inp = _to_input(c)
    facts = build_facts(inp)
    return {"facts_text": facts_to_text(facts)}


@app.post("/api/interpret")
async def api_interpret(c: Confirmed):
    sid = orchestrator.new_session(_to_input(c))
    asyncio.create_task(orchestrator.interpret(sid))
    return {"session_id": sid}


@app.get("/api/session/{sid}")
def api_session(sid: str):
    return orchestrator.public_state(sid)


class Ask(BaseModel):
    question: str


@app.post("/api/session/{sid}/ask")
async def api_ask(sid: str, a: Ask):
    answer = await orchestrator.ask(sid, a.question)
    return {"answer": answer}


def _to_input(c: Confirmed) -> dict:
    if c.bengua_name not in NAME_TABLE:
        raise ValueError(f"未知卦名 {c.bengua_name}")
    return {"question": c.question, "category": c.category,
            "ganzhi": c.ganzhi,
            "ben_lines": list(NAME_TABLE[c.bengua_name]["lines"]),
            "dong": sorted(set(int(d) for d in c.dong))}
