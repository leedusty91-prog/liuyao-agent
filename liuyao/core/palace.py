# -*- coding: utf-8 -*-
"""六十四卦生成：卦宫、世应、纳甲、六亲。全部由京房八宫算法程序化生成。"""
from .constants import (TRIGRAMS, TRIGRAM_LINES, TRIGRAM_SYMBOL, NAJIA,
                        PALACE_WUXING, PALACE_NAMES, SHI_POS, GENERATION_NAME,
                        ZHI_WUXING, liuqin_of)

Lines = tuple  # 六爻 bool 元组，自下而上


def hexagram_name(lines: Lines) -> str:
    return HEX_TABLE[tuple(int(x) for x in lines)]["name"]


def _flip(lines, i):
    l = list(lines)
    l[i] = 1 - l[i]
    return tuple(l)


def _gen_palace(pure: str):
    """生成一宫八卦的爻序列，依次：本宫→一世→…→五世→游魂→归魂。"""
    seq = []
    lines = TRIGRAM_LINES[pure] * 2
    seq.append(tuple(lines))
    cur = tuple(lines)
    for i in range(5):  # 一世至五世：依次变初爻到五爻
        cur = _flip(cur, i)
        seq.append(cur)
    cur = _flip(cur, 3)  # 游魂：五世卦再变四爻
    seq.append(cur)
    for i in range(3):  # 归魂：游魂卦内卦三爻俱变（还原为本宫内卦）
        cur = _flip(cur, i)
    seq.append(cur)
    return seq


# 构建全表：lines -> info
HEX_TABLE = {}
NAME_TABLE = {}
for _palace, _names in PALACE_NAMES.items():
    for _gen, _lines in enumerate(_gen_palace(_palace)):
        _info = {
            "name": _names[_gen],
            "palace": _palace,
            "palace_wuxing": PALACE_WUXING[_palace],
            "generation": GENERATION_NAME[_gen],
            "shi": SHI_POS[_gen],
            "ying": (SHI_POS[_gen] + 3 - 1) % 6 + 1,
            "lines": _lines,
        }
        HEX_TABLE[_lines] = _info
        NAME_TABLE[_names[_gen]] = _info


def najia_of(lines: Lines):
    """返回六爻纳甲 [(干, 支, 五行) x6]，自下而上。"""
    lower = TRIGRAMS[tuple(lines[:3])]
    upper = TRIGRAMS[tuple(lines[3:])]
    (g_in, _), zhi_in, _ = NAJIA[lower]
    (_, g_out), _, zhi_out = NAJIA[upper]
    result = []
    for z in zhi_in:
        result.append((g_in, z, ZHI_WUXING[z]))
    for z in zhi_out:
        result.append((g_out, z, ZHI_WUXING[z]))
    return result


def build_hexagram(lines: Lines) -> dict:
    """由六爻阴阳构建完整卦信息（纳甲、六亲、世应、卦宫）。"""
    lines = tuple(int(x) for x in lines)
    info = dict(HEX_TABLE[lines])
    nj = najia_of(lines)
    pw = info["palace_wuxing"]
    info["yao"] = [{
        "pos": i + 1,
        "yinyang": "阳" if lines[i] else "阴",
        "gan": g, "zhi": z, "wuxing": w,
        "liuqin": liuqin_of(pw, w),
        "shiying": "世" if i + 1 == info["shi"] else ("应" if i + 1 == info["ying"] else None),
    } for i, (g, z, w) in enumerate(nj)]
    return info


def find_fushen(ben: dict) -> list:
    """六亲不全时，从本宫首卦取伏神。返回 [{pos, liuqin, gan, zhi, wuxing}]"""
    present = {y["liuqin"] for y in ben["yao"]}
    missing = [q for q in ["父母", "兄弟", "子孙", "妻财", "官鬼"] if q not in present]
    if not missing:
        return []
    pure = build_hexagram(TRIGRAM_LINES[ben["palace"]] * 2)
    out = []
    for q in missing:
        for y in pure["yao"]:
            if y["liuqin"] == q:
                out.append({"pos": y["pos"], "liuqin": q, "gan": y["gan"],
                            "zhi": y["zhi"], "wuxing": y["wuxing"]})
    return out


def by_name(name: str) -> dict:
    return build_hexagram(NAME_TABLE[name]["lines"])
