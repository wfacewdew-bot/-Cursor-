from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFontDialog,
    QFileDialog,
)


class ControlPanel(QWidget):
    """弹幕控制面板，用于调节速度、数量、区域、样式等。"""

    def __init__(
        self,
        on_toggle_running: Callable[[], None],
        on_speed_changed: Callable[[int], None],
        on_max_words_changed: Callable[[int], None],
        on_region_changed: Callable[[str], None],
        on_color_changed: Callable[[str], None],
        on_font_changed: Callable[[QFont], None],
        on_border_radius_changed: Callable[[int], None],
        on_import_word_file: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_toggle_running = on_toggle_running
        self._on_speed_changed = on_speed_changed
        self._on_max_words_changed = on_max_words_changed
        self._on_region_changed = on_region_changed
        self._on_color_changed = on_color_changed
        self._on_font_changed = on_font_changed
        self._on_border_radius_changed = on_border_radius_changed
        self._on_import_word_file = on_import_word_file

        self._running = True

        self.setWindowTitle("弹幕控制面板")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 速度滑块
        self.speed_slider = QSlider(Qt.Horizontal, self)
        self.speed_slider.setRange(1, 20)
        self.speed_slider.setValue(4)
        self.speed_slider.valueChanged.connect(self._handle_speed_changed)
        form.addRow(QLabel("单词移动速度："), self.speed_slider)

        # 同屏数量
        self.max_words_spin = QSpinBox(self)
        self.max_words_spin.setRange(5, 200)
        self.max_words_spin.setValue(30)
        self.max_words_spin.valueChanged.connect(self._handle_max_words_changed)
        form.addRow(QLabel("同屏最大单词数："), self.max_words_spin)

        # 屏幕区域
        self.region_combo = QComboBox(self)
        self.region_combo.addItem("全屏", "full")
        self.region_combo.addItem("上半屏", "top")
        self.region_combo.addItem("中间 1/3", "middle")
        self.region_combo.addItem("下半屏", "bottom")
        self.region_combo.currentIndexChanged.connect(self._handle_region_changed)
        form.addRow(QLabel("单词所在区域："), self.region_combo)

        # 边框圆角
        self.border_radius_spin = QSpinBox(self)
        self.border_radius_spin.setRange(0, 100)
        self.border_radius_spin.setValue(30)
        self.border_radius_spin.valueChanged.connect(self._handle_border_radius_changed)
        form.addRow(QLabel("边框圆角半径："), self.border_radius_spin)

        layout.addLayout(form)

        # 样式按钮
        style_layout = QHBoxLayout()

        self.color_btn = QPushButton("选择文字颜色", self)
        self.color_btn.clicked.connect(self._choose_color)
        style_layout.addWidget(self.color_btn)

        self.font_btn = QPushButton("选择字体", self)
        self.font_btn.clicked.connect(self._choose_font)
        style_layout.addWidget(self.font_btn)

        self.import_btn = QPushButton("导入词库 (CSV/Excel)", self)
        self.import_btn.clicked.connect(self._import_word_file)
        style_layout.addWidget(self.import_btn)

        layout.addLayout(style_layout)

        # 运行控制
        control_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("暂停弹幕", self)
        self.toggle_btn.clicked.connect(self._toggle_running)
        control_layout.addWidget(self.toggle_btn)

        self.close_btn = QPushButton("关闭程序", self)
        self.close_btn.clicked.connect(self._exit_all)
        control_layout.addWidget(self.close_btn)

        layout.addLayout(control_layout)

        self.setLayout(layout)

    # 槽函数

    def _handle_speed_changed(self, value: int) -> None:
        self._on_speed_changed(int(value))

    def _handle_max_words_changed(self, value: int) -> None:
        self._on_max_words_changed(int(value))

    def _handle_region_changed(self, index: int) -> None:  # noqa: ARG002
        mode = self.region_combo.currentData()
        if isinstance(mode, str):
            self._on_region_changed(mode)

    def _handle_border_radius_changed(self, value: int) -> None:
        self._on_border_radius_changed(int(value))

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(parent=self, title="选择单词颜色")
        if color.isValid():
            self._on_color_changed(color.name())

    def _choose_font(self) -> None:
        ok, font = QFontDialog.getFont(self)
        if ok:
            self._on_font_changed(font)

    def _toggle_running(self) -> None:
        self._running = not self._running
        self._on_toggle_running()
        self.toggle_btn.setText("恢复弹幕" if not self._running else "暂停弹幕")

    def _exit_all(self) -> None:
        # 让上层负责真正关闭窗口和应用
        self.close()
        # 其余窗口及应用退出逻辑在 main.py 中处理

    def _import_word_file(self) -> None:
        """选择本地 CSV/Excel 文件并交给上层导入到数据库。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择词库文件（CSV/Excel）",
            "",
            "词库文件 (*.csv *.xlsx *.xlsm *.xltx *.xltm);;所有文件 (*.*)",
        )
        if file_path:
            self._on_import_word_file(file_path)

