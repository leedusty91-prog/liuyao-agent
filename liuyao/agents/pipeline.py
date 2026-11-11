# -*- coding: utf-8 -*-
"""流水线分析层：用神 → 旺衰 → 动变 → 应期。顺序执行，各自输出JSON。"""
from .client import achat, parse_json

SYS = ("你是严谨的六爻分析师。你收到的【卦理事实表】由规则引擎精确计算，"
       "旺衰、空破、合冲、纳甲等事实不得推翻，你的职责是在事实之上做专业判断。"
       "只输出JSON，不要其他文字。")

YONGSHEN_PROMPT = """【卦理事实表】
{facts}

任务：为此占定用神、原神、忌神、仇神。
要点：
- 依求测事项定用神六亲（求财看妻财、问病看用神视占者角色、测事业官运看官鬼、
  问子女看子孙、问父母文书房车看父母、问兄弟朋友看兄弟、自占吉凶看世爻）
- 用神多现时取舍口诀：舍其旺相取休囚、舍其静爻取动爻、舍其不破取月破、
  舍其不空取旬空、逢持世之爻优先
- 用神不上卦则取伏神，注意伏神能否引拔
- 原神=生用神者，忌神=克用神者，仇神=克原神生忌神者

输出JSON：
{{
  "yongshen": {{"liuqin": "妻财", "pos": 1, "zhi": "丑", "is_fushen": false,
               "reason": "取舍理由（若多现须说明为何取此爻）"}},
  "yuanshen": {{"liuqin": "...", "pos": 0或伏神注明, "zhi": "..."}},
  "jishen":   {{"liuqin": "...", "pos": 0, "zhi": "..."}},
  "choushen": {{"liuqin": "...", "pos": 0, "zhi": "..."}},
  "shiyao_role": "世爻在此占中的角色说明",
  "notes": "特殊情况说明（用神多现/伏藏/两用神等）"
}}"""

WANGSHUAI_PROMPT = """【卦理事实表】
{facts}

【用神判定】
{yongshen}

任务：综合月建日辰，权衡用神、原神、忌神三方力量对比。不要重算事实表已给的旺衰，
只做力量权衡与解释（如：月破但日生是否有救、旬空是否到底为空、暗动之力等）。

输出JSON：
{{
  "yongshen_strength": {{"level": "旺|偏旺|中平|偏弱|衰绝", "analysis": "…"}},
  "yuanshen_strength": {{"level": "…", "analysis": "…"}},
  "jishen_strength": {{"level": "…", "analysis": "…"}},
  "balance": "三方力量对比总评，明确谁占上风",
  "key_flags": ["月破待实", "旬空待冲", "…关键状态标记"]
}}"""

DONGBIAN_PROMPT = """【卦理事实表】
{facts}

【用神判定】
{yongshen}

【旺衰权衡】
{wangshuai}

任务：分析动爻作用链对用神的最终影响。
要点：多动爻时注意作用顺序与贪生忘克、连续相生、接续相克；
动爻自身空破墓绝则作用打折；变爻回头生克只作用于本动爻；
六冲卦/六合卦、三合局对格局的影响；暗动之爻亦有作用力。

输出JSON：
{{
  "chains": [{{"desc": "动爻作用链描述，如：5爻鬼酉金动生2爻父亥水，贪生忘克…",
              "effect_on_yongshen": "利|害|中性"}}],
  "geju": "格局评价（六冲变六合/反吟伏吟/三合成局等对全局的影响）",
  "net_effect": "动变对用神的净影响结论",
  "special": "特殊象（用神伏吟反吟、世应关系变化等）"
}}"""

YINGQI_PROMPT = """【卦理事实表】
{facts}

【用神判定】
{yongshen}

【旺衰权衡】
{wangshuai}

【动变分析】
{dongbian}

任务：推断应期。规则提示：
- 用神旺相：应值日值月；休囚：应生旺之期
- 旬空：应出空、冲空之日；月破：应出月、实破、合破之日
- 入墓：应冲墓开库之期；受合：应冲开之期；被冲：应合住之期
- 动爻应合日或值日，静爻应冲日值日
- 近事应日，远事应月应年；结合求测事项性质取时间尺度

输出JSON：
{{
  "candidates": [
    {{"time": "地支纪日/月，如'酉日'或'午月'", "basis": "推断依据", "likelihood": "高|中|低"}}
  ],
  "timescale": "日|月|年",
  "summary": "应期综合判断"
}}"""


async def run_pipeline(facts_text: str, notify=None) -> dict:
    """顺序执行四个分析Agent，返回各步JSON。notify(stage)用于进度回报。"""
    out = {}

    async def step(name, prompt):
        if notify:
            await notify(name)
        raw = await achat([{"role": "system", "content": SYS},
                           {"role": "user", "content": prompt}])
        out[name] = parse_json(raw)
        return out[name]

    ys = await step("yongshen", YONGSHEN_PROMPT.format(facts=facts_text))
    ws = await step("wangshuai", WANGSHUAI_PROMPT.format(
        facts=facts_text, yongshen=_j(ys)))
    db = await step("dongbian", DONGBIAN_PROMPT.format(
        facts=facts_text, yongshen=_j(ys), wangshuai=_j(ws)))
    await step("yingqi", YINGQI_PROMPT.format(
        facts=facts_text, yongshen=_j(ys), wangshuai=_j(ws), dongbian=_j(db)))
    return out


def _j(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, indent=1)
