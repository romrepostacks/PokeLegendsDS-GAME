# Compares the head and hat on the bike with walking, and draws a strip of every hat.
#
#   python tools/art/check_bike_hats.py LPC_DIR OUT_DIR
#
# Prints each hat's size in the walk and ride frames. Faces are compared with the hat off.

import sys

from PIL import Image

import paint_character as c

out_dir = sys.argv[2]
HEAD_ROWS = 28


def head(look, anim, row, f):
    """The frame's pixels from the head layers up, as a tight crop."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for name, layer in c.parts(look, anim, row, f):
        if name == "head" or name.startswith(("hair-", "hat-")):
            img.alpha_composite(layer)
    return img.crop(img.getbbox())


bad = 0
for label, base in (("boy", c.LOOK_BOY), ("girl", c.LOOK_GIRL)):
    for row, name in ((c.UP, "up"), (c.LEFT, "left"), (c.DOWN, "down"), (c.RIGHT, "right")):
        for hat in c.HATS:
            look = {**base, "hat": hat}
            walk, ride = head(look, "walk", row, 0), head(look, "ride", row, 0)
            same = walk.tobytes() == ride.tobytes()
            bad += not same
            print(f"{label:4} {name:5} {hat:8} walk {walk.size} ride {ride.size} {'same' if same else 'DIFFERENT'}")

    strip = Image.new("RGBA", (64 * len(c.HATS), 64 * 2), c.GREY)
    for i, hat in enumerate(c.HATS):
        look = {**base, "hat": hat}
        strip.alpha_composite(c.cell(look, "walk", c.DOWN, 0), (i * 64, 0))
        strip.alpha_composite(c.cell(look, "ride", c.DOWN, 0), (i * 64, 64))
    c.x(strip, 3).save(f"{out_dir}/hats-{label}.png")
print("different:", bad)
