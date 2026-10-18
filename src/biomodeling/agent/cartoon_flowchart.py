"""
cartoon_flowchart.py — draw a polished cartoon showcasing the MATHEMATICAL MODELS
found in / built from literature.

Output: output/cartoon_modeling_flow.png

Focused purely on the created models (NO agent workflow ribbon). Boxes and
lines are refined: cards get a soft drop-shadow + rounded double border + a
coloured header band + a thin inner frame; the three model cards are linked by
a smooth decorative spine of dashed connector lines and small node dots.

Re-run this script any time to regenerate the image.
"""

import os
import numpy as np

os.environ.setdefault("MPLCONFIGDIR", os.path.join("output", ".mplconfig"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import (FancyBboxPatch, FancyArrowPatch, Ellipse,
                                Circle, Polygon, Rectangle)

# ---- register a Chinese-capable font (cartoon handwriting style) ----
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\STKAITI.TTF",   # 华文楷体 (handwritten, playful)
    r"C:\Windows\Fonts\simhei.ttf",    # 黑体 (bold fallback)
    r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑 (fallback)
    r"C:\Windows\Fonts\Deng.ttf",      # 等线 (fallback)
]
_map = {}
for path in _FONT_CANDIDATES:
    try:
        if os.path.exists(path):
            font_manager.fontManager.addfont(path)
            _map[path] = font_manager.FontProperties(fname=path).get_name()
    except Exception:
        pass
_PRIMARY = _map.get(_FONT_CANDIDATES[0]) or _map.get(_FONT_CANDIDATES[1])
if _PRIMARY:
    plt.rcParams["font.family"] = _PRIMARY
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join("output", "cartoon_modeling_flow.png")
os.makedirs("output", exist_ok=True)

# ============================ palette ============================
C_BG     = "#FFF8EE"
C_EDGE   = "#6B4E2C"
C_TXT    = "#46352A"
C_SOFT   = "#B9A28A"
C_ACCENT = "#E8724E"
C_STAR   = "#FFD75E"

HEADERS = ["#FFC9A3", "#B7DCFF", "#C7F0C9"]   # coral / sky / mint headers
CARD_BG = ["#FFF3E0", "#EAF5FF", "#EDFBEE"]
EQ_BG   = "#FBF3E6"


def soft_shadow(ax, x, y, w, h, radius=1.0, off=1.1):
    """A soft drop shadow behind a rounded rectangle."""
    ax.add_patch(FancyBboxPatch((x + off, y - off), w, h,
                                boxstyle=f"round,pad=0,rounding_size={radius}",
                                fc="#000000", ec="none", alpha=0.08, zorder=1))


def card(ax, x, y, w, h, header_h=5.6, header_c="#FFC9A3", body_c="#FFF3E0",
         radius=1.0, z=3):
    """A polished card: drop shadow + rounded white outer + header band +
    thin inner frame (dashed). Returns nothing; draws in place."""
    soft_shadow(ax, x, y, w, h, radius=radius)
    # main rounded card
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={radius}",
                                fc="#FFFDF8", ec=C_EDGE, lw=2.6, zorder=z))
    # header band (rounds only at top visually via separate rounded patch)
    ax.add_patch(FancyBboxPatch((x + 1.0, y + h - header_h), w - 2.0, header_h - 1.4,
                                boxstyle="round,pad=0,rounding_size=0.7",
                                fc=header_c, ec="none", lw=0, zorder=z + 1))
    ax.plot([x + 0.6, x + w - 0.6], [y + h - header_h, y + h - header_h],
            color=C_EDGE, lw=1.4, zorder=z + 1)
    # thin inner frame
    ax.add_patch(FancyBboxPatch((x + 1.1, y + 1.1), w - 2.2, h - 2.2,
                                boxstyle=f"round,pad=0,rounding_size={radius - 0.2}",
                                fc="none", ec=C_SOFT, lw=1.0, linestyle=(0, (4, 3)),
                                zorder=z + 1))


def spine_dot(ax, x, y, r=0.8, fc=C_ACCENT, ec=C_EDGE, z=5):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=1.6, zorder=z))


def spine_line(ax, p0, p1, color=C_ACCENT, lw=3.0, ls=(0, (5, 3)), z=2, alpha=0.9):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=lw,
            linestyle=ls, zorder=z, alpha=alpha, solid_capstyle="round")


def text(ax, x, y, s, size=11, fc=C_TXT, weight="normal", z=6, italic=False,
         ha="center", alpha=1.0):
    ax.text(x, y, s, ha=ha, va="center", fontsize=size, color=fc,
            fontweight=weight, zorder=z, style="italic" if italic else "normal",
            alpha=alpha)


def eq_text(ax, x, y, lines, size=10.2, z=6, color="#33312C"):
    n = len(lines)
    for i, ln in enumerate(lines):
        text(ax, x, y - (i - (n - 1) / 2) * (size / 11 * 4.6), ln,
             size=size, fc=color, weight="bold", z=z)


# =====================================================================
fig, ax = plt.subplots(figsize=(15.5, 9.2), dpi=150)
fig.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
ax.set_xlim(0, 100); ax.set_ylim(0, 64); ax.axis("off")

# ---- gentle background decoration (low-key, refined) ----
rng = np.random.default_rng(9)
for _ in range(22):
    ax.scatter([rng.uniform(2, 98)], [rng.uniform(3, 61)], s=rng.uniform(30, 60),
               color=C_ACCENT, alpha=0.07, zorder=0, marker="*")
for _ in range(30):
    ax.scatter([rng.uniform(2, 98)], [rng.uniform(3, 61)], s=rng.uniform(6, 14),
               color=C_EDGE, alpha=0.12, zorder=0)

# ---------------- Title ----------------
text(ax, 50, 60.6, "文献中的数学模型", size=28, fc=C_ACCENT, weight="bold")
text(ax, 50, 56.4, "Mathematical models in literature · 卡通展示", size=12.5,
     fc=C_SOFT, italic=True)

# a small accent rule under the title
ax.plot([36, 64], [54.6, 54.6], color=C_ACCENT, lw=3, solid_capstyle="round", zorder=3,
        alpha=0.7)
ax.add_patch(Ellipse((64, 54.6), 2.2, 0.8, fc=C_ACCENT, ec="none", zorder=3))

# ================= three model cards =================
card_w, card_h, top = 29.4, 33.5, 16.6
mid = 50 - card_w / 2          # centre card x
left_x = 2.7                    # left card x
right_x = 100 - 2.7 - card_w    # right card x
gap = (mid - (left_x + card_w)) // 2 if False else 4.2   # horizontal hand-space

card_xs = [left_x, mid, right_x]

models = [
    dict(
        title="捕食 - 被捕食",
        en="Lotka-Volterra",
        eq=["dX/dt = aX − bXY", "dY/dt = cXY − dY"],
        note="猎物与捕食者的振荡共存",
        kind="bunny_wolf",
        header=HEADERS[0], body=CARD_BG[0],
    ),
    dict(
        title="反应扩散波",
        en="Fisher–KPP",
        eq=["∂u/∂t = D·∂²u/∂x²", "+ r·u·(1−u)"],
        note="从中心向外传播的行波",
        kind="wave",
        header=HEADERS[1], body=CARD_BG[1],
    ),
    dict(
        title="恒化器竞争",
        en="Monod chemostat",
        eq=["dA/dt = μA(S)·A − D·A", "dB/dt = μB(S)·B − D·B"],
        note="双菌株争夺限制性营养",
        kind="flasks",
        header=HEADERS[2], body=CARD_BG[2],
    ),
]

# ---- decorative spine linking the three cards through their centres ----
cy = top + card_h / 2 - 4.0
gap_c_l = (left_x + card_w + mid) / 2          # between card 1 and card 2
gap_c_r = (mid + card_w + right_x) / 2         # between card 2 and card 3
spine_line(ax, (left_x + card_w * 0.55, cy), (gap_c_l, cy))
spine_line(ax, (gap_c_l, cy), (mid - card_w * 0.42, cy))
spine_line(ax, (mid + card_w * 0.42, cy), (gap_c_r, cy))
spine_line(ax, (gap_c_r, cy), (right_x + card_w * 0.45, cy))
spine_dot(ax, gap_c_l, cy)
spine_dot(ax, gap_c_r, cy)
ax.add_patch(Ellipse((mid, cy), 3.2, 3.2, fc=C_STAR, ec=C_EDGE, lw=1.6, zorder=5))

for cx, m in zip(card_xs, models):
    card(ax, cx, top, card_w, card_h,
         header_c=m["header"], body_c=m["body"], radius=1.1)

    # header text
    text(ax, cx + card_w / 2, top + card_h - 3.6, m["title"], size=14.5,
         fc="#5A4220", weight="bold", z=7)
    text(ax, cx + card_w / 2, top + card_h - 6.4, m["en"], size=9.5,
         fc=C_EDGE, italic=True, alpha=0.85, z=7)

    # icon area
    ic_x, ic_y = cx + card_w / 2, top + 23.0

    if m["kind"] == "bunny_wolf":
        # --- rabbit (prey) ---
        rx, ry = ic_x - 6.6, ic_y - 2.6
        ax.add_patch(Ellipse((rx, ry + 0.2), 5.8, 6.6, fc="#F6CE9F", ec=C_EDGE, lw=1.9, zorder=5))
        ax.add_patch(Ellipse((rx - 1.15, ry + 5.0), 1.8, 3.2, fc="#F6CE9F", ec=C_EDGE, lw=1.5, zorder=4))
        ax.add_patch(Ellipse((rx + 1.15, ry + 5.0), 1.8, 3.2, fc="#F6CE9F", ec=C_EDGE, lw=1.5, zorder=4))
        ax.scatter([rx - 1.0, rx + 0.8], [ry + 1.0, ry + 1.0], s=34, color="#3A2A1A", zorder=6)
        ax.add_patch(Circle((rx - 0.55, ry - 1.7), 0.9, fc="#F1948A", ec=C_EDGE, lw=1.2, zorder=6))
        ax.add_patch(Circle((rx + 0.55, ry - 1.7), 0.9, fc="#F1948A", ec=C_EDGE, lw=1.2, zorder=6))
        ax.plot([rx - 1.6, rx - 2.6, rx - 2.6], [ry + 3.4, ry + 4.2, ry + 3.2], color=C_EDGE, lw=1.2, zorder=5)
        ax.plot([rx + 1.6, rx + 2.6, rx + 2.6], [ry + 3.4, ry + 4.2, ry + 3.2], color=C_EDGE, lw=1.2, zorder=5)
        # --- wolf (predator) ---
        wx, wy = ic_x + 6.2, ic_y - 3.2
        ax.add_patch(Ellipse((wx, wy + 0.2), 5.6, 5.8, fc="#9FACB0", ec=C_EDGE, lw=1.9, zorder=5))
        ax.add_patch(Polygon([(wx - 4.2, wy + 1.6), (wx - 3.4, wy - 0.6), (wx - 2.6, wy + 0.8)],
                             fc="#9FACB0", ec=C_EDGE, lw=1.5, zorder=5))
        ax.scatter([wx - 1.3, wx + 1.0], [wy + 1.0, wy + 1.0], s=28, color="#3A2A1A", zorder=6)
        ax.add_patch(Circle((wx - 1.7, wy - 1.3), 0.6, fc="#B03A2E", ec=C_EDGE, lw=1.2, zorder=6))
        ax.add_patch(Circle((wx + 0.9, wy - 1.3), 0.6, fc="#B03A2E", ec=C_EDGE, lw=1.2, zorder=6))
        # small arrow prey -> predator
        ax.add_patch(FancyArrowPatch((rx + 3.2, ry - 1.0), (wx - 3.0, wy - 1.2),
                                     arrowstyle="-|>", mutation_scale=16, color=C_ACCENT,
                                     lw=2.4, zorder=6))

    elif m["kind"] == "wave":
        base = ic_y - 4.2
        xs = np.linspace(ic_x - 10.5, ic_x + 10.5, 220)
        env = np.exp(-((xs - ic_x) / 9.5) ** 2)
        ys = base + 3.3 * np.sin((xs - ic_x) * 0.62 - 1.0) * env
        # underlying axis
        ax.plot([ic_x - 11, ic_x + 11], [base, base], color=C_SOFT, lw=1.5,
                linestyle=(0, (4, 3)), zorder=4)
        ax.plot(xs, ys, color="#3A8FD4", lw=4.5, zorder=5, solid_capstyle="round", alpha=0.95)
        ax.plot(xs, ys, color="#7FB8E6", lw=1.6, zorder=6, alpha=0.6)
        # travelling front + a little fish
        f_i = int(np.argmax(ys))
        ax.add_patch(Circle((xs[f_i], ys[f_i] + 1.4), 1.5, fc=C_ACCENT, ec=C_EDGE, lw=1.8, zorder=6))
        ax.plot([xs[f_i] - 1.6, xs[f_i] - 3.0], [ys[f_i] + 1.0, ys[f_i] + 2.6], color=C_EDGE, lw=1.5, zorder=7)
        ax.scatter([xs[f_i] - 0.6, xs[f_i] + 0.4], [ys[f_i] + 1.4, ys[f_i] + 1.4], s=30, color="white", zorder=7)
        # direction arrows
        for axx in (ic_x - 7.5, ic_x + 0.5):
            ax.add_patch(FancyArrowPatch((axx + 3, base + 0.2), (axx + 6, base + 0.2),
                                         arrowstyle="-|>", mutation_scale=13, color=C_SOFT,
                                         lw=1.8, zorder=4))

    else:  # flasks
        for dx, col, cap in ((-6.4, "#F9D976", "#D4A017"), (4.6, "#8FE0AC", "#27AE60")):
            fx = ic_x + dx
            ax.add_patch(Rectangle((fx - 2.1, ic_y - 6.4), 4.9, 7.3, fc=col, ec=C_EDGE, lw=1.9, zorder=5))
            ax.add_patch(Rectangle((fx - 1.0, ic_y + 1.2), 2.6, 2.4, fc="#EADFF2", ec=C_EDGE, lw=1.5, zorder=5))
            ax.add_patch(Ellipse((fx, ic_y + 1.2), 2.6, 0.9, fc="#D9C7E8", ec=C_EDGE, lw=1.5, zorder=6))
            for b in ((fx - 1.0, ic_y - 4.4), (fx + 0.4, ic_y - 2.8), (fx + 1.2, ic_y - 5.0),
                      (fx - 0.3, ic_y - 5.8)):
                ax.scatter([b[0]], [b[1]], s=46, color="#5B2A0A", alpha=0.5, zorder=6)

    # ---- equation area ----
    eq_y = top + 6.6
    ax.add_patch(FancyBboxPatch((cx + 1.6, eq_y - 1.7), card_w - 3.2, 5.4,
                                boxstyle="round,pad=0,rounding_size=0.5",
                                fc=EQ_BG, ec=C_EDGE, lw=1.4, linestyle=(0, (4, 3)), zorder=5))
    eq_text(ax, cx + card_w / 2, eq_y + 3.0, m["eq"], size=10.4, z=6)

    # bottom note
    note_y = top + 2.6
    text(ax, cx + card_w / 2, note_y, m["note"], size=9.6, fc=C_SOFT, italic=True, z=6)

# ================= bottom output banner (small, refined) =================
bw, bh = 54, 4.6
bx, by = 50 - bw / 2, 4.6
soft_shadow(ax, bx, by, bw, bh, radius=0.7, off=0.9)
ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.7",
                            fc="#EFF7EA", ec=C_EDGE, lw=2.2, zorder=4))
text(ax, 50, by + bh / 2 + 0.3, "方程 · 参数 · 数值模拟 · 曲线图",
     size=11, fc="#3F5B32", weight="bold", z=6)

# small corner stars
for sx, sy, s in ((3.2, 3.2, 1.6), (96.2, 3.4, 1.3), (3.5, 58.5, 1.2), (96.0, 57.8, 1.4)):
    ax.add_patch(Polygon([(sx, sy + s), (sx + 0.4*s, sy + 0.3*s), (sx + s, sy + 0.3*s),
                          (sx + 0.5*s, sy - 0.2*s), (sx + 0.7*s, sy - s),
                          (sx, sy - 0.4*s), (sx - 0.7*s, sy - s), (sx - 0.5*s, sy - 0.2*s),
                          (sx - s, sy + 0.3*s), (sx - 0.4*s, sy + 0.3*s)],
                         fc=C_STAR, ec=C_EDGE, lw=1.2, zorder=6))

plt.tight_layout()
fig.savefig(OUT, facecolor=C_BG, bbox_inches="tight")
print("saved:", OUT)
