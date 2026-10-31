# Hand-pixelled trainers at 32x32: square-cut head and hair about half the height, then a
# real body and legs, with a dark outline and 2-3 tone shading. Original winter outfits.
#
#   python tools/art/new_characters.py OUT_DIR
#
# Each frame stacks a head, a body and legs, drawn as rows of palette letters, with the feet
# on the bottom row. Lines are padded out to the sprite width, so short rows are fine.

import os
import sys

from PIL import Image

import make_player

PAL = {
    "o": (28, 30, 52), "W": (244, 246, 250), "w": (190, 202, 218),
    "S": (250, 212, 176), "s": (226, 168, 132),
    "H": (0, 0, 0), "h": (0, 0, 0),             # hair
    "C": (0, 0, 0), "c": (0, 0, 0),             # coat
    "A": (0, 0, 0), "a": (0, 0, 0),             # hat
    "N": (46, 58, 98), "n": (32, 40, 70),       # bottoms
    "B": (120, 76, 48), "b": (80, 50, 34),      # boots
}
BOY = {"H": (92, 62, 44), "h": (64, 42, 32), "C": (214, 74, 52), "c": (156, 46, 44),
       "A": (44, 150, 170), "a": (30, 104, 128)}
GIRL = {"H": (196, 96, 56), "h": (150, 64, 42), "C": (50, 72, 136), "c": (34, 50, 100),
        "A": (206, 58, 76), "a": (150, 40, 60)}

BOY_FRONT = """
.....oooooo.....
...ooAAAAAAoo...
...oAAAAAAaAo...
...oAAAWWAAao...
..ooAAAAAAAaoo..
.oaaaaaaaaaaaao.
.ooHHoHHoHHoHoo.
..oHSSSSSSSSHo..
..oSoWSSSSWoSo..
..oSoaSSSSaoSo..
..oSSSSSSSSSso..
...oSSSssSSso...
....oooooooo....
"""

BOY_BACK = """
.....oooooo.....
...ooAAAAAAoo...
...oAAAAAAaAo...
...oAAAAAAAao...
..ooAAAAAAAaoo..
.oaAAAAAAAAAAao.
.ooHHoHHoHHoHoo.
..oHHHHHHHHHHo..
..oHHhHHHHhHHo..
..oHHHHHHHHHHo..
..oHhHHHHHHhHo..
...oHHHHHHHHo...
....oooooooo....
"""

BOY_SIDE = """
.....ooooooo....
...ooAAAAAAAo...
..oAAAAAAAAAao..
..oAAWAAAAAAao..
..oAAAAAAAAAao..
ooaaaaaaaAAAAao.
.ooSHHHHHHHHHoHo
...oSSHHHHHHHHHo
..oSoWSSHHHHHHo.
..oSoaSSSHHHHHHo
..oSSSSSSHHHHo..
...oSSSSsHHoo...
....oooooo......
"""

BODY_BOY_FRONT = """
...oWWWWWWWWo...
..oCCCCoCCCCCo..
.oCcoCCoCCCoCco.
.oCcoCCoCCCoCco.
.oCcoCCoCCcoCco.
.oCcoCCoCCcoCco.
.oNNoCCoCCcoNNo.
..oooCCoCCcooo..
....oCCCCCco....
....oooooooo....
"""

BODY_BOY_BACK = """
...oWWWWWWWWo...
..oCoooooooooCo.
.oCcoAAAAAAoCco.
.oCcoAaaaaAoCco.
.oCcoAAAAAAoCco.
.oCcoAAAAAAoCco.
.oNNoooooooooNo.
..oooCCCCCcooo..
....oCCCCCco....
....oooooooo....
"""

BODY_BOY_SIDE = """
....oWWWWWoAo...
...oCCCCCCcoAo..
...oCCoCCCcoAAo.
...oCCoCCCcoAao.
...oCCoCCCcoAao.
...oCCoCCCcoAao.
...oNNoCCCcoAo..
....oooCCCcoo...
....oCCCCCco....
....ooooooo.....
"""

BODY_BOY_RUN_BACK = """
....oWWWWWoAo...
...oCCCCCCcoAo..
...oCCCCoCcoAAo.
...oCCCCoCcoAao.
...oCCCCCoNoAao.
...oCCCCCCoooo..
....oCCCCco.....
....oCCCCco.....
....oCCCCco.....
....ooooooo.....
"""

BODY_BOY_RUN_FORWARD = """
....oWWWWWoAo...
...oCCCCCCcoAo..
..ooCCCCCCcoAAo.
.oNCCoCCCCcoAao.
.oooooCCCCcoAao.
...oCCCCCCcoAo..
....oCCCCco.....
....oCCCCco.....
....oCCCCco.....
....ooooooo.....
"""

GIRL_FRONT = """
....ooooooooo...
..ooAAAAAAAAAoo.
.oAAAAAAAAAAAAo.
.ooAAAAAAAAAaoo.
..oooooooooooo..
..oHHHHHHHHHHo..
.oHHHHHHHHHHHHo.
.oHHSSSSSSSSHHo.
.oHSoWSSSSWoSHo.
.oHSoaSSSSaoSHo.
.oHSSSSSSSSSsHo.
.oHHoSSssSSoHHo.
.oHHHooooooHHHo.
"""

GIRL_BACK = """
....ooooooooo...
..ooAAAAAAAAAoo.
.oAAAAAAAAAAAAo.
.ooAAAAAAAAAaoo.
..oooooooooooo..
..oHHHHHHHHHHo..
.oHHHHHHHHHHHHo.
.oHHhHHHHHHhHHo.
.oHHHHHHHHHHHHo.
.oHHhHHHHHHhHHo.
.oHHHHHHHHHHHHo.
.oHHhHHHHHHhHHo.
.oHHHHHHHHHHHHo.
"""

GIRL_SIDE = """
....ooooooooo...
..ooAAAAAAAAAoo.
.oAAAAAAAAAAAAo.
.ooAAAAAAAAAaoo.
..oooooooooooo..
..oHHHHHHHHHHo..
..oHHHHHHHHHHHo.
..oSSHHHHHHHHHo.
..oSoWSSHHHHHHo.
..oSoaSSHHHHHHo.
..oSSSSSHHHHHHo.
...oSSSsHHhHHHo.
....oooHHHHHHHo.
"""

BODY_GIRL_FRONT = """
.oHHoWWWWWWoHHo.
.oHoCCCWWCCCoHo.
.oHoCWCCCCWCoHo.
.oHoCCCCCCCCoHo.
.oCoCWCCCCWCoCo.
.oSoCCCCCCCCoSo.
..ooCCCCCCCCoo..
...oCCCCCCcco...
..oCCCCCCCCcco..
..oooooooooooo..
"""

BODY_GIRL_BACK = """
.oHHHHHHHHHHHHo.
.oCoHHHHHHHHoCo.
.oCoHHhHHhHHoCo.
.oCoHHHHHHHHoCo.
.oCoCCHHHHCCoCo.
.oSoCCCCCCCCoSo.
..ooCCCCCCCCoo..
...oCCCCCCcco...
..oCCCCCCCCcco..
..oooooooooooo..
"""

BODY_GIRL_SIDE = """
....oWWWWoHHHo..
...oCCCCCcoHHHo.
...oCWCCCcoHHo..
...oCoCCCcoHHo..
...oCoCCCcoHo...
...oCoCCCcco....
...oSoCCCCco....
....oCCCCCCco...
...oCCCCCCCcco..
...ooooooooooo..
"""

BODY_GIRL_RUN_BACK = """
....oWWWWoHHHo..
...oCCCCCcoHHHo.
...oCWCoCcoHHo..
...oCCCoCcoHHo..
...oCCCCoSoHo...
...oCCCCCooo....
...oCCCCCCco....
....oCCCCCCco...
...oCCCCCCCcco..
...ooooooooooo..
"""

BODY_GIRL_RUN_FORWARD = """
....oWWWWoHHHo..
...oCCCCCcoHHHo.
..ooCWCCCcoHHo..
.oSCCoCCCcoHHo..
.oooooCCCcoHo...
...oCCCCCcco....
...oCCCCCCco....
....oCCCCCCco...
...oCCCCCCCcco..
...ooooooooooo..
"""

LEGS_FRONT = """
....oNNooNNo....
....oNNooNNo....
....oNnoonNo....
....oBBooBBo....
...oBBBooBBBo...
...obbboobbbo...
...oooo..oooo...
"""

LEGS_SIDE = """
.....oNNNNo.....
.....oNNNNo.....
.....oNNnNo.....
.....oBBBBo.....
....oBBBBBo.....
....obbbbbo.....
....ooooooo.....
"""

LEGS_WALK = """
.....oNNNNo.....
....oNNooNNo....
....oNNooNNo....
...oBBo..oBBo...
..oBBBo..oBBBo..
..obbbo..obbbo..
..ooooo..ooooo..
"""

# Run strides: the leading leg reaches forward, the trailing leg bends up behind. The dark
# trousers (n) are the far leg, so the two strides differ in shape as well as shade.
LEGS_RUN_NEAR = """
....oNNNoonno...
...oNNNo.onnno..
..oNNNo...onnnoo
..oBBo.....onBBo
.oBBBo......oooo
.obbbo..........
.ooooo..........
"""

LEGS_RUN_FAR = """
....onnnooNNo...
...onnno.oNNNo..
..onnno...oNNNoo
..oBbo.....oNBBo
.oBbbo......oooo
.obbbo..........
.ooooo..........
"""


def frame(parts, shifts=(0, 0, 0)):
    """Stacks head, body and legs into a 32x32 RGBA frame. shifts moves each part sideways:
    head furthest and body less gives the forward lean of a run."""
    rows = []
    for part, dx in zip(parts, shifts):
        rows.extend((line, dx) for line in part.split())
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    top = 32 - len(rows)
    assert top >= 0, len(rows)
    for y, (line, dx) in enumerate(rows):
        for x, c in enumerate(line):
            if c != ".":
                img.putpixel((x + 8 + dx, y + top), (*PALETTE[c], 255))
    return img


def strip(frames):
    out = Image.new("RGBA", (32 * len(frames), 32), (200, 208, 220, 255))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * 32, 0))
    return out


LEAN = (-2, -1, 0)


def character(front, back, side, body_front, body_back, body_side, run_back, run_forward):
    return strip([frame([front, body_front, LEGS_FRONT]), frame([back, body_back, LEGS_FRONT]),
                  frame([side, body_side, LEGS_SIDE]), frame([side, body_side, LEGS_WALK]),
                  frame([side, run_back, LEGS_RUN_NEAR], LEAN),
                  frame([side, run_forward, LEGS_RUN_FAR], LEAN)])


out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
PALETTE = {**PAL, **BOY}
boy = character(BOY_FRONT, BOY_BACK, BOY_SIDE, BODY_BOY_FRONT, BODY_BOY_BACK, BODY_BOY_SIDE,
                BODY_BOY_RUN_BACK, BODY_BOY_RUN_FORWARD)
PALETTE = {**PAL, **GIRL}
girl = character(GIRL_FRONT, GIRL_BACK, GIRL_SIDE, BODY_GIRL_FRONT, BODY_GIRL_BACK, BODY_GIRL_SIDE,
                 BODY_GIRL_RUN_BACK, BODY_GIRL_RUN_FORWARD)

p = make_player
current = [p.walk_down(0), p.walk_down(0, back=True), p.walk_left(0), p.walk_left(1),
           p.run_left(1), p.run_left(-1)]
old = strip([p.to_image(f) for f in current])

board = Image.new("RGBA", (32 * 6, 34 * 3), (255, 255, 255, 255))
for i, row in enumerate((old, boy, girl)):
    board.paste(row, (0, i * 34))


def x4(img):
    return img.resize((img.width * 4, img.height * 4), Image.NEAREST)


x4(boy).save(f"{out_dir}/boy.png")
x4(girl).save(f"{out_dir}/girl.png")
x4(board).save(f"{out_dir}/comparison.png")
print("round 4 ->", out_dir)
