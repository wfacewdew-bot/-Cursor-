from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import requests

from config import CET6_URL


def _parse_cet6_lines(lines: Iterable[str]) -> List[Tuple[str, str]]:
    """
    从 CET6_edited.txt 的行中解析出英文单词及其释义。

    每行大致格式：
    abandon vt.放弃,遗弃; ...
    """
    entries: List[Tuple[str, str]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if not parts:
            continue
        word = parts[0].strip()
        # 过滤掉明显不是单词的内容
        if not word.isalpha():
            continue
        meaning = ""
        if len(parts) > 1:
            meaning = parts[1].strip()
        entries.append((word, meaning))
    return entries


def download_cet6_entries(timeout: int = 20) -> List[Tuple[str, str]]:
    """从网络下载六级词库并解析出 (英文, 释义) 列表。"""
    resp = requests.get(CET6_URL, timeout=timeout)
    resp.raise_for_status()
    text = resp.text
    lines = text.splitlines()
    return _parse_cet6_lines(lines)


def download_cet6_words(timeout: int = 20) -> List[str]:
    """兼容旧接口：仅返回英文单词列表。"""
    entries = download_cet6_entries(timeout=timeout)
    return [w for w, _ in entries]


def build_cet6_dict(timeout: int = 20) -> Dict[str, str]:
    """构建 word -> 中文释义 的字典，用于点击单词时展示。"""
    entries = download_cet6_entries(timeout=timeout)
    return {w: m for w, m in entries}

