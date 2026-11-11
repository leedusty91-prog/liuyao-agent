# -*- coding: utf-8 -*-
"""干支相关：解析、旬空。"""
from .constants import GAN, ZHI, GAN_WUXING, ZHI_WUXING


def parse_gz(gz: str):
    """'壬寅' -> ('壬','寅')，并校验合法性。"""
    g, z = gz[0], gz[1]
    if g not in GAN or z not in ZHI:
        raise ValueError(f"非法干支: {gz}")
    if (GAN.index(g) - ZHI.index(z)) % 2 != 0:
        raise ValueError(f"干支不匹配（阴阳错位）: {gz}")
    return g, z


def xunkong(gz: str):
    """由日柱求旬空两支。壬寅 -> ('辰','巳')"""
    g, z = parse_gz(gz)
    start = (ZHI.index(z) - GAN.index(g)) % 12  # 旬首地支
    return ZHI[(start + 10) % 12], ZHI[(start + 11) % 12]


def gz_wuxing(gz: str):
    g, z = parse_gz(gz)
    return GAN_WUXING[g], ZHI_WUXING[z]
