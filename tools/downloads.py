"""统计所有公开仓库 Release 附件的累计下载次数，画成 README 里那块计数牌。

    GITHUB_TOKEN=... python tools/downloads.py

由 .github/workflows/downloads.yml 每天跑一次；数字没变就不会产生提交。
只算 Release 里上传的附件（exe / apk 等），GitHub 自动生成的源码包和 git clone 不计。

计数牌是铜版雕刻式的细线矢量：三道金线框、四角卷草角花、两侧尖拱窗、
顶上一枚放光的十字，项目列表用目录式的点线引导。
README 里的 SVG 当图片加载、拿不到网页字体，所以把 tools/fonts 里的 Noto Serif SC
子集（OFL）以 base64 嵌进去；排版时用同一份字体的字宽来算位置，点线才接得严丝合缝。
"""
import base64
import json
import math
import os
import random
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont

OWNER = "YZH2006517"
ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
# 计数牌上的名字；没列在这里的仓库用仓库名本身
LABELS = {
    "SpektraLab-Windows-NANATATA": "SpektraLab",
    "Photo-All-Android": "Photo All · Film Camera",
    "Photo-All": "Photo All Studio",
    "Photo-All-Tether": "Photo All · Tether",
    "ai-virtual-streamer": "AI Virtual Streamer",
}

PAL = {
    "light": dict(bg1="#fdfaf2", bg2="#f3ebd7", ink="#1b2a5c", mute="#7a6f55", gold="#b1802b", gold2="#ecc874",
                  deep="#7d5612", hair="#c8a35a", track="#e7dcc0", glow="#f6dc96"),
    "dark": dict(bg1="#121d4c", bg2="#0a1232", ink="#eef2ff", mute="#a8b2d8", gold="#e3b95d", gold2="#ffe6a6",
                 deep="#a57622", hair="#c9a45a", track="#27345f", glow="#5a4a1c"),
}

# ───────── 数据 ─────────

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
            rows.append((LABELS.get(repo["name"], repo["name"].replace("-", " ")), n))
    return sorted(rows, key=lambda r: -r[1])

# ───────── 字体：嵌入 + 量字宽 ─────────

class Face:
    def __init__(self, weight):
        path = FONTS / f"serif-{weight}.woff2"
        self.weight = weight
        self.b64 = base64.b64encode(path.read_bytes()).decode()
        f = TTFont(path)
        self.upm = f["head"].unitsPerEm
        self.cmap = f.getBestCmap()
        self.hmtx = f["hmtx"]

    def width(self, text, size, spacing=0.0):
        adv = sum(self.hmtx[self.cmap.get(ord(c), ".notdef")][0] for c in text)
        return adv * size / self.upm + spacing * len(text)

    def css(self):
        return (f"@font-face{{font-family:S{self.weight};font-weight:{self.weight};"
                f"src:url(data:font/woff2;base64,{self.b64}) format('woff2')}}")


F5, F7 = Face(500), Face(700)


def text(t, x, y, size, fill, face=F5, spacing=0, anchor="start", extra=""):
    t = t.replace("&", "&amp;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="S{face.weight}, serif" font-weight="{face.weight}" '
            f'font-size="{size}" letter-spacing="{spacing}" text-anchor="{anchor}" fill="{fill}"{extra}>{t}</text>')

# ───────── 纹样 ─────────

def quatrefoil(cx, cy, r, stroke, sw=0.8):
    """四叶饰：四个小圆围一圈，中间一点。"""
    g = "".join(f'<circle cx="{cx + dx * r:.2f}" cy="{cy + dy * r:.2f}" r="{r:.2f}"/>' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    return f'<g fill="none" stroke="{stroke}" stroke-width="{sw}">{g}</g><circle cx="{cx}" cy="{cy}" r="{r * .45:.2f}" fill="{stroke}"/>'


def corner(p):
    """左上角的角花：一道 1/4 圆弧、两枝卷草、角上一枚四叶饰。其余三角镜像。"""
    g = p["gold"]
    return (f'<g fill="none" stroke="{g}" stroke-width="1" stroke-linecap="round">'
            f'<path d="M22 70 Q22 22 70 22"/>'
            f'<path d="M30 84 Q30 30 84 30" stroke-width=".6" opacity=".7"/>'
            f'<path d="M44 58 Q44 44 58 44" stroke-width=".8"/>'
            f'<path d="M22 100 V112 M100 22 H112" stroke-width="1.4"/></g>'
            + quatrefoil(36, 36, 5, g, 0.9)
            + f'<circle cx="84" cy="30" r="1.6" fill="{g}"/><circle cx="30" cy="84" r="1.6" fill="{g}"/>')


def lancet(cx, y0, y1, p):
    """一道细长尖拱窗：外框两道细线，拱顶一枚三叶，窗身一串菱形与小十字交替，底下一层座。"""
    g, w = p["gold"], 44
    def arch(inset):
        l, r, top = cx - w / 2 + inset, cx + w / 2 - inset, y0 + inset * 1.4
        spring = y0 + w * 0.95
        return (f"M{l} {y1 - inset}V{spring}C{l} {spring - w * .45} {cx - 4} {top + 10} {cx} {top}"
                f"C{cx + 4} {top + 10} {r} {spring - w * .45} {r} {spring}V{y1 - inset}Z")
    s = [f'<path d="{arch(0)}" fill="{p["glow"]}" fill-opacity=".18" stroke="{g}" stroke-width="1.3"/>',
         f'<path d="{arch(5)}" fill="none" stroke="{p["hair"]}" stroke-width=".7"/>']
    ty = y0 + w * 0.72
    for dx, dy in ((0, -6), (-5.5, 3.5), (5.5, 3.5)):  # 拱顶三叶
        s.append(f'<circle cx="{cx + dx}" cy="{ty + dy}" r="5" fill="none" stroke="{g}" stroke-width=".8"/>')
    s.append(f'<circle cx="{cx}" cy="{ty}" r="1.6" fill="{g}"/>')
    s.append(f'<line x1="{cx}" y1="{ty + 14}" x2="{cx}" y2="{y1 - 18}" stroke="{p["hair"]}" stroke-width=".6"/>')
    for k, y in enumerate(range(int(ty + 28), int(y1 - 26), 24)):
        if k % 2:
            s.append(f'<path d="M{cx} {y - 6}L{cx + 4} {y}L{cx} {y + 6}L{cx - 4} {y}Z" fill="{p["bg1"]}" stroke="{g}" stroke-width=".9"/>')
        else:
            s.append(f'<path d="M{cx - .8} {y - 6}h1.6v4.2h4.2v1.6h-4.2V{y + 6}h-1.6v-4.2h-4.2v-1.6h4.2Z" fill="{g}"/>')
    s.append(f'<path d="M{cx - w / 2 - 6} {y1 + 4}H{cx + w / 2 + 6}M{cx - w / 2 - 3} {y1 + 8}H{cx + w / 2 + 3}" stroke="{g}" stroke-width="1"/>')
    return "".join(s)


def glory_cross(cx, cy, p):
    """顶上一枚放光的十字：细光芒一长一短，中间一枚十字架。"""
    rays = []
    for i in range(32):
        a = i / 32 * 2 * math.pi
        r0, r1 = 13, (30 if i % 2 == 0 else 22)
        rays.append(f"M{cx + math.cos(a) * r0:.1f} {cy + math.sin(a) * r0:.1f}L{cx + math.cos(a) * r1:.1f} {cy + math.sin(a) * r1:.1f}")
    return (f'<g class="halo"><path d="{"".join(rays)}" stroke="{p["gold"]}" stroke-width=".7" stroke-linecap="round"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="11" fill="{p["bg1"]}" stroke="{p["gold"]}" stroke-width=".9"/>'
            f'<path d="M{cx - 1.4} {cy - 8}h2.8v4.6h4.6v2.8h-4.6V{cy + 8}h-2.8v-5.6h-4.6v-2.8h4.6Z" fill="url(#gold)"/>')


def rule(cx, y, half, p):
    """花纹分隔线：两段细线，末端小圆，中间一枚带点的菱形和两撇卷草。"""
    g = p["gold"]
    return (f'<g stroke="{g}" fill="none" stroke-width=".9" stroke-linecap="round">'
            f'<path d="M{cx - half} {y}H{cx - 22}M{cx + 22} {y}H{cx + half}"/>'
            f'<path d="M{cx - 22} {y}c4 -6 9 -6 12 0M{cx + 22} {y}c-4 -6 -9 -6 -12 0"/></g>'
            f'<circle cx="{cx - half - 3}" cy="{y}" r="1.8" fill="{g}"/><circle cx="{cx + half + 3}" cy="{y}" r="1.8" fill="{g}"/>'
            f'<path d="M{cx} {y - 6}L{cx + 6} {y}L{cx} {y + 6}L{cx - 6} {y}Z" fill="{p["bg1"]}" stroke="{g}" stroke-width="1"/>'
            f'<circle cx="{cx}" cy="{y}" r="1.6" fill="{g}"/>')


STYLE = """<style>
{fonts}
.sheen{{animation:sheen 4s ease-in-out infinite}}
@keyframes sheen{{0%{{transform:translateX(-260px)}}60%,100%{{transform:translateX(260px)}}}}
.grow{{transform-box:fill-box;transform-origin:left center;animation:grow 1.6s cubic-bezier(.2,.8,.2,1) both}}
@keyframes grow{{from{{transform:scaleX(0)}}}}
.halo{{transform-box:fill-box;transform-origin:center;animation:spin 60s linear infinite}}
@keyframes spin{{to{{transform:rotate(1turn)}}}}
.star{{animation:star 3.6s ease-in-out infinite}}
@keyframes star{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>"""

# ───────── 计数牌 ─────────

def plaque(theme, rows):
    p = PAL[theme]
    W, C = 900, 450
    L, R = 248, 652                       # 项目列表那一栏的左右边
    top = 304
    H = top + len(rows) * 46 + 64
    total = sum(n for _, n in rows)
    big = f"{total:,}"
    peak = max(n for _, n in rows)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Total downloads: {total} across {len(rows)} projects">',
         STYLE.format(fonts=F5.css() + F7.css()),
         f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["bg1"]}"/>'
         f'<stop offset="1" stop-color="{p["bg2"]}"/></linearGradient>'
         f'<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/>'
         f'<stop offset=".5" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["deep"]}"/></linearGradient>'
         f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["deep"]}"/>'
         f'<stop offset=".8" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["gold2"]}"/></linearGradient>'
         f'<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset=".35" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="#fff" stop-opacity=".85"/><stop offset=".65" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<radialGradient id="glow"><stop offset="0" stop-color="{p["glow"]}" stop-opacity=".75"/>'
         f'<stop offset="1" stop-color="{p["glow"]}" stop-opacity="0"/></radialGradient>'
         f'<clipPath id="num">{text(big, C, 194, 80, "#000", F7, 3, "middle")}</clipPath></defs>',
         # 牌面与三道框线
         f'<rect x="4" y="4" width="{W - 8}" height="{H - 8}" rx="3" fill="url(#bg)" stroke="{p["gold"]}" stroke-width="1.6"/>',
         f'<rect x="11" y="11" width="{W - 22}" height="{H - 22}" fill="none" stroke="{p["gold"]}" stroke-width=".8"/>',
         f'<rect x="15" y="15" width="{W - 30}" height="{H - 30}" fill="none" stroke="{p["hair"]}" stroke-width=".5" stroke-opacity=".7"/>']

    # 四角角花（左上画一枚，其余镜像）
    c = corner(p)
    for tx, ty, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        s.append(f'<g transform="translate({tx} {ty}) scale({sx} {sy})">{c}</g>')

    # 两侧尖拱窗，镜像对称
    s.append(lancet(104, 70, H - 70, p))
    s.append(lancet(W - 104, 70, H - 70, p))

    # 上半：放光十字、标题、烫金总数、说明
    s.append(f'<ellipse cx="{C}" cy="164" rx="260" ry="96" fill="url(#glow)"/>')
    s.append(glory_cross(C, 54, p))
    s.append(text("TOTAL DOWNLOADS", C, 106, 12, p["gold"], F5, 6, "middle"))
    s.append(text("累计下载", C, 126, 11, p["mute"], F5, 8, "middle"))
    s.append(text(big, C + 1.5, 195.5, 80, p["deep"], F7, 3, "middle", ' opacity=".35"'))
    s.append(text(big, C, 194, 80, "url(#gold)", F7, 3, "middle", f' stroke="{p["deep"]}" stroke-width=".6"'))
    s.append(f'<g clip-path="url(#num)"><rect class="sheen" x="{C - 130}" y="118" width="260" height="90" fill="url(#sh)"/></g>')
    s.append(text(f"ACROSS {len(rows)} PROJECTS  ·  UPDATED DAILY", C, 228, 10.5, p["mute"], F5, 3.5, "middle"))
    s.append(rule(C, 258, 170, p))

    # 下半：目录式列表——名字、点线引导、数字；底下一道细金条按比例
    for i, (name, n) in enumerate(rows):
        y = top + i * 46
        num = f"{n:,}"
        nw = F5.width(name, 14.5, 1.2)
        vw = F7.width(num, 14.5, 1)
        s.append(text(name, L, y, 14.5, p["ink"], F5, 1.2))
        s.append(text(num, R, y, 14.5, p["gold"], F7, 1, "end"))
        x0, x1 = L + nw + 10, R - vw - 10
        if x1 > x0:
            dots = "".join(f'<circle cx="{x:.1f}" cy="{y - 4.5}" r=".85"/>' for x in [x0 + k * 7 for k in range(int((x1 - x0) // 7) + 1)])
            s.append(f'<g fill="{p["hair"]}">{dots}</g>')
        w = max(3, (R - L) * n / peak)
        s.append(f'<rect x="{L}" y="{y + 11}" width="{R - L}" height="1" fill="{p["track"]}"/>')
        s.append(f'<rect class="grow" style="animation-delay:{.12 * i:.2f}s" x="{L}" y="{y + 10}" width="{w:.1f}" height="3" rx="1.5" fill="url(#bar)"/>')
        s.append(f'<path d="M{L + w:.1f} {y + 7.5}l4 4 -4 4 -4 -4z" fill="{p["gold"]}" class="grow" style="animation-delay:{.12 * i:.2f}s"/>')

    # 底边正中一小串菱形，与顶上的十字呼应
    by = H - 30
    s.append(f'<g fill="{p["gold"]}">' + "".join(
        f'<path d="M{C + dx} {by - 3.5}l3.5 3.5 -3.5 3.5 -3.5 -3.5z" opacity="{1 - abs(dx) / 60:.2f}"/>' for dx in (-48, -32, -16, 0, 16, 32, 48)) + "</g>")

    rnd = random.Random(7)
    for _ in range(10):  # 零星几颗小星，一明一暗
        x, y, r = rnd.randint(190, W - 190), rnd.randint(30, H - 40), rnd.choice((3, 4, 5))
        s.append(f'<path class="star" style="animation-delay:-{rnd.random() * 3.6:.1f}s" fill="{p["gold2"]}" '
                 f'd="M{x} {y - r}Q{x} {y} {x + r} {y}Q{x} {y} {x} {y + r}Q{x} {y} {x - r} {y}Q{x} {y} {x} {y - r}Z"/>')
    s.append("</svg>")
    return "".join(s)


if __name__ == "__main__":
    rows = counts()
    for name, n in rows:
        print(f"{n:>8}  {name}")
    print(f"{sum(n for _, n in rows):>8}  TOTAL")
    for t in ("light", "dark"):
        (ROOT / "assets" / f"downloads-{t}.svg").write_text(plaque(t, rows), encoding="utf-8")
