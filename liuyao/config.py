# -*- coding: utf-8 -*-
"""配置：从 .env / 环境变量读取 LLM 接口设置。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8045/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-3-flash-agent")
# 识卦与裁判可单独指定更强模型；默认与主模型相同
LLM_VISION_MODEL = os.environ.get("LLM_VISION_MODEL", LLM_MODEL)
LLM_JUDGE_MODEL = os.environ.get("LLM_JUDGE_MODEL", LLM_MODEL)
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "180"))

KB_DIR = ROOT / "liuyao" / "kb" / "data"
