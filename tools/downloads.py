"""统计所有公开仓库 Release 附件的累计下载次数，画成 README 里那块烫金计数牌。

    GITHUB_TOKEN=... python tools/downloads.py

由 .github/workflows/downloads.yml 每天跑一次；数字没变就不会产生提交。
只算 Release 里上传的附件（exe / apk 等），GitHub 自动生成的源码包和 git clone 不计。
像素字和配色来自同目录的 sanctum.py，和入口图是一套；版式以中轴左右对称。
边框和两侧彩窗都是细像素画（2–3px 一格），用字符画生成后按颜色合并成 path。
"""
import json
import math
import os
import random
import urllib.request

from sanctum import FONT, PAL, ROOT, runs, text_svg

OWNER = "YZH2006517"
# 计数牌上的短名字；没列在这里的仓库用仓库名本身
LABELS = {
    "SpektraLab-Windows-NANATATA": "SPEKTRALAB",
    "Photo-All-Android": "PHOTO ALL FILM CAMERA",
    "Photo-All": "PHOTO ALL STUDIO",
    "Photo-All-Tether": "PHOTO ALL TETHER",
    "ai-virtual-streamer": "AI VIRTUAL STREAMER",
}
FONT[","] = "." * 27 + "#" + "..." + "#" + "..."


def api(path):
    """GitHub REST，自动翻页。"""
    out, url = [], f"https://api.github.com{path}{'&' if '?' in path else '?'}per_page=100"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "nanatata-downloads"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    while url:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            out += json.load(r)
            url = next((p.split(";")[0].strip(" <>") for p in r.headers.get("Link", "").split(",") if 'rel="next"' in p), None)
    return out


def counts():
    rows = []
    for repo in api(f"/users/{OWNER}/repos?type=owner"):
        if repo["private"] or repo["fork"]:
            continue
        n = sum(a["download_count"] for rel in api(f"/repos/{OWNER}/{repo['name']}/releases") for a in rel["assets"])
        if n:
            rows.append((LABELS.get(repo["name"], repo["name"].replace("-", " ").upper()[:22]), n))
    return sorted(rows, key=lambda r: -r[1])


def text_end(txt, x, y, px, fill):
    """右对齐的像素字。"""
    w = (len(txt) * 6 - 1) * px
    return text_svg(txt, x - w, y, px, fill, anchor="start")


STYLE = """<style>
.sheen{animation:sheen 3.6s linear infinite}
@keyframes sheen{from{transform:translateX(-300px)}to{transform:translateX(300px)}}
.grow{transform-box:fill-box;transform-origin:left center;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) both}
@keyframes grow{from{transform:scaleX(0)}}
.spin{transform-box:fill-box;transform-origin:center;animation:spin 40s linear infinite}
@keyframes spin{to{transform:rotate(1turn)}}
.tw0,.tw1,.tw2,.tw3{animation:tw 4.8s ease-in-out infinite}
.tw1{animation-delay:-1.2s}.tw2{animation-delay:-2.4s}.tw3{animation-delay:-3.6s}
@keyframes tw{0%,100%{opacity:1}50%{opacity:.62}}
.mote{animation:mote 5s steps(10) infinite}
@keyframes mote{0%{opacity:0;transform:translateY(0)}20%{opacity:1}100%{opacity:0;transform:translateY(-30px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>"""


def pix(grid, x0, y0, scale, colors, twinkle=""):
    """一张字符画按颜色合并成几条 path。twinkle 里的字符分四组各自呼吸。"""
    out = []
    for ch, fill in colors.items():
        if ch in twinkle:
            for k in range(4):
                sub = ["".join(c if c == ch and (x // 3 + y // 3) % 4 == k else "." for x, c in enumerate(row)) for y, row in enumerate(grid)]
                d = runs(sub, ch)
                if d:
                    out.append(f'<path class="tw{k}" fill="{fill}" d="{d}"/>')
        else:
            d = runs(grid, ch)
            if d:
                out.append(f'<path fill="{fill}" d="{d}"/>')
    return f'<g transform="translate({x0} {y0}) scale({scale})" shape-rendering="crispEdges">{"".join(out)}</g>'


def frame(W, H, p):
    """像素边框（2px 一格）：外细线、一条菱形链花纹带、内细线；四角是带十字的角饰。"""
    S = 2
    PW, PH = W // S, H // S
    g = [["."] * PW for _ in range(PH)]
    def put(x, y, ch):
        if 0 <= x < PW and 0 <= y < PH:
            g[y][x] = ch
    # 三道框：外线、花纹带上下边、内线
    for k in (1, 4, 10, 13):
        for x in range(k, PW - k):
            put(x, k, "g"); put(x, PH - 1 - k, "g")
        for y in range(k, PH - k):
            put(k, y, "g"); put(PW - 1 - k, y, "g")
    # 花纹带里一串菱形，菱心一点亮金，菱形之间一道连线
    def chain(along, length, fixed, horizontal):
        for t in range(18, length - 18):
            u = (t - 18) % 8 - 4
            for r in range(-2, 3):
                ch = None
                if abs(u) + abs(r) == 2:
                    ch = "g"
                elif u == 0 and r == 0:
                    ch = "y"
                elif r == 0 and abs(u) >= 3:
                    ch = "h"
                if ch:
                    put(t, fixed + r, ch) if horizontal else put(fixed + r, t, ch)
    chain(None, PW, 7, True)
    chain(None, PW, PH - 8, True)
    chain(None, PH, 7, False)
    chain(None, PH, PW - 8, False)
    # 四角：方框里一枚十字（端头外撇），正中一颗红宝石，外角三粒金点
    def corner(ox, oy, fx, fy):
        for j in range(17):
            for i in range(17):
                x, y = ox + i * fx, oy + j * fy
                ch = None
                if 2 <= i <= 14 and 2 <= j <= 14:
                    ch = "p"
                    if i in (2, 14) or j in (2, 14):
                        ch = "g"
                    elif (abs(i - 8) <= 1 and 4 <= j <= 12) or (abs(j - 8) <= 1 and 4 <= i <= 12):
                        ch = "y"
                    elif (j in (4, 12) and abs(i - 8) == 2) or (i in (4, 12) and abs(j - 8) == 2):
                        ch = "y"
                    elif i in (3, 13) and j in (3, 13):
                        ch = "h"
                    if i == 8 and j == 8:
                        ch = "r"
                elif (i, j) in ((0, 0), (1, 1), (0, 16), (16, 0)):
                    ch = "g"
                if ch:
                    put(x, y, ch)
    corner(0, 0, 1, 1)
    corner(PW - 1, 0, -1, 1)
    corner(0, PH - 1, 1, -1)
    corner(PW - 1, PH - 1, -1, -1)
    grid = ["".join(r) for r in g]
    return pix(grid, 0, 0, S, {"p": p["panel"], "g": p["frame"], "h": p["gold"], "y": p["gold2"], "r": p["red"]})


def glass_window(x0, y0, y1, p):
    """一扇像素彩色玻璃尖拱窗（3px 一格，15 格宽）：金框、铅条斜格、蓝玻璃里点缀红金，
    每隔一段一枚带十字的圆章，拱顶一组三叶，底下一层窗台。"""
    S, Wd = 3, 15
    N = int((y1 - y0) // S)
    spring = 12
    def inside(x, y):
        if y < 0 or y >= N - 3 or x < 0 or x >= Wd:
            return False
        if y >= spring:
            return True
        # 两段圆弧交成尖顶：圆心各在对面的起拱点
        return (x - (Wd - 1)) ** 2 + (y - spring) ** 2 <= (Wd - 1) ** 2 and x ** 2 + (y - spring) ** 2 <= (Wd - 1) ** 2
    rows = []
    for y in range(N):
        row = []
        for x in range(Wd):
            if y >= N - 3:                                   # 窗台
                row.append("g" if y != N - 2 else "h")
                continue
            if not inside(x, y):
                row.append(".")
                continue
            edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            edge2 = not all(inside(x + dx, y + dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)))
            if edge:
                row.append("g")
                continue
            if edge2:
                row.append("l")
                continue
            # 拱顶三叶
            if y < spring + 2:
                d = min(((x - 7) ** 2 + (y - 6) ** 2) ** .5, ((x - 5) ** 2 + (y - 9) ** 2) ** .5, ((x - 9) ** 2 + (y - 9) ** 2) ** .5)
                row.append("y" if d < 1.2 else "r" if d < 2.3 else "s")
                continue
            # 圆章：每 26 行一枚
            k = round((y - spring - 14) / 26)
            cy = spring + 14 + 26 * k
            if k >= 0 and cy < N - 10:
                dr = ((x - 7) ** 2 + (y - cy) ** 2) ** .5
                if dr <= 4.6:
                    if dr > 3.7:
                        row.append("y")
                    elif (x == 7 and abs(y - cy) <= 2) or (y == cy and abs(x - 7) <= 2):
                        row.append("y")
                    else:
                        row.append("r")
                    continue
            # 斜格铅条
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                row.append("l")
                continue
            q = ((x + y) // 6 * 7 + (x - y) // 6 * 13) % 11
            row.append("r" if q == 0 else "y" if q == 5 else "s" if q in (2, 7) else "b")
        rows.append("".join(row))
    return pix(rows, x0, y0, S, {"l": p["glass_lead"], "b": p["blue2"], "s": p["blue"], "r": p["red"],
                                 "y": p["gold2"], "g": p["frame"], "h": p["gold"]}, twinkle="bsr")


def vine(cx, y, half, p):
    """横向花纹分隔：两侧细线、菱点，正中一枚十字。"""
    g = [f'<rect x="{cx - half}" y="{y - 1}" width="{half - 26}" height="2" fill="{p["frame"]}"/>',
         f'<rect x="{cx + 26}" y="{y - 1}" width="{half - 26}" height="2" fill="{p["frame"]}"/>']
    for dx in (-half - 8, -18, 18, half + 8):
        g.append(f'<rect x="{cx + dx - 3}" y="{y - 3}" width="6" height="6" fill="{p["gold"]}" transform="rotate(45 {cx + dx} {y})"/>')
    g.append(f'<rect x="{cx - 2}" y="{y - 9}" width="4" height="18" fill="{p["gold"]}"/>'
             f'<rect x="{cx - 7}" y="{y - 4}" width="14" height="4" fill="{p["gold"]}"/>')
    return "".join(g)


def plaque(theme, rows):
    """以中轴对称的计数牌：上面烫金总数，下面每个项目一行，名字在轴左、数字在轴右，金条从轴心向两边长。"""
    p = PAL[theme]
    W, C = 900, 450
    top = 206
    H = top + len(rows) * 36 + 40
    H += H % 2
    total = sum(n for _, n in rows)
    big = f"{total:,}"
    px = min(9, 420 // (len(big) * 6 - 1))
    num_y = 62
    peak = max(n for _, n in rows)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{total} downloads in total across {len(rows)} projects">', STYLE.replace("transform-origin:left center", "transform-origin:center"),
         f'<defs><linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/>'
         f'<stop offset=".55" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["frame"]}"/>'
         f'<stop offset=".5" stop-color="{p["gold2"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset=".4" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="#fff" stop-opacity=".8"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<radialGradient id="glow"><stop offset="0" stop-color="{p["gold2"]}" stop-opacity=".5"/>'
         f'<stop offset="1" stop-color="{p["gold2"]}" stop-opacity="0"/></radialGradient>'
         f'<clipPath id="num">{text_svg(big, C, num_y, px, "#000")}</clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="{p["panel"]}"/>', frame(W, H, p)]
    # 左右两扇像素彩窗，镜像对称
    s.append(glass_window(42, 46, H - 40, p))
    s.append(glass_window(W - 42 - 45, 46, H - 40, p))

    # 上半：标题、烫金总数、说明
    s.append(f'<ellipse cx="{C}" cy="{num_y + 30}" rx="300" ry="90" fill="url(#glow)"/>')
    s.append(text_svg("TOTAL DOWNLOADS", C, 34, 2, p["gold"]))
    s.append(text_svg(big, C + 4, num_y + 4, px, p["glass_lead"]))
    s.append(text_svg(big, C, num_y, px, "url(#gold)"))
    s.append(f'<g clip-path="url(#num)"><rect class="sheen" x="{C - 100}" y="{num_y}" width="200" height="{7 * px}" fill="url(#sh)"/></g>')
    s.append(text_svg(f"ACROSS {len(rows)} PROJECTS · UPDATED DAILY", C, num_y + 7 * px + 16, 2, p["ink"]))
    s.append(vine(C, top - 30, 250, p))

    # 下半：每行名字在轴左、数字在轴右，金条从轴心向两边对称长出
    for i, (name, n) in enumerate(rows):
        y = top + i * 36
        s.append(text_end(name, C - 14, y, 2, p["ink"]))
        s.append(text_svg(f"{n:,}", C + 14, y, 2, p["gold"], anchor="start"))
        s.append(f'<rect x="{C - 3}" y="{y + 2}" width="6" height="10" fill="{p["frame"]}" transform="rotate(45 {C} {y + 7})"/>')
        w = max(6, round(560 * n / peak))
        s.append(f'<rect x="{C - 280}" y="{y + 20}" width="560" height="6" fill="{p["glass_lead"]}" opacity=".14"/>')
        s.append(f'<rect class="grow" style="animation-delay:{.15 * i:.2f}s" x="{C - w / 2:.1f}" y="{y + 20}" '
                 f'width="{w}" height="6" fill="url(#bar)"/>')

    rnd = random.Random(5)
    for _ in range(14):
        s.append(f'<rect class="mote" style="animation-delay:-{rnd.random() * 5:.1f}s" x="{rnd.randint(110, W - 110)}" '
                 f'y="{rnd.randint(30, H - 30)}" width="3" height="3" fill="{p["gold2"]}"/>')
    s.append("</svg>")
    return "".join(s)


if __name__ == "__main__":
    rows = counts()
    for name, n in rows:
        print(f"{n:>8}  {name}")
    print(f"{sum(n for _, n in rows):>8}  TOTAL")
    for t in ("light", "dark"):
        (ROOT / "assets" / f"downloads-{t}.svg").write_text(plaque(t, rows), encoding="utf-8")
