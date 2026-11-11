# -*- coding: utf-8 -*-
"""端到端流程测试：mock LLM，验证编排器与各Agent的数据流转。"""
import asyncio
import json
import pytest

from liuyao.agents import client as llm_client

MOCK_RESPONSES = {
    "yongshen": {"yongshen": {"liuqin": "父母", "pos": 3, "zhi": "亥",
                              "is_fushen": False, "reason": "自占病取世爻"},
                 "yuanshen": {"liuqin": "官鬼", "pos": 5, "zhi": "酉"},
                 "jishen": {"liuqin": "妻财", "pos": 6, "zhi": "未"},
                 "choushen": {"liuqin": "子孙", "pos": 0, "zhi": "午"},
                 "shiyao_role": "世爻即用神", "notes": ""},
    "wangshuai": {"yongshen_strength": {"level": "衰绝", "analysis": "月破日克"},
                  "yuanshen_strength": {"level": "中平", "analysis": "x"},
                  "jishen_strength": {"level": "旺", "analysis": "x"},
                  "balance": "忌神占上风", "key_flags": ["月破"]},
    "dongbian": {"chains": [{"desc": "未土动生酉金，接续相生", "effect_on_yongshen": "利"}],
                 "geju": "游魂卦", "net_effect": "有生但无根", "special": ""},
    "yingqi": {"candidates": [{"time": "卯日", "basis": "冲去元神", "likelihood": "高"}],
               "timescale": "日", "summary": "应在卯日"},
    "school": {"school": "MOCK派", "conclusion": {"direction": "凶", "degree": "大",
               "summary": "用神无根"}, "confidence": 0.8,
               "arguments": ["亥水月破"], "yingqi": "卯日",
               "citations": [], "dissent": None},
    "judge": {"yongshen_review": {"agree": True, "final_yongshen": "3爻父母亥水",
              "note": "取用正确"}, "direction": "凶", "degree": "大",
              "confidence": 0.85, "verdict": "病凶", "reasoning": "用神无根",
              "yingqi": {"best": "卯日", "alternatives": [], "basis": "冲元神"},
              "disagreements": [], "xiang_notes": "大过有栋桡之象",
              "advice": ["速就医"], "caveats": ""},
}


def fake_chat(messages, **kw):
    text = json.dumps(messages, ensure_ascii=False)
    if "定用神、原神" in text:
        key = "yongshen"
    elif "权衡用神、原神、忌神三方力量" in text:
        key = "wangshuai"
    elif "动爻作用链" in text:
        key = "dongbian"
    elif "推断应期" in text:
        key = "yingqi"
    elif "以本派方法独立断此卦" in text:
        key = "school"
    elif "终审并输出完整断卦报告" in text:
        key = "judge"
    else:
        return "追问回答：依卦而论。"
    return json.dumps(MOCK_RESPONSES[key], ensure_ascii=False)


@pytest.fixture
def mock_llm(monkeypatch):
    monkeypatch.setattr(llm_client, "chat", fake_chat)


def test_full_flow(mock_llm):
    from liuyao.agents import orchestrator
    sid = orchestrator.new_session({
        "question": "自占病", "category": "疾病",
        "ganzhi": {"month": "巳", "day": "乙未"},
        "ben_lines": [0, 1, 1, 1, 1, 0], "dong": [5, 6]})
    s = asyncio.run(orchestrator.interpret(sid))
    assert s["stage"] == "done"
    assert s["report"]["direction"] == "凶"
    assert len(s["schools"]) == 4
    assert all(sc["conclusion"]["direction"] == "凶" for sc in s["schools"])
    assert "泽风大过" in s["facts_text"] and "火风鼎" in s["facts_text"]
    # 追问
    ans = asyncio.run(orchestrator.ask(sid, "还有救吗？"))
    assert "追问回答" in ans
    assert len(orchestrator.SESSIONS[sid]["history"]) == 2
    # 公开状态
    st = orchestrator.public_state(sid)
    assert st["stage"] == "done" and st["report"]


def test_vision_verify():
    """识卦校验逻辑（不调LLM，直接喂识别结果）。"""
    from liuyao.agents.vision import verify
    r = verify({"ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅", "hour": "甲辰"},
                "bengua_name": "泽风大过", "biangua_name": "离为火",
                "dong": [1, 2, 5, 6], "palace_label": "震",
                "xunkong_label": ["辰", "巳"], "shi_label": 4,
                "najia_check": ["丑", "亥", "酉", "亥", "酉", "未"], "uncertain": []})
    assert r["warnings"] == []
    assert r["data"]["dong"] == [1, 2, 5, 6]
    # 动爻识别错误 → 变卦对不上 → 应有警告
    r2 = verify({"ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅"},
                 "bengua_name": "泽风大过", "biangua_name": "离为火",
                 "dong": [1, 2], "palace_label": "震", "shi_label": 4,
                 "najia_check": None, "xunkong_label": None, "uncertain": []})
    assert any("变卦" in w for w in r2["warnings"])
    # 日柱错误 → 旬空对不上
    r3 = verify({"ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬申"},
                 "bengua_name": "泽风大过", "biangua_name": "离为火",
                 "dong": [1, 2, 5, 6], "xunkong_label": ["辰", "巳"],
                 "palace_label": None, "shi_label": None,
                 "najia_check": None, "uncertain": []})
    assert any("旬空" in w or "日空" in w for w in r3["warnings"])


def test_api_endpoints(mock_llm):
    """单事件循环内跑 ASGI，后台断卦任务才能被调度（等价于 uvicorn 环境）。"""
    import httpx
    from liuyao.api.main import app

    async def flow():
        tr = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=tr, base_url="http://t") as c:
            assert len((await c.get("/api/guaming")).json()) == 64
            body = {"question": "自占病", "category": "疾病",
                    "ganzhi": {"month": "巳", "day": "乙未"},
                    "bengua_name": "泽风大过", "dong": [5, 6]}
            p = (await c.post("/api/preview", json=body)).json()
            assert "泽风大过" in p["facts_text"]
            sid = (await c.post("/api/interpret", json=body)).json()["session_id"]
            st = None
            for _ in range(100):
                await asyncio.sleep(0.05)
                st = (await c.get(f"/api/session/{sid}")).json()
                if st["stage"] == "done" or st["error"]:
                    break
            assert st["stage"] == "done", st.get("error")
            assert st["report"]["direction"] == "凶"
            a = (await c.post(f"/api/session/{sid}/ask",
                              json={"question": "何解？"})).json()
            assert "追问回答" in a["answer"]

    asyncio.run(flow())
