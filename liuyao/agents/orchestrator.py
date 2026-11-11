# -*- coding: utf-8 -*-
"""编排器：识卦 → 事实表 → 流水线 → 四派并行 → 裁判 → 报告 + 多轮追问。"""
import uuid

from ..core.facts import build_facts, facts_to_text
from ..kb.retriever import features_from_facts
from .pipeline import run_pipeline
from .schools import run_schools
from .judge import run_judge, followup

# 内存会话仓（单机部署够用；持久化时换SQLite）
SESSIONS = {}

STAGES = ["facts", "yongshen", "wangshuai", "dongbian", "yingqi",
          "schools", "judge", "done"]
STAGE_LABEL = {"facts": "计算卦理事实", "yongshen": "定用神", "wangshuai": "权衡旺衰",
               "dongbian": "分析动变", "yingqi": "推断应期",
               "schools": "四派并行断卦", "judge": "终审裁决", "done": "完成"}


def new_session(confirmed: dict) -> str:
    """confirmed: question/category/ganzhi/ben_lines/dong"""
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {"id": sid, "input": confirmed, "stage": "facts",
                     "error": None, "report": None, "history": []}
    return sid


async def interpret(sid: str):
    """执行完整断卦流程，逐阶段更新会话状态。"""
    s = SESSIONS[sid]

    async def notify(stage):
        s["stage"] = stage

    try:
        facts = build_facts(s["input"])
        s["facts"] = facts
        s["facts_text"] = facts_to_text(facts)
        pipeline = await run_pipeline(s["facts_text"], notify)
        s["pipeline"] = pipeline
        features = features_from_facts(facts)
        schools = await run_schools(s["facts_text"], pipeline,
                                    facts["category"], features, notify)
        s["schools"] = schools
        report = await run_judge(s["facts_text"], pipeline, schools, notify)
        s["report"] = report
        s["stage"] = "done"
    except Exception as e:
        s["error"] = f"{type(e).__name__}: {e}"
        raise
    return s


async def ask(sid: str, question: str) -> str:
    s = SESSIONS[sid]
    answer = await followup(s, s["history"], question)
    s["history"].append({"role": "user", "content": question})
    s["history"].append({"role": "assistant", "content": answer})
    return answer


def public_state(sid: str) -> dict:
    """给前端的会话视图。"""
    s = SESSIONS.get(sid)
    if not s:
        return {"error": "会话不存在"}
    return {"id": sid, "stage": s["stage"],
            "stage_label": STAGE_LABEL.get(s["stage"], s["stage"]),
            "stage_index": STAGES.index(s["stage"]) if s["stage"] in STAGES else 0,
            "total_stages": len(STAGES),
            "error": s["error"],
            "facts_text": s.get("facts_text"),
            "pipeline": s.get("pipeline"),
            "schools": s.get("schools"),
            "report": s.get("report"),
            "history": s.get("history", [])}
