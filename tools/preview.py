#!/usr/bin/env python3
"""
Modellerin onizlemesi (oyunu acmadan bakmak icin).
Calistir: python3 tools/preview.py   -> tools/preview.png

Sutunlar: envanter ikonu | birinci sahis (bos) | reload kareleri
Birinci sahis cizimi Minecraft'in el konumunu (0.56, -0.52, -0.72) ve 70 derece FOV'u taklit eder.
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np

import gen_models as gm

LIGHT = np.array([-0.35, 0.8, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
FACES = [
    ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
    ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
    ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
    ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]),
]


def hex_to_rgb01(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


COLORS = {name: hex_to_rgb01(h) for name, h in gm.PALETTE}


def project_faces(boxes, d, base_offset=(0, 0, 0)):
    """Kutulari ekran uzayina cevirir -> [(derinlik, 3D noktalar, renk)]"""
    rot = d["rotation"]
    s = d["scale"][0]
    R = gm.rot_xyz(*rot)
    t = np.array(d["translation"]) + np.array(base_offset)
    out = []
    for b in boxes:
        lo, hi = np.array(b["f"]), np.array(b["t"])
        for n, verts in FACES:
            pts = np.array([lo + np.array(v) * (hi - lo) for v in verts])
            pts = (R @ ((pts - gm.CENTER) * s).T).T + t
            nn = R @ np.array(n, dtype=float)
            out.append((pts[:, 2].mean(), pts, nn, COLORS[b["c"]]))
    return out


def shade(color, n):
    f = 0.45 + 0.55 * max(0.0, float(np.dot(n, LIGHT)))
    return tuple(min(1, c * f) for c in color)


def draw_gui(ax, boxes, d):
    ax.set_xlim(-8, 8)
    ax.set_ylim(-8, 8)
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((-8, -8), 16, 16, color="#8b8b8b"))
    faces = project_faces(boxes, d)
    for z, pts, nn, col in sorted(faces, key=lambda f: f[0]):
        if nn[2] <= 0:
            continue
        ax.add_patch(Polygon(pts[:, :2], closed=True, facecolor=shade(col, nn), edgecolor="none"))
    ax.axis("off")


def draw_fp(ax, boxes, d):
    aspect = 16 / 9
    fov = math.radians(70)
    th = math.tan(fov / 2)
    ax.set_xlim(-aspect, aspect)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((-aspect, -1), 2 * aspect, 1, color="#5a7a3a"))
    ax.add_patch(Rectangle((-aspect, 0), 2 * aspect, 1, color="#8fb6e6"))
    base = np.array([0.56, -0.52, -0.72]) * 16.0  # el konumu (birim = 1/16 blok)
    faces = project_faces(boxes, d, base_offset=base)
    # arkadan one (en uzak once) -> z kucuk olan once
    for z, pts, nn, col in sorted(faces, key=lambda f: f[0]):
        # arka yuz ayiklama: kameraya (orijin) bakan yuzler
        center = pts.mean(axis=0)
        if np.dot(nn, -center) <= 0:
            continue
        if np.any(pts[:, 2] >= -0.5):
            continue
        xy = np.array([[p[0] / (-p[2]) / th / aspect * aspect,
                        p[1] / (-p[2]) / th] for p in pts])
        ax.add_patch(Polygon(xy, closed=True, facecolor=shade(col, nn), edgecolor="none"))
    ax.plot([0, 0], [-0.03, 0.03], color="white", lw=0.6)
    ax.plot([-0.03, 0.03], [0, 0], color="white", lw=0.6)
    ax.axis("off")


def main():
    names = list(gm.WEAPONS.keys())
    cols = 8
    fig, axes = plt.subplots(len(names), cols, figsize=(cols * 2.6, len(names) * 2.2), dpi=110)
    fig.patch.set_facecolor("#222")
    for r, name in enumerate(names):
        cfg = gm.WEAPONS[name]
        row = axes[r]
        boxes, disp = gm.build_display(name, cfg, {})
        draw_gui(row[0], boxes, disp["gui"])
        row[0].set_title(f"{name} - envanter", color="white", fontsize=8)
        draw_fp(row[1], boxes, disp["firstperson_righthand"])
        row[1].set_title("elde (bos)", color="white", fontsize=8)
        frames = list(cfg["frames"])
        if frames:
            picks = np.linspace(0, len(frames) - 1, cols - 2).round().astype(int)
            for c, fi in enumerate(picks):
                b2, d2 = gm.build_display(name, cfg, frames[fi])
                draw_fp(row[2 + c], b2, d2["firstperson_righthand"])
                row[2 + c].set_title(f"reload {fi + 1}/{len(frames)}", color="white", fontsize=8)
        else:
            for c in range(2, cols):
                row[c].axis("off")
    plt.tight_layout()
    out = os.path.join(gm.HERE, "preview.png")
    plt.savefig(out, facecolor=fig.get_facecolor())
    print(out)


if __name__ == "__main__":
    main()
