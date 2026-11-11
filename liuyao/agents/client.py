# -*- coding: utf-8 -*-
"""LLM 客户端封装：OpenAI 兼容接口 + JSON 解析容错。"""
import base64
import json
import re
import asyncio

from ..config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY,
                         timeout=LLM_TIMEOUT)
    return _client


def chat(messages, model=None, temperature=0.3, max_tokens=4096):
    resp = get_client().chat.completions.create(
        model=model or LLM_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content or ""


async def achat(messages, **kw):
    return await asyncio.to_thread(chat, messages, **kw)


def image_content(image_bytes: bytes, mime: str = "image/png"):
    b64 = base64.b64encode(image_bytes).decode()
    return {"type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"}}


def parse_json(text: str):
    """从LLM输出中稳健提取JSON对象。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError(f"输出中无JSON: {text[:200]}")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    return json.loads(text[start:])
