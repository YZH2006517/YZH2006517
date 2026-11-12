"""生成个人网站和 GitHub 主页 README 共用的“神圣像素”素材。

    python tools/sanctum.py

输出：
  site/ornaments.css          网站用的像素花纹（CSS 遮罩 / 底纹，data URI）
  assets/banner-{light,dark}.svg        README 头图：玫瑰窗、天光、城市剪影、手抄本金框
  assets/plate-{studio,android}-{light,dark}.svg   两个项目的标题牌
  assets/divider-{light,dark}.svg       花纹分隔线
  assets/studio-altar.webp              三联祭坛式的观片台截图
  assets/studio-nave.webp               尖拱金框里的观片台主图

README 里的 SVG 是当 <img> 加载的，不能用网页字体，所以文字用下面这套 5×7 像素字自己画。
玫瑰窗的算法和 site/glory.js 里那份是同一个，改一边记得改另一边。
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "site" / "assets" / "img"

# ───────── 像素小工具 ─────────

def runs(grid, ch):
    """同色横向连续格合并成矩形，输出 path 的 d。"""
    d = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            if row[x] == ch:
                s = x
                while x < len(row) and row[x] == ch:
                    x += 1
                d.append(f"M{s} {y}h{x - s}v1h-{x - s}z")
            else:
                x += 1
    return "".join(d)

def field(w, h, fn):
    return [[fn(x + .5, y + .5) for x in range(w)] for y in range(h)]

def svg_uri(svg):
    return "url(\"data:image/svg+xml;utf8," + svg.replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"

# ───────── 网站用的花纹 ─────────

def ring(cx, cy, r, w=1.0):
    return lambda x, y: abs(math.hypot(x - cx, y - cy) - r) <= w / 2

def quatrefoil(cx, cy, s):
    """四叶饰：四个圆的外轮廓。"""
    cs = [(cx - s * .55, cy), (cx + s * .55, cy), (cx, cy - s * .55), (cx, cy + s * .55)]
    r = s * .5
    def f(x, y):
        inside = [math.hypot(x - a, y - b) <= r for a, b in cs]
        edge = [abs(math.hypot(x - a, y - b) - r) <= .55 for a, b in cs]
        return any(e and not any(inside[j] and math.hypot(x - cs[j][0], y - cs[j][1]) < r - .6 for j in range(4)) for e in edge)
    return f

def mask_svg(w, h, fn, fill="#000", opacity=None):
    g = ["#" if fn(x + .5, y + .5) else "." for y in range(h) for x in range(w)]
    grid = ["".join(g[y * w:(y + 1) * w]) for y in range(h)]
    op = f" fill-opacity='{opacity}'" if opacity else ""
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' shape-rendering='crispEdges'><path fill='{fill}'{op} d='{runs(grid, '#')}'/></svg>"

def ornaments_css():
    qf = quatrefoil(8, 8, 9)
    band = lambda x, y: qf(x, y) or (int(x) in (0, 15) and int(y) == 8) or (abs(x - 8) < .6 and abs(y - 8) < .6)

    def fleuron(x, y):
        X, Y = int(x), int(y)
        if X == 0 or Y == 0: return True                      # 外角两条边
        if (X == 3 and Y >= 3) or (Y == 3 and X >= 3): return True  # 内一道
        if quatrefoil(11, 11, 9)(x, y): return True           # 角上的四叶饰
        if X == Y and 5 <= X <= 7: return True                # 斜出的一枝
        if (X == 11 and 9 <= Y <= 13) or (Y == 11 and 9 <= X <= 13): return True  # 四叶饰中的小十字
        return False

    def diaper(x, y):
        X, Y = int(x), int(y)
        if (X + Y) % 16 == 0 or (X - Y) % 16 == 0: return True  # 菱格
        return (X, Y) in {(8, 7), (7, 8), (8, 8), (9, 8), (8, 9)}  # 每格中心一个小十字

    def tracery(x, y):
        # 一排尖拱：每 12 格一个拱，拱里套一个三叶
        u = x % 12
        top = 3 + 4.2 * (abs(u - 6) / 6) ** .7
        on_arch = abs(y - top) < .6 and y < 11
        trefoil = any(abs(math.hypot(u - cx, y - cy) - 1.4) < .5 for cx, cy in [(6, 6.4), (4.8, 8.2), (7.2, 8.2)])
        return on_arch or trefoil or (int(y) == 11) or (int(u) in (0,) and y > 7)

    out = [
        "/* 由 tools/sanctum.py 生成，别手改 */",
        ":root {",
        f"  --qf: {svg_uri(mask_svg(16, 16, band))};",
        f"  --fleuron: {svg_uri(mask_svg(16, 16, fleuron))};",
        f"  --diaper: {svg_uri(mask_svg(16, 16, diaper, '#c9973a', '.13'))};",
        f"  --tracery: {svg_uri(mask_svg(24, 12, tracery, '#e8b54e', '.42'))};",
        "}",
    ]
    (ROOT / "site" / "ornaments.css").write_text("\n".join(out) + "\n", encoding="utf-8")

# ───────── 玫瑰窗（和 glory.js 同一套算法）─────────

GLASS = ["lead", "gold", "gold2", "blue", "blue2", "sky", "red", "green", "violet"]

def rose(x, y):
    """x, y ∈ [-1, 1]。返回 (玻璃色, 格子编号) 或 None（窗外）。"""
    r = math.hypot(x, y)
    if r > 1: return None
    a = math.atan2(y, x) + math.pi
    if r > .94: return ("gold" if int(a / (2 * math.pi) * 64) % 2 else "gold2", 0)
    if r > .90: return ("lead", 0)
    if r > .72:
        n = 24; k = int(a / (2 * math.pi) * n)
        ca = (k + .5) / n * 2 * math.pi - math.pi
        d = math.hypot(x - .81 * math.cos(ca), y - .81 * math.sin(ca))
        if d < .066: return ("red" if k % 2 else "sky", 100 + k)
        if d < .084 or r < .74 or r > .885: return ("lead", 0)
        return ("blue2", 200 + k)
    if r > .70: return ("lead", 0)
    if r > .40:
        n = 12; s = a / (2 * math.pi) * n; k = int(s); u = abs(s - k - .5)
        top = .69 - .6 * u * u
        if u > .44: return ("lead", 0)
        if r > top: return ("lead", 0) if r < top + .025 else ("blue2", 300 + k)
        if abs(r - .55) < .012: return ("lead", 0)
        if u > .38: return ("gold", 400 + k)
        if r > .55: return (["gold", "red", "sky", "violet", "green", "red"][k % 6], 500 + k)
        return ("blue" if k % 2 else "red", 600 + k)
    if r > .38: return ("lead", 0)
    if r > .16:
        n = 8; k = int(a / (2 * math.pi) * n)
        ca = (k + .5) / n * 2 * math.pi - math.pi
        d = math.hypot(x - .27 * math.cos(ca), y - .27 * math.sin(ca))
        if d < .05: return ("red", 700 + k)
        if d < .095: return ("gold", 710 + k)
        if d < .112: return ("lead", 0)
        return ("blue", 720 + k)
    if r > .14: return ("lead", 0)
    if abs(x) < .024 or abs(y) < .024: return ("gold2", 800)
    return ("red" if x * y > 0 else "blue", 801)

PAL = {
    "light": dict(bg1="#d8f0ff", bg2="#f6fbff", ink="#0b2b7a", mute="#3d69ad", glass_lead="#0b1d5c",
                  gold="#c9912e", gold2="#f2cf73", blue="#2a63e0", blue2="#1b3fa8", sky="#7cc4f5", red="#c8423a",
                  green="#2e8f6c", violet="#6f45b8", city1="#9fd2f6", city2="#5f9fe8", city3="#2c5fd0", ray="#ffffff",
                  frame="#b9832a", panel="#eef9ff"),
    "dark": dict(bg1="#030a28", bg2="#12297e", ink="#e2f6ff", mute="#9cccf2", glass_lead="#020823",
                 gold="#e8b54e", gold2="#ffe39a", blue="#3a78f0", blue2="#1d48c0", sky="#6fd0ff", red="#ff5e52",
                 green="#3fb487", violet="#8a5cf0", city1="#1d48b8", city2="#14308e", city3="#0a1a5a", ray="#ffe39a",
                 frame="#f2c96c", panel="#0b1e62"),
}

def rose_svg(cx, cy, R, res, p, cls="rose"):
    """玫瑰窗按 res×res 栅格化，同色同闪烁组的格子合并成一条 path。"""
    groups = {}
    for j in range(res):
        for i in range(res):
            v = rose((i + .5) / res * 2 - 1, (j + .5) / res * 2 - 1)
            if not v: continue
            color, cell = v
            key = (color, 0 if color == "lead" else cell % 4)
            groups.setdefault(key, set()).add((i, j))
    s = R * 2 / res
    out = [f'<g class="{cls}" transform="translate({cx - R:.1f} {cy - R:.1f}) scale({s:.4f})" shape-rendering="crispEdges">']
    for (color, tw), cells in sorted(groups.items()):
        grid = [["#" if (i, j) in cells else "." for i in range(res)] for j in range(res)]
        fill = p["glass_lead"] if color == "lead" else p[color]
        twc = "" if color in ("lead", "gold", "gold2") else f' class="tw{tw}"'
        out.append(f'<path{twc} fill="{fill}" d="{runs(["".join(r) for r in grid], "#")}"/>')
    out.append("</g>")
    return "".join(out)

# ───────── 5×7 像素字 ─────────

FONT = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789·- ", [
    ".###.#...##...#######...##...##...#", "####.#...##...#####.#...##...#####.", ".###.#...##....#....#....#...#.###.",
    "####.#...##...##...##...##...#####.", "######....#....####.#....#....#####", "######....#....####.#....#....#....",
    ".###.#...##....#.####...##...#.####", "#...##...##...#######...##...##...#", ".###...#....#....#....#....#...###.",
    "..###...#....#....#....#.#..#..##..", "#...##..#.#.#..##...#.#..#..#.#...#", "#....#....#....#....#....#....#####",
    "#...###.###.#.##.#.##...##...##...#", "#...##...###..##.#.##..###...##...#", ".###.#...##...##...##...##...#.###.",
    "####.#...##...#####.#....#....#....", ".###.#...##...##...##.#.##..#..##.#", "####.#...##...#####.#.#..#..#.#...#",
    ".#####....#.....###.....#....#####.", "#####..#....#....#....#....#....#..", "#...##...##...##...##...##...#.###.",
    "#...##...##...##...##...#.#.#...#..", "#...##...##...##.#.##.#.##.#.#.#.#.", "#...##...#.#.#...#...#.#.#...##...#",
    "#...##...#.#.#...#....#....#....#..", "#####....#...#...#...#...#....#####", ".###.#...##..###.#.###..##...#.###.",
    "..#...##....#....#....#....#...###.", ".###.#...#....#...#...#...#...#####", "####.....#....#.###.....#....#####.",
    "...#...##..#.#.#..#.#####...#....#.", "######....####.....#....##...#.###.", "..##..#...#....####.#...##...#.###.",
    "#####....#...#...#...#....#....#...", ".###.#...##...#.###.#...##...#.###.", ".###.#...##...#.####....#...#..##..",
    "." * 17 + "#" + "." * 17, "." * 15 + ".###." + "." * 15, "." * 35,
]))
# 网址和箭头要用的几个符号
FONT.update({
    ".": "." * 32 + "#" + "..",
    ">": "#...." ".#..." "..#.." "...#." "..#.." ".#..." "#....",
    "<": "....#" "...#." "..#.." ".#..." "..#.." "...#." "....#",
})

def text_svg(txt, x, y, px, fill, anchor="middle", cls=""):
    """把一行大写字母画成像素矩形。px 是一个像素格的边长。"""
    txt = txt.upper()
    w = len(txt) * 6 - 1
    x0 = x - (w * px / 2 if anchor == "middle" else 0)
    d = []
    for n, ch in enumerate(txt):
        g = FONT.get(ch, FONT[" "]).ljust(35, ".")
        rows = [g[i * 5:(i + 1) * 5] for i in range(7)]
        for ry, row in enumerate(rows):
            cx = 0
            while cx < 5:
                if row[cx] == "#":
                    s = cx
                    while cx < 5 and row[cx] == "#": cx += 1
                    d.append(f"M{n * 6 + s} {ry}h{cx - s}v1h-{cx - s}z")
                else:
                    cx += 1
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} fill="{fill}" shape-rendering="crispEdges" transform="translate({x0:.1f} {y:.1f}) scale({px})" d="{"".join(d)}"/>'

# ───────── README：头图 ─────────

STYLE = """<style>
.tw0,.tw1,.tw2,.tw3{animation:tw 4.8s ease-in-out infinite}
.tw1{animation-delay:-1.2s}.tw2{animation-delay:-2.4s}.tw3{animation-delay:-3.6s}
@keyframes tw{0%,100%{opacity:1}50%{opacity:.62}}
.ray{animation:ray 7s ease-in-out infinite;transform-origin:600px -40px}
.r1{animation-delay:-1.4s}.r2{animation-delay:-2.8s}.r3{animation-delay:-4.2s}.r4{animation-delay:-5.6s}
@keyframes ray{0%,100%{opacity:.08}50%{opacity:.26}}
.sun{animation:sun 12s linear infinite}
@keyframes sun{from{transform:translateX(-170px)}to{transform:translateX(170px)}}
.mote{animation:mote 6s steps(12) infinite}
@keyframes mote{0%{opacity:0;transform:translateY(0)}20%{opacity:1}100%{opacity:0;transform:translateY(-60px)}}
.gild{animation:gild 5s linear infinite}
@keyframes gild{from{transform:translateX(-700px)}to{transform:translateX(700px)}}
.live{animation:live 1.2s steps(1) infinite}
@keyframes live{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>"""

def frame_svg(W, H, p, inset=10):
    """手抄本式金框：两道金线、上下一排四叶饰、四角各一枚十字花。"""
    g = [f'<g fill="none" stroke="{p["frame"]}" shape-rendering="crispEdges">',
         f'<rect x="{inset}" y="{inset}" width="{W - 2 * inset}" height="{H - 2 * inset}" stroke-width="3"/>',
         f'<rect x="{inset + 8}" y="{inset + 8}" width="{W - 2 * inset - 16}" height="{H - 2 * inset - 16}" stroke-width="1"/></g>']
    for x in range(inset + 40, W - inset - 30, 28):  # 上下两排小菱点
        for yy in (inset + 4, H - inset - 4):
            g.append(f'<rect x="{x - 2}" y="{yy - 2}" width="4" height="4" fill="{p["frame"]}" transform="rotate(45 {x} {yy})"/>')
    for cx, cy in [(inset, inset), (W - inset, inset), (inset, H - inset), (W - inset, H - inset)]:
        g.append(f'<g fill="{p["frame"]}"><rect x="{cx - 9}" y="{cy - 9}" width="18" height="18" fill="{p["bg1"]}" stroke="{p["frame"]}" stroke-width="2"/>'
                 f'<rect x="{cx - 1.5}" y="{cy - 7}" width="3" height="14"/><rect x="{cx - 7}" y="{cy - 1.5}" width="14" height="3"/></g>')
    return "".join(g)

def city_svg(W, H, p, seed=7):
    """底下的城市剪影：楼、尖塔、十字、直播塔、教堂双塔，三层由远到近。"""
    rnd = random.Random(seed)
    g = []
    for layer, (col, base, hmin, hmax) in enumerate([(p["city1"], H - 70, 30, 90), (p["city2"], H - 40, 20, 70), (p["city3"], H - 14, 10, 40)]):
        x = 20
        while x < W - 20:
            w = rnd.choice([18, 24, 30, 36, 44])
            if 470 < x < 730 and layer == 2:   # 标题下面留空
                x += w; continue
            h = rnd.randint(hmin, hmax)
            g.append(f'<rect x="{x}" y="{base - h}" width="{w - 4}" height="{H - base + h}" fill="{col}"/>')
            if rnd.random() < .3:  # 尖顶 + 十字
                cx = x + (w - 4) / 2
                g.append(f'<path fill="{col}" d="M{x} {base - h}L{cx} {base - h - w * .9}L{x + w - 4} {base - h}z"/>')
                if layer < 2:
                    ty = base - h - w * .9
                    g.append(f'<rect x="{cx - 1}" y="{ty - 14}" width="2" height="14" fill="{p["gold"]}"/><rect x="{cx - 5}" y="{ty - 10}" width="10" height="2" fill="{p["gold"]}"/>')
            elif rnd.random() < .4:  # 一排窗
                for wy in range(base - h + 6, H - 10, 10):
                    g.append(f'<rect x="{x + 4}" y="{wy}" width="{w - 12}" height="3" fill="{p["bg2"] if layer == 2 else p["city3"]}" opacity=".55"/>')
            x += w
    # 直播塔（右）与教堂双塔（左）
    tx = 980
    g.append(f'<path fill="{p["city2"]}" d="M{tx - 10} {H}L{tx - 4} {H - 210}h8L{tx + 10} {H}z"/>'
             f'<rect x="{tx - 26}" y="{H - 150}" width="52" height="8" fill="{p["city3"]}"/>'
             f'<rect x="{tx - 11}" y="{H - 236}" width="22" height="22" fill="{p["city3"]}"/>'
             f'<rect x="{tx - 1}" y="{H - 262}" width="2" height="26" fill="{p["city3"]}"/>'
             f'<rect class="live" x="{tx - 3}" y="{H - 268}" width="6" height="6" fill="{p["red"]}"/>')
    for k, rr in enumerate((40, 64, 88)):
        g.append(f'<circle cx="{tx}" cy="{H - 225}" r="{rr}" fill="none" stroke="{p["sky"]}" stroke-width="2" opacity="{.6 - k * .17}" stroke-dasharray="6 6"/>')
    cx = 220
    for dx in (-40, 40):
        g.append(f'<rect x="{cx + dx - 14}" y="{H - 190}" width="28" height="190" fill="{p["city2"]}"/>'
                 f'<path fill="{p["city2"]}" d="M{cx + dx - 14} {H - 190}L{cx + dx} {H - 250}L{cx + dx + 14} {H - 190}z"/>'
                 f'<rect x="{cx + dx - 1}" y="{H - 270}" width="2" height="20" fill="{p["gold"]}"/><rect x="{cx + dx - 6}" y="{H - 264}" width="12" height="2" fill="{p["gold"]}"/>')
    g.append(f'<path fill="{p["city2"]}" d="M{cx - 26} {H}V{H - 130}L{cx} {H - 168}L{cx + 26} {H - 130}V{H}z"/>')
    g.append(rose_svg(cx, H - 118, 18, 24, p, "rose small"))
    return "".join(g)

def banner(theme):
    p = PAL[theme]; W, H = 1200, 520
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="NANATATA — a pixel rose window over a blue city; Fiat lux">',
         STYLE,
         f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["bg1"]}"/><stop offset="1" stop-color="{p["bg2"]}"/></linearGradient>'
         f'<radialGradient id="glow"><stop offset="0" stop-color="{p["gold2"]}" stop-opacity=".55"/><stop offset="1" stop-color="{p["gold2"]}" stop-opacity="0"/></radialGradient>'
         f'<radialGradient id="sunlight"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/><stop offset=".55" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset=".4" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="roseclip"><circle cx="600" cy="200" r="160"/></clipPath>'
         f'<clipPath id="titleclip">{text_svg("NANATATA", 600, 388, 9, "#000")}</clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    for i, (a, w) in enumerate([(-58, 70), (-30, 90), (0, 120), (30, 90), (58, 70)]):  # 天光
        r = math.radians(a)
        x1, x2 = 600 + math.tan(r) * 560 - w, 600 + math.tan(r) * 560 + w
        s.append(f'<path class="ray r{i}" fill="{p["ray"]}" d="M590 -40L610 -40L{x2:.0f} 560L{x1:.0f} 560z"/>')
    s.append('<circle cx="600" cy="200" r="230" fill="url(#glow)"/>')
    s.append(rose_svg(600, 200, 160, 104, p))
    s.append('<g clip-path="url(#roseclip)"><circle class="sun" cx="600" cy="170" r="120" fill="url(#sunlight)"/></g>')
    s.append(city_svg(W, H, p))
    s.append(text_svg("FIAT LUX", 600, 26, 3, p["gold"]))
    # 标题：深色描边 + 金色渐变 + 一道扫过的金光
    s.append(text_svg("NANATATA", 604, 392, 9, p["glass_lead"]))
    s.append(text_svg("NANATATA", 600, 388, 9, "url(#gold)"))
    s.append('<g clip-path="url(#titleclip)"><rect class="gild" x="300" y="380" width="600" height="80" fill="url(#sheen)"/></g>')
    s.append(text_svg("TURN IDEAS INTO THINGS PEOPLE CAN USE", 600, 466, 3, p["ink"]))
    rnd = random.Random(3)
    for k in range(26):
        x, y = rnd.randint(60, 1140), rnd.randint(60, 420)
        s.append(f'<rect class="mote" style="animation-delay:-{rnd.random() * 6:.1f}s" x="{x}" y="{y}" width="3" height="3" fill="{p["gold2"]}"/>')
    s.append(frame_svg(W, H, p))
    s.append("</svg>")
    return "".join(s)

def plate(theme, title, sub, verse):
    p = PAL[theme]; W, H = 900, 170
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title.title()} — {sub.title()}">',
         STYLE.replace("translateX(-700px)", "translateX(-500px)").replace("translateX(700px)", "translateX(500px)"),
         f'<defs><linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/><stop offset=".55" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset=".4" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".7"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="tc">{text_svg(title, 450, 52, 5, "#000")}</clipPath></defs>',
         # 尖拱形的牌子
         f'<path d="M80 {H - 18}V60Q80 18 450 14Q820 18 820 60V{H - 18}z" fill="{p["panel"]}" stroke="{p["frame"]}" stroke-width="3"/>'
         f'<path d="M90 {H - 26}V64Q90 28 450 24Q810 28 810 64V{H - 26}z" fill="none" stroke="{p["frame"]}" stroke-width="1"/>',
         f'<rect x="440" y="2" width="20" height="20" fill="{p["panel"]}" stroke="{p["frame"]}" stroke-width="2"/><rect x="448" y="5" width="4" height="14" fill="{p["gold"]}"/><rect x="444" y="9" width="12" height="4" fill="{p["gold"]}"/>',
         rose_svg(40, H / 2, 34, 40, p), rose_svg(W - 40, H / 2, 34, 40, p),
         text_svg(title, 452, 54, 5, p["glass_lead"]), text_svg(title, 450, 52, 5, "url(#gold)"),
         f'<g clip-path="url(#tc)"><rect class="gild" x="150" y="50" width="600" height="40" fill="url(#sheen)"/></g>',
         text_svg(sub, 450, 104, 2, p["ink"]),
         text_svg(verse, 450, 132, 2, p["gold"]),
         "</svg>"]
    return "".join(s)

def divider(theme):
    p = PAL[theme]; W, H = 900, 40
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">', STYLE,
         f'<g fill="{p["frame"]}" shape-rendering="crispEdges"><rect x="120" y="19" width="290" height="2"/><rect x="490" y="19" width="290" height="2"/>']
    for x in (100, 420, 476, 796):
        s.append(f'<rect x="{x - 4}" y="16" width="8" height="8" transform="rotate(45 {x} 20)"/>')
    s.append('<rect x="447" y="2" width="6" height="36"/><rect x="434" y="11" width="32" height="6"/></g>')
    for i, x in enumerate((260, 640)):
        s.append(f'<rect class="mote" style="animation-delay:-{i * 3}s" x="{x}" y="14" width="3" height="3" fill="{p["gold2"]}"/>')
    s.append("</svg>")
    return "".join(s)

# ───────── README：截图装进尖拱金框 ─────────

def gothic_mask(w, h, rise):
    """尖拱：两段圆弧在正中交成尖顶，弧脚落在 y=rise 处接竖直的两边。
    圆心放在起拱线下方、偏向对侧 0.15w，所以拱是“压扁”的尖拱，不会把横幅截图吃掉一大块。"""
    e = .15 * w
    D = (w * w / 4 + w * e - rise * rise) / (2 * rise)
    cx, cy = w / 2 + e, rise + D
    R = math.hypot(cx, D)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for x in range(w):
        u = x if x <= w / 2 else w - 1 - x          # 右半边是左半边的镜像
        top = cy - math.sqrt(max(0.0, R * R - (u - cx) ** 2))
        d.line([(x, max(0, round(top))), (x, h - 1)], fill=255)
    return m

def framed(img, w, h, spring, gold=(201, 145, 46), light=(242, 207, 115)):
    """截图裁成尖拱，外面两道金边，尖顶立一枚十字。"""
    pad = 18
    W, H = w + pad * 2, h + pad * 2 + 30
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ph = img.convert("RGB")
    sc = max(w / ph.width, h / ph.height)
    ph = ph.resize((math.ceil(ph.width * sc), math.ceil(ph.height * sc)), Image.LANCZOS)
    ph = ph.crop(((ph.width - w) // 2, (ph.height - h) // 2, (ph.width - w) // 2 + w, (ph.height - h) // 2 + h))
    m = gothic_mask(w, h, spring)
    outer = gothic_mask(w + 24, h + 24, spring + 12)
    mid = gothic_mask(w + 14, h + 14, spring + 7)
    out.paste(Image.new("RGBA", outer.size, gold + (255,)), (pad - 12, pad + 30 - 12), outer)
    out.paste(Image.new("RGBA", mid.size, (255, 250, 236, 255)), (pad - 7, pad + 30 - 7), mid)
    inner = gothic_mask(w + 6, h + 6, spring + 3)
    out.paste(Image.new("RGBA", inner.size, light + (255,)), (pad - 3, pad + 30 - 3), inner)
    out.paste(ph, (pad, pad + 30), m)
    d = ImageDraw.Draw(out)
    cx = W // 2
    d.rectangle([cx - 3, 4, cx + 3, 40], fill=gold + (255,))
    d.rectangle([cx - 13, 13, cx + 13, 19], fill=gold + (255,))
    return out

def altar_assets():
    stage = Image.open(SHOTS / "lt-stage.webp")
    nave = framed(stage, 1100, 640, 300)
    nave.save(ROOT / "assets" / "studio-nave.webp", quality=84, method=6)
    panels = [framed(Image.open(SHOTS / n), 420, h, 190) for n, h in
              [("lt-loupe.webp", 520), ("lt-roll-1.webp", 600), ("lt-off-dark.webp", 520)]]
    W = sum(p.width for p in panels) + 40
    H = max(p.height for p in panels)
    tri = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 0
    for p in panels:
        tri.paste(p, (x, H - p.height), p)
        x += p.width + 20
    tri.save(ROOT / "assets" / "studio-altar.webp", quality=84, method=6)

ENTRY_STYLE = """<style>
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.35}50%{opacity:.85}}
.march{animation:march 1.6s linear infinite}
@keyframes march{to{stroke-dashoffset:-24}}
.spin{animation:spin 24s linear infinite;transform-box:fill-box;transform-origin:center}
.spin.rev{animation-direction:reverse}
@keyframes spin{to{transform:rotate(1turn)}}
.blink{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.nudgeL{animation:nudgeL .8s steps(2) infinite}
.nudgeR{animation:nudgeR .8s steps(2) infinite}
@keyframes nudgeL{50%{transform:translateX(8px)}}
@keyframes nudgeR{50%{transform:translateX(-8px)}}
.gild{animation:gild 3.2s linear infinite}
@keyframes gild{from{transform:translateX(-420px)}to{transform:translateX(420px)}}
.tw0,.tw1,.tw2,.tw3{animation:tw 4.8s ease-in-out infinite}
.tw1{animation-delay:-1.2s}.tw2{animation-delay:-2.4s}.tw3{animation-delay:-3.6s}
@keyframes tw{0%,100%{opacity:1}50%{opacity:.62}}
.mote{animation:mote 5s steps(10) infinite}
@keyframes mote{0%{opacity:0;transform:translateY(0)}20%{opacity:1}100%{opacity:0;transform:translateY(-40px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>"""

def rays(cx, cy, r0, r1, n, color, cls):
    d = []
    for i in range(n):
        a = i / n * 2 * math.pi
        r = r1 if i % 2 else r1 - 10
        d.append(f"M{cx + math.cos(a) * r0:.1f} {cy + math.sin(a) * r0:.1f}L{cx + math.cos(a) * r:.1f} {cy + math.sin(a) * r:.1f}")
    return f'<path class="{cls}" stroke="{color}" stroke-width="2" d="{"".join(d)}"/>'

def entry(theme):
    """README 里通往个人网站的大门：两扇玫瑰窗夹着一块尖拱金牌，外面一圈跑动的金虚线。"""
    p = PAL[theme]; W, H = 900, 300
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Enter the website: yzh2006517.github.io">',
         ENTRY_STYLE,
         f'<defs><radialGradient id="glow"><stop offset="0" stop-color="{p["gold2"]}" stop-opacity=".9"/><stop offset="1" stop-color="{p["gold2"]}" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/><stop offset=".55" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset=".4" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".8"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="tc">{text_svg("ENTER", 450, 92, 8, "#000")}</clipPath></defs>',
         # 呼吸的金光
         f'<ellipse class="pulse" cx="450" cy="150" rx="440" ry="150" fill="url(#glow)"/>',
         # 外面一圈：跑动的金虚线，四角十字
         f'<rect class="march" x="14" y="14" width="{W - 28}" height="{H - 28}" rx="6" fill="none" stroke="{p["frame"]}" stroke-width="3" stroke-dasharray="14 10"/>',
         f'<rect x="24" y="24" width="{W - 48}" height="{H - 48}" fill="none" stroke="{p["frame"]}" stroke-width="1" opacity=".7"/>']
    for cx, cy in [(14, 14), (W - 14, 14), (14, H - 14), (W - 14, H - 14)]:
        s.append(f'<g fill="{p["gold"]}"><rect x="{cx - 11}" y="{cy - 11}" width="22" height="22" fill="{p["panel"]}" stroke="{p["frame"]}" stroke-width="2"/>'
                 f'<rect x="{cx - 2}" y="{cy - 8}" width="4" height="16"/><rect x="{cx - 8}" y="{cy - 2}" width="16" height="4"/></g>')
    # 中间的尖拱金牌
    s.append(f'<path d="M190 236V96Q190 46 450 40Q710 46 710 96V236z" fill="{p["panel"]}" stroke="{p["frame"]}" stroke-width="4"/>'
             f'<path d="M202 226V100Q202 58 450 52Q698 58 698 100V226z" fill="none" stroke="{p["frame"]}" stroke-width="1"/>')
    # 两侧玫瑰窗：外圈光芒和齿环反向转
    for cx in (130, 770):
        s.append(f'<g fill="none">{rays(cx, 150, 96, 122, 48, p["gold"], "spin")}</g>')
        s.append(f'<circle class="spin rev" cx="{cx}" cy="150" r="91" fill="none" stroke="{p["gold"]}" stroke-width="8" stroke-dasharray="4 5"/>')
        s.append(f'<circle cx="{cx}" cy="150" r="86" fill="{p["glass_lead"]}"/>')
        s.append(rose_svg(cx, 150, 84, 64, p))
    # 文字
    s.append(text_svg("ENTER", 454, 96, 8, p["glass_lead"]))
    s.append(text_svg("ENTER", 450, 92, 8, "url(#gold)"))
    s.append('<g clip-path="url(#tc)"><rect class="gild" x="250" y="90" width="400" height="60" fill="url(#sheen)"/></g>')
    s.append(text_svg("YZH2006517.GITHUB.IO", 450, 168, 3, p["ink"]))
    s.append(f'<g class="blink">{text_svg("CLICK TO OPEN", 450, 202, 2, p["gold"])}</g>')
    s.append(f'<g class="nudgeL">{text_svg(">>>", 262, 196, 3, p["red"])}</g>')
    s.append(f'<g class="nudgeR">{text_svg("<<<", 638, 196, 3, p["red"])}</g>')
    rnd = random.Random(11)
    for k in range(18):
        x, y = rnd.randint(40, 860), rnd.randint(40, 260)
        s.append(f'<rect class="mote" style="animation-delay:-{rnd.random() * 5:.1f}s" x="{x}" y="{y}" width="3" height="3" fill="{p["gold2"]}"/>')
    s.append("</svg>")
    return "".join(s)

if __name__ == "__main__" and "--entry" in __import__("sys").argv:
    for t in ("light", "dark"):
        (ROOT / "assets" / f"entry-{t}.svg").write_text(entry(t), encoding="utf-8")
    raise SystemExit

if __name__ == "__main__":
    ornaments_css()
    A = ROOT / "assets"
    for t in ("light", "dark"):
        (A / f"banner-{t}.svg").write_text(banner(t), encoding="utf-8")
        (A / f"plate-studio-{t}.svg").write_text(plate(t, "PHOTO ALL STUDIO", "WINDOWS · AN ELECTRONIC LIGHT TABLE", "LUX IN TENEBRIS LUCET"), encoding="utf-8")
        (A / f"plate-android-{t}.svg").write_text(plate(t, "PHOTO ALL FILM CAMERA", "ANDROID · 22 FILMS · 9 PAPERS · 416 LUTS", "OMNIA TEMPUS HABENT"), encoding="utf-8")
        (A / f"divider-{t}.svg").write_text(divider(t), encoding="utf-8")
    altar_assets()
    for f in sorted(A.glob("*")):
        print(f"{f.stat().st_size:>8}  {f.name}")
