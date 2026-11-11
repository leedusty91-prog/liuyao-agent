# 六爻多Agent断卦平台

上传卦图 → 视觉识别（引擎交叉校验）→ 规则引擎算清卦理事实 → 流水线Agent（用神/旺衰/动变/应期）→ 四流派Agent并行断卦（增删卜易/卜筮正宗/火珠林/天纪经占，引经据典）→ 裁判Agent终审 → 断语报告 + 多轮追问。

架构详见 `DESIGN.md`。

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env          # 填入本地LLM代理配置
uvicorn liuyao.api.main:app --port 8046
# 打开 http://127.0.0.1:8046
```

要求本地代理模型支持图片输入（识卦用）；纯文字断卦不依赖多模态（可在确认页手动填卦）。

## 目录

```
liuyao/core/      规则引擎（纳甲/世应/旺衰/空破/合冲/动变/伏神 → 卦理事实表）
liuyao/agents/    识卦 / 流水线四Agent / 四流派 / 裁判 / 编排器
liuyao/kb/        典籍知识库（五部公版全文，677切片，标签+关键词检索）
liuyao/api/       FastAPI
web/              前端单页
tests/            规则引擎单测（pytest tests/）
eval/             评测：cases.jsonl 12例种子（增删卜易实证断例）
```

## 评测

```bash
python eval/run_eval.py            # 全量12例（每例约9-13次LLM调用）
python eval/run_eval.py --id zsby-s02
python eval/extract_cases.py       # 重新生成85例候选，供继续人工校对扩充
```

指标：吉凶大方向准确率、精确匹配率；用神与应期为文本描述，跑完后人工比对。

## 设计要点

事实与推理分离：所有可确定性计算的卦理（旺衰、空亡、月破、合冲、进退、墓绝、伏神、三合候选、暗动）由 `liuyao/core` 纯代码算出，LLM只做取舍、权衡与表达，且不得与事实表矛盾。识卦只提取最小必要信息（干支+卦名+动爻），六亲六神世应伏神全部由引擎重算并与图中标注交叉校验，不符则警告用户确认。
