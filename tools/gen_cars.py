#!/usr/bin/env python3
"""
Araba modelleri ve hasar dokulari ureticisi.

Calistir:  python3 tools/gen_cars.py   (PIL gerekir: pip install pillow)
Uretir:    textures/item/car_<tip>_<kademe>.png   (32x32 atlas, her kademe icin ayri)
           models/item/car_<tip>_<kademe>.json   (kutulardan 3D model)
           items/car_<tip>.json                  (custom_model_data -> hangi kademe)

Kademe: 0 = hasarsiz, 1 = hasarli (150+ hasar), 2 = agir hasarli (300+ hasar).
Kademe 2'de bazi parcalar (on tampon, bir teker, yan panel) kopar; doku kararir, camlar catlar.

KOORDINAT: model 16 birimlik blok olcegindedir. Araba merkezi x=8, z=8'de. Ileri = +Z.
Her parca (x, y, z) araligi merkeze gore verilir; kod 8 ekler.
"""
import json
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "src", "main", "resources", "assets", "silahmod"))
ATLAS = 32

# Atlas bolgeleri (x0, y0, x1, y1), piksel. Her parca bir bolgeyi kullanir.
REGIONS = {
    "body":   (0, 0, 16, 16),
    "roof":   (16, 0, 32, 8),
    "glass":  (16, 8, 32, 12),
    "trim":   (16, 12, 24, 16),
    "accent": (24, 12, 32, 16),
    "tire":   (0, 16, 8, 24),
    "light":  (8, 16, 12, 20),
    "armor":  (12, 16, 16, 24),
    "dark":   (16, 16, 32, 32),
}

PALETTE = {
    "black_sedan": {
        "body": "#121216", "roof": "#0c0c10", "glass": "#1d2a3a", "trim": "#1a1a20",
        "accent": "#c9a227", "tire": "#0b0b0b", "light": "#f2f2e0", "armor": "#1a1a20", "dark": "#0a0a0c",
    },
    "armored_skoda": {
        "body": "#4e5a4a", "roof": "#3f4a3c", "glass": "#2a2f35", "trim": "#2b2e33",
        "accent": "#3a3f45", "tire": "#111111", "light": "#cfd6dc", "armor": "#6d7470", "dark": "#24272b",
    },
    "lamborghini": {
        "body": "#e8b800", "roof": "#d9a800", "glass": "#14202c", "trim": "#111111",
        "accent": "#ff7a00", "tire": "#0a0a0a", "light": "#fffbe0", "armor": "#1b1b1b", "dark": "#101010",
    },
}

RUST = (122, 72, 36)
SOOT = (20, 18, 16)
CRACK = (225, 230, 235)
SCRATCH_DELTA = 45


# ----------------------------------------------------------------- doku

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clamp(v):
    return max(0, min(255, int(v)))


def shade(px, rect, factor):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * factor), clamp(g * factor), clamp(b * factor), a)


def blobs(px, rect, color, count, rmin, rmax, rng):
    x0, y0, x1, y1 = rect
    for _ in range(count):
        cx, cy = rng.randrange(x0, x1), rng.randrange(y0, y1)
        r = rng.uniform(rmin, rmax)
        for y in range(max(y0, int(cy - r)), min(y1, int(cy + r) + 1)):
            for x in range(max(x0, int(cx - r)), min(x1, int(cx + r) + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    px[x, y] = color + (255,)


def scratches(px, rect, count, rng):
    x0, y0, x1, y1 = rect
    for _ in range(count):
        x, y = rng.uniform(x0, x1 - 1), rng.uniform(y0, y1 - 1)
        dx, dy = rng.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
        for _ in range(rng.randint(3, 7)):
            xi, yi = int(x), int(y)
            if x0 <= xi < x1 and y0 <= yi < y1:
                r, g, b, a = px[xi, yi]
                px[xi, yi] = (clamp(r + SCRATCH_DELTA), clamp(g + SCRATCH_DELTA), clamp(b + SCRATCH_DELTA), a)
            x, y = x + dx, y + dy


def cracks(px, rect, count, length, rng):
    x0, y0, x1, y1 = rect
    for _ in range(count):
        x, y = rng.uniform(x0, x1 - 1), rng.uniform(y0, y1 - 1)
        ang = rng.uniform(0, math.tau)
        for _ in range(length):
            xi, yi = int(x), int(y)
            if x0 <= xi < x1 and y0 <= yi < y1:
                px[xi, yi] = CRACK + (255,)
            ang += rng.uniform(-0.6, 0.6)
            x, y = x + math.cos(ang), y + math.sin(ang)


def soot(px, rect, prob, rng):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            if rng.random() < prob:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp((r + SOOT[0]) / 2), clamp((g + SOOT[1]) / 2), clamp((b + SOOT[2]) / 2), a)


def make_texture(car, stage, rng):
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 255))
    px = img.load()
    for name, rect in REGIONS.items():
        color = hex_rgb(PALETTE[car][name]) + (255,)
        x0, y0, x1, y1 = rect
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[x, y] = color

    painted = ("body", "roof", "armor", "trim")
    if stage >= 1:
        for name in painted:
            shade(px, REGIONS[name], 0.92)
        blobs(px, REGIONS["body"], (30, 30, 34), 6, 1.2, 2.2, rng)       # cokuntuler
        scratches(px, REGIONS["body"], 8, rng)
        cracks(px, REGIONS["glass"], 1, 6, rng)
    if stage >= 2:
        for name in painted:
            shade(px, REGIONS[name], 0.62)
        soot(px, REGIONS["body"], 0.25, rng)
        soot(px, REGIONS["roof"], 0.3, rng)
        blobs(px, REGIONS["body"], RUST, 6, 1.0, 2.6, rng)              # pas lekeleri
        blobs(px, REGIONS["armor"], RUST, 3, 1.0, 2.0, rng)
        cracks(px, REGIONS["glass"], 5, 9, rng)
        shade(px, REGIONS["tire"], 0.6)
    return img


# ---------------------------------------------------------------- model

def box(parts, x0, x1, y0, y1, z0, z1, region, lost_at=None):
    """Merkez-relatif kutu. lost_at=2 ise 2. kademede yok olur."""
    parts.append({
        "from": [round(8 + x0, 3), round(y0, 3), round(8 + z0, 3)],
        "to": [round(8 + x1, 3), round(y1, 3), round(8 + z1, 3)],
        "region": region,
        "lost_at": lost_at,
    })


def black_sedan():
    p = []
    box(p, -7, 7, 2, 7, -14, 14, "body")                        # alt govde
    box(p, -6, 6, 7, 12, -7, 6, "roof")                         # kabin
    box(p, -5.5, 5.5, 7.2, 11.8, -7.1, -6.9, "glass")           # on cam
    box(p, -5.5, 5.5, 7.2, 11.8, 5.9, 6.1, "glass")             # arka cam
    box(p, -6, -3, 4.5, 6.5, -14.3, -13.9, "light")             # farlar
    box(p, 3, 6, 4.5, 6.5, -14.3, -13.9, "light")
    box(p, -7.5, 7.5, 1, 3.2, -14.6, -14, "trim", lost_at=2)    # on tampon
    box(p, -7.5, 7.5, 1, 3, 14, 14.6, "trim")                   # arka tampon
    box(p, 7, 7.2, 3, 3.6, -13, 13, "accent")                   # altin serit
    box(p, 7, 8.6, 0, 4, -10, -5, "tire", lost_at=2)            # on sol teker (kopar)
    box(p, 7, 8.6, 0, 4, 7, 12, "tire")
    box(p, -8.6, -7, 0, 4, -10, -5, "tire", lost_at=2)
    box(p, -8.6, -7, 0, 4, 7, 12, "tire")
    return p


def armored_skoda():
    p = []
    box(p, -8, 8, 2, 9, -15, 15, "body")                        # kutu govde
    box(p, -7, 7, 9, 13, -8, 7, "roof")                         # kabin
    box(p, -6.5, 6.5, 9.2, 12.8, -8.1, -7.9, "glass")           # on cam (kalin)
    box(p, 7.9, 8.5, 3, 8, -12, 12, "armor", lost_at=2)         # sag zirh paneli
    box(p, -8.5, -7.9, 3, 8, -12, 12, "armor")                  # sol zirh paneli
    box(p, -6, -3, 5, 7, -15.3, -14.9, "light")
    box(p, 3, 6, 5, 7, -15.3, -14.9, "light")
    box(p, -8.5, 8.5, 1, 3, -15.6, -15, "trim", lost_at=2)      # on tampon
    box(p, -8.5, 8.5, 1, 3, 15, 15.6, "dark")                   # arka tampon
    box(p, 8, 9.6, 0, 5, -11, -5, "tire", lost_at=2)            # on sag teker
    box(p, 8, 9.6, 0, 5, 6, 12, "tire")
    box(p, -9.6, -8, 0, 5, -11, -5, "tire")
    box(p, -9.6, -8, 0, 5, 6, 12, "tire")
    return p


def lamborghini():
    p = []
    box(p, -8, 8, 1, 5, -16, 16, "body")                        # alcak govde
    box(p, -6, 6, 5, 8, -6, 5, "roof")                          # alcak kabin
    box(p, -5.5, 5.5, 5.2, 7.8, -6.1, -5.9, "glass")            # on cam
    box(p, -5.5, 5.5, 5.2, 7.8, 4.9, 5.1, "glass")              # arka cam
    box(p, -6.5, -2.5, 3, 4.5, -16.3, -15.9, "light")
    box(p, 2.5, 6.5, 3, 4.5, -16.3, -15.9, "light")
    box(p, 7.9, 8.3, 2, 4, -4, 2, "accent")                     # yan hava girisi
    box(p, -8.3, -7.9, 2, 4, -4, 2, "accent")
    box(p, -7, 7, 5, 6, 12, 14, "accent")                       # arka spoiler
    box(p, -8.5, 8.5, 0.5, 1.5, -16.6, -16, "trim", lost_at=2)  # on splitter
    box(p, 8, 9.2, 0, 3, -11, -6, "tire", lost_at=2)            # on sag teker
    box(p, 8, 9.2, 0, 3, 6, 12, "tire")
    box(p, -9.2, -8, 0, 3, -11, -6, "tire")
    box(p, -9.2, -8, 0, 3, 6, 12, "tire")
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
            write_json(os.path.join(ASSETS, "models", "item", f"car_{car}_{stage}.json"), model_json(car, stage, parts))
        write_json(os.path.join(ASSETS, "items", f"car_{car}.json"), item_json(car))
    print("Arabalar uretildi:", ", ".join(CARS))


if __name__ == "__main__":
    main()
