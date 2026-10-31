# Paints our own characters over LPC body animation, as 64x64 frames, from a list of options.
#
#   python tools/art/paint_character.py LPC_DIR OUT_DIR
#
# The body, head, eyes, legs and footwear come from LPC layers, recoloured. Hats, hair, scarf
# and coat details are drawn here, once per facing, and anchored in every frame to where the
# LPC head and torso actually are, so they move with the animation. Sheets have 4 rows: up,
# left, down, right. A look picks one of each option; see LOOK_BOY and the OPTIONS lists.

import colorsys
import glob
import json
import math
import os
import sys

from PIL import Image, ImageDraw

from colour_options import COLOURS, EYES, HAIR_COLOURS, SKINS

lpc, out_dir = sys.argv[1:3]

UP, LEFT, DOWN, RIGHT = range(4)
OUTLINE = (28, 30, 52, 255)
FRAMES = {"walk": 9, "run": 8}

HATS = ("none", "beanie", "knitcap", "cap", "hood", "earmuffs")
HAIRS = ("short", "crop", "spiky", "shaggy", "wavy", "ponytail", "bob", "braids")
TOPS = ("padded", "parka", "vest", "longcoat")
BOTTOMS = ("trousers", "leggings", "shorts", "skirt")
SHOES = ("boots", "tallboots", "sneakers")

LOOK_BOY = {
    "body": "male", "hat": "beanie", "hair": "short", "top": "padded", "bottoms": "trousers",
    "shoes": "boots", "scarf": False, "skin": SKINS[0], "eyes": EYES[0],
    "hat_colour": (140, 146, 156), "pompom": (232, 234, 238), "hair_colour": (112, 70, 44),
    "top_colour": (112, 118, 130), "trim": (196, 52, 52), "bottoms_colour": (184, 56, 52),
    "under_colour": (64, 56, 60), "shoe_colour": (124, 80, 48), "scarf_colour": (70, 170, 160),
}
LOOK_GIRL = {
    **LOOK_BOY, "body": "female", "hair": "wavy", "top": "longcoat", "bottoms": "leggings",
    "scarf": True, "hat_colour": (46, 140, 136), "hair_colour": (236, 196, 96),
    "top_colour": (46, 146, 140), "trim": (120, 80, 50), "bottoms_colour": (64, 56, 60),
}
LEGS = {"trousers": "legs_cuffed", "leggings": "legs_leggings", "shorts": "legs_leggings",
        "skirt": "legs_leggings"}
FEET = {"boots": "feet_boots_basic", "tallboots": "feet_boots_fold", "sneakers": "feet_shoes_basic"}


def definition(name):
    found = glob.glob(f"{lpc}/sheet_definitions/**/{name}.json", recursive=True)
    with open(found[0], encoding="utf8") as f:
        return json.load(f)


def recolour(img, colour):
    """Maps the layer's shades, darkest to lightest, onto a ramp of the chosen colour."""
    px = img.load()
    shades = sorted({px[x, y][:3] for y in range(img.height) for x in range(img.width) if px[x, y][3]},
                    key=lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
    if not shades:
        return img
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in colour))
    ramp = {}
    for i, shade in enumerate(shades):
        t = i / max(1, len(shades) - 1)
        rgb = colorsys.hsv_to_rgb(h, s, min(1.0, v * (0.55 + 0.6 * t)))
        ramp[shade] = tuple(int(c * 255) for c in rgb)
    out = img.copy()
    o = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                o[x, y] = (*ramp[(r, g, b)], a)
    return out


raw_cache = {}


def raw_layer(name, body, anim):
    key = (name, body, anim)
    if key not in raw_cache:
        d = definition(name)
        path = d[sorted(k for k in d if k.startswith("layer_"))[0]].get(body)
        base = f"{lpc}/spritesheets/{path}"
        file = f"{base}{anim}.png" if os.path.isfile(f"{base}{anim}.png") else f"{base}{anim}/white.png"
        raw_cache[key] = Image.open(file).convert("RGBA")
    return raw_cache[key]


coloured_cache = {}


def layer(name, body, anim, area, colour):
    key = (name, body, anim, area, colour)
    if key not in coloured_cache:
        coloured_cache[key] = recolour(raw_layer(name, body, anim).crop(area), colour)
    return coloured_cache[key]


def eye_layer(anim, area, colour):
    key = ("eyes", anim, area, colour)
    if key not in coloured_cache:
        file = sorted(glob.glob(f"{lpc}/spritesheets/eyes/human/adult/default/{anim}/*.png"))[0]
        coloured_cache[key] = recolour(Image.open(file).convert("RGBA").crop(area), colour)
    return coloured_cache[key]


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)


def rgba(c):
    return tuple(c[:3]) + (255,)


def box(img):
    return img.getbbox() or (24, 16, 40, 40)


# --- Hair -----------------------------------------------------------------------------

def hair_top(d, cx, top, w, col, dark):
    """The crown of the head. Hats sit over this."""
    x0, x1 = cx - w // 2 - 1, cx + w // 2 + 1
    d.pieslice((x0, top - 2, x1, top + 18), 180, 360, fill=col)
    for x in range(x0 + 3, x1 - 1, 4):
        d.line((x, top + 1, x + 1, top + 6), fill=dark)


def fringe(d, x0, x1, y, col, length=2):
    for x in range(x0, x1 + 1, 2):
        d.line((x, y, x, y + (length if (x - x0) % 4 == 0 else 1)), fill=col)


def wavy(d, x0, x1, y0, y1, col, dark, wave):
    """A wavy lock of hair: each row shifts a little, so the edge is soft and curling."""
    for y in range(y0, y1 + 1):
        dx = int(round(math.sin(y * 0.8 + wave) * 1.4))
        d.line((x0 + dx, y, x1 + dx, y), fill=col)
        if (y - y0) % 3 == 0:
            d.point((x1 + dx, y), fill=dark)


def braid(d, x, y, col, dark, tie):
    for i in range(0, 15):
        d.line((x, y + i, x + 3, y + i), fill=dark if i % 4 == 3 else col)
    d.rectangle((x, y + 15, x + 3, y + 16), fill=tie)


def side_back(cx, x0, x1, facing, inset):
    """The span of the back of the head in a side view."""
    return (cx + inset, x1 + 1) if facing == LEFT else (x0 - 1, cx - inset)


def draw_hair(d, cx, top, w, facing, look):
    style, col, dark = look["hair"], rgba(look["hair_colour"]), shade(look["hair_colour"], 0.72)
    tie = rgba(look["trim"])
    y = top + 8
    x0, x1 = cx - w // 2, cx + w // 2
    if style == "spiky" and look["hat"] in ("none", "earmuffs"):
        for x in range(x0, x1 - 2, 4):
            d.polygon([(x, top + 2), (x + 2, top - 5), (x + 4, top + 2)], fill=col)
    hair_top(d, cx, top, w, col, dark)

    if facing == DOWN:
        if style == "crop":
            fringe(d, x0 + 2, x1 - 2, y, col, 1)
        elif style in ("short", "spiky"):
            fringe(d, x0, x1, y, col)
            d.rectangle((x0 - 1, y, x0 + 1, y + 5), fill=col)
            d.rectangle((x1 - 1, y, x1 + 1, y + 5), fill=dark)
        elif style == "shaggy":
            fringe(d, x0, x1, y, col, 3)
            wavy(d, x0 - 2, x0 + 1, y, y + 9, col, dark, 0)
            wavy(d, x1 - 1, x1 + 2, y, y + 9, col, dark, 1.5)
        elif style == "wavy":
            fringe(d, x0, x1, y, col)
            wavy(d, x0 - 3, x0 + 2, y, y + 15, col, dark, 0)
            wavy(d, x1 - 2, x1 + 3, y, y + 15, col, dark, 1.5)
        elif style == "ponytail":
            fringe(d, x0, x1, y, col)
            wavy(d, x1 + 2, x1 + 5, top + 3, y + 10, col, dark, 0.5)
        elif style == "bob":
            fringe(d, x0, x1, y, col)
            d.rectangle((x0 - 3, y, x0 + 2, y + 9), fill=col)
            d.rectangle((x1 - 2, y, x1 + 3, y + 9), fill=dark)
        elif style == "braids":
            fringe(d, x0, x1, y, col)
            braid(d, x0 - 4, y, col, dark, tie)
            braid(d, x1 + 1, y, col, dark, tie)
    elif facing == UP:
        if style == "crop":
            d.rectangle((x0, y, x1, y + 4), fill=col)
        elif style in ("short", "spiky"):
            d.rectangle((x0 - 1, y, x1 + 1, y + 8), fill=col)
            for x in range(x0 - 1, x1 + 2, 3):
                d.line((x, y + 8, x, y + 9), fill=dark)
        elif style == "shaggy":
            wavy(d, x0 - 2, x1 + 2, y, y + 11, col, dark, 0)
        elif style == "wavy":
            wavy(d, x0 - 3, x1 + 3, y, y + 17, col, dark, 0)
            for x in range(x0, x1, 4):
                d.line((x, y + 2, x + 1, y + 15), fill=dark)
        elif style == "ponytail":
            d.rectangle((x0 - 1, y, x1 + 1, y + 7), fill=col)
            wavy(d, cx - 3, cx + 3, y + 2, y + 18, col, dark, 0)
            d.rectangle((cx - 3, y + 2, cx + 3, y + 3), fill=tie)
        elif style == "bob":
            d.rectangle((x0 - 3, y, x1 + 3, y + 10), fill=col)
            d.line((x0 - 3, y + 10, x1 + 3, y + 10), fill=dark)
        elif style == "braids":
            d.rectangle((x0 - 1, y, x1 + 1, y + 7), fill=col)
            braid(d, x0 - 4, y, col, dark, tie)
            braid(d, x1 + 1, y, col, dark, tie)
    else:
        if style == "crop":
            a, b = side_back(cx, x0, x1, facing, 4)
            d.rectangle((a, y, b, y + 4), fill=col)
        elif style in ("short", "spiky"):
            a, b = side_back(cx, x0, x1, facing, 3)
            d.rectangle((a, y, b, y + 7), fill=col)
            for x in range(a, b + 1, 3):
                d.line((x, y + 7, x, y + 8), fill=dark)
        elif style == "shaggy":
            a, b = side_back(cx, x0, x1, facing, 2)
            wavy(d, a, b, y, y + 10, col, dark, 0.3)
        elif style == "wavy":
            a, b = side_back(cx, x0, x1, facing, 2)
            wavy(d, a - (0 if facing == LEFT else 3), b + (3 if facing == LEFT else 0), y, y + 16, col, dark, 0.7)
        elif style == "ponytail":
            a, b = side_back(cx, x0, x1, facing, 3)
            d.rectangle((a, y, b, y + 6), fill=col)
            tail = x1 + 1 if facing == LEFT else x0 - 5
            wavy(d, tail, tail + 4, y - 3, y + 12, col, dark, 0.2)
        elif style == "bob":
            a, b = side_back(cx, x0, x1, facing, 2)
            d.rectangle((a, y, b + (2 if facing == LEFT else 0), y + 9), fill=col)
        elif style == "braids":
            a, b = side_back(cx, x0, x1, facing, 3)
            d.rectangle((a, y, b, y + 6), fill=col)
            braid(d, (cx + 3) if facing == LEFT else (cx - 6), y + 4, col, dark, tie)


# --- Hats -----------------------------------------------------------------------------

def draw_beanie(d, cx, top, w, facing, look):
    x0, x1 = cx - w // 2 - 1, cx + w // 2 + 1
    base, dark = rgba(look["hat_colour"]), shade(look["hat_colour"], 0.72)
    d.pieslice((x0, top - 4, x1, top + 14), 180, 360, fill=base)
    d.rectangle((x0, top + 4, x1, top + 7), fill=shade(look["hat_colour"], 1.18))
    for x in range(x0 + 1, x1, 3):
        d.line((x, top + 4, x, top + 7), fill=dark)
    for x in range(x0 + 2, x1 - 1, 4):
        d.line((x, top - 2, x, top + 3), fill=dark)
    px = cx + {LEFT: 2, RIGHT: -2}.get(facing, 0)
    d.ellipse((px - 3, top - 8, px + 3, top - 2), fill=rgba(look["pompom"]))
    d.point((px + 2, top - 3), fill=shade(look["pompom"], 0.78))


def draw_knitcap(d, cx, top, w, facing, look):
    """A plain ribbed cap that slouches to one side, with no pompom."""
    x0, x1 = cx - w // 2 - 1, cx + w // 2 + 1
    base, dark = rgba(look["hat_colour"]), shade(look["hat_colour"], 0.72)
    d.pieslice((x0, top - 5, x1, top + 14), 180, 360, fill=base)
    slouch = {LEFT: x1 - 4, RIGHT: x0 - 1}.get(facing, x1 - 3)
    d.ellipse((slouch, top - 5, slouch + 6, top + 2), fill=base)
    d.rectangle((x0, top + 5, x1, top + 7), fill=dark)
    for x in range(x0 + 2, x1 - 1, 3):
        d.line((x, top - 3, x, top + 4), fill=dark)


def draw_cap(d, cx, top, w, facing, look):
    x0, x1 = cx - w // 2 - 1, cx + w // 2 + 1
    base, dark = rgba(look["hat_colour"]), shade(look["hat_colour"], 0.72)
    d.pieslice((x0, top - 2, x1, top + 14), 180, 360, fill=base)
    d.line((x0, top + 5, x1, top + 5), fill=dark)
    if facing == DOWN:
        d.rectangle((x0 + 1, top + 6, x1 - 1, top + 7), fill=dark)
    elif facing == LEFT:
        d.rectangle((x0 - 6, top + 5, cx, top + 6), fill=dark)
    elif facing == RIGHT:
        d.rectangle((cx, top + 5, x1 + 6, top + 6), fill=dark)
    else:
        d.rectangle((cx - 2, top + 4, cx + 2, top + 6), fill=shade(look["hat_colour"], 1.2))


def draw_hood(d, c, cx, top, w, bot, facing, look):
    """The parka's hood up, framing the face. Fur trims the opening."""
    x0, x1 = cx - w // 2 - 3, cx + w // 2 + 3
    base, dark = rgba(look["top_colour"]), shade(look["top_colour"], 0.72)
    fur = rgba(look["pompom"])
    d.ellipse((x0, top - 3, x1, bot + 3), fill=base)
    if facing == UP:
        d.line((cx, top - 2, cx, bot + 2), fill=dark)
    elif facing == DOWN:
        d.ellipse((cx - w // 2 + 1, top + 4, cx + w // 2 - 1, bot + 1), outline=fur, width=2)
        c.ellipse((cx - w // 2 + 3, top + 6, cx + w // 2 - 3, bot - 1), fill=(0, 0, 0, 0))
    else:
        a = x0 - 1 if facing == LEFT else cx + 1
        b = cx if facing == LEFT else x1 + 1
        c.rectangle((a, top + 5, b, bot + 1), fill=(0, 0, 0, 0))
        edge = cx if facing == LEFT else cx + 1
        d.line((edge, top + 4, edge, bot + 2), fill=fur, width=2)


def draw_earmuffs(d, cx, top, w, facing, look):
    x0, x1 = cx - w // 2 - 2, cx + w // 2 + 2
    base, dark = rgba(look["hat_colour"]), shade(look["hat_colour"], 0.72)
    d.arc((x0, top - 3, x1, top + 18), 180, 360, fill=dark, width=2)
    y = top + 8
    if facing in (DOWN, UP):
        d.ellipse((x0 - 2, y - 2, x0 + 3, y + 5), fill=base)
        d.ellipse((x1 - 3, y - 2, x1 + 2, y + 5), fill=base)
    else:
        d.ellipse((cx - 3, y - 2, cx + 3, y + 5), fill=base)
        d.point((cx, y + 1), fill=dark)


# --- One frame ------------------------------------------------------------------------

def paint_clothes(u, t, px, facing, look, boxes):
    tx0, ttop, tx1, tbot = boxes
    tcx = (tx0 + tx1) // 2
    style = look["top"]
    coat, dark = rgba(look["top_colour"]), shade(look["top_colour"], 0.72)
    trim = rgba(look["trim"])
    if style == "vest":
        # Sleeves stay the shirt colour; only the body is the vest.
        for y in range(ttop + 1, tbot):
            for x in range(tcx - 6, tcx + 6):
                if 0 <= x < 64 and px[x, y][3]:
                    u.point((x, y), fill=dark if (y - ttop) % 4 == 3 else coat)
    else:
        for y in range(ttop + 3, tbot, 4):
            for x in range(tx0, tx1):
                if px[x, y][3]:
                    u.point((x, y), fill=dark)
    if style == "padded" and facing == DOWN:
        u.line((tcx - 4, ttop + 1, tcx - 4, ttop + 8), fill=trim)
        u.line((tcx + 3, ttop + 1, tcx + 3, ttop + 8), fill=trim)
    if style == "parka":
        # Fur collar, and a longer hem over the hips.
        fur = rgba(look["pompom"])
        u.rectangle((tcx - 6, ttop, tcx + 6, ttop + 2), fill=fur)
        u.line((tcx - 6, ttop + 2, tcx + 6, ttop + 2), fill=shade(look["pompom"], 0.78))
        half = min((tx1 - tx0) // 2, 8) if facing in (DOWN, UP) else 6
        u.rectangle((tcx - half, tbot - 1, tcx + half, tbot + 3), fill=coat)
        u.line((tcx - half, tbot + 3, tcx + half, tbot + 3), fill=dark)
    if style != "longcoat" and facing == DOWN:
        u.line((tcx, ttop + 2, tcx, tbot - 2), fill=shade(look["top_colour"], 0.6))
    if style == "longcoat":
        half = (tx1 - tx0) // 2 if facing in (DOWN, UP) else 5
        # Ends at the knee, so the legs still show in the walk.
        for i in range(0, 8):
            r = min(half, 8) + i // 2
            u.line((tcx - r, tbot - 2 + i, tcx + r, tbot - 2 + i), fill=coat)
            u.point((tcx + r, tbot - 2 + i), fill=dark)
        if facing == DOWN:
            u.line((tcx, ttop + 2, tcx, tbot + 4), fill=dark)


def paint_bottoms(look, legs, tbot, tcx, facing):
    """Shorts and skirts, drawn over the leggings."""
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    col, dark = rgba(look["bottoms_colour"]), shade(look["bottoms_colour"], 0.72)
    if look["bottoms"] == "shorts":
        px = legs.load()
        for y in range(tbot - 2, min(64, tbot + 6)):
            for x in range(64):
                if px[x, y][3]:
                    d.point((x, y), fill=col)
    elif look["bottoms"] == "skirt":
        half = 8 if facing in (DOWN, UP) else 6
        for i in range(0, 8):
            r = half + i // 2
            d.line((tcx - r, tbot - 2 + i, tcx + r, tbot - 2 + i), fill=dark if i % 3 == 2 else col)
    return out


def outline(img):
    """Dark edge around everything we painted."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    for y in range(64):
        for x in range(64):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 64 and 0 <= ny < 64 and src[nx, ny][3]:
                    dst[x, y] = OUTLINE
                    break
    out.alpha_composite(img)
    return out


def cell(look, anim, row, f):
    """One finished 64x64 frame."""
    area = (f * 64, row * 64, (f + 1) * 64, (row + 1) * 64)
    body = look["body"]
    head_name = "heads_human_male" if body == "male" else "heads_human_female"
    skin = tuple(look["skin"])
    base = layer("body", body, anim, area, skin)
    head = layer(head_name, body, anim, area, skin)
    # Shorts and skirts wear dark leggings underneath.
    over_leggings = look["bottoms"] in ("shorts", "skirt")
    leg_colour = look["under_colour"] if over_leggings else look["bottoms_colour"]
    legs = layer(LEGS[look["bottoms"]], body, anim, area, tuple(leg_colour))
    feet = layer(FEET[look["shoes"]], body, anim, area, tuple(look["shoe_colour"]))
    shirt_colour = look["trim"] if look["top"] == "vest" else look["top_colour"]
    top = layer("torso_clothes_longsleeve2", body, anim, area, tuple(shirt_colour))

    frame = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    frame.alpha_composite(base)
    frame.alpha_composite(legs)
    frame.alpha_composite(feet)
    hx0, htop, hx1, hbot = box(head)
    boxes = box(top)
    tcx = (boxes[0] + boxes[2]) // 2
    frame.alpha_composite(paint_bottoms(look, legs, boxes[3], tcx, row))

    under = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    paint_clothes(ImageDraw.Draw(under), top, top.load(), row, look, boxes)
    coat = top.copy()
    coat.alpha_composite(under)
    frame.alpha_composite(outline(coat))
    frame.alpha_composite(head)
    frame.alpha_composite(eye_layer(anim, area, tuple(look["eyes"])))

    over = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    cx, w = (hx0 + hx1) // 2, hx1 - hx0
    hat = look["hat"]
    if hat != "hood":
        draw_hair(d, cx, htop, w, row, look)
    if look["scarf"]:
        scarf, dark = rgba(look["scarf_colour"]), shade(look["scarf_colour"], 0.72)
        d.rectangle((tcx - 6, hbot - 1, tcx + 6, hbot + 2), fill=scarf)
        d.line((tcx - 6, hbot + 2, tcx + 6, hbot + 2), fill=dark)
        if row == DOWN:
            d.rectangle((tcx + 2, hbot + 2, tcx + 5, hbot + 9), fill=scarf)
            d.line((tcx + 5, hbot + 2, tcx + 5, hbot + 9), fill=dark)
    if hat == "beanie":
        draw_beanie(d, cx, htop, w, row, look)
    elif hat == "knitcap":
        draw_knitcap(d, cx, htop, w, row, look)
    elif hat == "cap":
        draw_cap(d, cx, htop, w, row, look)
    elif hat == "earmuffs":
        draw_earmuffs(d, cx, htop, w, row, look)
    elif hat == "hood":
        draw_hood(d, d, cx, htop, w, hbot, row, look)
    frame.alpha_composite(outline(over))
    return frame


def sheet(look, anim):
    count = FRAMES[anim]
    out = Image.new("RGBA", (count * 64, 256), (0, 0, 0, 0))
    for row in range(4):
        for f in range(count):
            out.alpha_composite(cell(look, anim, row, f), (f * 64, row * 64))
    return out


# --- Previews -------------------------------------------------------------------------

GREY = (200, 208, 220, 255)


def x(img, n):
    return img.resize((img.width * n, img.height * n), Image.NEAREST)


FRONT, SIDE_RUN = ("walk", DOWN, 0), ("run", LEFT, 2)


def grid(name, looks, cols=8, poses=(FRONT, SIDE_RUN)):
    """Each look in the front idle pose and one side run frame."""
    cw = 40 * len(poses)
    rows = (len(looks) + cols - 1) // cols
    out = Image.new("RGBA", (cols * cw, rows * 58), (255, 255, 255, 255))
    for i, look in enumerate(looks):
        for p, (anim, row, f) in enumerate(poses):
            c = Image.new("RGBA", (64, 64), GREY)
            c.alpha_composite(cell(look, anim, row, f))
            out.paste(c.crop((12, 4, 52, 62)), (i % cols * cw + p * 40, i // cols * 58))
    x(out, 3).save(f"{out_dir}/{name}.png")


def options(key, values):
    return [{**b, key: v} for v in values for b in (LOOK_BOY, LOOK_GIRL)]


os.makedirs(out_dir, exist_ok=True)
for name, look in (("boy", LOOK_BOY), ("girl", LOOK_GIRL)):
    sheet(look, "walk").save(f"{out_dir}/{name}-walk-sheet.png")
    sheet(look, "run").save(f"{out_dir}/{name}-run-sheet.png")

BACK = ("walk", UP, 0)
grid("hair-shapes", [{**LOOK_BOY, "hat": "none", "hair": h} for h in HAIRS] +
     [{**LOOK_GIRL, "hat": "none", "hair": h} for h in HAIRS], poses=(FRONT, SIDE_RUN, BACK), cols=4)
grid("hats", options("hat", HATS), cols=4)
grid("tops", [{**l, "hat": "none"} for l in options("top", TOPS)], cols=4)
grid("scarf", options("scarf", (False, True)), cols=4)
grid("bottoms", [{**l, "top": "padded"} for l in options("bottoms", BOTTOMS)], cols=4)
grid("shoes", options("shoes", SHOES), cols=3)
grid("skin", options("skin", SKINS), cols=4)
grid("eyes", options("eyes", EYES), cols=4)
for part, key, values in (("top", "top_colour", COLOURS), ("hat", "hat_colour", COLOURS),
                          ("bottoms", "bottoms_colour", COLOURS), ("shoes", "shoe_colour", COLOURS),
                          ("hair", "hair_colour", HAIR_COLOURS)):
    base = {**LOOK_BOY, "hat": "none"} if part == "hair" else LOOK_BOY
    grid(f"colours-{part}", [{**base, key: v} for v in values], cols=10, poses=(FRONT,))
print("options ->", out_dir)
