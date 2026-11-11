# -*- coding: utf-8 -*-
"""标签+关键词混合检索（无外部依赖）。
按 求测类别 + 卦理特征标签 定向检索，非纯语义检索。"""
import json
from pathlib import Path

CHUNKS_FILE = Path(__file__).parent / "data" / "chunks.jsonl"
_cache = None


def load_chunks():
    global _cache
    if _cache is None:
        if not CHUNKS_FILE.exists():
            from .ingest import ingest
            ingest()
        _cache = [json.loads(l) for l in
                  CHUNKS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return _cache


def features_from_facts(facts: dict) -> list:
    """从卦理事实表提取检索用特征标签。"""
    feats = set()
    g = facts["global"]
    if g["liuchong"] or g.get("bian_liuchong"):
        feats.add("六冲")
    if g["liuhe"] or g.get("bian_liuhe"):
        feats.add("六合")
    if g["generation"] in ("游魂", "归魂"):
        feats.add("游魂归魂")
    if g["sanhe"]:
        feats.add("三合")
    if facts["fushen"]:
        feats.add("伏神")
    for y in facts["yao"]:
        if y["kong"] or (y["bian"] and y["bian"]["kong"]):
            feats.add("旬空")
        if y["yue"]["yuepo"]:
            feats.add("月破")
        if y["andong"]:
            feats.add("暗动")
        for h in y["hua"]:
            if "进神" in h or "退神" in h:
                feats.add("进退神")
            if h in ("伏吟", "反吟"):
                feats.add("反吟伏吟")
            if h in ("化墓", "化绝"):
                feats.add("墓绝")
            if "回头" in h:
                feats.add("回头生克")
        if "入日墓" in y["ri"]:
            feats.add("墓绝")
    feats.add("用神")
    feats.add("应期")
    return sorted(feats)


def retrieve(books: list, category: str, features: list, k: int = 6,
             query: str = "") -> list:
    """打分：类别标签命中+3，特征标签命中+2，query词命中每次+1，章题命中额外+2。"""
    out = []
    for c in load_chunks():
        if c["book"] not in books:
            continue
        score = 0
        if category in c["tags"]:
            score += 3
        score += 2 * len(set(features) & set(c["tags"]))
        for w in query.split():
            if w and w in c["text"]:
                score += 1
        if category and category[:2] in c["chapter"]:
            score += 4  # 章题直接命中类别（如"求财章"）权重最高
        if c["chapter"] == "卷首":
            score -= 2  # 序言/目录降权
        if score > 0:
            out.append((score, c))
    out.sort(key=lambda x: -x[0])
    # 结果多样化：每章最多取2条
    seen, result = {}, []
    for s, c in out:
        key = (c["book"], c["chapter"])
        if seen.get(key, 0) >= 2:
            continue
        seen[key] = seen.get(key, 0) + 1
        result.append(c)
        if len(result) >= k:
            break
    return result
