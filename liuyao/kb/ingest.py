# -*- coding: utf-8 -*-
"""典籍切片入库：raw/*.txt → chunks.jsonl（书/章/段 + 特征标签）。"""
import json
import re
from pathlib import Path

RAW = Path(__file__).parent / "data" / "raw"
OUT = Path(__file__).parent / "data" / "chunks.jsonl"

BOOK_NAMES = {"zengshanbuyi": "增删卜易", "bushizhengzong": "卜筮正宗",
              "huozhulin": "火珠林", "zhouyi": "周易", "meihuayishu": "梅花易数"}

HEADING_PAT = [
    re.compile(r"^\d+[．.]\s*\S{1,12}$"),           # 火珠林 "1．易中明义"
    re.compile(r"^\d+\.\s*\S+（卦[一二三四五六七八九十百零\d]+）"),  # 周易卦
    re.compile(r"^\S{1,18}(章|篇|诀|歌|赋|论|说|例|要|法)$"),
    # 增删卜易 "用神章第八" / "六亲歌章第五"（'—'为OCR之'一'）
    re.compile(r"^\S{1,16}(章|歌|论|赋|篇|诀)第[又]?[—一二三四五六七八九十百\d]*\s*$"),
    re.compile(r"^(第?[一二三四五六七八九十百]+[问论]|凡例|序|自序|启蒙节要)"),
    re.compile(r"^卷[之一二三四五六七八九十]+$"),
    re.compile(r"^\S{1,14}(问答|凡例|之谬)$"),
]

FEATURE_TAGS = {
    "旬空": ["旬空", "空亡", "出空", "冲空", "填空"],
    "月破": ["月破", "出破", "实破", "破而"],
    "伏神": ["伏神", "伏藏", "飞神", "出伏", "引拔"],
    "进退神": ["进神", "退神"],
    "反吟伏吟": ["反吟", "伏吟"],
    "三合": ["三合", "合局", "成局"],
    "六冲": ["六冲", "冲卦", "冲中"],
    "六合": ["六合", "合处"],
    "墓绝": ["入墓", "化墓", "墓库", "化绝", "开库"],
    "暗动": ["暗动"],
    "应期": ["应期", "应在", "何日", "何时", "断日"],
    "用神": ["用神", "元神", "原神", "忌神", "仇神"],
    "世应": ["世爻", "应爻", "世应", "持世"],
    "游魂归魂": ["游魂", "归魂"],
    "回头生克": ["回头生", "回头克"],
    "独发尽发": ["独发", "尽发", "独静", "尽静"],
    "卦身": ["卦身", "月卦"],
}

CATEGORY_TAGS = {
    "求财": ["求财", "财爻", "买卖", "生意", "货物", "开行", "开店", "放债", "索债"],
    "婚姻": ["婚姻", "占婚", "嫁", "娶", "妻妾", "夫妇", "媒"],
    "官司": ["词讼", "官司", "占讼", "讼事", "官非", "罪责"],
    "疾病": ["疾病", "占病", "病症", "医药", "痊愈", "医治", "病愈"],
    "出行": ["出行", "行人", "舟船", "途中", "归期", "远行"],
    "失物": ["失物", "盗贼", "寻人", "走失", "遗失"],
    "事业": ["功名", "仕宦", "升迁", "谋事", "求名", "赴任", "考试", "官运"],
    "子女": ["六甲", "胎孕", "生产", "子嗣", "占产"],
    "天时": ["天时", "晴雨", "占雨", "占晴"],
    "家宅": ["家宅", "阳宅", "迁居", "屋舍"],
}


def is_heading(line: str) -> bool:
    line = line.strip()
    return bool(line) and len(line) <= 30 and any(p.match(line) for p in HEADING_PAT)


def tag_chunk(chapter: str, text: str) -> list:
    tags = set()
    hay = chapter + " " + text
    for tag, kws in {**FEATURE_TAGS, **CATEGORY_TAGS}.items():
        # 章节标题命中权重高：只要标题或正文出现关键词即打标
        if any(k in hay for k in kws):
            tags.add(tag)
    return sorted(tags)


def ingest(max_len=700, min_len=100):
    chunks = []
    for f in sorted(RAW.glob("*.txt")):
        book = f.stem
        name = BOOK_NAMES.get(book, book)
        lines = [l.replace("　", " ").replace("\t", " ").strip() for l in
                 f.read_text(encoding="utf-8").splitlines()]
        lines = [l for l in lines if not l.startswith("#")]
        chapter, buf = "卷首", ""

        def flush():
            nonlocal buf
            t = buf.strip()
            if len(t) >= min_len:
                chunks.append({"book": book, "book_name": name,
                               "chapter": chapter, "text": t,
                               "tags": tag_chunk(chapter, t)})
            buf = ""

        for l in lines:
            if not l:
                continue
            if is_heading(l):
                flush()
                chapter = l
                continue
            if len(buf) + len(l) > max_len and len(buf) >= min_len:
                flush()
            buf += l + "\n"
        flush()
    OUT.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in chunks),
                   encoding="utf-8")
    return chunks


if __name__ == "__main__":
    cs = ingest()
    from collections import Counter
    print(f"共 {len(cs)} 个切片")
    print(Counter(c["book"] for c in cs))
