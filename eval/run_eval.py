# -*- coding: utf-8 -*-
"""评测运行器：对 cases.jsonl 逐例跑完整断卦流程，统计准确率。
需本地LLM代理可用。用法：python eval/run_eval.py [--limit N] [--id zsby-s02]"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from liuyao.agents import orchestrator  # noqa: E402

CASES = Path(__file__).parent / "cases.jsonl"
OUT = Path(__file__).parent / "results"

# 大方向归一：先凶后吉视作吉（最终结果），先吉后凶视作凶
COARSE = {"吉": "吉", "凶": "凶", "先凶后吉": "吉", "先吉后凶": "凶", "平": "平"}


async def run_case(case):
    sid = orchestrator.new_session({
        "question": case["question"], "category": case["category"],
        "ganzhi": case["ganzhi"], "ben_lines": case["ben_lines"],
        "dong": case["dong"]})
    t0 = time.time()
    try:
        s = await orchestrator.interpret(sid)
        rep = s["report"]
        got = rep.get("direction", "平")
        exp = case["expected"]["direction"]
        return {"id": case["id"], "ok": True, "seconds": round(time.time() - t0, 1),
                "expected": exp, "got": got,
                "exact": got == exp,
                "coarse": COARSE.get(got, got) == COARSE.get(exp, exp),
                "got_yingqi": rep.get("yingqi", {}).get("best"),
                "expected_yingqi": case["expected"].get("yingqi"),
                "got_yongshen": rep.get("yongshen_review", {}).get("final_yongshen"),
                "expected_yongshen": case["expected"].get("yongshen"),
                "verdict": rep.get("verdict"),
                "confidence": rep.get("confidence")}
    except Exception as e:
        return {"id": case["id"], "ok": False, "error": f"{type(e).__name__}: {e}"}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--id", default=None)
    args = ap.parse_args()

    cases = [json.loads(l) for l in CASES.read_text(encoding="utf-8").splitlines()]
    if args.id:
        cases = [c for c in cases if c["id"] == args.id]
    if args.limit:
        cases = cases[:args.limit]

    results = []
    for c in cases:  # 串行跑，避免压垮本地代理
        print(f"▶ {c['id']} {c['question']} {c['bengua_name']}→{c['biangua_name']}…",
              flush=True)
        r = await run_case(c)
        results.append(r)
        mark = "✓" if r.get("coarse") else ("✗" if r.get("ok") else "⚠")
        print(f"  {mark} 期望{r.get('expected')} 得到{r.get('got', r.get('error'))}")

    done = [r for r in results if r.get("ok")]
    if done:
        print("\n===== 评测汇总 =====")
        print(f"跑通 {len(done)}/{len(results)}")
        print(f"吉凶大方向准确率: {sum(r['coarse'] for r in done)}/{len(done)}"
              f" = {sum(r['coarse'] for r in done)/len(done):.0%}")
        print(f"吉凶精确匹配率:   {sum(r['exact'] for r in done)}/{len(done)}"
              f" = {sum(r['exact'] for r in done)/len(done):.0%}")
        print("（用神/应期为文本描述，需人工比对下表）")
        for r in done:
            print(f"  {r['id']} 用神:{r['got_yongshen']} vs 期望:{r['expected_yongshen']}"
                  f" | 应期:{r['got_yingqi']} vs {r['expected_yingqi']}")
    OUT.mkdir(exist_ok=True)
    f = OUT / f"eval_{time.strftime('%Y%m%d_%H%M%S')}.json"
    f.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n明细已存 {f}")


if __name__ == "__main__":
    asyncio.run(main())
