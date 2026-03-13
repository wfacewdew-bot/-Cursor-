from pathlib import Path


# 本地 SQLite 数据库文件路径
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "words.db"

# 六级词库下载地址（GitHub 原始文本）
# 数据示例：abandon vt.放弃,遗弃; ...
CET6_URL = (
    "https://raw.githubusercontent.com/hehonghui/en_dict/master/CET6_edited.txt"
)

# 弹幕配置

# 同屏最大单词数量
MAX_WORDS_ON_SCREEN = 30

# 单个单词的移动速度（像素/帧，帧率由 MOVE_INTERVAL_MS 决定）
WORD_SPEED_PX_PER_TICK = 4

# 弹幕移动计时器间隔（毫秒）——越小越流畅但更占 CPU
MOVE_INTERVAL_MS = 30

# 新单词生成的间隔（毫秒）
SPAWN_INTERVAL_MS = 800

# 字体配置
FONT_FAMILY = "Segoe UI"
FONT_POINT_SIZE = 18

# 文本颜色（CSS 格式）
TEXT_COLOR = "#ffffff"

# 文本阴影/描边可以通过样式表简单模拟
TEXT_OUTLINE_COLOR = "#000000"

