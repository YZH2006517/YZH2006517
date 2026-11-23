"""把 Noto Serif SC（SIL OFL 1.1）裁成计数牌要用的两个小字体，嵌进 README 的 SVG 里。

    python tools/build_plaque_font.py

只在本机跑一次；产物 tools/fonts/serif-{500,700}.woff2 提交进仓库，
GitHub Actions 每天重画计数牌时直接读它们（嵌入 + 量字宽），不依赖系统字体。
以后计数牌上要加新的汉字，把字加进 CHARS 重跑一次。
"""
import string
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

SRC = Path(r"C:\Windows\Fonts\NotoSerifSC-VF.ttf")
OUT = Path(__file__).resolve().parent / "fonts"
CHARS = string.ascii_letters + string.digits + " ,.·-+&:/()" + "累计下载每日更新个项目"

OUT.mkdir(exist_ok=True)
for weight in (500, 700):
    font = TTFont(SRC)
    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "lnum", "tnum"]
    opts.name_IDs = ["*"]          # 保留版权和 OFL 许可信息
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    font = instancer.instantiateVariableFont(font, {"wght": weight})
    font.flavor = "woff2"
    path = OUT / f"serif-{weight}.woff2"
    font.save(path)
    print(path.name, path.stat().st_size, "bytes")
