"""统计所有公开仓库 Release 附件的累计下载次数，画成 README 里那块烫金计数牌。

    GITHUB_TOKEN=... python tools/downloads.py

由 .github/workflows/downloads.yml 每天跑一次；数字没变就不会产生提交。
只算 Release 里上传的附件（exe / apk 等），GitHub 自动生成的源码包和 git clone 不计。
画图用的玫瑰窗、像素字和配色都来自同目录的 sanctum.py，和头图、入口图是一套。
"""
import json
import math
import os
import random
import urllib.request

from sanctum import FONT, PAL, ROOT, rose_svg, text_svg

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


def plaque(theme, rows):
    p = PAL[theme]
    W = 900
    H = max(250, 70 + len(rows) * 36 + 30)
    total = sum(n for _, n in rows)
    big = f"{total:,}"
    px = min(8, 248 // (len(big) * 6 - 1))
    cy = H / 2
    num_y = cy - 32
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{total} downloads in total across {len(rows)} projects">', STYLE,
         f'<defs><linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["gold2"]}"/>'
         f'<stop offset=".55" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["frame"]}"/></linearGradient>'
         f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["frame"]}"/>'
         f'<stop offset=".7" stop-color="{p["gold"]}"/><stop offset="1" stop-color="{p["gold2"]}"/></linearGradient>'
         f'<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset=".4" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="#fff" stop-opacity=".8"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<radialGradient id="glow"><stop offset="0" stop-color="{p["gold2"]}" stop-opacity=".5"/>'
         f'<stop offset="1" stop-color="{p["gold2"]}" stop-opacity="0"/></radialGradient>'
         f'<clipPath id="num">{text_svg(big, 300, num_y, px, "#000")}</clipPath></defs>',
         # 牌面：底色、两道金框、四角十字
         f'<rect x="6" y="6" width="{W - 12}" height="{H - 12}" fill="{p["panel"]}" stroke="{p["frame"]}" stroke-width="3"/>',
         f'<rect x="16" y="16" width="{W - 32}" height="{H - 32}" fill="none" stroke="{p["frame"]}" stroke-width="1" opacity=".7"/>']
    for x in range(60, W - 50, 24):  # 上下两排小菱点
        for y in (11, H - 11):
            s.append(f'<rect x="{x - 2}" y="{y - 2}" width="4" height="4" fill="{p["frame"]}" transform="rotate(45 {x} {y})"/>')
    for kx, ky in [(6, 6), (W - 6, 6), (6, H - 6), (W - 6, H - 6)]:
        s.append(f'<g fill="{p["gold"]}"><rect x="{kx - 10}" y="{ky - 10}" width="20" height="20" fill="{p["panel"]}" '
                 f'stroke="{p["frame"]}" stroke-width="2"/><rect x="{kx - 2}" y="{ky - 7}" width="4" height="14"/>'
                 f'<rect x="{kx - 7}" y="{ky - 2}" width="14" height="4"/></g>')

    # 左：玫瑰窗徽章 + 总数
    s.append(f'<circle cx="300" cy="{cy}" r="150" fill="url(#glow)"/>')
    rays = "".join(f"M{96 + math.cos(a) * 62:.1f} {cy + math.sin(a) * 62:.1f}"
                   f"L{96 + math.cos(a) * (78 if i % 2 else 70):.1f} {cy + math.sin(a) * (78 if i % 2 else 70):.1f}"
                   for i, a in enumerate([k / 36 * 6.2832 for k in range(36)]))
    s.append(f'<path class="spin" fill="none" stroke="{p["gold"]}" stroke-width="2" d="{rays}"/>')
    s.append(f'<circle cx="96" cy="{cy}" r="58" fill="{p["glass_lead"]}" stroke="{p["frame"]}" stroke-width="3"/>')
    s.append(rose_svg(96, cy, 55, 48, p))
    s.append(text_svg("TOTAL DOWNLOADS", 300, cy - 66, 2, p["gold"]))
    s.append(text_svg(big, 304, num_y + 4, px, p["glass_lead"]))
    s.append(text_svg(big, 300, num_y, px, "url(#gold)"))
    s.append(f'<g clip-path="url(#num)"><rect class="sheen" x="200" y="{num_y}" width="200" height="{7 * px}" fill="url(#sh)"/></g>')
    s.append(text_svg(f"ACROSS {len(rows)} PROJECTS", 300, num_y + 7 * px + 16, 2, p["ink"]))
    s.append(text_svg("UPDATED DAILY", 300, num_y + 7 * px + 38, 2, p["mute"]))

    # 中间一道金线，正中一枚菱形
    s.append(f'<rect x="489" y="34" width="2" height="{H - 68}" fill="{p["frame"]}" opacity=".7"/>'
             f'<rect x="484" y="{cy - 6}" width="12" height="12" fill="{p["gold"]}" transform="rotate(45 490 {cy})"/>')

    # 右：每个项目一行，名字、数字、一根金条
    top = (H - len(rows) * 36) / 2 + 4
    peak = max(n for _, n in rows)
    for i, (name, n) in enumerate(rows):
        y = top + i * 36
        s.append(text_svg(name, 520, y, 2, p["ink"], anchor="start"))
        s.append(text_end(f"{n:,}", 864, y, 2, p["gold"]))
        s.append(f'<rect x="520" y="{y + 19}" width="344" height="8" fill="{p["glass_lead"]}" opacity=".18"/>')
        s.append(f'<rect class="grow" style="animation-delay:{.15 * i:.2f}s" x="520" y="{y + 19}" '
                 f'width="{max(4, round(344 * n / peak))}" height="8" fill="url(#bar)"/>')

    rnd = random.Random(5)
    for _ in range(14):
        s.append(f'<rect class="mote" style="animation-delay:-{rnd.random() * 5:.1f}s" x="{rnd.randint(30, W - 30)}" '
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
