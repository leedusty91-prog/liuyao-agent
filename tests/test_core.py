# -*- coding: utf-8 -*-
import pytest
from liuyao.core.palace import build_hexagram, by_name, NAME_TABLE, HEX_TABLE
from liuyao.core.ganzhi import xunkong, parse_gz
from liuyao.core.facts import build_facts
from liuyao.core.relations import yue_wangshuai, jin_tui, hua_relation
from liuyao.core.constants import TRIGRAM_LINES


def test_table_complete():
    assert len(HEX_TABLE) == 64
    assert len(NAME_TABLE) == 64


def test_daguo_structure():
    """样例卦图：震宫 泽风大过（游魂）"""
    h = by_name("泽风大过")
    assert h["palace"] == "震"
    assert h["generation"] == "游魂"
    assert h["shi"] == 4 and h["ying"] == 1
    # 与卦图逐爻核对：辛丑/辛亥/辛酉/丁亥/丁酉/丁未
    expect = [("辛", "丑", "土", "妻财"), ("辛", "亥", "水", "父母"),
              ("辛", "酉", "金", "官鬼"), ("丁", "亥", "水", "父母"),
              ("丁", "酉", "金", "官鬼"), ("丁", "未", "土", "妻财")]
    for y, (g, z, w, q) in zip(h["yao"], expect):
        assert (y["gan"], y["zhi"], y["wuxing"], y["liuqin"]) == (g, z, w, q)


def test_lihuo_structure():
    """变卦：离为火（六冲），世6应3"""
    h = by_name("离为火")
    assert h["palace"] == "离" and h["shi"] == 6
    expect = [("卯", "木"), ("丑", "土"), ("亥", "水"),
              ("酉", "金"), ("未", "土"), ("巳", "火")]
    for y, (z, w) in zip(h["yao"], expect):
        assert (y["zhi"], y["wuxing"]) == (z, w)


def test_xunkong():
    assert xunkong("壬寅") == ("辰", "巳")  # 卦图：日空辰巳
    assert xunkong("甲子") == ("戌", "亥")
    assert xunkong("癸巳") == ("午", "未")  # 卦图：月空午未
    assert xunkong("丙午") == ("寅", "卯")  # 卦图：年空寅卯
    with pytest.raises(ValueError):
        parse_gz("甲丑")


def test_sample_facts():
    """样例卦图全量事实：丙午年 癸巳月 壬寅日，大过之离，初二五上动"""
    lines = list(NAME_TABLE["泽风大过"]["lines"])
    facts = build_facts({
        "question": "测试", "category": "其他",
        "ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅", "hour": "甲辰"},
        "ben_lines": lines, "dong": [1, 2, 5, 6],
    })
    assert facts["biangua"]["name"] == "离为火"
    assert facts["global"]["liuchong"] is False
    assert facts["global"]["bian_liuchong"] is True
    # 六神：壬日初爻起玄武（与卦图一致：玄武/青龙/朱雀/勾陈/螣蛇/白虎）
    assert [y["liushen"] for y in facts["yao"]] == \
        ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"]
    # 变爻六亲核对卦图：初爻财丑土→兄卯木，2爻父亥水→财丑土，5爻鬼酉金→财未土，6爻财未土→孙巳火
    assert facts["yao"][0]["bian"]["liuqin"] == "兄弟"
    assert facts["yao"][1]["bian"]["liuqin"] == "妻财"
    assert facts["yao"][4]["bian"]["liuqin"] == "妻财"
    assert facts["yao"][5]["bian"]["liuqin"] == "子孙"
    # 伏神：大过缺子孙、兄弟 → 本宫震为雷取 孙庚午火(4爻)、兄庚寅木(2爻)…卦图六伏全列但缺者才是真伏
    fu = {f["liuqin"]: f for f in facts["fushen"]}
    assert set(fu) == {"子孙", "兄弟"}
    assert (fu["子孙"]["gan"], fu["子孙"]["zhi"]) == ("庚", "午")
    assert fu["子孙"]["fei_pos"] == 4
    assert (fu["兄弟"]["gan"], fu["兄弟"]["zhi"]) == ("庚", "寅")
    # 旬空：辰巳空 → 六爻中无辰巳；伏神孙午火不空
    assert not any(y["kong"] for y in facts["yao"])
    # 巳月：酉金官鬼囚? 巳月金死?（巳火克金→死）亥水囚?（水克火→囚）
    assert facts["yao"][2]["yue"]["wangshuai"] == "死"
    assert facts["yao"][1]["yue"]["wangshuai"] == "囚"
    # 寅日：亥水爻 日合（寅亥合）
    assert "日合" in facts["yao"][1]["ri"]
    # 月建巳 冲 亥 → 2爻4爻月破
    assert facts["yao"][1]["yue"]["yuepo"] is True
    assert facts["yao"][3]["yue"]["yuepo"] is True


def test_wangshuai():
    assert yue_wangshuai("火", "火") == "旺"
    assert yue_wangshuai("土", "火") == "相"
    assert yue_wangshuai("木", "火") == "休"
    assert yue_wangshuai("水", "火") == "囚"
    assert yue_wangshuai("金", "火") == "死"


def test_jintui_hua():
    assert jin_tui("寅", "卯") == "化进神"
    assert jin_tui("卯", "寅") == "化退神"
    assert jin_tui("丑", "辰") == "化进神"
    assert jin_tui("戌", "丑") == "化进神"  # 土循环回转
    assert jin_tui("寅", "巳") is None
    assert "化回头克" in hua_relation("午", "亥")  # 午火化亥水
    assert "化墓" in hua_relation("寅", "未")      # 木化未墓
    assert "伏吟" in hua_relation("子", "子")
    assert "反吟" in hua_relation("子", "午")


def test_liuhe_gua():
    facts = build_facts({"question": "t", "category": "其他",
                         "ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅"},
                         "ben_lines": list(NAME_TABLE["地天泰"]["lines"]), "dong": []})
    assert facts["global"]["liuhe"] is True
    facts2 = build_facts({"question": "t", "category": "其他",
                          "ganzhi": {"year": "丙午", "month": "癸巳", "day": "壬寅"},
                          "ben_lines": list(NAME_TABLE["天雷无妄"]["lines"]), "dong": []})
    assert facts2["global"]["liuchong"] is True


def test_all_palaces_shi_ying():
    for name, info in NAME_TABLE.items():
        h = by_name(name)
        assert abs(h["shi"] - h["ying"]) == 3
        assert len({y["zhi"] for y in h["yao"]}) >= 3
