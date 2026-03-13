from __future__ import annotations

import csv
import sys
import traceback
from pathlib import Path
from typing import Optional

import openpyxl
from PySide6.QtWidgets import QApplication

from config import DB_PATH
from control_panel import ControlPanel
from danmaku_window import DanmakuWindow
from db import bulk_insert_words, count_words, get_random_word, init_db
from word_source import build_cet6_dict, download_cet6_words


def ensure_db_initialized() -> None:
    """初始化数据库并在需要时下载六级词库写入。"""
    print(f"使用本地数据库: {DB_PATH}")
    init_db()
    existing = count_words()
    print(f"当前数据库中单词数量: {existing}")

    if existing > 0:
        return

    print("数据库为空，开始从网络下载 CET-6 词库...")
    try:
        words = download_cet6_words()
    except Exception as exc:  # noqa: BLE001
        print("下载或解析六级词库失败：", exc)
        traceback.print_exc()
        print("程序将退出，请检查网络或稍后重试。")
        sys.exit(1)

    print(f"下载完成，共解析出 {len(words)} 个单词，开始写入数据库...")
    inserted = bulk_insert_words(words)
    print(f"成功写入 {inserted} 个新单词。")

    if inserted == 0:
        print("警告：未能写入任何单词，请检查数据源。")


def load_words_from_file(path: str) -> list[str]:
    """从本地 CSV/Excel 文件读取第一列作为单词列表。"""
    words: list[str] = []
    suffix = Path(path).suffix.lower()

    try:
        if suffix == ".csv":
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    w = str(row[0]).strip()
                    if w:
                        words.append(w)
        elif suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(min_row=1, values_only=True):
                cell = row[0]
                if not cell:
                    continue
                w = str(cell).strip()
                if w:
                    words.append(w)
        else:
            print(f"不支持的词库文件类型: {path}")
    except Exception as exc:  # noqa: BLE001
        print(f"读取词库文件失败: {path} -> {exc}")

    return words


def main() -> None:
    ensure_db_initialized()

    # 如果本地已经有单词，就不再从网络加载六级释义，避免每次启动都访问网络。
    if count_words() > 0:
        print("检测到本地已有单词，将跳过网络加载六级词库释义。")
        cet6_dict: dict[str, str] = {}
    else:
        print("正在加载六级词库释义（用于点击单词查看中文）...")
        cet6_dict = build_cet6_dict()

    def get_meaning(word: str) -> Optional[str]:
        return cet6_dict.get(word)

    app = QApplication.instance() or QApplication([])

    # 弹幕窗口
    danmaku = DanmakuWindow(get_word_func=get_random_word, get_meaning_func=get_meaning)
    danmaku.showFullScreen()

    # 控制面板
    def toggle_running() -> None:
        danmaku.toggle_running()

    def change_speed(value: int) -> None:
        danmaku.set_word_speed(value)

    def change_max_words(value: int) -> None:
        danmaku.set_max_words(value)

    def change_region(mode: str) -> None:
        danmaku.set_region_mode(mode)

    def change_color(color: str) -> None:
        danmaku.set_text_color(color)

    def change_font(font) -> None:
        danmaku.set_font(font)

    def change_border_radius(value: int) -> None:
        danmaku.set_border_radius(value)

    def import_word_file(path: str) -> None:
        print(f"开始从本地文件导入词库: {path}")
        words = load_words_from_file(path)
        if not words:
            print("未从文件读取到任何单词。")
            return
        inserted = bulk_insert_words(words)
        print(f"导入完成，本次新增单词数量: {inserted}")

    panel = ControlPanel(
        on_toggle_running=toggle_running,
        on_speed_changed=change_speed,
        on_max_words_changed=change_max_words,
        on_region_changed=change_region,
        on_color_changed=change_color,
        on_font_changed=change_font,
        on_border_radius_changed=change_border_radius,
        on_import_word_file=import_word_file,
    )
    panel.show()

    print("已启动弹幕窗口和控制面板。关闭控制面板或弹幕窗口即可退出程序。")
    app.exec()


if __name__ == "__main__":
    main()

