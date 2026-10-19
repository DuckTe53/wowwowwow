#!/usr/bin/env python3
"""
Silah modelleri uretici.

Calistir:   python3 tools/gen_models.py
Uretir:     assets/silahmod/models/item/*.json   (3D modeller + reload kareleri)
            assets/silahmod/items/*.json         (hangi kare ne zaman gosterilir)
            assets/silahmod/textures/item/palette.png

Silahlar kucuk kutulardan (cuboid) olusur. Hepsi ayni 16x16'lik renk paletini kullanir,
yani ekstra doku cizmen gerekmez.

KOORDINAT MANTIGI (silah-yerel):
    l = yanlamasina (- sol, oyuncunun gordugu taraf)
    y = yukseklik
    u = ileri (namlu yonu). Minecraft'ta namlu KUZEYE (-Z) bakar.

RELOAD KARELERI:
    Her silahin FRAMES listesi var. Kare sayisini degistirirsen WeaponConfig'deki
    RELOAD_FRAMES sabitini de ayni sayiya getir.
"""
import json
import math
import os
import struct
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "src", "main", "resources", "assets", "silahmod"))
EMPTY_FRAME = 99  # (su an kullanilmiyor) mermisi bitmis ozel model icin kare numarasi

# --------------------------------------------------------------------------- palet
PALETTE = [
    ("gunmetal", "#2f3237"), ("steel_dark", "#1c1e22"), ("steel", "#6b7078"), ("steel_light", "#aab0b8"),
    ("wood", "#6e4a2a"), ("wood_dark", "#4a301b"), ("brass", "#d4a82a"), ("olive", "#4d5535"),
    ("olive_dark", "#363c25"), ("black", "#0d0d0f"), ("rocket_grey", "#7d838b"), ("rocket_red", "#b8391c"),
    ("lens", "#2f5d86"), ("leather", "#3a281d"), ("tube", "#58603f"), ("white", "#e8e8e8"),
    # --- zirhlar (tools/gen_armor.py kullanir) ---
    ("helm_green", "#1f5a46"), ("helm_green_dark", "#14382c"), ("helm_dark", "#3a3d3b"),
    ("helm_rail", "#5a5f5c"), ("visor", "#0f1318"), ("strap_black", "#1a1b1c"),
    ("vest_grey", "#8f9389"), ("vest_grey_dark", "#5f645e"), ("vest_grey_light", "#b0b4aa"),
    ("vest_brown", "#76633f"), ("vest_brown_dark", "#4a3d27"), ("vest_brown_light", "#97835a"),
    # --- medkit ---
    ("kit_red", "#d92a1e"), ("kit_white", "#eceff1"),
    # --- tufek / SMG renkleri ---
    ("fde", "#a08c63"), ("fde_dark", "#7a6a47"), ("ak_wood", "#9a5a2c"), ("ak_wood_dark", "#6a3a1a"),
    ("plum", "#3d2427"),
]
IDX = {name: i for i, (name, _) in enumerate(PALETTE)}


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def write_palette_png(path):
    w = h = 16
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            i = y * w + x
            r, g, b = hex_rgb(PALETTE[i][1]) if i < len(PALETTE) else (255, 0, 255)
            row += bytes((r, g, b, 255))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


# --------------------------------------------------------------------------- kutu yardimcilari
def G(color, l1, l2, y1, y2, u1, u2):
    """Silah-yerel koordinatla kutu. Donus: model uzayinda kutu."""
    return {"c": color, "f": (8 + l1, y1, 8 - u2), "t": (8 + l2, y2, 8 - u1)}


def sh(boxes, dl=0.0, dy=0.0, du=0.0):
    """Kutulari kaydir (animasyon icin)."""
    return [{"c": b["c"],
             "f": (b["f"][0] + dl, b["f"][1] + dy, b["f"][2] - du),
             "t": (b["t"][0] + dl, b["t"][1] + dy, b["t"][2] - du)} for b in boxes]


# --------------------------------------------------------------------------- ORTAK: sarjor + kurma kolu animasyonu
# Her silah: sabit govde kutulari + 'mag' (sarjor) + 'bolt' (kapak/kurma kolu) gruplari.
# st["mag_dy"]  : sarjor kaymasi (negatif = asagi, None = sarjor yok). P90'da sarjor ustte oldugu icin yon ters.
# st["bolt_du"] : kapak / kurma kolunun geri kaymasi (negatif = geriye)
# st["dr"]      : birinci sahista el donusu (reload sirasinda silah hafif yatar)
def assemble(body, mag, bolt, st, mag_sign=1.0):
    b = list(body)
    mag_dy = st.get("mag_dy", 0.0)
    if mag_dy is not None:
        b += sh(mag, dy=mag_dy * mag_sign)
    b += sh(bolt, du=st.get("bolt_du", 0.0))
    return b


# 5 kare (WeaponConfig.RELOAD_FRAMES ile ayni olmali):
#   1 sarjor serbest  2 dusuyor  3 sarjor yok  4 yeni sarjor giriyor  5 oturdu + kurma
RELOAD_FRAMES_STD = [
    dict(mag_dy=-0.8, dr=(3, 0, -5)),
    dict(mag_dy=-3.5, dr=(6, 0, -9)),
    dict(mag_dy=None, dr=(8, 0, -12)),
    dict(mag_dy=-3.0, dr=(6, 0, -9)),
    dict(mag_dy=0.0, bolt_du=-1.3, dr=(2, 0, -4)),
]


# --------------------------------------------------------------------------- PISTOL (klasik, ahsap kabzali)
def pistol(st):
    b = []
    # govde (frame)
    b += [G("gunmetal", -0.62, 0.62, 6.6, 8.4, -3.0, 3.4)]
    b += [G("gunmetal", -0.62, 0.62, 7.0, 8.4, 3.4, 5.0)]             # on ray
    # tetik koruma + tetik
    b += [G("steel_dark", -0.35, 0.35, 5.8, 6.6, -0.8, 3.0), G("steel_dark", -0.35, 0.35, 5.8, 7.6, 2.5, 3.0)]
    b += [G("black", -0.25, 0.25, 6.4, 7.7, -0.5, 0.0)]
    # kabza (ahsap, geriye egimli) + arka kayis
    b += [G("wood", -0.85, 0.85, 5.0, 6.6, -3.5, -0.9)]
    b += [G("wood", -0.85, 0.85, 3.6, 5.0, -3.8, -1.2)]
    b += [G("steel_dark", -0.5, 0.5, 3.6, 8.4, -4.3, -3.7)]
    b += [G("steel_dark", -0.5, 0.5, 8.0, 9.2, -3.8, -3.0)]           # kabza emniyeti
    # namlu ucu
    b += [G("steel_dark", -0.4, 0.4, 8.8, 9.9, 5.6, 6.8)]
    # sarjor
    mag = [G("steel_dark", -0.8, 0.8, 1.9, 2.8, -4.1, -1.3), G("steel", -0.62, 0.62, 2.8, 3.6, -3.9, -1.5)]
    # kapak (slide)
    bolt = [G("steel_light", -0.78, 0.78, 8.4, 10.6, -3.8, 5.8),
            G("steel", -0.8, 0.8, 8.4, 9.0, -3.8, 5.8),                 # alt golge seridi
            G("steel_light", -0.3, 0.3, 10.6, 10.9, -3.6, 5.6),         # ust nisan rayi
            G("black", -0.2, 0.2, 10.9, 11.5, 5.0, 5.5),                # on arpacik
            G("black", -0.5, 0.5, 10.9, 11.5, -3.6, -3.0),              # arka nisangah
            G("steel_dark", -0.8, 0.8, 8.7, 10.3, -3.5, -3.3), G("steel_dark", -0.8, 0.8, 8.7, 10.3, -3.0, -2.8),
            G("steel_dark", -0.8, 0.8, 8.7, 10.3, -2.5, -2.3)]          # kavrama oluklari
    return assemble(b, mag, bolt, st)


# --------------------------------------------------------------------------- GLOCK 17 (polimer govde, kare kapak)
def glock_17(st):
    b = []
    # polimer govde (frame) + on ray
    b += [G("black", -0.72, 0.72, 6.7, 8.4, -3.4, 4.2)]
    b += [G("black", -0.72, 0.72, 7.3, 8.4, 4.2, 5.8)]
    # kabza (hafif geriye egimli) + doku paneli
    b += [G("black", -0.82, 0.82, 6.0, 6.7, -3.5, -0.4)]
    b += [G("black", -0.82, 0.82, 4.6, 6.0, -3.8, -0.7)]
    b += [G("black", -0.82, 0.82, 3.4, 4.6, -4.1, -1.0)]
    b += [G("gunmetal", -0.86, -0.8, 3.9, 5.9, -3.7, -1.2)]
    # tetik koruma + tetik
    b += [G("black", -0.4, 0.4, 5.9, 6.7, -0.4, 3.6), G("black", -0.4, 0.4, 5.9, 7.4, 3.2, 3.6)]
    b += [G("steel", -0.2, 0.2, 6.4, 7.4, -0.2, 0.2)]
    # namlu ucu
    b += [G("steel_dark", -0.35, 0.35, 8.9, 9.8, 6.0, 6.7)]
    # sarjor
    mag = [G("black", -0.84, 0.84, 2.4, 3.4, -4.3, -1.0), G("gunmetal", -0.7, 0.7, 3.4, 4.0, -3.9, -1.4)]
    # kapak (slide): kare, duz ust, firlatma penceresi
    bolt = [G("gunmetal", -0.76, 0.76, 8.4, 10.5, -3.6, 6.0),
            G("steel_dark", -0.78, -0.72, 9.0, 10.1, 0.0, 2.6),         # firlatma penceresi (gorunen yan)
            G("black", -0.4, 0.4, 10.5, 10.8, -3.4, 5.8),
            G("black", -0.2, 0.2, 10.8, 11.3, 5.3, 5.8),                # on arpacik
            G("black", -0.5, 0.5, 10.8, 11.3, -3.4, -2.8),              # arka nisangah
            G("steel_dark", -0.78, 0.78, 8.7, 10.2, -3.4, -3.2), G("steel_dark", -0.78, 0.78, 8.7, 10.2, -2.9, -2.7),
            G("steel_dark", -0.78, 0.78, 8.7, 10.2, -2.4, -2.2),
            G("steel_dark", -0.78, 0.78, 8.7, 10.2, 5.0, 5.2), G("steel_dark", -0.78, 0.78, 8.7, 10.2, 5.4, 5.6)]
    return assemble(b, mag, bolt, st)


# --------------------------------------------------------------------------- M4 ailesi (M4A1-S susturuculu, M4A4 normal)
def m4_family(st, silenced, accent, accent_dark, mag_len):
    """M4A1-S ve M4A4 ayni silueti paylasir; fark: susturucu ve aksan rengi (kabza, kundak, on kundak)."""
    b = []
    # ust ve alt govde
    b += [G("black", -0.9, 0.9, 8.0, 10.2, -2.0, 5.4)]
    b += [G("black", -0.9, 0.9, 6.4, 8.0, -2.4, 3.4)]
    b += [G("steel_dark", -0.92, -0.88, 8.4, 9.8, 0.2, 2.8)]          # firlatma pencere kapagi (gorunen yan)
    # kundak: tampon borusu + omuz dayama
    b += [G("gunmetal", -0.5, 0.5, 8.0, 9.4, -8.0, -2.0)]
    b += [G(accent, -0.8, 0.8, 6.2, 9.6, -12.0, -7.8)]
    b += [G("steel_dark", -0.82, 0.82, 6.2, 9.6, -12.4, -12.0)]       # kundak pedi
    # tabanca kabzasi (egimli)
    b += [G(accent, -0.8, 0.8, 5.0, 6.4, -3.6, -2.0)]
    b += [G(accent, -0.8, 0.8, 3.2, 5.0, -4.2, -2.6)]
    # tetik koruma + tetik
    b += [G("steel_dark", -0.35, 0.35, 5.7, 6.4, -1.8, 1.4), G("steel_dark", -0.35, 0.35, 5.7, 7.2, 1.0, 1.4)]
    b += [G("black", -0.22, 0.22, 6.4, 7.5, -0.6, -0.2)]
    # on kundak (handguard) + havalandirma delikleri
    b += [G(accent_dark, -0.86, 0.86, 7.6, 10.0, 5.4, 12.6)]
    for u in (6.2, 7.6, 9.0, 10.4):
        b += [G("black", -0.9, -0.85, 8.3, 9.3, u, u + 0.7)]
    # ust ray + nisanlar
    b += [G("steel_dark", -0.42, 0.42, 10.2, 10.7, -2.0, 12.4)]
    b += [G("black", -0.2, 0.2, 10.7, 11.7, 11.6, 12.0)]              # on arpacik
    b += [G("black", -0.45, 0.45, 10.7, 11.4, -1.8, -1.2)]            # arka nisangah
    # namlu
    b += [G("steel_dark", -0.35, 0.35, 8.6, 9.6, 12.6, 13.4)]
    if silenced:
        b += [G("steel", -0.8, 0.8, 8.1, 10.1, 13.4, 19.6)]           # susturucu
        b += [G("steel_light", -0.82, 0.82, 8.1, 10.1, 15.2, 15.5), G("steel_light", -0.82, 0.82, 8.1, 10.1, 17.0, 17.3)]
        b += [G("black", -0.78, 0.78, 8.3, 9.9, 19.6, 20.0)]          # uc kapagi
    else:
        b += [G("steel_dark", -0.5, 0.5, 8.4, 9.8, 13.4, 15.2)]       # alev sondurucu
        b += [G("black", -0.52, 0.52, 8.7, 9.5, 14.0, 14.3), G("black", -0.52, 0.52, 8.7, 9.5, 14.7, 15.0)]
    # sarjor (hafif one egimli)
    mag = [G("gunmetal", -0.75, 0.75, 5.0 - mag_len * 0.5, 6.4, 0.2, 2.6),
           G("gunmetal", -0.75, 0.75, 3.6 - mag_len, 5.0 - mag_len * 0.5, 0.5, 2.9),
           G("black", -0.78, 0.78, 3.3 - mag_len, 3.6 - mag_len, 0.5, 3.0)]
    # kurma kolu
    bolt = [G("steel_dark", -0.5, 0.5, 10.2, 10.9, -3.4, -2.2)]
    return assemble(b, mag, bolt, st)


def m4a1_s(st):
    return m4_family(st, True, "black", "gunmetal", 0.0)


def m4a4(st):
    return m4_family(st, False, "fde", "fde_dark", 0.8)


# --------------------------------------------------------------------------- AK ailesi (AK-47 ahsap, AK-74M polimer)
def ak_family(st, furniture, furniture_dark, mag_color, folding, brake):
    b = []
    # govde (damgalanmis kapak) + ust kapak
    b += [G("steel_dark", -0.85, 0.85, 7.6, 9.8, -3.0, 6.0)]
    b += [G("gunmetal", -0.8, 0.8, 9.8, 10.2, -3.0, 6.0)]
    b += [G("steel", -0.88, -0.84, 8.0, 9.2, 0.4, 0.9)]               # firlatma penceresi cizgisi
    # kundak
    if folding:
        b += [G(furniture, -0.55, 0.55, 7.0, 9.2, -11.0, -3.0)]       # katlanir kundak (AK-74M)
        b += [G("steel_dark", -0.6, 0.6, 7.0, 9.2, -11.4, -11.0)]
        b += [G("steel_dark", -0.7, 0.7, 7.6, 9.0, -3.4, -2.6)]       # mentese
    else:
        b += [G(furniture, -0.8, 0.8, 6.4, 9.4, -8.0, -3.0)]
        b += [G(furniture, -0.8, 0.8, 5.2, 9.0, -11.2, -8.0)]
        b += [G("steel_dark", -0.82, 0.82, 5.2, 9.0, -11.6, -11.2)]
    # tabanca kabzasi
    b += [G(furniture_dark, -0.8, 0.8, 5.4, 7.6, -3.8, -2.2)]
    b += [G(furniture_dark, -0.8, 0.8, 3.4, 5.4, -4.4, -2.8)]
    # tetik koruma + tetik
    b += [G("steel_dark", -0.35, 0.35, 6.6, 7.2, -2.0, 1.6), G("steel_dark", -0.35, 0.35, 6.6, 7.8, 1.2, 1.6)]
    b += [G("black", -0.22, 0.22, 7.0, 8.0, -0.8, -0.4)]
    # on kundak (alt + ust) ve gaz borusu
    b += [G(furniture, -0.86, 0.86, 7.2, 9.2, 6.0, 11.6)]
    b += [G(furniture_dark, -0.8, 0.8, 9.2, 10.2, 6.0, 11.6)]
    b += [G("steel_dark", -0.45, 0.45, 10.2, 11.0, 6.0, 12.4)]
    b += [G("steel_dark", -0.5, 0.5, 8.4, 11.4, 12.4, 13.4)]          # gaz blogu
    b += [G("black", -0.15, 0.15, 11.4, 12.4, 12.6, 13.0)]            # on arpacik
    b += [G("black", -0.5, 0.5, 10.2, 11.0, 3.6, 4.8)]                # arka nisangah
    # namlu + agiz freni
    b += [G("steel_dark", -0.4, 0.4, 8.6, 9.6, 13.4, 16.2)]
    if brake == "slant":
        b += [G("steel", -0.55, 0.55, 8.4, 9.8, 16.2, 17.8), G("black", -0.57, 0.57, 8.9, 9.3, 16.8, 17.0)]
    else:
        b += [G("steel_dark", -0.65, 0.65, 8.3, 9.9, 16.2, 18.2), G("black", -0.67, 0.67, 8.7, 9.5, 16.8, 17.1),
              G("black", -0.67, 0.67, 8.7, 9.5, 17.4, 17.7)]
    # sarjor (muz gibi one dogru kivrilir)
    mag = [G(mag_color, -0.75, 0.75, 5.6, 7.6, -0.4, 2.8),
           G(mag_color, -0.75, 0.75, 3.6, 5.6, 0.0, 3.2),
           G(mag_color, -0.75, 0.75, 1.8, 3.6, 0.8, 3.8)]
    # kurma kolu (gorunen tarafa konuldu ki animasyon gorunsun)
    bolt = [G("steel", -1.25, -0.85, 8.6, 9.3, -1.4, -0.2)]
    return assemble(b, mag, bolt, st)


def ak_47(st):
    return ak_family(st, "ak_wood", "ak_wood_dark", "steel_dark", False, "slant")


def ak_74m(st):
    return ak_family(st, "plum", "black", "plum", True, "heavy")


# --------------------------------------------------------------------------- FN P90 (bullpup PDW)
def p90(st):
    b = []
    # arka blok (omuz) + ust kol + alt kol: aradaki bosluk basparmak deligi
    b += [G("fde", -0.95, 0.95, 5.0, 9.4, -7.6, -4.2)]
    b += [G("fde", -0.95, 0.95, 7.6, 9.4, -4.2, 0.4)]
    b += [G("fde", -0.95, 0.95, 5.0, 6.2, -4.2, 0.4)]
    b += [G("steel_dark", -0.97, 0.97, 5.0, 9.4, -8.0, -7.6)]         # omuz pedi
    # on kabza (el tutusu) + tetik + govde on kismi
    b += [G("fde", -0.95, 0.95, 4.4, 9.4, 0.4, 2.8)]
    b += [G("black", -0.2, 0.2, 6.4, 7.6, 3.0, 3.4)]                  # tetik
    b += [G("fde", -0.95, 0.95, 6.0, 9.4, 2.8, 6.6)]
    b += [G("fde_dark", -0.96, 0.96, 6.0, 6.5, 2.8, 6.6)]             # alt golge seridi
    # namlu kilifi + alev sondurucu
    b += [G("black", -0.6, 0.6, 7.4, 9.2, 6.6, 9.2)]
    b += [G("steel_dark", -0.5, 0.5, 7.6, 9.0, 9.2, 10.6)]
    # ust ray + kirmizi nokta nisangah
    b += [G("black", -0.5, 0.5, 9.4, 10.1, -5.4, 5.8)]
    b += [G("black", -0.7, 0.7, 10.1, 11.9, -2.4, 0.2)]
    b += [G("lens", -0.55, 0.55, 10.4, 11.6, 0.2, 0.35)]
    # sarjor: ustte, yarisaydam (kirli duman rengi). P90'da sarjor yukari-geri kayar (mag_sign = -1)
    mag = [G("steel_dark", -0.8, 0.8, 9.4, 10.5, -5.6, 5.6),
           G("lens", -0.82, 0.82, 9.6, 10.3, -4.8, 4.8)]
    # kurma kolu
    bolt = [G("black", -1.25, -0.9, 8.4, 9.2, 3.8, 5.0)]
    return assemble(b, mag, bolt, st, mag_sign=-1.0)


# --------------------------------------------------------------------------- KRISS VECTOR (SMG)
def kriss_vector(st):
    b = []
    # ana govde + alt kisim
    b += [G("black", -0.9, 0.9, 7.4, 10.2, -4.4, 6.4)]
    b += [G("gunmetal", -0.86, 0.86, 6.4, 7.4, -2.4, 3.8)]
    b += [G("steel_dark", -0.92, -0.88, 8.2, 9.6, -0.6, 2.2)]         # firlatma penceresi (gorunen yan)
    # namlu kilifi (yivli) + agiz
    b += [G("gunmetal", -0.85, 0.85, 7.8, 9.8, 6.4, 12.8)]
    for u in (7.2, 8.4, 9.6, 10.8):
        b += [G("black", -0.88, -0.84, 8.2, 9.4, u, u + 0.6)]
    b += [G("steel_dark", -0.5, 0.5, 8.2, 9.4, 12.8, 14.0)]
    # ust ray + katlanir nisanlar
    b += [G("steel_dark", -0.45, 0.45, 10.2, 10.7, -3.6, 10.0)]
    b += [G("black", -0.2, 0.2, 10.7, 11.6, 9.4, 9.8)]
    b += [G("black", -0.5, 0.5, 10.7, 11.4, -3.4, -2.6)]
    # iskelet kundak (H seklinde)
    b += [G("black", -0.5, 0.5, 8.4, 9.6, -9.6, -4.4)]
    b += [G("steel_dark", -0.4, 0.4, 6.6, 8.4, -9.8, -9.2)]
    b += [G("black", -0.8, 0.8, 6.4, 10.0, -10.4, -9.6)]
    # tabanca kabzasi (sarjor yuvasi, hafif one egimli)
    b += [G("black", -0.8, 0.8, 5.0, 7.4, -3.8, -1.8)]
    b += [G("black", -0.8, 0.8, 3.4, 5.0, -3.5, -1.5)]
    # tetik koruma + tetik
    b += [G("black", -0.4, 0.4, 6.0, 6.5, -1.6, 2.4), G("black", -0.4, 0.4, 6.0, 7.4, 2.0, 2.4)]
    b += [G("steel", -0.2, 0.2, 6.5, 7.4, -0.3, 0.1)]
    # on dikey kabza
    b += [G("gunmetal", -0.75, 0.75, 4.2, 6.4, 3.6, 5.2)]
    # sarjor (Glock tipi, kabzanin icinde)
    mag = [G("steel_dark", -0.84, 0.84, 2.0, 3.4, -3.7, -1.3), G("gunmetal", -0.72, 0.72, 3.4, 4.0, -3.5, -1.5)]
    # kurma kolu
    bolt = [G("steel", -1.2, -0.9, 9.0, 9.7, -1.4, -0.2)]
    return assemble(b, mag, bolt, st)


# --------------------------------------------------------------------------- BICAK
def knife(st):
    b = []
    b += [G("steel_light", -0.3, 0.3, 9.0, 10.2, 1.6, 8.6)]           # sirt
    b += [G("steel", -0.31, 0.31, 8.5, 9.0, 1.9, 8.2)]                # kesici kenar
    b += [G("steel_light", -0.3, 0.3, 9.4, 10.2, 8.6, 10.2)]          # uc (basamakli)
    b += [G("steel_light", -0.3, 0.3, 9.8, 10.2, 10.2, 11.2)]
    b += [G("steel_dark", -0.9, 0.9, 8.2, 10.4, 1.0, 1.6)]            # siper
    b += [G("leather", -0.6, 0.6, 8.0, 10.1, -4.0, 1.0)]              # sap
    for a, c in ((-3.4, -3.0), (-2.2, -1.8), (-1.0, -0.6)):
        b += [G("black", -0.68, 0.68, 7.9, 10.2, a, c)]               # tutus halkalari
    b += [G("steel_dark", -0.7, 0.7, 7.7, 10.4, -4.6, -4.0)]          # pomel
    return b


# --------------------------------------------------------------------------- ekran (display) matematigi
def rot_xyz(rx, ry, rz):
    """Minecraft: vertex once Z, sonra Y, sonra X ile doner (Rx @ Ry @ Rz)."""
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


CENTER = np.array([8.0, 8.0, 8.0])


def bbox_center(boxes):
    lo = np.min([b["f"] for b in boxes], axis=0)
    hi = np.max([b["t"] for b in boxes], axis=0)
    return (lo + hi) / 2, hi - lo


def disp(rot, scale, pivot, hand):
    """Pivot noktasi (tutus yeri) elin oldugu noktaya (hand) gelsin diye ceviri hesapla."""
    R = rot_xyz(*rot)
    t = np.array(hand) - scale * (R @ (np.array(pivot) - CENTER))
    return {"rotation": [round(float(v), 2) for v in rot],
            "translation": [round(float(v), 2) for v in t],
            "scale": [scale, scale, scale]}


def disp_centered(rot, scale, boxes):
    """Modelin ortasi merkeze gelsin (gui / yer / cerceve icin)."""
    R = rot_xyz(*rot)
    c, _ = bbox_center(boxes)
    t = -scale * (R @ (c - CENTER))
    return {"rotation": list(rot),
            "translation": [round(float(v), 2) for v in t],
            "scale": [scale, scale, scale]}


def fit_scale(rot, boxes, target):
    """Dondurulmus modelin ekrandaki en buyuk boyutu 'target' birim olsun."""
    R = rot_xyz(*rot)
    pts = []
    for b in boxes:
        for x in (b["f"][0], b["t"][0]):
            for y in (b["f"][1], b["t"][1]):
                for z in (b["f"][2], b["t"][2]):
                    pts.append(R @ (np.array([x, y, z]) - CENTER))
    pts = np.array(pts)
    ext = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
    return round(min(4.0, target / ext), 3)


# Her silah icin ayarlar.
#   pivot : tutus noktasi (model koordinati: x=8+l, y, z=8-u). Tabanca kabzasinin ortasi.
#   fp    : birinci sahis. rot=(pitch, yaw, roll), scale, hand=(x,y,z) el konumuna ek kaydirma
#   tp    : ucuncu sahis
PISTOL_FP = dict(rot=(6, 20, -3), scale=1.05, hand=(0.0, 5.5, -2.0))
PISTOL_TP = dict(rot=(90, 0, 0), scale=0.72, hand=(0, 1.5, 0))
RIFLE_FP = dict(rot=(4, 18, 0), scale=0.72, hand=(1.0, 5.5, -3.0))
RIFLE_TP = dict(rot=(90, 0, 0), scale=0.52, hand=(0, 1.5, 0))
SMG_FP = dict(rot=(4, 20, 0), scale=0.9, hand=(1.0, 5.5, -3.0))
SMG_TP = dict(rot=(90, 0, 0), scale=0.64, hand=(0, 1.5, 0))


def weapon(build, pivot, fp, tp):
    return dict(build=build, frames=RELOAD_FRAMES_STD, empty=None, hide_scoped=False, pivot=pivot, fp=fp, tp=tp)


WEAPONS = {
    "pistol": weapon(pistol, (8, 5.0, 10.4), PISTOL_FP, PISTOL_TP),
    "glock_17": weapon(glock_17, (8, 5.0, 10.2), PISTOL_FP, PISTOL_TP),
    "m4a1_s": weapon(m4a1_s, (8, 4.8, 11.2), RIFLE_FP, RIFLE_TP),
    "m4a4": weapon(m4a4, (8, 4.8, 11.2), RIFLE_FP, RIFLE_TP),
    "ak_47": weapon(ak_47, (8, 5.2, 11.3), RIFLE_FP, RIFLE_TP),
    "ak_74m": weapon(ak_74m, (8, 5.2, 11.3), RIFLE_FP, RIFLE_TP),
    "p90": weapon(p90, (8, 6.8, 6.4), SMG_FP, SMG_TP),
    "kriss_vector": weapon(kriss_vector, (8, 5.2, 10.8), SMG_FP, SMG_TP),
    # Bicak: sarjor/reload yok, tek model
    "knife": dict(build=knife, frames=[], empty=None, hide_scoped=False,
                  pivot=(8, 9.0, 9.5),
                  fp=dict(rot=(30, 16, 0), scale=1.1, hand=(0.0, 5.0, -2.0)),
                  tp=dict(rot=(90, 0, 0), scale=0.85, hand=(0, 1.5, 0))),
}

GUI_ROT = (24, -52, 0)

# Birinci sahista silahi "geriye gom" (Elmas Kazma gibi sag-alta yaslansin, namlu ucu ekranin ortasina uzanmasin).
# Boyut (scale) degismez, sadece konum/aci kayar. Daha fazla gommek istersen sayilari buyut, azaltmak icin kucult.
#   shift = (saga, asagi(-), geriye/oyuncuya dogru)   pitch = namlu ucunu asagi egme (derece)   yaw = disa acma
FP_BACK = dict(shift=(6.0, -6.5, 4.0), pitch=28.0, yaw=8.0)


def build_display(name, cfg, st):
    boxes = cfg["build"](st)
    fp = cfg["fp"]
    dr = st.get("dr", (0, 0, 0))
    fp_rot = tuple(fp["rot"][i] + dr[i] for i in range(3))
    fp_rot = (fp_rot[0] + FP_BACK["pitch"], fp_rot[1] + FP_BACK["yaw"], fp_rot[2])
    fp_hand = tuple(fp["hand"][i] + FP_BACK["shift"][i] for i in range(3))
    fp_d = disp(fp_rot, fp["scale"], cfg["pivot"], fp_hand)
    tp = cfg["tp"]
    tp_d = disp(tp["rot"], tp["scale"], cfg["pivot"], tp["hand"])
    idle = cfg["build"]({})
    gs = fit_scale(GUI_ROT, idle, 14.5)
    gui = disp_centered(GUI_ROT, gs, idle)
    ground = disp_centered((0, 0, 0), 0.45, idle)
    fixed = disp_centered((0, 90, 0), min(1.0, fit_scale((0, 90, 0), idle, 13.0)), idle)
    return boxes, {
        "thirdperson_righthand": tp_d,
        "thirdperson_lefthand": tp_d,
        "firstperson_righthand": fp_d,
        "firstperson_lefthand": fp_d,
        "gui": gui,
        "ground": ground,
        "fixed": fixed,
        "head": disp_centered((0, 0, 0), 0.6, idle),
    }


# --------------------------------------------------------------------------- JSON cikti
def r1(v):
    return round(float(v), 3)


def element(b):
    k = IDX[b["c"]]
    px, py = k % 16, k // 16
    uv = [px + 0.3, py + 0.3, px + 0.7, py + 0.7]
    face = {"uv": uv, "texture": "#0"}
    return {
        "from": [r1(v) for v in b["f"]],
        "to": [r1(v) for v in b["t"]],
        "faces": {side: dict(face) for side in ("north", "south", "east", "west", "up", "down")},
    }


def model_json(boxes, display):
    return {
        "textures": {"0": "silahmod:item/palette", "particle": "silahmod:item/palette"},
        "texture_size": [16, 16],
        "elements": [element(b) for b in boxes],
        "display": display,
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def item_definition(name, n_frames, has_empty, hide_scoped):
    def model(n):
        return {"type": "minecraft:model", "model": f"silahmod:item/{n}"}

    if n_frames:
        entries = [{"threshold": float(i), "model": model(f"{name}_r{i}")} for i in range(1, n_frames + 1)]
        if has_empty:
            entries.append({"threshold": float(EMPTY_FRAME), "model": model(f"{name}_empty")})
        body = {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data",
                "index": 0, "fallback": model(name), "entries": entries}
    else:
        body = model(name)

    if hide_scoped:
        # Scope acikken (sag tik basili) birinci sahista silahi gizle; scope katmani zaten ekrani kaplar.
        body = {
            "type": "minecraft:select", "property": "minecraft:display_context",
            "cases": [{"when": ["firstperson_righthand", "firstperson_lefthand"],
                       "model": {"type": "minecraft:condition", "property": "minecraft:using_item",
                                 "on_true": {"type": "minecraft:empty"}, "on_false": body}}],
            "fallback": body,
        }
    return {"model": body}


def main():
    write_palette_png(os.path.join(ASSETS, "textures", "item", "palette.png"))
    summary = []
    for name, cfg in WEAPONS.items():
        boxes, display = build_display(name, cfg, {})
        write_json(os.path.join(ASSETS, "models", "item", f"{name}.json"), model_json(boxes, display))
        for i, st in enumerate(cfg["frames"], start=1):
            boxes, display = build_display(name, cfg, st)
            write_json(os.path.join(ASSETS, "models", "item", f"{name}_r{i}.json"), model_json(boxes, display))
        if cfg["empty"] is not None:
            boxes, display = build_display(name, cfg, cfg["empty"])
            write_json(os.path.join(ASSETS, "models", "item", f"{name}_empty.json"), model_json(boxes, display))
        write_json(os.path.join(ASSETS, "items", f"{name}.json"),
                   item_definition(name, len(cfg["frames"]), cfg["empty"] is not None, cfg["hide_scoped"]))
        summary.append(f"{name}: {len(boxes)} parca, {len(cfg['frames'])} reload karesi")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
