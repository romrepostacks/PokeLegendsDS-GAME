# Bike previews: all 4 directions for both bodies, with a pedal strip and a GIF per direction.
#
#   python tools/art/preview_bike.py LPC_DIR OUT_DIR

import os
import sys

from PIL import Image

from paint_character import DOWN, GREY, LEFT, LOOK_BOY, LOOK_GIRL, PHASES, RIGHT, UP, cell, x

out_dir = sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
NAMES = {UP: "up", LEFT: "left", DOWN: "down", RIGHT: "right"}


def on_grey(look, row, phase):
    c = Image.new("RGBA", (64, 64), GREY)
    c.alpha_composite(cell(look, "ride", row, phase))
    return c


for name, look in (("boy", LOOK_BOY), ("girl", LOOK_GIRL)):
    sheet = Image.new("RGBA", (64 * PHASES, 64 * 4), GREY)
    for row in range(4):
        for phase in range(PHASES):
            sheet.paste(on_grey(look, row, phase), (phase * 64, row * 64))
        frames = [x(on_grey(look, row, p), 3).convert("P") for p in range(PHASES)]
        frames[0].save(f"{out_dir}/{name}-{NAMES[row]}.gif", save_all=True, append_images=frames[1:],
                       duration=120, loop=0)
    # Walking next to the 4 bike frames, to check the legs match.
    strip = Image.new("RGBA", (64 * (1 + PHASES), 64), GREY)
    strip.alpha_composite(cell(look, "walk", DOWN, 0))
    for phase in range(PHASES):
        strip.alpha_composite(cell(look, "ride", DOWN, phase), ((phase + 1) * 64, 0))
    x(strip, 3).save(f"{out_dir}/compare-{name}.png")
    sheet.save(f"{out_dir}/{name}-1x.png")
    x(sheet, 3).save(f"{out_dir}/{name}-3x.png")
print("bike ->", out_dir)
