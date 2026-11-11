# -*- coding: utf-8 -*-
"""卦理事实表：输入结构化卦象，输出确定性计算的全部卦理事实。
下游所有Agent以此为共同事实基础，不得与之矛盾。"""
from .constants import (ZHI, ZHI_WUXING, LIUSHEN, LIUSHEN_START,
                        wuxing_relation)
from .ganzhi import parse_gz, xunkong
from .palace import build_hexagram, find_fushen, hexagram_name
from .relations import (yue_wangshuai, ri_relation, hua_relation, chong, he,
                        sanhe_candidates)

MONTH_SCORE = {"旺": 2, "相": 1, "休": 0, "囚": -1, "死": -2}


def _liuchong_liuhe(yao):
    pairs = [(0, 3), (1, 4), (2, 5)]
    zs = [y["zhi"] for y in yao]
    is_chong = all(chong(zs[a], zs[b]) for a, b in pairs)
    is_he = all(he(zs[a], zs[b]) for a, b in pairs)
    return is_chong, is_he


def _guashen(ben):
    """月卦身：世爻阳从子起、阴从午起，顺数至世爻位。"""
    shi = ben["shi"]
    start = 0 if ben["yao"][shi - 1]["yinyang"] == "阳" else 6
    return ZHI[(start + shi - 1) % 12]


def build_facts(data: dict) -> dict:
    """data: question, category, ganzhi{year,month,day,hour}, ben_lines[6], dong[]"""
    gz = dict(data["ganzhi"])
    # 古籍卦例常只记月日；月柱允许只给地支（如"巳月"记为"巳"）
    if len(gz["month"]) == 1:
        month_zhi = gz["month"]
        if month_zhi not in ZHI:
            raise ValueError(f"非法月支: {month_zhi}")
    else:
        _, month_zhi = parse_gz(gz["month"])
    day_gan, day_zhi = parse_gz(gz["day"])
    kong = xunkong(gz["day"])
    month_wx = ZHI_WUXING[month_zhi]

    ben_lines = tuple(int(x) for x in data["ben_lines"])
    dong = sorted(set(int(d) for d in data.get("dong") or []))
    ben = build_hexagram(ben_lines)

    bian = None
    if dong:
        bian_lines = tuple(1 - l if i + 1 in dong else l for i, l in enumerate(ben_lines))
        bian = build_hexagram(bian_lines)

    start = LIUSHEN_START[day_gan]
    yao_facts = []
    for i, y in enumerate(ben["yao"]):
        pos = i + 1
        f = dict(y)
        f["liushen"] = LIUSHEN[(start + i) % 6]
        f["dong"] = pos in dong
        f["kong"] = y["zhi"] in kong
        # 月建
        ws = yue_wangshuai(y["wuxing"], month_wx)
        f["yue"] = {"wangshuai": ws, "yuepo": chong(month_zhi, y["zhi"]),
                    "yuehe": he(month_zhi, y["zhi"])}
        # 日辰
        rels = ri_relation(y["zhi"], day_zhi)
        f["ri"] = rels
        f["andong"] = (not f["dong"]) and "日冲" in rels and ws in ("旺", "相")
        f["ripo"] = (not f["dong"]) and "日冲" in rels and ws not in ("旺", "相")
        # 动化
        f["bian"] = None
        f["hua"] = []
        if f["dong"] and bian:
            by = bian["yao"][i]
            # 变爻六亲以本宫五行论
            from .constants import liuqin_of
            f["bian"] = {"gan": by["gan"], "zhi": by["zhi"], "wuxing": by["wuxing"],
                         "liuqin": liuqin_of(ben["palace_wuxing"], by["wuxing"]),
                         "kong": by["zhi"] in kong}
            f["hua"] = hua_relation(y["zhi"], by["zhi"])
        # 简易力量分（仅参考，权衡交给Agent）
        score = MONTH_SCORE[ws]
        score += sum(1 for r in rels if r in ("临日", "日扶", "日生"))
        score -= sum(1 for r in rels if r in ("日克", "日泄"))
        if f["yue"]["yuepo"]:
            score -= 2
        if "化回头生" in f["hua"]:
            score += 1
        if "化回头克" in f["hua"]:
            score -= 2
        f["score"] = score
        yao_facts.append(f)

    # 动爻对他爻的作用
    for f in yao_facts:
        if not (f["dong"] or f["andong"]):
            continue
        effects = []
        for g in yao_facts:
            if g["pos"] == f["pos"]:
                continue
            rel = wuxing_relation(f["wuxing"], g["wuxing"])
            if rel in ("生", "克"):
                entry = {"target": g["pos"], "target_liuqin": g["liuqin"], "rel": rel}
                if chong(f["zhi"], g["zhi"]):
                    entry["chong"] = True
                if he(f["zhi"], g["zhi"]):
                    entry["he"] = True
                effects.append(entry)
        f["dong_effects"] = effects

    # 伏神与飞伏关系
    fushen = []
    for fs in find_fushen(ben):
        fly = yao_facts[fs["pos"] - 1]
        rel = wuxing_relation(fly["wuxing"], fs["wuxing"])
        label = {"生": "飞来生伏(得长生)", "克": "飞来克伏(伏受制)",
                 "被生": "伏去生飞(泄气)", "被克": "伏克飞神(出暴)",
                 "同": "飞伏比和"}[rel]
        fushen.append({**fs, "fei_pos": fs["pos"], "fei_zhi": fly["zhi"],
                       "feifu": label, "kong": fs["zhi"] in kong,
                       "yue_wangshuai": yue_wangshuai(fs["wuxing"], month_wx),
                       "ri": ri_relation(fs["zhi"], day_zhi)})

    # 三合局候选：动爻支 + 变爻支 + 日 + 月
    members = [(y["zhi"], f"{y['pos']}爻") for y in yao_facts if y["dong"] or y["andong"]]
    members += [(y["bian"]["zhi"], f"{y['pos']}爻变") for y in yao_facts if y["bian"]]
    members += [(day_zhi, "日辰"), (month_zhi, "月建")]
    sanhe = [s for s in sanhe_candidates(members)
             if any("爻" in m for m in s["members"])]

    is_chong, is_he = _liuchong_liuhe(ben["yao"])
    g = {"liuchong": is_chong, "liuhe": is_he,
         "generation": ben["generation"], "guashen": _guashen(ben),
         "sanhe": sanhe}
    if bian:
        bc, bh = _liuchong_liuhe(bian["yao"])
        g["bian_liuchong"], g["bian_liuhe"] = bc, bh

    return {
        "question": data.get("question", ""),
        "category": data.get("category", "其他"),
        "ganzhi": {**gz, "xunkong": list(kong), "month_zhi": month_zhi,
                   "day_gan": day_gan, "day_zhi": day_zhi},
        "bengua": {"name": ben["name"], "palace": ben["palace"],
                   "palace_wuxing": ben["palace_wuxing"],
                   "generation": ben["generation"],
                   "shi": ben["shi"], "ying": ben["ying"]},
        "biangua": None if not bian else {"name": bian["name"], "palace": bian["palace"]},
        "dong": dong,
        "yao": yao_facts,
        "fushen": fushen,
        "global": g,
    }


def facts_to_text(facts: dict) -> str:
    """渲染为给LLM看的紧凑中文事实表。"""
    gz = facts["ganzhi"]
    L = []
    L.append(f"求测：{facts['question']}（类别：{facts['category']}）")
    L.append(f"干支：{gz.get('year') or '—'}年 {gz['month']}月 {gz['day']}日"
             + (f" {gz['hour']}时" if gz.get("hour") else "")
             + f"，旬空{''.join(gz['xunkong'])}")
    b = facts["bengua"]
    line = f"本卦：{b['palace']}宫·{b['name']}（{b['generation']}），世{b['shi']}爻 应{b['ying']}爻"
    if facts["biangua"]:
        line += f" → 变卦：{facts['biangua']['name']}"
    L.append(line)
    gl = facts["global"]
    tags = []
    if gl["liuchong"]:
        tags.append("本卦六冲")
    if gl["liuhe"]:
        tags.append("本卦六合")
    if gl.get("bian_liuchong"):
        tags.append("变卦六冲")
    if gl.get("bian_liuhe"):
        tags.append("变卦六合")
    tags.append(f"卦身{gl['guashen']}")
    for s in gl["sanhe"]:
        tags.append(f"三合{s['ju']}候选({'+'.join(s['members'])})")
    L.append("卦象标记：" + "、".join(tags))
    L.append("各爻（自下而上）：")
    for y in facts["yao"]:
        seg = [f"{y['pos']}爻 {y['liushen']} {y['liuqin']}{y['gan']}{y['zhi']}{y['wuxing']}"]
        if y["shiying"]:
            seg.append(y["shiying"])
        if y["dong"]:
            seg.append("动")
        if y["andong"]:
            seg.append("暗动")
        seg.append(f"月{y['yue']['wangshuai']}")
        if y["yue"]["yuepo"]:
            seg.append("月破")
        if y["ri"]:
            seg.append("/".join(y["ri"]))
        if y["kong"]:
            seg.append("旬空")
        if y["ripo"]:
            seg.append("日破")
        if y["bian"]:
            seg.append(f"化{y['bian']['liuqin']}{y['bian']['zhi']}{y['bian']['wuxing']}"
                       + ("(空)" if y["bian"]["kong"] else ""))
        if y["hua"]:
            seg.append("/".join(y["hua"]))
        if y.get("dong_effects"):
            eff = ";".join(f"{e['rel']}{e['target']}爻{e['target_liuqin']}"
                           + ("冲" if e.get("chong") else "")
                           + ("合" if e.get("he") else "")
                           for e in y["dong_effects"])
            seg.append(f"作用[{eff}]")
        seg.append(f"力量分{y['score']:+d}")
        L.append("  " + " ".join(seg))
    if facts["fushen"]:
        L.append("伏神：")
        for fs in facts["fushen"]:
            L.append(f"  {fs['liuqin']}{fs['gan']}{fs['zhi']}{fs['wuxing']} 伏{fs['fei_pos']}爻"
                     f"{fs['fei_zhi']}下 {fs['feifu']} 月{fs['yue_wangshuai']}"
                     + (" 旬空" if fs["kong"] else "")
                     + (" " + "/".join(fs["ri"]) if fs["ri"] else ""))
    return "\n".join(L)
