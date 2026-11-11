# -*- coding: utf-8 -*-
"""流派断卦层：增删卜易 / 卜筮正宗 / 火珠林 / 天纪经占，并行执行。"""
import asyncio
import json

from .client import achat, parse_json
from ..kb.retriever import retrieve

SCHOOLS = {
    "zengshan": {
        "name": "增删卜易派",
        "books": ["zengshanbuyi"],
        "style": """你宗《增删卜易》野鹤老人之法断卦：
- 删繁就简，专重用神旺衰与日月生克，"卦之关键在用神"
- 不尚神煞，六神仅作参考点缀
- 重实证：旬空、月破、动变、应期皆以验例为准
- 断语直截了当，吉则言吉，凶则言凶，忌模棱两可""",
    },
    "zhengzong": {
        "name": "卜筮正宗派",
        "books": ["bushizhengzong"],
        "style": """你宗《卜筮正宗》王洪绪之法断卦：
- 体系全面：用神分类严依十八论，原忌仇神层层推究
- 精于飞伏、进退、反吟伏吟、尽静尽发诸章法度
- 遵十八问答辨疑：如用神两现、卦变生克墓绝等疑难依正宗定例
- 断语条理分明，先列纲目再下结论""",
    },
    "huozhulin": {
        "name": "火珠林派",
        "books": ["huozhulin"],
        "style": """你宗《火珠林》古法断卦：
- 以财官为纲："财官辅助，用爻为主"，先看财官二字
- 重世应关系与卦身，占事以世为我、应为彼
- 兼取卦宫五行、六亲根源，"根源者，八卦之宫主"
- 断语古朴简峻，直指核心""",
    },
    "tianji": {
        "name": "天纪经占派",
        "books": ["zhouyi", "meihuayishu"],
        "style": """你宗倪海厦《天纪》经占风格，以象法直断：
- 先看卦名卦象取义：本卦是现状，变卦是结果，卦名本身就是答案
  （如占事得"大过"即有太过、非常之象；变"离"有散离、光明之辨）
- 重上下卦互动之象与《周易》卦辞爻辞：动爻爻辞往往直指事态
- 结合互卦、综卦之象辅助（如需自行推演）
- 断语口语化、生活化、直白痛快，像倪师讲课一样举象说事，
  但吉凶判断必须明确，不打太极""",
    },
}

SCHOOL_PROMPT = """{style}

【卦理事实表】（规则引擎计算，事实不得推翻）
{facts}

【前置分析】（流水线Agent结论，供参考，你可依本派立场质疑其用神取舍）
{pipeline}

【本派典籍相关文段】（检索所得，引用时注明出处）
{passages}

任务：以本派方法独立断此卦。输出JSON：
{{
  "school": "{name}",
  "conclusion": {{"direction": "吉|凶|先凶后吉|先吉后凶|平", "degree": "大|中|小",
                 "summary": "一句话结论"}},
  "confidence": 0.0到1.0,
  "arguments": ["论据1（须落在具体爻象/事实上）", "论据2", "…"],
  "yingqi": "本派对应期的看法（无则填null）",
  "citations": [{{"book": "书名", "text": "所引原文片段（须来自上面检索文段，勿杜撰）"}}],
  "dissent": "对前置分析的异议（无则null）"
}}"""


async def run_school(key: str, facts_text: str, pipeline: dict,
                     category: str, features: list) -> dict:
    cfg = SCHOOLS[key]
    passages = retrieve(books=cfg["books"], category=category,
                        features=features, k=6)
    ptext = "\n---\n".join(
        f"《{p['book_name']}·{p['chapter']}》{p['text']}" for p in passages) or "（无检索结果）"
    prompt = SCHOOL_PROMPT.format(
        style=cfg["style"], name=cfg["name"], facts=facts_text,
        pipeline=json.dumps(pipeline, ensure_ascii=False, indent=1),
        passages=ptext)
    raw = await achat([{"role": "user", "content": prompt}], temperature=0.5)
    try:
        r = parse_json(raw)
    except Exception:
        r = {"school": cfg["name"], "conclusion": {"direction": "平", "degree": "小",
             "summary": "解析失败"}, "confidence": 0.0, "arguments": [raw[:500]],
             "citations": [], "yingqi": None, "dissent": None}
    r["school_key"] = key
    return r


async def run_schools(facts_text: str, pipeline: dict, category: str,
                      features: list, notify=None) -> list:
    if notify:
        await notify("schools")
    tasks = [run_school(k, facts_text, pipeline, category, features)
             for k in SCHOOLS]
    return list(await asyncio.gather(*tasks))
