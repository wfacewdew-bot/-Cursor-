from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QLabel, QMessageBox, QWidget

import config


class ClickableLabel(QLabel):
    """可点击的标签，用于单词弹幕。"""

    clicked = Signal(str)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        super().mousePressEvent(event)
        self.clicked.emit(self.text())


@dataclass
class DanmakuItem:
    """表示一个在屏幕上移动的单词。"""

    label: ClickableLabel
    speed: int
    bg_color: str


class DanmakuWindow(QWidget):
    """全屏透明窗口，用来显示单词弹幕，并支持运行时调节。"""

    def __init__(
        self,
        get_word_func: Callable[[], Optional[str]],
        get_meaning_func: Callable[[str], Optional[str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._get_word = get_word_func
        self._get_meaning = get_meaning_func
        self.items: List[DanmakuItem] = []

        # 当前运行参数（可被控制面板修改）
        self._word_speed = max(1, int(config.WORD_SPEED_PX_PER_TICK))
        self._max_words = int(config.MAX_WORDS_ON_SCREEN)
        self._region_mode = "top"  # full/top/middle/bottom
        self._font = QFont(config.FONT_FAMILY, config.FONT_POINT_SIZE)
        self._text_color = config.TEXT_COLOR
        self._outline_color = config.TEXT_OUTLINE_COLOR
        self._paused = False
        self._border_radius = 999  # 默认很大的圆角，让边框呈椭圆形

        # 全屏、置顶、无边框、背景透明
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.setGeometry(geometry)

        flags = (
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # 防止任务栏出现图标
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 不获取焦点，尽量减少对用户操作的干扰
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # 创建定时器
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._on_move_timer)
        self.move_timer.start(config.MOVE_INTERVAL_MS)

        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self._on_spawn_timer)
        self.spawn_timer.start(config.SPAWN_INTERVAL_MS)

        # 预先填充一些单词
        # for _ in range(min(self._max_words, 10)):
        #     self._spawn_one_word()

    # 对外控制接口（供控制面板调用）

    def toggle_running(self) -> None:
        if self._paused:
            self._resume()
        else:
            self._pause()

    def _pause(self) -> None:
        if self._paused:
            return
        self._paused = True
        self.move_timer.stop()
        self.spawn_timer.stop()

    def _resume(self) -> None:
        if not self._paused:
            return
        self._paused = False
        self.move_timer.start(config.MOVE_INTERVAL_MS)
        self.spawn_timer.start(config.SPAWN_INTERVAL_MS)

    def set_word_speed(self, speed: int) -> None:
        self._word_speed = max(1, int(speed))
        # 同时更新所有已经在屏幕上的单词速度
        for item in self.items:
            item.speed = self._word_speed

    def set_max_words(self, count: int) -> None:
        self._max_words = max(1, int(count))

    def set_region_mode(self, mode: str) -> None:
        if mode in {"full", "top", "middle", "bottom"}:
            self._region_mode = mode

    def set_text_color(self, color: str) -> None:
        self._text_color = color
        self._refresh_labels_style()

    def set_font(self, font: QFont) -> None:
        self._font = font
        for item in self.items:
            item.label.setFont(self._font)
            item.label.adjustSize()

    def set_border_radius(self, radius: int) -> None:
        """由控制面板调用，动态调整圆角大小。"""
        self._border_radius = max(0, int(radius))
        self._refresh_labels_style()

    # 内部逻辑

    def _current_region(self) -> tuple[int, int]:
        """根据区域模式返回 (min_y, max_y)。"""
        screen_rect = self.geometry()
        h = screen_rect.height()

        if self._region_mode == "full":
            top_ratio, bottom_ratio = 0.0, 1.0
        elif self._region_mode == "middle":
            top_ratio, bottom_ratio = 1 / 3, 2 / 3
        elif self._region_mode == "bottom":
            top_ratio, bottom_ratio = 0.5, 1.0
        else:  # 默认上半屏
            top_ratio, bottom_ratio = 0.0, 0.5

        min_y = screen_rect.top() + int(h * top_ratio)
        max_y = screen_rect.top() + int(h * bottom_ratio)
        return min_y, max_y

    def _label_stylesheet(self, bg_color: str) -> str:
        # 椭圆背景 + 内边距 + 文本阴影
        return (
            f"color: {self._text_color};"
            f"text-shadow: 1px 1px 2px {self._outline_color};"
            f"background-color: {bg_color};"
            f"border-radius: {self._border_radius}px;"  # 动态圆角，形成椭圆胶囊形状
            "padding: 4px 10px;"     # 上下/左右内边距
        )

    def _refresh_labels_style(self) -> None:
        for item in self.items:
            item.label.setStyleSheet(self._label_stylesheet(item.bg_color))

    def _random_bg_color(self) -> str:
        """生成一个随机但不接近白色的背景颜色。"""
        # 使用 HSL 思路手动控制，避免太亮：随机 RGB，每个分量限制在 0-220
        r = random.randint(0, 220)
        g = random.randint(0, 220)
        b = random.randint(0, 220)
        # 如果太接近灰色/白色，就稍微压一压
        if r > 200 and g > 200 and b > 200:
            r, g, b = 180, 180, 180
        return f"rgb({r}, {g}, {b})"

    def _on_label_clicked(self, word: str) -> None:
        if not self._get_meaning:
            return
        meaning = self._get_meaning(word) or "（没有找到释义）"
        QMessageBox.information(self, word, f"{word}\n\n{meaning}")

    def _create_label_for_word(self, word: str) -> tuple[ClickableLabel, str]:
        bg_color = self._random_bg_color()
        label = ClickableLabel(word, self)
        label.setFont(self._font)
        label.setStyleSheet(self._label_stylesheet(bg_color))
        if self._get_meaning:
            meaning = self._get_meaning(word)
            if meaning:
                label.setToolTip(meaning)
        label.clicked.connect(self._on_label_clicked)
        label.adjustSize()
        label.show()
        return label, bg_color

    def _spawn_one_word(self) -> None:
        if len(self.items) >= self._max_words:
            return

        word = self._get_word()
        if not word:
            return

        label, bg_color = self._create_label_for_word(word)
        screen_rect = self.geometry()

        # 单词从右侧随机高度进入
        x = screen_rect.right()
        min_y, max_y = self._current_region()
        y = random.randint(min_y, max_y)

        label.move(QPoint(x, y))

        speed = max(1, int(self._word_speed))
        self.items.append(DanmakuItem(label=label, speed=speed, bg_color=bg_color))

    def _on_move_timer(self) -> None:
        if not self.items:
            return

        screen_rect = self.geometry()
        to_remove: List[DanmakuItem] = []

        for item in self.items:
            label = item.label
            pos = label.pos()
            new_x = pos.x() - item.speed

            if new_x + label.width() < screen_rect.left():
                # 飞出屏幕，标记删除
                to_remove.append(item)
            else:
                label.move(new_x, pos.y())

        # 删除飞出屏幕的单词
        for item in to_remove:
            self.items.remove(item)
            item.label.deleteLater()

    def _on_spawn_timer(self) -> None:
        # 控制同屏数量
        if len(self.items) < self._max_words:
            self._spawn_one_word()
