from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """获取到本地 SQLite 数据库的连接。"""
    db_path = Path(DB_PATH)
    conn = sqlite3.connect(db_path)
    # 返回行时用字典访问更方便
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库（如果不存在则创建）。"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE
            );
            """
        )
        conn.commit()


def count_words() -> int:
    """返回当前库中单词数量。"""
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) AS c FROM words;")
        row = cur.fetchone()
        return int(row["c"]) if row else 0


def bulk_insert_words(words: Iterable[str]) -> int:
    """批量插入单词，返回成功插入的数量。"""
    cleaned: List[str] = []
    for w in words:
        w = w.strip()
        if not w:
            continue
        cleaned.append(w)

    if not cleaned:
        return 0

    with get_connection() as conn:
        # 使用 INSERT OR IGNORE 避免重复导致报错
        conn.executemany(
            "INSERT OR IGNORE INTO words (word) VALUES (?);",
            ((w,) for w in cleaned),
        )
        conn.commit()

        cur = conn.execute("SELECT changes() AS changed;")
        row = cur.fetchone()
        return int(row["changed"]) if row else 0


def get_random_words(limit: int) -> List[str]:
    """随机返回若干个单词。"""
    if limit <= 0:
        return []

    with get_connection() as conn:
        cur = conn.execute(
            "SELECT word FROM words ORDER BY RANDOM() LIMIT ?;", (limit,)
        )
        return [r["word"] for r in cur.fetchall()]


def get_random_word() -> str | None:
    """随机返回一个单词。"""
    words = get_random_words(1)
    return words[0] if words else None

