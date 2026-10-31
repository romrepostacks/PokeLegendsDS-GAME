# Art review previews for the character creator: boy and girl, and every colour option.
# Colours are swapped the way the game will swap them, by replacing palette entries.
#
#   python tools/art/preview_character.py OUT_DIR

import os
import sys

from PIL import Image

import make_player
from colour_options import COLOURS

BASE_PAL = dict(make_player.PAL)
PARTS = {"top": ("R", "r"), "hat": ("G", "g"), "bottoms": ("N", None), "shoes": ("B", None),
         "hair": ("H", None)}
GREY = (200, 208, 220, 255)


def frames():
    p = make_player
    return [p.walk_down(0), p.walk_down(0, back=True), p.walk_left(0), p.walk_left(1),
            p.walk_down(1), p.run_left(1), p.run_left(-1)]


def strip(body, pal=None):
    make_player.BODY = body
    make_player.PAL.clear()
    make_player.PAL.update(pal or BASE_PAL)
    fs = frames()
    out = Image.new("RGBA", (32 * len(fs), 32), GREY)
    for i, f in enumerate(fs):
        out.alpha_composite(make_player.to_image(f), (i * 32, 0))
    return out


def swapped(part, option):
    pal = dict(BASE_PAL)
    base, shade = PARTS[part]
    pal[base] = option[0]
    if shade:
        pal[shade] = option[1]
    return pal


def x4(img):
    return img.resize((img.width * 4, img.height * 4), Image.NEAREST)


out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
boy = strip("boy")
x4(boy).save(f"{out_dir}/boy.png")
for tag, hair in (("a-braids", "braids"), ("b-ponytail", "ponytail"), ("c-bob", "bob")):
    make_player.HAIR = hair
    girl = strip("girl")
    x4(girl).save(f"{out_dir}/girl-{tag}.png")
    both = Image.new("RGBA", (boy.width, 66), (255, 255, 255, 255))
    both.paste(boy, (0, 0))
    both.paste(girl, (0, 34))
    x4(both).save(f"{out_dir}/girl-{tag}-vs-boy.png")

make_player.HAIR = "braids"
sheet = Image.new("RGBA", (10 + 34 * 30, 34 * len(PARTS)), (255, 255, 255, 255))
for row, part in enumerate(PARTS):
    for i, option in enumerate(COLOURS):
        make_player.BODY = "girl" if part == "hair" else "boy"
        make_player.PAL.clear()
        make_player.PAL.update(swapped(part, option))
        tile = Image.new("RGBA", (32, 32), GREY)
        tile.alpha_composite(make_player.to_image(make_player.walk_down(0)))
        sheet.paste(tile, (10 + i * 34, row * 34))
sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(f"{out_dir}/palettes.png")
print("previews ->", out_dir)
