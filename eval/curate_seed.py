# -*- coding: utf-8 -*-
"""种子评测集：从《增删卜易》候选断例中人工校对的12例（结局在原文中明确记载）。
ben_lines/dong 由卦名程序推出，防手工错误。运行生成 cases.jsonl。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from liuyao.core.palace import NAME_TABLE  # noqa: E402

SEEDS = [
    dict(id="zsby-s01", month="酉", day="辛亥", q="占求财", cat="求财",
         ben="兑为泽", bian="雷水解",
         direction="吉", yingqi="寅日（巳火化空待甲寅出空，寅木财生官生世）",
         note="原文：寅日得见财亦如心，果于寅日早见木日得财"),
    dict(id="zsby-s02", month="巳", day="乙未", q="自占病", cat="疾病",
         ben="泽风大过", bian="火风鼎",
         direction="凶", yongshen="世爻父母亥水",
         yingqi="卯日（冲去元神酉金之日）",
         note="原文：亥水月冲日克月破被克，用神无根元神有力亦难生，果卒于癸卯日"),
    dict(id="zsby-s03", month="卯", day="戊寅", q="占父官事已拟重罪", cat="官司",
         ben="泽地萃", bian="天火同人",
         direction="凶", yongshen="父母未土",
         note="原文：外卦未土父母卯月克之，内卦亥卯未合木局相克，月克日刑全无助，果至重刑"),
    dict(id="zsby-s04", month="辰", day="丙申", q="占弟癌症业已临危", cat="疾病",
         ben="水火既济", bian="泽火革",
         direction="吉", yongshen="兄弟亥水（世）",
         yingqi="本日酉时遇救，巳亥日全生",
         note="原文：月建辰土虽克亥水，兄弟赖申日以生之又得动爻相生，临危有救"),
    dict(id="zsby-s05", month="寅", day="丙申", q="占官之升迁", cat="事业",
         ben="艮为山", bian="山雷颐",
         direction="吉", yongshen="官鬼寅木（世）",
         yingqi="三月（辰土出空之月）",
         note="原文：寅木官星持世临月建，申子辰合水局生官，果于三月升任云南太守"),
    dict(id="zsby-s06", month="午", day="丁未", q="占弟被讼吉凶", cat="官司",
         ben="泽水困", bian="雷风恒",
         direction="凶", yongshen="兄弟酉金",
         yingqi="本年下狱，申年重刑（化退神退至申年无路）",
         note="原文：月建作忌神动于卦中为祸不浅，大凶之象，果于本年下狱至申年而重刑"),
    dict(id="zsby-s07", month="寅", day="丁酉", q="占开铺面", cat="求财",
         ben="艮为山", bian="地火明夷",
         direction="先吉后凶",
         yingqi="六月疾至（木墓于未），八月伙计盗尽",
         note="原文：世临寅木得令目下热闹，日辰克世世化回头克又六冲卦不吉，八月伙计盗尽鸣官分文不复"),
    dict(id="zsby-s08", month="午", day="丙辰", q="占出外经商贸易财如何", cat="求财",
         ben="雷风恒", bian="雷地豫",
         direction="吉", yongshen="世爻酉金／戌土财暗动生世",
         note="原文：冲中逢合，戌土财暗动生世，虽反复不常却有财利，果去而复反三次中途发财"),
    dict(id="zsby-s09", month="巳", day="甲寅", q="占延师训子", cat="其他",
         ben="天地否", bian="乾为天",
         direction="先吉后凶",
         yingqi="两月内",
         note="原文：应临父旺乃饱学之士，独嫌六合变六冲不久之兆，子水子孙旬空父动，后两月其子病死辞师"),
    dict(id="zsby-s10", month="寅", day="庚申", q="占子痘症", cat="疾病",
         ben="风火家人", bian="离为火",
         direction="凶", yongshen="子孙巳火",
         yingqi="寅日寅时",
         note="原文：巳火子孙当春令许可治，后死于寅日寅时——寅申巳三刑，野鹤自记误断之例（难例）"),
    dict(id="zsby-s11", month="丑", day="丁酉", q="占父出外一载无音", cat="出行",
         ben="风水涣", bian="坎为水",
         direction="吉", yongshen="父母卯木？（六爻卯木父动化子水回头生）",
         yingqi="交春二月归（世空至春填实）",
         note="原文：卯木父爻发动生世又化回头生，许在外平安，果于二月得意而回"),
    dict(id="zsby-s12", month="午", day="丙寅", q="占主病", cat="疾病",
         ben="离为火", bian="坎为水",
         direction="凶",
         yingqi="冬令必危（火衰之时）",
         note="原文：离火变坎水回头来克，午月火旺许之冬令必危，果卒于九月丁亥日"),
]


def main():
    out = []
    for s in SEEDS:
        lb = list(NAME_TABLE[s["ben"]]["lines"])
        lv = list(NAME_TABLE[s["bian"]]["lines"])
        dong = [i + 1 for i in range(6) if lb[i] != lv[i]]
        out.append({
            "id": s["id"], "source": "增删卜易",
            "question": s["q"], "category": s["cat"],
            "ganzhi": {"month": s["month"], "day": s["day"]},
            "bengua_name": s["ben"], "ben_lines": lb,
            "biangua_name": s["bian"], "dong": dong,
            "expected": {"direction": s["direction"],
                         "yongshen": s.get("yongshen"),
                         "yingqi": s.get("yingqi"),
                         "curated": True},
            "note": s["note"],
        })
    p = Path(__file__).parent / "cases.jsonl"
    p.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in out),
                 encoding="utf-8")
    print(f"{len(out)} 例 → {p.name}")
    for c in out:
        print(c["id"], c["bengua_name"], "→", c["biangua_name"], "动", c["dong"],
              "期望:", c["expected"]["direction"])


if __name__ == "__main__":
    main()
