# Art review previews for the character creator: boy and girl, with sample colour swaps.
# Colours are swapped the way the game will swap them, by replacing palette entries.
#
#   python tools/art/preview_character.py OUT_DIR

import os
import sys

from PIL import Image

import make_player

FAMILIES = {   # palette keys: base colour, shade
    "top": ("R", "r"), "hat": ("G", "g"), "bottoms": ("N",), "shoes": ("B",), "hair": ("H",),
}
LOOKS = {
    "default": {},
    "blue": {"top": [(70, 120, 200), (44, 80, 150)], "hat": [(240, 200, 80), (190, 150, 50)],
             "bottoms": [(90, 74, 66)], "shoes": [(60, 60, 70)], "hair": [(40, 34, 40)]},
    "pink": {"top": [(232, 120, 160), (180, 80, 120)], "hat": [(120, 90, 190), (84, 60, 150)],
             "bottoms": [(70, 80, 120)], "shoes": [(200, 200, 210)], "hair": [(200, 150, 70)]},
}


def sheet(body, look):
    make_player.BODY = body
    pal = dict(BASE_PAL)
    for part, colours in LOOKS[look].items():
        for key, colour in zip(FAMILIES[part], colours):
            pal[key] = colour
    make_player.PAL.clear()
    make_player.PAL.update(pal)
    frames = [make_player.walk_down(0), make_player.walk_down(0, back=True), make_player.walk_left(0),
              make_player.walk_left(1), make_player.run_left(1), make_player.run_left(-1)]
    out = Image.new("RGBA", (32 * len(frames), 32), (200, 208, 220, 255))
    for i, f in enumerate(frames):
        img = make_player.to_image(f)
        out.alpha_composite(img, (i * 32, 0))
    return out


BASE_PAL = dict(make_player.PAL)
out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
rows = [(b, l) for b in ("boy", "girl") for l in LOOKS]
board = Image.new("RGBA", (32 * 6, 34 * len(rows)), (255, 255, 255, 255))
for i, (body, look) in enumerate(rows):
    s = sheet(body, look)
    s.resize((s.width * 4, s.height * 4), Image.NEAREST).save(f"{out_dir}/{body}-{look}.png")
    board.alpha_composite(s, (0, i * 34))
board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(f"{out_dir}/overview.png")
print("previews ->", out_dir)
