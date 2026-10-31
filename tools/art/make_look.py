# Packs every character option for the game, as layers of palette indices.
#
#   python tools/art/make_look.py LPC_DIR data/textures include/look_data.h
#
# Each part is painted in its own key colour, so a pixel's hue says which part it belongs to and
# its brightness says which of the part's 8 shades it is. Palette index = 2 + part * 8 + shade,
# and index 1 is the outline. The DS copies a chosen colour's 8 shades into the palette, so
# changing a colour needs no redrawing. Layers are written per body, in LAYERS order, and each
# frame is trimmed to its bounding box: x, y, w, h, then w*h bytes, padded to 4.

import colorsys
import struct
import sys

from colour_options import COLOURS, EYES, HAIR_COLOURS, SKINS
from paint_character import BOTTOMS, HAIRS, HATS, LOOK_BOY, LOOK_GIRL, OUTLINE, SHOES, TOPS, parts

lpc, data_dir, header = sys.argv[1:4]

SLOTS = ("skin", "eyes", "hair", "hat", "pompom", "top", "trim", "bottoms", "under", "shoe", "scarf")
SHADES = 8
KEY_V = 0.7
LOW, HIGH = 0.35, 1.25   # darkest and lightest shade, as a multiple of the base colour
FRAMES = [("walk", f) for f in range(9)] + [("run", f) for f in range(8)]


def factor(shade):
    return LOW + (HIGH - LOW) * shade / (SHADES - 1)


def key(name):
    h = SLOTS.index(name) / len(SLOTS)
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, 1, KEY_V))


def index(r, g, b):
    if (r, g, b) == OUTLINE[:3]:
        return 1
    h, _, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    slot = round(h * len(SLOTS)) % len(SLOTS)
    return 2 + slot * SHADES + max(0, min(SHADES - 1, round((v / KEY_V - LOW) / (HIGH - LOW) * (SHADES - 1))))


LOOK_KEY = {
    "skin": key("skin"), "eyes": key("eyes"), "hair_colour": key("hair"), "hat_colour": key("hat"),
    "pompom": key("pompom"), "top_colour": key("top"), "trim": key("trim"),
    "bottoms_colour": key("bottoms"), "under_colour": key("under"), "shoe_colour": key("shoe"),
    "scarf_colour": key("scarf"),
}

LAYERS = (["body", "legs-trousers", "legs-leggings", "legs-under"] + [f"feet-{s}" for s in SHOES] +
          ["bottoms-shorts", "bottoms-skirt"] + [f"top-{t}" for t in TOPS] + ["head"] +
          [f"hair-{h}" for h in HAIRS] + ["scarf"] + [f"hat-{h}" for h in HATS[1:]])
BASES = {n: LAYERS.index(f"{n.lower()}-{first}") for n, first in
         (("LEGS", "trousers"), ("FEET", SHOES[0]), ("BOTTOMS", "shorts"), ("TOP", TOPS[0]),
          ("HAIR", HAIRS[0]), ("HAT", HATS[1]))}


def looks(body):
    base = {**(LOOK_BOY if body == "male" else LOOK_GIRL), **LOOK_KEY, "scarf": True, "hat": HATS[1]}
    yield base
    for bottoms in BOTTOMS:
        yield {**base, "bottoms": bottoms}
    for name, values in (("shoes", SHOES), ("top", TOPS), ("hair", HAIRS), ("hat", HATS[1:])):
        for v in values:
            yield {**base, name: v}


records = {}
for b, body in enumerate(("male", "female")):
    for look in looks(body):
        for fi, (anim, f) in enumerate(FRAMES):
            for row in range(4):
                for name, img in parts(look, anim, row, f):
                    k = (b, LAYERS.index(name), row * len(FRAMES) + fi)
                    if k not in records:
                        records[k] = img

count = len(LAYERS) * 2 * 4 * len(FRAMES)
offsets = [0] * count
blob = bytearray()
start = count * 4
for (b, l, fr), img in records.items():
    bbox = img.getbbox()
    if not bbox:
        continue
    x0, y0, x1, y1 = bbox
    px = img.load()
    rec = bytearray((x0, y0, x1 - x0, y1 - y0))
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, bl, a = px[x, y]
            rec.append(index(r, g, bl) if a else 0)
    rec += bytes(-len(rec) % 4)
    offsets[(b * len(LAYERS) + l) * 4 * len(FRAMES) + fr] = start + len(blob)
    blob += rec

with open(f"{data_dir}/look.bin", "wb") as f:
    f.write(struct.pack(f"<{count}I", *offsets) + blob)

# Colour rows: 8 shades each, the same maths as paint_character's recolour.
FIXED = [LOOK_BOY["trim"], LOOK_GIRL["trim"], LOOK_BOY["pompom"], LOOK_BOY["under_colour"]]
ramps = bytearray()
for c in list(COLOURS) + list(HAIR_COLOURS) + list(SKINS) + list(EYES) + FIXED:
    h, s, v = colorsys.rgb_to_hsv(*(n / 255 for n in c))
    for shade in range(SHADES):
        r, g, bl = colorsys.hsv_to_rgb(h, s, min(1.0, v * factor(shade)))
        ramps += struct.pack("<H", int(r * 31) | int(g * 31) << 5 | int(bl * 31) << 10)
with open(f"{data_dir}/look_ramps.bin", "wb") as f:
    f.write(ramps)



def nearest(c):
    return min(range(len(COLOURS)), key=lambda i: sum((a - b) ** 2 for a, b in zip(COLOURS[i], c)))


swatch = min(range(SHADES), key=lambda i: abs(factor(i) - 1))
with open(header, "w", newline="\n") as f:
    f.write("// Written by tools/art/make_look.py.\n#pragma once\n\n")
    f.write(f"#define LOOK_LAYERS {len(LAYERS)}\n#define LOOK_FRAMES {len(FRAMES)}\n")
    f.write(f"#define LOOK_SHADES {SHADES}\n#define LOOK_SWATCH_SHADE {swatch}\n#define LOOK_RUN_FRAME 9\n")
    for n in ("body", "head", "scarf"):
        f.write(f"#define LAYER_{n.upper()} {LAYERS.index(n)}\n")
    f.write(f"#define LAYER_LEGS_UNDER {LAYERS.index('legs-under')}\n")
    for n, v in BASES.items():
        f.write(f"#define LAYER_{n} {v}\n")
    f.write("\n")
    for i, s in enumerate(SLOTS):
        f.write(f"#define SLOT_{s.upper()} {i}\n")
    f.write(f"#define SLOT_COUNT {len(SLOTS)}\n")
    skin = len(COLOURS) + len(HAIR_COLOURS)
    f.write(f"\n#define RAMP_COLOURS 0\n#define RAMP_HAIR {len(COLOURS)}\n#define RAMP_SKIN {skin}\n")
    f.write(f"#define RAMP_EYES {skin + len(SKINS)}\n#define RAMP_FIXED {skin + len(SKINS) + len(EYES)}\n")
    for name, c in (("HAT", "hat_colour"), ("TOP", "top_colour"), ("BOTTOMS", "bottoms_colour"),
                    ("SHOE", "shoe_colour"), ("SCARF", "scarf_colour")):
        f.write(f"#define DEFAULT_{name}_COLOUR {nearest(LOOK_BOY[c])}\n")
    hair = min(range(len(HAIR_COLOURS)), key=lambda i: sum((a - b) ** 2 for a, b in zip(HAIR_COLOURS[i], LOOK_BOY["hair_colour"])))
    f.write(f"#define DEFAULT_HAIR_COLOUR {hair}\n")
    f.write(f"#define COUNT_COLOURS {len(COLOURS)}\n#define COUNT_SKIN {len(SKINS)}\n#define COUNT_EYES {len(EYES)}\n")
print("look.bin", start + len(blob), "bytes,", len(records), "frames")
