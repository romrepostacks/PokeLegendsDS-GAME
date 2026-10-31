# Paints our own characters over LPC body animation, as 64x64 frames, from a list of options.
#
#   python tools/art/paint_character.py LPC_DIR OUT_DIR
#
# The body, head, hair, eyes, legs and footwear come from LPC layers, recoloured. Hats, scarf
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

lpc = sys.argv[1]

UP, LEFT, DOWN, RIGHT = range(4)
OUTLINE = (28, 30, 52, 255)
FRAMES = {"walk": 9, "run": 8}

HATS = ("none", "beanie", "knitcap", "cap", "hood", "earmuffs")
HAIRS = ("short", "spiky", "wavy", "highpony", "sidepony", "braid", "bob", "long")
# Hand-drawn LPC hair. Styles with two layers have a part behind the body as well.
LPC_HAIR = {"short": "hair_parted3", "spiky": "hair_spiked", "wavy": "hair_xlong_wavy",
            "highpony": "hair_high_ponytail", "sidepony": "hair_shoulderr", "braid": "hair_braid",
            "bob": "hair_bob", "long": "hair_long_straight"}
# Hats that hide the hair on top of the head: hair above this line, from the top of the head,
# goes, and whatever hangs below the hat stays.
HAT_CLIP = {"beanie": 8, "knitcap": 8, "cap": 8}
TOPS = ("padded", "parka", "vest", "longcoat")
BOTTOMS = ("trousers", "leggings", "shorts", "skirt")
SHOES = ("boots", "tallboots", "sneakers")

LOOK_BOY = {
    "body": "male", "hat": "beanie", "hair": "short", "top": "padded", "bottoms": "trousers",
    "shoes": "boots", "scarf": False, "skin": SKINS[0], "eyes": EYES[0],
    "hat_colour": (140, 146, 156), "pompom": (232, 234, 238), "hair_colour": (112, 70, 44),
    "top_colour": (112, 118, 130), "trim": (196, 52, 52), "bottoms_colour": (184, 56, 52),
    "under_colour": (64, 56, 60), "shoe_colour": (124, 80, 48), "scarf_colour": (70, 170, 160),
    "bike_colour": (196, 52, 52), "metal_colour": (200, 208, 220),
}
LOOK_GIRL = {
    **LOOK_BOY, "body": "female", "hair": "long", "top": "longcoat", "bottoms": "leggings",
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


def raw_layer(name, body, anim, which=0):
    key = (name, body, anim, which)
    if key not in raw_cache:
        d = definition(name)
        path = d[sorted(k for k in d if k.startswith("layer_"))[which]].get(body)
        base = f"{lpc}/spritesheets/{path}"
        file = f"{base}{anim}.png"
        if not os.path.isfile(file):
            file = f"{base}{anim}/white.png"
        if not os.path.isfile(file):
            file = sorted(glob.glob(f"{base}{anim}/*.png"))[0]
        raw_cache[key] = Image.open(file).convert("RGBA")
    return raw_cache[key]


def layer_count(name):
    return sum(k.startswith("layer_") for k in definition(name))


coloured_cache = {}


def layer(name, body, anim, area, colour, which=0):
    key = (name, body, anim, area, colour, which)
    if key not in coloured_cache:
        coloured_cache[key] = recolour(raw_layer(name, body, anim, which).crop(area), colour)
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


def parts(look, anim, row, f):
    """One frame as (layer name, 64x64 image) pairs, bottom to top. The game combines the same
    layers on the DS, see tools/art/make_look.py."""
    if anim == "ride":
        return ride_parts(look, row, f)
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

    hx0, htop, hx1, hbot = box(head)
    boxes = box(top)
    tcx = (boxes[0] + boxes[2]) // 2
    hair_name = LPC_HAIR[look["hair"]]
    hair_colour = tuple(look["hair_colour"])

    def hair(which):
        """Hair layer, without what the hat hides."""
        img = layer(hair_name, body, anim, area, hair_colour, which).copy()
        clip = HAT_CLIP.get(look["hat"])
        if clip:
            ImageDraw.Draw(img).rectangle((0, 0, 63, htop + clip - 1), fill=(0, 0, 0, 0))
        return img

    out = []
    if layer_count(hair_name) > 1 and look["hat"] != "hood":
        out.append((f"hairback-{look['hair']}", hair(1)))
    out += [("body", base), ("legs-under" if over_leggings else f"legs-{look['bottoms']}", legs),
           (f"feet-{look['shoes']}", feet)]
    if over_leggings:
        out.append((f"bottoms-{look['bottoms']}", paint_bottoms(look, legs, boxes[3], tcx, row)))

    under = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    paint_clothes(ImageDraw.Draw(under), top, top.load(), row, look, boxes)
    coat = top.copy()
    coat.alpha_composite(under)
    out.append((f"top-{look['top']}", outline(coat)))
    face = head.copy()
    face.alpha_composite(eye_layer(anim, area, tuple(look["eyes"])))
    out.append(("head", face))

    def over():
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    cx, w = (hx0 + hx1) // 2, hx1 - hx0
    hat = look["hat"]
    if hat != "hood":
        out.append((f"hair-{look['hair']}", hair(0)))
    if look["scarf"]:
        img, d = over()
        scarf, dark = rgba(look["scarf_colour"]), shade(look["scarf_colour"], 0.72)
        d.rectangle((tcx - 6, hbot - 1, tcx + 6, hbot + 2), fill=scarf)
        d.line((tcx - 6, hbot + 2, tcx + 6, hbot + 2), fill=dark)
        if row == DOWN:
            d.rectangle((tcx + 2, hbot + 2, tcx + 5, hbot + 9), fill=scarf)
            d.line((tcx + 5, hbot + 2, tcx + 5, hbot + 9), fill=dark)
        out.append(("scarf", outline(img)))
    if hat != "none":
        img, d = over()
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
        out.append((f"hat-{hat}", outline(img)))
    return out


def cell(look, anim, row, f):
    """One finished 64x64 frame."""
    frame = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for _, img in parts(look, anim, row, f):
        frame.alpha_composite(img)
    return frame


# --- Bike -----------------------------------------------------------------------------
# No bike exists in LPC, so the bike is drawn here. The rider is LPC poses: side views take the
# arms from the thrust pose and the legs from the chair-sit pose, front and back views take the
# whole chair-sit pose. In side views the legs are drawn here, following the crank, because the
# sit pose's legs stick straight out. These are frames of an animation called "ride", with the
# same layers as walking plus bike-back and bike-front.

PHASES = 4
SIT = ("sit", 2)
ARMS_OUT = ("thrust", 4)
PEDAL_Y = 58         # where the rider's feet end up


def tube(d, a, b, col, dark, width=2):
    """An outlined frame tube, lit from above."""
    d.line((a, b), fill=OUTLINE, width=width + 2)
    d.line((a, b), fill=dark, width=width)
    d.line(((a[0], a[1] - (width - 1)), (b[0], b[1] - (width - 1))), fill=col)


def wheel(d, cx, cy, phase, look):
    metal = look["metal_colour"]
    TYRE, RIM, SPOKE = shade(metal, 0.35), shade(metal, 1.1), shade(metal, 0.72)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=OUTLINE)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=TYRE)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=RIM)
    d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(0, 0, 0, 0))
    a = phase * math.pi / 8
    for s in (0, math.pi / 3, 2 * math.pi / 3):
        x, y = math.cos(a + s) * 6, math.sin(a + s) * 6
        d.line((cx - x, cy - y, cx + x, cy + y), fill=SPOKE)
    d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=RIM)


def blank():
    return Image.new("RGBA", (64, 64), (0, 0, 0, 0))


def bike_left(look, phase, bar):
    """Touring bike, side view facing left. bar is where the rider's hand is."""
    back, front = blank(), blank()
    b, f = ImageDraw.Draw(back), ImageDraw.Draw(front)
    col, dark = shade(look["bike_colour"], 1.15), rgba(look["bike_colour"])
    deep = shade(look["bike_colour"], 0.65)
    metal = look["metal_colour"]
    TYRE, RIM = shade(metal, 0.35), shade(metal, 1.1)
    hx, hy = bar
    FRONT, REAR = (hx - 2, 53), (hx + 30, 53)
    head = (hx + 3, hy + 6)
    axle = (hx + 16, 54)
    seat = (hx + 21, hy + 7)
    wheel(b, *FRONT, phase, look)
    wheel(b, *REAR, phase, look)
    # Mudguards and a rear rack: it's a winter tourer.
    b.arc((REAR[0] - 11, REAR[1] - 11, REAR[0] + 11, REAR[1] + 11), 180, 340, fill=deep, width=2)
    b.arc((FRONT[0] - 11, FRONT[1] - 11, FRONT[0] + 11, FRONT[1] + 11), 200, 360, fill=deep, width=2)
    tube(b, REAR, axle, col, dark, 1)
    tube(b, REAR, seat, col, dark, 1)
    tube(b, head, FRONT, col, dark)
    tube(b, axle, head, col, dark)
    tube(b, seat, head, col, dark)
    tube(b, axle, seat, col, dark)
    b.rectangle((seat[0] + 3, seat[1] + 2, REAR[0] + 3, seat[1] + 3), fill=OUTLINE)
    b.rectangle((seat[0] - 3, seat[1] - 3, seat[0] + 4, seat[1] - 1), fill=OUTLINE)
    b.line((seat[0] - 2, seat[1] - 3, seat[0] + 3, seat[1] - 3), fill=TYRE)
    # Crank, over the rider's legs, turning.
    a = phase * math.pi / 2
    crank = (axle[0] + round(math.cos(a) * 5), axle[1] + round(math.sin(a) * 5))
    f.ellipse((axle[0] - 3, axle[1] - 3, axle[0] + 3, axle[1] + 3), fill=OUTLINE)
    f.ellipse((axle[0] - 2, axle[1] - 2, axle[0] + 2, axle[1] + 2), fill=RIM)
    f.line((axle, crank), fill=OUTLINE, width=2)
    f.rectangle((crank[0] - 2, crank[1], crank[0] + 2, crank[1] + 1), fill=OUTLINE)
    # Handlebars under the hand.
    tube(f, head, (hx + 2, hy + 1), col, dark, 1)
    f.line((hx - 3, hy + 1, hx + 3, hy + 1), fill=OUTLINE, width=2)
    return back, front


def bike_end(look, phase, facing, bar_y):
    """Front or back view: the wheel edge on, with the bars across."""
    back, front = blank(), blank()
    b, f = ImageDraw.Draw(back), ImageDraw.Draw(front)
    col, dark = shade(look["bike_colour"], 1.15), rgba(look["bike_colour"])
    near = f
    metal = look["metal_colour"]
    TYRE, SPOKE = shade(metal, 0.35), shade(metal, 0.72)
    near.rectangle((29, bar_y + 3, 34, 63), fill=OUTLINE)
    near.rectangle((30, bar_y + 3, 33, 62), fill=TYRE)
    for y in range(bar_y + 3 + phase % 2, 62, 2):
        near.line((31, y, 32, y), fill=SPOKE)
    # Mudguard over the wheel.
    near.rectangle((29, bar_y + 3, 34, bar_y + 8), fill=OUTLINE)
    near.rectangle((30, bar_y + 3, 33, bar_y + 7), fill=dark)
    near.line((30, bar_y + 3, 33, bar_y + 3), fill=col)
    bars = f if facing == DOWN else b
    bars.rectangle((19, bar_y - 1, 44, bar_y + 2), fill=OUTLINE)
    bars.line((21, bar_y, 42, bar_y), fill=dark)
    bars.line((21, bar_y + 1, 42, bar_y + 1), fill=SPOKE)
    bars.rectangle((19, bar_y - 1, 22, bar_y + 2), fill=TYRE)
    bars.rectangle((41, bar_y - 1, 44, bar_y + 2), fill=TYRE)
    return back, front


def lifted(img, dx, dy):
    out = blank()
    out.alpha_composite(img, (max(dx, 0), max(dy, 0)), (max(-dx, 0), max(-dy, 0)))
    return out


def pedal(img, row, phase):
    """Seen end on, each leg rises and falls in turn."""
    out = blank()
    lift = (0, -2, -4, -2)
    for side, box_ in enumerate(((0, 0, 32, 64), (32, 0, 64, 64))):
        half = blank()
        half.paste(img.crop(box_), box_[:2])
        out.alpha_composite(lifted(half, 0, lift[(phase + side * 2) % 4]))
    return out


def trail(img, row, phase):
    """Long hair and the scarf end stream a little behind."""
    if row == LEFT or row == RIGHT:
        dx = (1 + phase % 2) * (1 if row == LEFT else -1)
        top = img.crop((0, 0, 64, 34))
        out = blank()
        out.paste(top, (0, 0))
        out.paste(img.crop((0, 34, 64, 64)), (dx, 34))
        return out
    return img


def body_box(look, pose, row):
    anim, f = pose
    area = (f * 64, row * 64, (f + 1) * 64, (row + 1) * 64)
    return box(layer("body", look["body"], anim, area, tuple(look["skin"])))


def ride_offsets(look, row):
    """How far the legs and the top half move: (legs dy, top dy)."""
    legs_dy = PEDAL_Y - body_box(look, SIT, row)[3]
    return (legs_dy, legs_dy) if row in (UP, DOWN) else (0, -6)


def knee_of(hip, foot):
    """Where the knee goes for a thigh and shin of 10, bending forward (left)."""
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    d = math.hypot(dx, dy) or 1
    bend = math.sqrt(max(0, 10.5 ** 2 - (d / 2) ** 2))
    return (round((hx + fx) / 2 + dy / d * -bend), round((hy + fy) / 2 + dx / d * bend))


def limb(d, a, b, colour, k=1.0):
    d.line((a, b), fill=OUTLINE, width=6)
    d.line((a, b), fill=shade(colour, 0.72 * k), width=4)
    d.line(((a[0] - 1, a[1] - 1), (b[0] - 1, b[1] - 1)), fill=shade(colour, k), width=2)


def side_leg(name, look, hip, foot, k):
    """One leg, for one layer: leg, shorts or skirt over it, or the shoe."""
    img = blank()
    d = ImageDraw.Draw(img)
    knee = knee_of(hip, foot)
    if name.startswith("legs"):
        colour = look["under_colour"] if name == "legs-under" else look["bottoms_colour"]
        limb(d, hip, knee, colour, k)
        limb(d, knee, foot, colour, k)
    elif name.startswith("bottoms"):
        limb(d, hip, knee, look["bottoms_colour"], k)
    else:
        fx, fy = foot
        colour = look["shoe_colour"]
        d.rounded_rectangle((fx - 5, fy - 3, fx + 2, fy + 2), 1, fill=OUTLINE)
        d.rectangle((fx - 4, fy - 2, fx + 1, fy + 1), fill=shade(colour, k))
        d.line((fx - 4, fy + 1, fx + 1, fy + 1), fill=shade(colour, 0.72 * k))
    return img


def ride_parts(look, row, phase):
    pose = SIT if row in (UP, DOWN) else ARMS_OUT
    legs_dy, top_dy = ride_offsets(look, row)
    wear = parts(look, pose[0], row, pose[1])
    lower = parts(look, SIT[0], row, SIT[1])
    cut = 46 if pose == ARMS_OUT else 63
    legs = [(n, img) for n, img in lower if n.split("-")[0] in ("legs", "feet", "bottoms")]
    out = []
    for name, img in wear:
        if name.split("-")[0] in ("legs", "feet", "bottoms"):
            continue
        img = img.copy()
        ImageDraw.Draw(img).rectangle((0, cut, 63, 63), fill=(0, 0, 0, 0))
        img = lifted(img, 0, top_dy)
        if name.startswith("hairback") or name == "scarf":
            img = trail(img, row, phase)
        out.append((name, img))
    body_at = next(i for i, (n, _) in enumerate(out) if n == "body")
    body = out[body_at][1]
    if row in (LEFT, RIGHT):
        # Find the hand: the outermost pixel of the arm.
        px = body.load()
        xs = [(x, y) for y in range(64) for x in range(64) if px[x, y][3]]
        hand = min(xs) if row == LEFT else max(xs)
        bar = hand if row == LEFT else (63 - hand[0], hand[1])
        back, front = bike_left(look, phase, bar)
        hip = (bar[0] + 20, bar[1] + 5)
        axle = (bar[0] + 16, 54)
        a = phase * math.pi / 2
        drawn = []
        for name, _ in legs:
            near = (axle[0] + round(math.cos(a) * 5), axle[1] + round(math.sin(a) * 5))
            far = (axle[0] - round(math.cos(a) * 5), axle[1] - round(math.sin(a) * 5))
            img = side_leg(name, look, hip, far, 0.72)
            img.alpha_composite(side_leg(name, look, hip, near, 1.0))
            drawn.append((name, img))
        if row == RIGHT:
            back, front = back.transpose(Image.FLIP_LEFT_RIGHT), front.transpose(Image.FLIP_LEFT_RIGHT)
            drawn = [(n, i.transpose(Image.FLIP_LEFT_RIGHT)) for n, i in drawn]
        out[body_at + 1:body_at + 1] = drawn
    else:
        out[body_at + 1:body_at + 1] = [(n, pedal(lifted(i, 0, legs_dy), row, phase)) for n, i in legs]
        back, front = bike_end(look, phase, row, 40)
    return [("bike-back", back)] + out + [("bike-front", front)]


def ride_head_top(look, row):
    """Top of the head in a ride frame, for clipping hair under hats."""
    pose = SIT if row in (UP, DOWN) else ARMS_OUT
    anim, f = pose
    area = (f * 64, row * 64, (f + 1) * 64, (row + 1) * 64)
    head_name = "heads_human_male" if look["body"] == "male" else "heads_human_female"
    return box(layer(head_name, look["body"], anim, area, tuple(look["skin"])))[1] + ride_offsets(look, row)[3]


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
    out.save(f"{out_dir}/{name}-1x.png")
    x(out, 3).save(f"{out_dir}/{name}.png")


def options(key, values):
    return [{**b, key: v} for v in values for b in (LOOK_BOY, LOOK_GIRL)]


if __name__ == "__main__":
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    FRONT_BACK = (FRONT, SIDE_RUN, ("walk", UP, 0))
    grid("hair-styles", [{**LOOK_BOY, "hat": "none", "hair": h} for h in HAIRS] +
         [{**LOOK_GIRL, "hat": "none", "hair": h} for h in HAIRS], poses=FRONT_BACK, cols=4)
    grid("hair-with-hats", [{**LOOK_GIRL, "hat": a, "hair": h} for h in HAIRS for a in HATS[1:]],
         poses=(FRONT, ("walk", LEFT, 0)), cols=5)
    grid("colours-hair", [{**LOOK_GIRL, "hat": "none", "hair_colour": v} for v in HAIR_COLOURS],
         cols=10, poses=(FRONT,))
    print("options ->", out_dir)
