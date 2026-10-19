#!/usr/bin/env python3
"""
Araba modelleri ve dokulari ureticisi (gercek boyutlara yakin).

Calistir:  python3 tools/gen_cars.py      (pip install pillow)
Uretir:    textures/item/car_<tip>_<kademe>.png   (64x64 atlas, kademe 0/1/2)
           models/item/car_<tip>_<kademe>.json
           items/car_<tip>.json

OLCU: Model birimi = 1/16 blok. Kodda display olcegi S = 1.8 (CarEntity.SCALE).
Yani 1 model birimi ~ 0.1125 blok ~ 0.11 m. Araba ~40 birim = ~4.5 m uzunlugunda.
Model koordinatlari Minecraft'in [-16, 32] sinirinda kalmali; merkez x=8, z=8.
Ileri = +Z. Hasar kademesi 2'de bazi parcalar kopar (tampon, bir teker, zirh paneli).
"""
import json
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "src", "main", "resources", "assets", "silahmod"))
ATLAS = 64

# Atlas bolgeleri (x0, y0, x1, y1). Birbirine girmez.
REGIONS = {
    "body":   (0, 0, 24, 24),
    "roof":   (24, 0, 40, 12),
    "glass":  (24, 12, 40, 20),
    "dark":   (24, 20, 40, 28),
    "trim":   (40, 0, 52, 8),
    "accent": (40, 8, 52, 16),
    "tire":   (40, 16, 52, 28),
    "light":  (52, 0, 60, 6),
    "armor":  (52, 6, 64, 16),
    "rim":    (52, 16, 64, 28),
}

PALETTE = {
    "black_sedan": {
        "body": "#15151a", "roof": "#101014", "glass": "#1b2636", "dark": "#0b0b0e",
        "trim": "#b9bcc4", "accent": "#d4a72c", "tire": "#0c0c0c", "light": "#fff6d6",
        "armor": "#1a1a20", "rim": "#9aa0aa",
    },
    "armored_skoda": {
        "body": "#56634f", "roof": "#4a5645", "glass": "#262c33", "dark": "#1d2024",
        "trim": "#7b8088", "accent": "#3a4048", "tire": "#111111", "light": "#dfe6ec",
        "armor": "#6d7470", "rim": "#5d636b",
    },
    "lamborghini": {
        "body": "#f0b400", "roof": "#e0a600", "glass": "#122030", "dark": "#101010",
        "trim": "#c9ccd2", "accent": "#ff6a00", "tire": "#0a0a0a", "light": "#fffbe0",
        "armor": "#1b1b1b", "rim": "#b8bcc4",
    },
}

RUST = (122, 72, 36)
SOOT = (20, 18, 16)
CRACK = (228, 232, 236)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clamp(v):
    return max(0, min(255, int(round(v))))


def mul(c, f):
    return (clamp(c[0] * f), clamp(c[1] * f), clamp(c[2] * f))


def mix(a, b, t):
    return tuple(clamp(a[i] * (1 - t) + b[i] * t) for i in range(3))


# ------------------------------------------------------------- boyama

def paint_region(px, name, base, rng):
    x0, y0, x1, y1 = REGIONS[name]
    w, h = x1 - x0, y1 - y0
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        for x in range(w):
            u, v = x, y
            t = v / max(1, h - 1)
            if name == "body":
                c = mul(base, 1.12 - 0.22 * t)                      # ust daha acik
                if v % 8 == 0:
                    c = mul(c, 0.7)                                 # panel birlestirme cizgisi
                if 3 <= v <= 4:
                    c = mul(c, 1.25)                                # gunes yansimasi
                c = mul(c, 1 + rng.uniform(-0.02, 0.02))
            elif name == "roof":
                c = mul(base, 1.08 - 0.12 * t)
            elif name == "glass":
                c = mix((40, 60, 85), mul(base, 1.4), t)
                if (u + v) % 11 < 2:
                    c = mix(c, (200, 215, 235), 0.45)               # cam yansimasi
            elif name == "dark":
                c = mul(base, 0.75 if ((u // 2) + (v // 2)) % 2 else 1.1)   # izgara
            elif name == "trim":
                c = mul(base, 0.85 + 0.35 * math.sin(math.pi * t))
                if 2 <= u <= 3:
                    c = mul(c, 1.2)
            elif name == "accent":
                c = mul(base, 1.1 if abs(v - cy) < 1.5 else 0.95)
            elif name == "tire":
                c = mul(base, 1 + rng.uniform(-0.12, 0.12))
            elif name == "light":
                d = math.hypot(u - cx, v - cy) / (w / 2.0)
                c = mix((255, 255, 240), base, min(1.0, d))
            elif name == "armor":
                c = mul(base, 1 + rng.uniform(-0.05, 0.05))
                if u % 6 == 1 and v % 6 == 1:
                    c = mul(c, 1.35)                                # perçin
            elif name == "rim":
                ang = math.atan2(v - cy, u - cx)
                spoke = int((ang + math.pi) * 5 / math.pi) % 2
                c = mul(base, 1.25 if spoke else 0.75)
                if math.hypot(u - cx, v - cy) < 2.2:
                    c = (60, 60, 64)                                # jant merkezi
            else:
                c = base
            px[x0 + x, y0 + y] = c + (255,)


def make_texture(car, stage, rng):
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 255))
    px = img.load()
    for name in REGIONS:
        paint_region(px, name, hex_rgb(PALETTE[car][name]), rng)

    def region_pixels(name):
        x0, y0, x1, y1 = REGIONS[name]
        return [(x, y) for y in range(y0, y1) for x in range(x0, x1)]

    def shade(name, f):
        for (x, y) in region_pixels(name):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), a)

    def blobs(name, color, count, rmin, rmax):
        x0, y0, x1, y1 = REGIONS[name]
        for _ in range(count):
            cx, cy = rng.uniform(x0, x1 - 1), rng.uniform(y0, y1 - 1)
            r = rng.uniform(rmin, rmax)
            for (x, y) in region_pixels(name):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    px[x, y] = color + (255,)

    def scratches(name, count):
        x0, y0, x1, y1 = REGIONS[name]
        for _ in range(count):
            x, y = rng.uniform(x0, x1 - 1), rng.uniform(y0, y1 - 1)
            dx, dy = rng.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
            for _ in range(rng.randint(4, 9)):
                xi, yi = int(x), int(y)
                if x0 <= xi < x1 and y0 <= yi < y1:
                    r, g, b, a = px[xi, yi]
                    px[xi, yi] = (clamp(r + 55), clamp(g + 55), clamp(b + 55), a)
                x, y = x + dx, y + dy

    def cracks(name, count, length):
        x0, y0, x1, y1 = REGIONS[name]
        for _ in range(count):
            x, y = rng.uniform(x0, x1 - 1), rng.uniform(y0, y1 - 1)
            ang = rng.uniform(0, math.tau)
            for _ in range(length):
                xi, yi = int(x), int(y)
                if x0 <= xi < x1 and y0 <= yi < y1:
                    px[xi, yi] = CRACK + (255,)
                ang += rng.uniform(-0.6, 0.6)
                x, y = x + math.cos(ang), y + math.sin(ang)

    def soot(name, prob):
        for (x, y) in region_pixels(name):
            if rng.random() < prob:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp((r + SOOT[0]) / 2), clamp((g + SOOT[1]) / 2), clamp((b + SOOT[2]) / 2), a)

    painted = ("body", "roof", "armor", "trim")
    if stage >= 1:
        for n in painted:
            shade(n, 0.93)
        blobs("body", (32, 32, 36), 5, 1.2, 2.4)           # cokuntuler
        scratches("body", 8)
        cracks("glass", 1, 8)
    if stage >= 2:
        for n in painted:
            shade(n, 0.6)
        soot("body", 0.28)
        soot("roof", 0.3)
        blobs("body", RUST, 6, 1.2, 3.0)                    # pas
        blobs("armor", RUST, 3, 1.0, 2.2)
        cracks("glass", 5, 12)
        shade("tire", 0.6)
        shade("rim", 0.7)
    return img


# ----------------------------------------------------------- model

def B(parts, x0, x1, y0, y1, z0, z1, region, lost=None):
    """Merkez-relatif kutu (x,z merkeze gore). lost=2 ise 2. kademede kopar."""
    parts.append({
        "from": [round(8 + x0, 3), round(y0, 3), round(8 + z0, 3)],
        "to": [round(8 + x1, 3), round(y1, 3), round(8 + z1, 3)],
        "region": region,
        "lost_at": lost,
    })


def wheels(p, inner, tire_w, h, length, zc, rim_w=0.3, lost_front_left=True):
    """4 teker. inner = govdeye yakin kenar (|x|), tire_w = lastik kalinligi, h = teker yuksekligi."""
    for s in (-1, 1):
        for z in (-zc, zc):
            lost = 2 if (lost_front_left and s < 0 and z > 0) else None
            if s < 0:
                xa, xb = -inner - tire_w, -inner
                rx0, rx1 = xa - rim_w, xa
            else:
                xa, xb = inner, inner + tire_w
                rx0, rx1 = xb, xb + rim_w
            B(p, xa, xb, 0, h, z - length / 2, z + length / 2, "tire", lost)
            B(p, rx0, rx1, h * 0.3, h * 0.7, z - length * 0.3, z + length * 0.3, "rim", lost)


def black_sedan():
    p = []
    B(p, -8, 8, 1.3, 4.8, -20, 20, "body")                        # alt govde
    B(p, -7, 7, 4.8, 9.5, -7, 6, "roof")                          # kabin
    B(p, -6.6, 6.6, 4.8, 9.1, -7.25, -6.95, "glass")              # on cam
    B(p, -6.6, 6.6, 4.8, 9.1, 5.95, 6.25, "glass")                # arka cam
    B(p, -7.15, -6.85, 5.3, 8.9, -6, 5, "glass")                  # sol yan cam
    B(p, 6.85, 7.15, 5.3, 8.9, -6, 5, "glass")                    # sag yan cam
    B(p, -5, 5, 2.0, 4.0, 19.9, 20.3, "dark")                     # izgara
    B(p, -7.5, -3.8, 3.6, 4.6, 19.6, 20.2, "light")               # farlar
    B(p, 3.8, 7.5, 3.6, 4.6, 19.6, 20.2, "light")
    B(p, -7.5, -4, 3.2, 4.4, -20.2, -19.6, "accent")              # stop lambalari
    B(p, 4, 7.5, 3.2, 4.4, -20.2, -19.6, "accent")
    B(p, -8.2, 8.2, 1.3, 2.6, 20, 20.7, "trim", lost=2)           # on tampon
    B(p, -8.2, 8.2, 1.3, 2.6, -20.7, -20, "trim")                 # arka tampon
    B(p, -9, -8, 6.5, 7.2, -3.5, -2.5, "body")                    # ayna
    B(p, 8, 9, 6.5, 7.2, -3.5, -2.5, "body")
    B(p, 8.05, 8.25, 2.8, 3.2, -19.5, 19.5, "accent")             # yan serit
    wheels(p, inner=6.2, tire_w=2.1, h=5.8, length=5.6, zc=12)
    return p


def armored_skoda():
    p = []
    B(p, -8, 8, 1.3, 6.0, -20, 20, "body")                        # kutu govde
    B(p, -7, 7, 6.0, 10.5, -8, 6, "roof")                         # kabin
    B(p, -6.5, 6.5, 6.4, 10.1, -8.25, -7.95, "glass")             # on cam
    B(p, -6.5, 6.5, 6.4, 10.1, 5.95, 6.25, "glass")               # arka cam
    B(p, -7.15, -6.85, 7.0, 9.8, -6, 4, "glass")                  # yan camlar
    B(p, 6.85, 7.15, 7.0, 9.8, -6, 4, "glass")
    B(p, 8.0, 8.6, 2.0, 6.0, -18, 18, "armor", lost=2)            # sag zirh paneli
    B(p, -8.6, -8.0, 2.0, 6.0, -18, 18, "armor")                  # sol zirh paneli
    B(p, -8, 8, 1.3, 3.0, 20, 20.8, "armor")                      # on zirh
    B(p, -5, 5, 2.0, 4.0, 20.2, 20.6, "dark")                     # izgara
    B(p, -7, -4.5, 3.2, 4.6, 20.2, 20.6, "light")                 # farlar
    B(p, 4.5, 7, 3.2, 4.6, 20.2, 20.6, "light")
    B(p, -7.5, -4, 3.2, 4.8, -20.6, -20.1, "accent")              # stop lambalari
    B(p, 4, 7.5, 3.2, 4.8, -20.6, -20.1, "accent")
    B(p, -3, 3, 2.5, 5.5, -21.5, -20.5, "tire")                   # arka yedek lastik
    B(p, -8.5, 8.5, 1.3, 2.2, 20.8, 21.2, "trim", lost=2)         # on tampon
    B(p, -9.2, -8.6, 7.0, 7.8, -4, -3, "dark")                    # aynalar
    B(p, 8.6, 9.2, 7.0, 7.8, -4, -3, "dark")
    wheels(p, inner=6.3, tire_w=2.2, h=6.4, length=6.0, zc=12)
    return p


def lamborghini():
    p = []
    B(p, -8, 8, 0.8, 3.6, -20, 20, "body")                        # alcak govde
    B(p, -8, 8, 3.6, 4.6, -20, 10, "body")                        # kaput ustu / kanat
    B(p, -6, 6, 3.6, 6.2, -6, 5, "roof")                          # alcak kabin
    B(p, -5.5, 5.5, 3.8, 6.0, -6.6, -6.2, "glass")                # on cam (egimli)
    B(p, -5.5, 5.5, 3.8, 6.0, 4.8, 5.2, "glass")                  # arka cam
    B(p, -6.1, -5.9, 4.0, 5.6, -5.5, 4.5, "glass")                # yan camlar
    B(p, 5.9, 6.1, 4.0, 5.6, -5.5, 4.5, "glass")
    B(p, 8.0, 8.4, 1.4, 3.4, -4, 2, "accent")                     # yan hava girisi
    B(p, -8.4, -8.0, 1.4, 3.4, -4, 2, "accent")
    B(p, -7, 7, 5.4, 6.0, 13, 16, "accent")                       # arka spoiler
    B(p, -6.5, -6.0, 3.6, 5.4, 13, 14, "dark")                    # spoiler ayaklari
    B(p, 6.0, 6.5, 3.6, 5.4, 13, 14, "dark")
    B(p, -4.5, -1.5, 2.2, 3.0, 19.8, 20.2, "light")               # farlar (ince)
    B(p, 1.5, 4.5, 2.2, 3.0, 19.8, 20.2, "light")
    B(p, -7.5, -3.5, 2.0, 2.8, -20.2, -19.6, "accent")            # stop serit
    B(p, 3.5, 7.5, 2.0, 2.8, -20.2, -19.6, "accent")
    B(p, -8.5, 8.5, 0.5, 1.2, 20, 20.7, "trim", lost=2)           # on splitter
    wheels(p, inner=6.4, tire_w=2.0, h=5.0, length=5.2, zc=12)
    return p


CARS = {
    "black_sedan": black_sedan,
    "armored_skoda": armored_skoda,
    "lamborghini": lamborghini,
}


def element(part):
    uv = list(REGIONS[part["region"]])
    faces = {f: {"uv": uv, "texture": "#0"} for f in ("north", "south", "east", "west", "up", "down")}
    return {"from": part["from"], "to": part["to"], "faces": faces}


def model_json(car, stage, parts):
    tex = f"silahmod:item/car_{car}_{stage}"
    kept = [part for part in parts if part["lost_at"] is None or stage < part["lost_at"]]
    return {
        "textures": {"0": tex, "particle": tex},
        "texture_size": [ATLAS, ATLAS],
        "elements": [element(part) for part in kept],
    }


def item_json(car):
    def model_ref(stage):
        return {"type": "minecraft:model", "model": f"silahmod:item/car_{car}_{stage}"}
    return {
        "model": {
            "type": "minecraft:range_dispatch",
            "property": "minecraft:custom_model_data",
            "index": 0,
            "fallback": model_ref(0),
            "entries": [
                {"threshold": 1.0, "model": model_ref(1)},
                {"threshold": 2.0, "model": model_ref(2)},
            ],
        }
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    for car, builder in CARS.items():
        parts = builder()
        for stage in range(3):
            rng = random.Random(f"{car}-{stage}")
            tex = make_texture(car, stage, rng)
            tex_path = os.path.join(ASSETS, "textures", "item", f"car_{car}_{stage}.png")
            os.makedirs(os.path.dirname(tex_path), exist_ok=True)
            tex.save(tex_path)
            write_json(os.path.join(ASSETS, "models", "item", f"car_{car}_{stage}.json"),
                       model_json(car, stage, parts))
        write_json(os.path.join(ASSETS, "items", f"car_{car}.json"), item_json(car))
    print("Arabalar uretildi:", ", ".join(CARS))


if __name__ == "__main__":
    main()
