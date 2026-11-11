# -*- coding: utf-8 -*-
"""识卦Agent：视觉LLM提取最小必要信息，引擎重算并交叉校验。

设计要点：图中六亲/六神/伏神/世应/纳甲全部可由引擎推出，
故只提取 干支四柱 + 本卦 + 动爻，其余图上信息用作校验而非采信。"""
from ..config import LLM_VISION_MODEL
from ..core.palace import NAME_TABLE, build_hexagram
from ..core.ganzhi import xunkong, parse_gz
from .client import chat, image_content, parse_json

VISION_PROMPT = """你是六爻排盘图识别专家。仔细读图，提取以下信息，只输出JSON：

{
  "ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅", "hour": "甲辰"},
  "bengua_name": "泽风大过",        // 本卦全名（左列卦）
  "biangua_name": "离为火",         // 变卦全名（右列卦），无变卦填null
  "dong": [1, 2, 5, 6],            // 动爻位置，自下而上1-6；X和O都是动爻(X阴动/O阳动)
  "palace_label": "震",             // 图中标注的本卦卦宫（如"震宫"取"震"）
  "xunkong_label": ["辰", "巳"],    // 图中标注的日空
  "shi_label": 4,                   // 图中"世"标记在本卦第几爻（自下而上）
  "najia_check": ["丑", "亥", "酉", "亥", "酉", "未"],  // 本卦六爻地支自下而上，用于校验
  "uncertain": []                   // 读不清的字段名列表
}

注意：
- 爻的顺序自下而上：图最下一行是初爻(1)，最上一行是6爻
- X 标记 = 阴爻动，O 标记 = 阳爻动，都计入 dong
- 伏神列（灰色小字）不需要提取
- 只输出JSON，不要其他文字"""


def recognize(image_bytes: bytes, mime: str = "image/png") -> dict:
    """识别卦图 → {data, warnings, raw}。data可直接送 build_facts（还差question）。"""
    out = chat([{"role": "user", "content": [
        {"type": "text", "text": VISION_PROMPT},
        image_content(image_bytes, mime),
    ]}], model=LLM_VISION_MODEL, temperature=0)
    r = parse_json(out)
    return verify(r)


def verify(r: dict) -> dict:
    """引擎重算，交叉校验图中标注，产出警告列表。"""
    warnings = list(r.get("uncertain") or [])
    name = r.get("bengua_name", "")
    if name not in NAME_TABLE:
        return {"data": None, "warnings": [f"本卦名'{name}'不在六十四卦中，需人工确认"],
                "raw": r}
    ben = build_hexagram(NAME_TABLE[name]["lines"])
    dong = sorted(set(r.get("dong") or []))

    # 校验1：纳甲地支
    if r.get("najia_check"):
        real = [y["zhi"] for y in ben["yao"]]
        if list(r["najia_check"]) != real:
            warnings.append(f"图中六爻地支{r['najia_check']}与{name}纳甲{real}不符，"
                            "可能卦名识别错误")
    # 校验2：卦宫
    if r.get("palace_label") and r["palace_label"] != ben["palace"]:
        warnings.append(f"图标卦宫{r['palace_label']}≠引擎推算{ben['palace']}")
    # 校验3：世爻
    if r.get("shi_label") and r["shi_label"] != ben["shi"]:
        warnings.append(f"图标世爻{r['shi_label']}≠引擎推算{ben['shi']}")
    # 校验4：变卦名
    if dong and r.get("biangua_name"):
        lines = list(NAME_TABLE[name]["lines"])
        for d in dong:
            lines[d - 1] = 1 - lines[d - 1]
        from ..core.palace import hexagram_name
        real_bian = hexagram_name(tuple(lines))
        if real_bian != r["biangua_name"]:
            warnings.append(f"依动爻{dong}推算变卦为{real_bian}，"
                            f"图中为{r['biangua_name']}，动爻识别可能有误")
    elif dong and not r.get("biangua_name"):
        warnings.append("有动爻但未识别到变卦，请确认")
    elif not dong and r.get("biangua_name"):
        warnings.append("识别到变卦但无动爻，请确认动爻标记")
    # 校验5：旬空
    try:
        parse_gz(r["ganzhi"]["day"])
        k = xunkong(r["ganzhi"]["day"])
        if r.get("xunkong_label") and tuple(r["xunkong_label"]) != k:
            warnings.append(f"图标日空{r['xunkong_label']}≠依{r['ganzhi']['day']}日"
                            f"推算{list(k)}，日柱识别可能有误")
    except (ValueError, KeyError) as e:
        warnings.append(f"日柱异常: {e}")

    data = {"ganzhi": r["ganzhi"], "bengua_name": name,
            "ben_lines": list(NAME_TABLE[name]["lines"]), "dong": dong}
    return {"data": data, "warnings": warnings, "raw": r}
