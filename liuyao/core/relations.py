# -*- coding: utf-8 -*-
"""地支与五行作用关系：合冲、旺衰、进退、墓绝、日月作用。"""
from .constants import (ZHI, ZHI_WUXING, SHENG, KE, LIUHE, LIUCHONG, SANHE,
                        MU, JUE, JIN_CYCLE)


def he(a, b):
    return LIUHE.get(a) == b


def chong(a, b):
    return LIUCHONG[a] == b


def yue_wangshuai(yao_wx: str, month_wx: str) -> str:
    """月建定旺相休囚死。"""
    if yao_wx == month_wx:
        return "旺"
    if SHENG[month_wx] == yao_wx:
        return "相"
    if SHENG[yao_wx] == month_wx:
        return "休"
    if KE[yao_wx] == month_wx:
        return "囚"
    return "死"  # 月克爻


def ri_relation(yao_zhi: str, day_zhi: str) -> list:
    """日辰对爻的作用（可多重）。"""
    out = []
    yw, dw = ZHI_WUXING[yao_zhi], ZHI_WUXING[day_zhi]
    if yao_zhi == day_zhi:
        out.append("临日")
    if chong(day_zhi, yao_zhi):
        out.append("日冲")
    if he(day_zhi, yao_zhi):
        out.append("日合")
    if yao_zhi != day_zhi:
        if dw == yw:
            out.append("日扶")
        elif SHENG[dw] == yw:
            out.append("日生")
        elif KE[dw] == yw:
            out.append("日克")
        elif SHENG[yw] == dw:
            out.append("日泄")
    if MU[yw] == day_zhi:
        out.append("入日墓")
    if JUE[yw] == day_zhi:
        out.append("临日绝")
    return out


def jin_tui(cur: str, to: str):
    """动化进神/退神；非同五行返回 None。"""
    wx = ZHI_WUXING[cur]
    if ZHI_WUXING[to] != wx:
        return None
    cyc = JIN_CYCLE[wx]
    if cur not in cyc or to not in cyc or cur == to:
        return None
    i, j = cyc.index(cur), cyc.index(to)
    if len(cyc) == 2:  # 寅卯/巳午/申酉/亥子：顺序即进
        return "化进神" if j > i else "化退神"
    return "化进神" if (j - i) % len(cyc) == 1 else "化退神"


def hua_relation(ben_zhi: str, bian_zhi: str) -> list:
    """动爻与变爻的关系。"""
    out = []
    bw, vw = ZHI_WUXING[ben_zhi], ZHI_WUXING[bian_zhi]
    jt = jin_tui(ben_zhi, bian_zhi)
    if jt:
        out.append(jt)
    if ben_zhi == bian_zhi:
        out.append("伏吟")
    if chong(ben_zhi, bian_zhi):
        out.append("反吟")
    if SHENG[vw] == bw:
        out.append("化回头生")
    if KE[vw] == bw:
        out.append("化回头克")
    if MU[bw] == bian_zhi:
        out.append("化墓")
    if JUE[bw] == bian_zhi:
        out.append("化绝")
    if he(ben_zhi, bian_zhi):
        out.append("化合")
    return out


def sanhe_candidates(branches_with_labels: list) -> list:
    """检查三合局候选。入参 [(支, 标签)]，返回 [{'ju':五行, 'members':[标签]}]"""
    out = []
    for combo, wx in SANHE.items():
        hit = [(z, lb) for z, lb in branches_with_labels if z in combo]
        zs = {z for z, _ in hit}
        if zs == set(combo):
            out.append({"ju": wx + "局", "members": [f"{lb}{z}" for z, lb in hit]})
    return out
