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
ATLAS = 128
CELL = 8

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
        "body": "#2e2e36", "roof": "#25252c", "glass": "#5f9fd8", "dark": "#18181c",
        "trim": "#d7dbe3", "accent": "#e0b030", "tire": "#2a2a2e", "light": "#fff3a0",
        "armor": "#3a3a42", "rim": "#dfe3ea",
    },
    "armored_skoda": {
        "body": "#66755e", "roof": "#596852", "glass": "#6b9fc9", "dark": "#2a2d31",
        "trim": "#a7acb4", "accent": "#4a5058", "tire": "#2a2a2a", "light": "#fff8d0",
        "armor": "#7d847e", "rim": "#b9bec6",
    },
    "lamborghini": {
        "body": "#f5b800", "roof": "#e6aa00", "glass": "#6aa4dc", "dark": "#2a2a2a",
        "trim": "#d7dbe3", "accent": "#ff7a10", "tire": "#2a2a2a", "light": "#fffbd0",
        "armor": "#2e2e2e", "rim": "#e2e6ec",
    },
}

def patch(name):
    """Bolgenin ortasinda 4x4 tek renkli yama. Yuzler bunu kullanir -> mozaik/serit olmaz."""
    x0, y0, x1, y1 = REGIONS[name]
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    return (cx - 2, cy - 2, cx + 2, cy + 2)


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
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = base + (255,)


def make_texture(car, stage, rng):
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 255))
    px = img.load()
    for name in REGIONS:
        base = hex_rgb(PALETTE[car][name])
        paint_region(px, name, base, rng)
        x0, y0, x1, y1 = patch(name)
        color = base
        if stage >= 1 and name in ("body", "roof", "armor", "trim"):
            color = mul(base, 0.85)
        if stage >= 2:
            if name in ("body", "roof", "armor"):
                color = mix(mul(base, 0.6), RUST, 0.35)
            elif name == "glass":
                color = mul(base, 0.6)
            elif name in ("tire", "rim"):
                color = mul(base, 0.6)
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[x, y] = color + (255,)
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


def wheels(p, inner, tire_w, h, length, zc, rim_w=0.45, lost_front_left=True):
    """4 teker. inner = govdeye yakin kenar (|x|), tire_w = lastik kalinligi, h = teker yuksekligi."""
    for s in (-1, 1):
        for z in (-zc, zc):
            lost = 2 if (lost_front_left and s < 0 and z > 0) else None
            if s < 0:
                xa, xb = -inner - tire_w, -inner
                rx0, rx1 = xa - rim_w * 2, xa
            else:
                xa, xb = inner, inner + tire_w
                rx0, rx1 = xb, xb + rim_w * 2
            B(p, xa, xb, 0, h, z - length / 2, z + length / 2, "tire", lost)
            B(p, rx0, rx1, h * 0.3, h * 0.7, z - length * 0.3, z + length * 0.3, "rim", lost)


def black_sedan():
    """Gercek sedan profili: alcak kaput, egimli on cam, kabin, bagaj."""
    p = []
    B(p, -8, 8, 1.3, 4.8, -20, 6, "body")                        # bagaj + orta govde
    B(p, -8, 8, 1.3, 4.2, 6, 20, "body")                          # alcak kaput
    B(p, -7, 7, 4.8, 9.5, -4, 4.5, "roof")                        # kabin tavani
    B(p, -7, 7, 4.8, 7.6, -8, -4, "roof")                         # on cam egimi (alt)
    B(p, -7, 7, 4.8, 6.2, -10, -8, "roof")                        # on cam egimi (alt-on)
    B(p, -6.6, 6.6, 6.2, 9.1, -8.4, -7.6, "glass")                # on cam (egimli yuzey)
    B(p, -6.6, 6.6, 7.6, 9.1, -4.2, -3.6, "glass")                # on cam ust kisim
    B(p, -6.6, 6.6, 4.8, 9.1, 4.4, 5.6, "glass")                  # arka cam
    B(p, -7, 7, 4.8, 7.4, 4.5, 7, "roof")                         # arka cam egimi
    B(p, -7.25, -6.8, 5.3, 8.9, -6, 4, "glass")                   # sol yan cam
    B(p, 6.8, 7.25, 5.3, 8.9, -6, 4, "glass")                     # sag yan cam
    B(p, -5, 5, 2.0, 4.0, 19.9, 20.3, "dark")                     # izgara
    B(p, -7.5, -3.8, 3.2, 4.2, 19.6, 20.2, "light")               # farlar
    B(p, 3.8, 7.5, 3.2, 4.2, 19.6, 20.2, "light")
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


def assign_cells(parts):
    """Her parcaya atlas'ta kendi 8x8 piksel hucresini ver (16x16 izgara, en fazla 256 parca)."""
    if len(parts) > 256:
        raise ValueError("Cok fazla parca: %d" % len(parts))
    for i, part in enumerate(parts):
        cx, cy = i % 16, i // 16
        part["cell"] = [cx * CELL, cy * CELL, cx * CELL + CELL, cy * CELL + CELL]


def paint_detail(px, cell, role, base, stage, rng):
    """Bir hucreyi parca tipine uygun detayla boyar (cam yansimasi, far, izgara, lastik, jant...)."""
    x0, y0, x1, y1 = cell
    n = CELL - 1
    cx = cy = n / 2.0
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = x - x0, y - y0
            t = v / n
            if role == "body":
                c = mul(base, 1.10 - 0.14 * t)
                if u == 0 or v == 0 or u == n or v == n:
                    c = mul(c, 0.72)                       # panel kenari
                if v == 1:
                    c = mul(c, 1.25)                       # gunes yansimasi
            elif role == "roof":
                c = mul(base, 1.12 - 0.1 * t)
                if u == 0 or v == 0:
                    c = mul(c, 0.8)
            elif role == "glass":
                c = mix((28, 42, 66), (120, 170, 220), t)
                if (u + v) % 5 == 0:
                    c = mix(c, (235, 242, 255), 0.55)      # cam yansimasi
            elif role == "dark":
                c = mul(base, 0.65 if (u + v) % 2 else 1.1)  # izgara agi
            elif role == "trim":
                c = mul(base, 0.75 + 0.45 * (1 - abs(u - cx) / cx))   # krom parlaklik seridi
            elif role == "accent":
                c = mul(base, 1.12 if v in (3, 4) else 0.95)  # serit
            elif role == "light":
                d = math.hypot(u - cx, v - cy) / cx
                c = mix((255, 255, 240), base, min(1.0, d * 1.1))   # far parlakligi
            elif role == "tire":
                c = mul(base, 0.85 + 0.3 * rng.random())
                if v % 3 == 0:
                    c = mul(c, 0.6)                        # lastik dişli
            elif role == "rim":
                ang = math.atan2(v - cy, u - cx)
                spoke = int((ang + math.pi) * 3 / math.pi) % 2
                c = mul(base, 1.3 if spoke else 0.7)
                if math.hypot(u - cx, v - cy) < 1.3:
                    c = (58, 58, 64)                       # jant merkezi
            elif role == "armor":
                c = mul(base, 1.0)
                if u % 4 == 1 and v % 4 == 1:
                    c = mul(c, 1.35)                       # persin
            else:
                c = base
            # hasar kademeleri
            if stage >= 1 and role in ("body", "roof", "armor", "trim"):
                c = mul(c, 0.9)
            if stage >= 2:
                if role in ("body", "roof", "armor"):
                    c = mix(mul(c, 0.7), RUST, 0.3)
                elif role in ("glass", "tire", "rim"):
                    c = mul(c, 0.6)
            px[x, y] = c + (255,)
    if stage >= 2 and role == "glass" and rng.random() < 0.7:
        # cam catlagi
        for k in range(4):
            px[x0 + min(n, k + 1), y0 + min(n, 2 * k % CELL)] = CRACK + (255,)


def make_texture(car, parts, stage):
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 255))
    px = img.load()
    for part in parts:
        role = part["region"]
        base = hex_rgb(PALETTE[car][role])
        rng = random.Random(f"{car}-{stage}-{part['cell'][0]}-{part['cell'][1]}")
        paint_detail(px, tuple(part["cell"]), role, base, stage, rng)
    return img


def element(part):
    uv = list(part["cell"])
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
        assign_cells(parts)
        for stage in range(3):
            tex = make_texture(car, parts, stage)
            tex_path = os.path.join(ASSETS, "textures", "item", f"car_{car}_{stage}.png")
            os.makedirs(os.path.dirname(tex_path), exist_ok=True)
            tex.save(tex_path)
            write_json(os.path.join(ASSETS, "models", "item", f"car_{car}_{stage}.json"),
                       model_json(car, stage, parts))
        write_json(os.path.join(ASSETS, "items", f"car_{car}.json"), item_json(car))
    print("Arabalar uretildi:", ", ".join(CARS))


if __name__ == "__main__":
    main()
