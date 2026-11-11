# -*- coding: utf-8 -*-
"""从《增删卜易》全文半自动抽取断例 → candidates.jsonl。
动爻由 本卦→变卦 之差程序推出；expected 字段留给人工依原文校对填写。"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from liuyao.core.palace import NAME_TABLE  # noqa: E402

RAW = Path(__file__).parent.parent / "liuyao" / "kb" / "data" / "raw" / "zengshanbuyi.txt"
OUT = Path(__file__).parent / "candidates.jsonl"

# 卦名别名（书中常用简称）
ALIAS = {}
for full in NAME_TABLE:
    ALIAS[full] = full
    if full[1] == "为":  # 乾为天 → 乾
        ALIAS[full[0]] = full
    else:
        ALIAS[full[2:]] = full  # 泽风大过 → 大过

PAT = re.compile(
    r"([子丑寅卯辰巳午未申酉戌亥])月[，,]?\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日"
    r"([^：]{0,50}?)[卜占]([^：]{0,40}?)得([一-龥]{1,8}?)(?:[变之]([一-龥]{1,8}?))?卦")

CATEGORY_KW = [("求财", ["财", "生意", "买卖", "铺", "经商", "贸易"]),
               ("疾病", ["病", "症", "痊", "危", "痘"]),
               ("官司", ["讼", "罪", "官司", "官非"]),
               ("事业", ["功名", "升迁", "出仕", "文书", "考", "任", "官之"]),
               ("婚姻", ["婚", "嫁", "娶"]),
               ("出行", ["出外", "行人", "归", "出行"]),
               ("子女", ["子", "痘", "胎", "产"])]


def guess_category(text):
    for cat, kws in CATEGORY_KW:
        if any(k in text for k in kws):
            return cat
    return "其他"


def dong_from(ben, bian):
    lb, lv = NAME_TABLE[ben]["lines"], NAME_TABLE[bian]["lines"]
    return [i + 1 for i in range(6) if lb[i] != lv[i]]


def main():
    t = RAW.read_text(encoding="utf-8").replace("　", "")
    flat = t.replace("\n", "")
    out = []
    for m in PAT.finditer(flat):
        month, day, who, what, ben_raw, bian_raw = m.groups()
        ben = ALIAS.get(ben_raw.strip("，, "))
        if not ben:
            continue
        bian = ALIAS.get((bian_raw or "").strip("，, ")) if bian_raw else None
        if not bian:  # 处理"得X卦变Y卦"：匹配结束位置向后找"变Y卦"
            m2 = re.match(r"[变之]([一-龥]{1,8}?)卦", flat[m.end():m.end() + 14])
            if m2:
                bian = ALIAS.get(m2.group(1).strip("，, "))
        dong = dong_from(ben, bian) if bian else []
        q = (who + "占" + what).strip("，, ")
        excerpt = flat[m.start():m.start() + 420]
        out.append({
            "id": f"zsby-{len(out)+1:03d}",
            "source": "增删卜易",
            "question": q, "category": guess_category(q),
            "ganzhi": {"month": month, "day": day},
            "bengua_name": ben, "ben_lines": list(NAME_TABLE[ben]["lines"]),
            "biangua_name": bian, "dong": dong,
            "source_excerpt": excerpt,
            "expected": {"direction": None, "yongshen": None, "yingqi": None,
                         "curated": False},
        })
    OUT.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in out),
                   encoding="utf-8")
    print(f"抽取 {len(out)} 例 → {OUT.name}（expected 需人工依 source_excerpt 校对）")


if __name__ == "__main__":
    main()
