#!/usr/bin/env python3
"""
Zirh (kask + yelek) uretici.

Calistir:   python3 tools/gen_armor.py
Uretir:     assets/silahmod/models/item/<zirh>.json                    (envanter / yer / elde 3D model)
            assets/silahmod/items/<zirh>.json                          (esya tanimi)
            assets/silahmod/equipment/<zirh>.json                      (giyilince hangi doku)
            assets/silahmod/textures/entity/equipment/humanoid/<zirh>.png   (giyilince gorunen 64x32 doku)

Zirhlar: helmet_1, vest_1, helmet_2, vest_2
Koordinat mantigi gen_models.py ile ayni (l = yan, y = yukseklik, u = one dogru; on = +u).
"""
import math
import os
import random

import numpy as np
from PIL import Image

import gen_models as gm

G = gm.G
ASSETS = gm.ASSETS
EQUIP_TEX = os.path.join(ASSETS, "textures", "entity", "equipment", "humanoid")


# --------------------------------------------------------------------------- 3D esya modelleri
def dome(color, layers):
    return [G(color, -hl, hl, y1, y2, -hu, hu) for (y1, y2, hl, hu) in layers]


def helmet_1():
    """Yesil, yuvarlak kask: on tarafta koyu siperlik acikligi."""
    b = []
    b += [G("helm_green_dark", -5.0, 5.0, 2.0, 3.5, -5.0, 5.0)]          # alt kenar
    b += dome("helm_green", [(3.5, 5.5, 5.6, 5.6), (5.5, 7.5, 5.2, 5.2), (7.5, 9.0, 4.2, 4.2), (9.0, 10.0, 2.8, 2.8)])
    b += [G("helm_green_dark", -2.0, 2.0, 10.0, 10.4, -2.0, 2.0)]        # tepe
    b += [G("visor", -3.8, 3.8, 3.7, 5.4, 5.55, 5.95)]                   # on acikligi
    b += [G("strap_black", 5.65, 5.9, 2.6, 5.4, -1.0, 1.2)]              # yan kayis tokasi
    b += [G("strap_black", -5.9, -5.65, 2.6, 5.4, -1.0, 1.2)]
    b += [G("strap_black", 4.3, 4.8, 0.6, 2.0, 0.0, 0.8)]                # cene kayisi
    b += [G("strap_black", -4.8, -4.3, 0.6, 2.0, 0.0, 0.8)]
    b += [G("strap_black", -4.8, 4.8, 0.6, 1.1, 0.8, 1.3)]
    return b


def helmet_2():
    """Koyu savas kaski: genis siperlik, yan raylar, arka plaka."""
    b = []
    b += [G("helm_rail", -5.0, 5.0, 2.0, 3.6, -5.0, 5.0)]
    b += dome("helm_dark", [(3.6, 6.0, 5.6, 5.6), (6.0, 8.0, 5.2, 5.2), (8.0, 9.6, 4.2, 4.2), (9.6, 10.4, 2.8, 2.8)])
    b += [G("visor", -4.6, 4.6, 4.2, 6.4, 5.55, 6.0)]                    # siperlik
    b += [G("helm_rail", -4.9, 4.9, 6.4, 6.9, 5.55, 6.1)]                # siperlik ust cercevesi
    b += [G("helm_rail", -4.9, 4.9, 3.9, 4.2, 5.55, 6.1)]                # siperlik alt cercevesi
    b += [G("helm_rail", 5.6, 6.2, 4.0, 6.6, -2.5, 2.5)]                 # yan raylar
    b += [G("helm_rail", -6.2, -5.6, 4.0, 6.6, -2.5, 2.5)]
    b += [G("helm_rail", -0.6, 0.6, 10.4, 10.9, -3.2, 3.2)]              # tepe rayi
    b += [G("helm_rail", -3.2, 3.2, 3.2, 6.8, -6.0, -5.6)]               # arka plaka
    b += [G("strap_black", 4.3, 4.8, 0.6, 2.0, 0.0, 0.8)]
    b += [G("strap_black", -4.8, -4.3, 0.6, 2.0, 0.0, 0.8)]
    b += [G("strap_black", -4.8, 4.8, 0.6, 1.1, 0.8, 1.3)]
    return b


def vest(main, dark, light, big_pouches, collar, seed):
    rnd = random.Random(seed)
    b = []
    b += [G(main, -5.0, 5.0, 1.0, 11.0, 1.0, 2.6)]                       # on plaka
    b += [G(main, -5.0, 5.0, 1.0, 11.0, -2.6, -1.0)]                     # arka plaka
    b += [G(dark, 5.0, 5.5, 1.0, 9.0, -2.6, 2.6)]                        # yan kusak
    b += [G(dark, -5.5, -5.0, 1.0, 9.0, -2.6, 2.6)]
    for sgn in (-1, 1):                                                  # omuz kayislari
        l1, l2 = (1.6, 4.6) if sgn > 0 else (-4.6, -1.6)
        b += [G(dark, l1, l2, 11.0, 12.2, -2.6, 2.6)]
    # on cepler
    pw = [(-4.5, -1.7), (-1.3, 1.3), (1.7, 4.5)]
    top = 5.0 if big_pouches else 4.4
    for (l1, l2) in pw:
        b += [G(dark, l1, l2, 1.4, top, 2.6, 3.7 if big_pouches else 3.4)]
        b += [G(light, l1, l2, top, top + 0.35, 2.6, 3.8 if big_pouches else 3.5)]   # cep kapagi
    # MOLLE seritleri
    for y in (6.2, 8.6):
        b += [G(light, -4.8, 4.8, y, y + 0.3, 2.6, 2.75)]
    # kamuflaj / doku lekeleri
    for _ in range(9):
        l = rnd.uniform(-4.4, 3.4)
        y = rnd.uniform(5.2, 10.2)
        b += [G(dark if rnd.random() < 0.5 else light, l, l + rnd.uniform(0.8, 1.6), y, y + rnd.uniform(0.6, 1.3), 2.6, 2.72)]
    for _ in range(7):
        l = rnd.uniform(-4.4, 3.4)
        y = rnd.uniform(2.0, 10.0)
        b += [G(dark, l, l + rnd.uniform(0.8, 1.6), y, y + rnd.uniform(0.6, 1.3), -2.72, -2.6)]
    if collar:
        b += [G(dark, -3.8, 3.8, 12.2, 13.8, -2.8, -1.4)]                # yuksek yaka (arka)
        b += [G(dark, -3.8, -3.0, 12.2, 13.4, -1.4, 2.0)]
        b += [G(dark, 3.0, 3.8, 12.2, 13.4, -1.4, 2.0)]
        b += [G(dark, -3.0, 3.0, 6.0, 10.0, 2.6, 3.3)]                   # merkez plaka cebi
    return b


def vest_1():
    return vest("vest_grey", "vest_grey_dark", "vest_grey_light", big_pouches=False, collar=False, seed=11)


def vest_2():
    return vest("vest_brown", "vest_brown_dark", "vest_brown_light", big_pouches=True, collar=True, seed=23)


def medkit():
    """Beyaz govdeli, ortasi kirmizi seritli, ustunde beyaz hac olan kalkan seklinde medkit."""
    b = []
    b += [G("strap_black", -6.2, 6.2, 0.0, 1.0, -4.6, 4.6)]                    # alt koyu kenar
    for (y1, y2, hl, hu) in [(1.0, 4.0, 6.0, 4.4), (4.0, 6.0, 5.4, 4.0), (6.0, 7.4, 4.2, 3.2)]:
        b += [G("kit_white", -hl, -1.6, y1, y2, -hu, hu)]
        b += [G("kit_red", -1.6, 1.6, y1, y2, -hu, hu)]
        b += [G("kit_white", 1.6, hl, y1, y2, -hu, hu)]
    b += [G("kit_white", -2.6, 2.6, 7.4, 7.9, -0.8, 0.8)]                      # hac
    b += [G("kit_white", -0.8, 0.8, 7.4, 7.9, -2.6, -0.8)]
    b += [G("kit_white", -0.8, 0.8, 7.4, 7.9, 0.8, 2.6)]
    for (l, u) in [(4.7, 0.0), (-4.7, 0.0)]:                                   # civatalar (yanlar)
        b += [G("steel_dark", l - 0.3, l + 0.3, 6.0, 6.35, u - 0.3, u + 0.3)]
    for u in (3.6, -3.6):
        b += [G("steel_dark", -0.3, 0.3, 6.0, 6.35, u - 0.3, u + 0.3)]
    return b


ARMORS = {"helmet_1": helmet_1, "vest_1": vest_1, "helmet_2": helmet_2, "vest_2": vest_2}

ARMOR_GUI_ROT = (22, 148, 0)   # on yuz gorunsun


def armor_display(boxes):
    gs = gm.fit_scale(ARMOR_GUI_ROT, boxes, 14.5)
    gui = gm.disp_centered(ARMOR_GUI_ROT, gs, boxes)
    ground = gm.disp_centered((0, 0, 0), 0.5, boxes)
    fixed = gm.disp_centered((0, 180, 0), min(1.0, gm.fit_scale((0, 180, 0), boxes, 13.0)), boxes)
    hand = gm.disp_centered((0, 180, 0), 0.5, boxes)
    return {
        "thirdperson_righthand": hand, "thirdperson_lefthand": hand,
        "firstperson_righthand": hand, "firstperson_lefthand": hand,
        "gui": gui, "ground": ground, "fixed": fixed,
        "head": gm.disp_centered((0, 180, 0), 0.9, boxes),
    }


def held_display(boxes, hand, rot, scale, gui_scale_target=14.5, ground_scale=0.8):
    """Elde tutulan / yere atilan esya (medkit, el bombasi) icin goruntu ayarlari."""
    c, _ = gm.bbox_center(boxes)
    fp = gm.disp(rot, scale, c, hand)
    tp = gm.disp((0, 0, 0), scale * 0.7, c, (0.0, 3.0, 1.0))
    gs = gm.fit_scale(ARMOR_GUI_ROT, boxes, gui_scale_target)
    return {
        "thirdperson_righthand": tp, "thirdperson_lefthand": tp,
        "firstperson_righthand": fp, "firstperson_lefthand": fp,
        "gui": gm.disp_centered(ARMOR_GUI_ROT, gs, boxes),
        "ground": gm.disp_centered((0, 0, 0), ground_scale, boxes),
        "fixed": gm.disp_centered((0, 180, 0), min(1.0, gm.fit_scale((0, 180, 0), boxes, 13.0)), boxes),
        "head": gm.disp_centered((0, 180, 0), 0.9, boxes),
    }


# --------------------------------------------------------------------------- giyilince gorunen doku (64x32)
def rgb(h):
    return np.array(gm.hex_rgb(h), dtype=float)


PAL = {n: rgb(h) for n, h in gm.PALETTE}


class Tex:
    def __init__(self, seed):
        self.a = np.zeros((32, 64, 4), dtype=np.uint8)
        self.r = random.Random(seed)

    def fill(self, x1, y1, x2, y2, color, jitter=6):
        base = PAL[color] if isinstance(color, str) else color
        for y in range(y1, y2):
            for x in range(x1, x2):
                j = self.r.uniform(-jitter, jitter)
                self.a[y, x, :3] = np.clip(base + j, 0, 255)
                self.a[y, x, 3] = 255

    def clear(self, x1, y1, x2, y2):
        self.a[y1:y2, x1:x2] = 0

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(self.a, "RGBA").save(path)


# Kafa yuzleri (her biri 8x8): ust (8,0) alt (16,0) | sag (0,8) on (8,8) sol (16,8) arka (24,8)
def tex_helmet_1():
    t = Tex(1)
    t.fill(0, 0, 32, 16, "helm_green", 7)                       # tum kafa kabugu
    t.fill(8, 0, 16, 8, "helm_green", 7)
    t.fill(11, 0, 13, 8, "helm_green_dark", 4)                  # tepe seridi
    t.clear(16, 0, 24, 8)                                        # alt yuz yok
    for x0 in (0, 16, 24):                                       # yan + arka alt kenar koyu
        t.fill(x0, 14, x0 + 8, 16, "helm_green_dark", 4)
    t.fill(1, 11, 5, 12, "strap_black", 2)                       # yan kayis
    t.fill(18, 11, 22, 12, "strap_black", 2)
    t.fill(8, 8, 16, 10, "helm_green", 6)                        # on: alin
    t.fill(8, 10, 16, 13, "helm_green_dark", 3)
    t.fill(9, 10, 15, 13, "visor", 2)                            # on: siperlik acikligi
    t.a[10, 9:15, :3] = np.clip(PAL["visor"] + 22, 0, 255)       # hafif yansima
    t.clear(8, 13, 16, 16)                                       # cene acik
    return t


def tex_helmet_2():
    t = Tex(2)
    t.fill(0, 0, 32, 16, "helm_dark", 6)
    t.clear(16, 0, 24, 8)
    t.fill(11, 0, 13, 8, "helm_rail", 4)                         # tepe rayi
    for x0 in (0, 16):
        t.fill(x0 + 1, 10, x0 + 7, 13, "helm_rail", 4)           # yan raylar
        t.fill(x0, 14, x0 + 8, 16, "helm_rail", 4)
    t.fill(24, 9, 32, 15, "helm_rail", 5)                        # arka plaka
    t.fill(26, 10, 30, 14, "helm_dark", 4)
    t.fill(8, 8, 16, 10, "helm_dark", 5)
    t.fill(8, 8, 16, 9, "helm_rail", 3)
    t.fill(8, 10, 16, 13, "visor", 2)                            # genis siperlik
    t.a[10, 9:15, :3] = np.clip(PAL["visor"] + 30, 0, 255)
    t.clear(8, 13, 16, 16)
    return t


# Govde yuzleri: ust (20,16,28,20) alt (28,16,36,20) | sag (16,20,20,32) on (20,20,28,32) sol (28,20,32,32) arka (32,20,40,32)
def tex_vest(main, dark, light, big, seed):
    t = Tex(seed)
    t.fill(16, 20, 40, 32, main, 7)                              # yan + on + arka
    # kamuflaj lekeleri (on ve arka)
    for (x1, x2) in ((20, 28), (32, 40)):
        for _ in range(9):
            x = t.r.randint(x1, x2 - 2)
            y = t.r.randint(20, 29)
            t.fill(x, y, min(x2, x + t.r.randint(1, 3)), min(32, y + t.r.randint(1, 3)),
                   dark if t.r.random() < 0.55 else light, 5)
    # omuz kayislari (on ve arka ust)
    for x in (21, 26):
        t.fill(x, 20, x + 2, 24, dark, 3)
        t.fill(x + 12, 20, x + 14, 24, dark, 3)
    # MOLLE seritleri
    for y in (25, 27):
        t.fill(20, y, 28, y + 1, light, 4)
    # on cepler
    top = 26 if big else 27
    for (x1, x2) in ((20, 22), (22, 26), (26, 28)):
        t.fill(x1, top, x2, 32, dark, 3)
        t.fill(x1, top, x2, top + 1, light, 3)
        t.a[top:32, x2 - 1, :3] = np.clip(PAL[main] * 0.8, 0, 255)  # cepler arasi ince bosluk
    if big:
        t.fill(21, 21, 27, 26, dark, 3)                          # plaka cebi
        t.fill(21, 21, 27, 22, light, 3)
    # yan kusak koyu
    t.fill(16, 26, 20, 32, dark, 4)
    t.fill(28, 26, 32, 32, dark, 4)
    # ust / alt yuzler
    t.fill(20, 16, 28, 20, dark, 4)
    t.fill(28, 16, 36, 20, dark, 4)
    return t


# --------------------------------------------------------------------------- cikti
def main():
    gm.write_palette_png(os.path.join(ASSETS, "textures", "item", "palette.png"))
    for name, build in ARMORS.items():
        boxes = build()
        gm.write_json(os.path.join(ASSETS, "models", "item", f"{name}.json"), gm.model_json(boxes, armor_display(boxes)))
        gm.write_json(os.path.join(ASSETS, "items", f"{name}.json"),
                      {"model": {"type": "minecraft:model", "model": f"silahmod:item/{name}"}})
        gm.write_json(os.path.join(ASSETS, "equipment", f"{name}.json"),
                      {"layers": {"humanoid": [{"texture": f"silahmod:{name}"}]}})
        print(f"{name}: {len(boxes)} parca")
    # --- medkit (zirh degil ama ayni model altyapisi) ---
    mk = medkit()
    gm.write_json(os.path.join(ASSETS, "models", "item", "medkit.json"),
                  gm.model_json(mk, held_display(mk, hand=(1.0, 4.5, -3.0), rot=(8, -30, 0), scale=0.95)))
    # Medkit kullanilirken (sag tik basili) 1. sahista elde gizlenir: kol animasyonu ekrana cizilir (MedkitOverlay)
    gm.write_json(os.path.join(ASSETS, "items", "medkit.json"), {"model": {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": ["firstperson_righthand", "firstperson_lefthand"], "model": {
            "type": "minecraft:condition", "property": "minecraft:using_item",
            "on_true": {"type": "minecraft:empty"},
            "on_false": {"type": "minecraft:model", "model": "silahmod:item/medkit"}}}],
        "fallback": {"type": "minecraft:model", "model": "silahmod:item/medkit"}}})
    print(f"medkit: {len(mk)} parca")
    tex_helmet_1().save(os.path.join(EQUIP_TEX, "helmet_1.png"))
    tex_helmet_2().save(os.path.join(EQUIP_TEX, "helmet_2.png"))
    tex_vest("vest_grey", "vest_grey_dark", "vest_grey_light", False, 5).save(os.path.join(EQUIP_TEX, "vest_1.png"))
    tex_vest("vest_brown", "vest_brown_dark", "vest_brown_light", True, 6).save(os.path.join(EQUIP_TEX, "vest_2.png"))


if __name__ == "__main__":
    main()
