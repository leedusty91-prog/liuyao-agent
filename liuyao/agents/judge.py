# -*- coding: utf-8 -*-
"""裁判Agent：仲裁四派结论 → 终审断语报告；并承接多轮追问。"""
import json

from .client import achat, parse_json
from ..config import LLM_JUDGE_MODEL

JUDGE_SYS = ("你是六爻断卦终审裁判，深谙各派章法。"
             "卦理事实表为铁律；对流派分歧依证据强度裁决，"
             "纳甲法（增删/正宗/火珠林）主吉凶生克，天纪象法作取象补充视角，"
             "两路参照不强行对立。终审必须先二次校验用神取舍是否正确——用神错则全盘错。")

JUDGE_PROMPT = """【卦理事实表】
{facts}

【流水线分析】
{pipeline}

【四派独立断卦】
{schools}

任务：终审并输出完整断卦报告JSON：
{{
  "yongshen_review": {{"agree": true/false, "final_yongshen": "最终认定的用神（爻位+六亲+地支）",
                      "note": "校验说明；若推翻流水线取用须详述理由"}},
  "direction": "吉|凶|先凶后吉|先吉后凶|平",
  "degree": "大|中|小",
  "confidence": 0.0到1.0,
  "verdict": "核心断语，3-5句，明确回答求测之事",
  "reasoning": "核心卦理阐述（用神状态→日月生克→动变影响→结局），须句句有据",
  "yingqi": {{"best": "最可能应期", "alternatives": ["备选"], "basis": "依据"}},
  "disagreements": [{{"issue": "分歧点", "sides": "各派立场", "ruling": "裁决及理由"}}],
  "xiang_notes": "象法补充（取自天纪派的可用之象，无则null）",
  "advice": "宜忌建议，2-4条，务实可操作",
  "caveats": "断卦局限说明（如信息不足之处）"
}}"""

FOLLOWUP_SYS = ("你是六爻断卦师，正在与求测人复盘一个已断完的卦。"
                "下面给你完整案卷（卦理事实表、各Agent分析、终审报告）。"
                "回答追问时：以案卷为据，可深入细节；若求测人补充的新背景"
                "改变了用神取舍或吉凶格局，明确说明并给出修正判断；"
                "回答用自然中文，直接、具体，不打太极。")


async def run_judge(facts_text: str, pipeline: dict, schools: list,
                    notify=None) -> dict:
    if notify:
        await notify("judge")
    prompt = JUDGE_PROMPT.format(
        facts=facts_text,
        pipeline=json.dumps(pipeline, ensure_ascii=False, indent=1),
        schools=json.dumps(schools, ensure_ascii=False, indent=1))
    raw = await achat([{"role": "system", "content": JUDGE_SYS},
                       {"role": "user", "content": prompt}],
                      model=LLM_JUDGE_MODEL, temperature=0.3, max_tokens=6000)
    return parse_json(raw)


async def followup(session: dict, history: list, question: str) -> str:
    """多轮追问：携带完整案卷上下文。history: [{role, content}]"""
    dossier = json.dumps({
        "facts_text": session["facts_text"],
        "pipeline": session["pipeline"],
        "schools": session["schools"],
        "report": session["report"],
    }, ensure_ascii=False)
    messages = [{"role": "system", "content": FOLLOWUP_SYS},
                {"role": "user", "content": f"【案卷】\n{dossier}"},
                {"role": "assistant", "content": "案卷已阅，请提问。"}]
    messages += history
    messages.append({"role": "user", "content": question})
    return await achat(messages, model=LLM_JUDGE_MODEL,
                       temperature=0.4, max_tokens=3000)
