# Paints our own characters over LPC body animation, as 64x64 walk and run sheets.
#
#   python tools/art/paint_character.py LPC_DIR OUT_DIR
#
# The body, head, face, legs and boots come from LPC layers, recoloured. The hat, hair, scarf
# and coat details are drawn here, once per facing, and anchored in every frame to where the
# LPC head and torso actually are, so they move with the animation. Sheets have 4 rows: up,
# left, down, right. Each outfit part keeps its own colours, so the game can swap them.

import colorsys
import glob
import json
import math
import os
import sys

from PIL import Image, ImageDraw

lpc, out_dir = sys.argv[1:3]

UP, LEFT, DOWN, RIGHT = range(4)
OUTLINE = (28, 30, 52, 255)
FRAMES = {"walk": 9, "run": 8}

BOY = {
    "body": "male", "head": "heads_human_male", "top": "torso_clothes_longsleeve2",
    "legs": "legs_cuffed", "boots": "feet_shoes_basic",
    "skin": (246, 200, 160), "hat": (140, 146, 156), "pompom": (232, 234, 238),
    "hair": (112, 70, 44), "coat": (112, 118, 130), "trim": (196, 52, 52),
    "trousers": (184, 56, 52), "shoes": (124, 80, 48), "scarf": None, "skirt": False,
}
GIRL = {
    "body": "female", "head": "heads_human_female", "top": "torso_clothes_longsleeve2",
    "legs": "legs_leggings", "boots": "feet_boots_basic",
    "skin": (248, 206, 170), "hat": (46, 140, 136), "pompom": (232, 234, 238),
    "hair": (236, 196, 96), "coat": (46, 146, 140), "trim": (120, 80, 50),
    "trousers": (64, 56, 60), "shoes": (124, 80, 48), "scarf": (70, 170, 160), "skirt": True,
}


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


def layer(name, body, anim, colour):
    d = definition(name)
    keys = sorted(k for k in d if k.startswith("layer_"))
    path = d[keys[0]].get(body)
    base = f"{lpc}/spritesheets/{path}"
    if os.path.isfile(f"{base}{anim}.png"):
        return recolour(Image.open(f"{base}{anim}.png").convert("RGBA"), colour)
    return recolour(Image.open(f"{base}{anim}/white.png").convert("RGBA"), colour)


def eyes(anim):
    return recolour(sorted_eye(anim), (70, 110, 170))


def sorted_eye(anim):
    return Image.open(sorted(glob.glob(f"{lpc}/spritesheets/eyes/human/adult/default/{anim}/*.png"))[0]).convert("RGBA")


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)


def rgba(c):
    return tuple(c) + (255,)


def box(img):
    return img.getbbox() or (24, 16, 40, 40)


def draw_beanie(d, c, cx, top, w, facing, look):
    """A ribbed knit hat with a folded band and a pompom."""
    x0, x1 = cx - w // 2 - 1, cx + w // 2 + 1
    base, dark = rgba(look["hat"]), shade(look["hat"], 0.72)
    d.ellipse((x0, top - 4, x1, top + 12), fill=base)
    d.rectangle((x0, top + 8, x1, top + 12), fill=(0, 0, 0, 0))
    d.rectangle((x0, top + 4, x1, top + 7), fill=shade(look["hat"], 1.18))
    for x in range(x0 + 1, x1, 3):
        d.line((x, top + 4, x, top + 7), fill=dark)
    for x in range(x0 + 2, x1 - 1, 4):
        d.line((x, top - 2, x, top + 3), fill=dark)
    d.rectangle((x1 - 2, top, x1, top + 3), fill=dark)
    px = cx + {LEFT: 2, RIGHT: -2}.get(facing, 0)
    d.ellipse((px - 3, top - 8, px + 3, top - 2), fill=rgba(look["pompom"]))
    d.point((px + 2, top - 3), fill=shade(look["pompom"], 0.78))


def draw_boy_hair(d, c, cx, top, w, facing, look):
    hair, dark = rgba(look["hair"]), shade(look["hair"], 0.72)
    y = top + 8
    x0, x1 = cx - w // 2, cx + w // 2
    if facing == DOWN:
        for x in range(x0, x1 + 1, 2):
            d.line((x, y, x, y + (2 if (x - x0) % 4 == 0 else 1)), fill=hair)
        d.rectangle((x0 - 1, y, x0 + 1, y + 5), fill=hair)
        d.rectangle((x1 - 1, y, x1 + 1, y + 5), fill=dark)
    elif facing == UP:
        d.rectangle((x0 - 1, y, x1 + 1, y + 8), fill=hair)
        for x in range(x0 - 1, x1 + 2, 3):
            d.line((x, y + 8, x, y + 9), fill=dark)
    else:
        back = 1 if facing == LEFT else -1
        a, b = (cx + 3, x1 + 1) if back > 0 else (x0 - 1, cx - 3)
        d.rectangle((a, y, b, y + 7), fill=hair)
        for x in range(a, b + 1, 3):
            d.line((x, y + 7, x, y + 8), fill=dark)


def wavy(d, x0, x1, y0, y1, col, dark, wave):
    """A wavy lock of hair: each row shifts a little, so the edge is soft and curling."""
    for y in range(y0, y1 + 1):
        dx = int(round(math.sin(y * 0.8 + wave) * 1.4))
        d.line((x0 + dx, y, x1 + dx, y), fill=col)
        if (y - y0) % 3 == 0:
            d.point((x1 + dx, y), fill=dark)


def draw_girl_hair(d, c, cx, top, w, facing, look):
    hair, dark = rgba(look["hair"]), shade(look["hair"], 0.74)
    y = top + 8
    x0, x1 = cx - w // 2, cx + w // 2
    if facing == DOWN:
        wavy(d, x0 - 3, x0 + 2, y, y + 15, hair, dark, 0)
        wavy(d, x1 - 2, x1 + 3, y, y + 15, hair, dark, 1.5)
        for x in range(x0 + 1, x1, 3):
            d.line((x, y, x, y + 2), fill=hair)
    elif facing == UP:
        wavy(d, x0 - 3, x1 + 3, y, y + 17, hair, dark, 0)
        for x in range(x0, x1, 4):
            d.line((x, y + 2, x + 1, y + 15), fill=dark)
    else:
        back = 1 if facing == LEFT else -1
        a, b = (cx + 2, x1 + 4) if back > 0 else (x0 - 4, cx - 2)
        wavy(d, a, b, y, y + 16, hair, dark, 0.7)


def paint_frame(cell_head, cell_top, facing, look, frame_i):
    """The painted parts of one 64x64 frame, as one transparent image for each draw layer."""
    under = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    over = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    u, o = ImageDraw.Draw(under), ImageDraw.Draw(over)
    hx0, htop, hx1, hbot = box(cell_head)
    tx0, ttop, tx1, tbot = box(cell_top)
    cx, w = (hx0 + hx1) // 2, hx1 - hx0
    px = cell_top.load()

    # Padded jacket: quilting lines across the sleeves and body, plus the trim.
    quilt = shade(look["coat"], 0.74)
    for y in range(ttop + 3, tbot, 4):
        for x in range(tx0, tx1):
            if px[x, y][3]:
                u.point((x, y), fill=quilt)
    tcx = (tx0 + tx1) // 2
    trim = rgba(look["trim"])
    if facing in (DOWN, UP):
        u.line((tcx - 4, ttop + 1, tcx - 4, ttop + 8), fill=trim)
        u.line((tcx + 3, ttop + 1, tcx + 3, ttop + 8), fill=trim)
    if facing == DOWN and not look["skirt"]:
        u.line((tcx, ttop + 2, tcx, tbot - 2), fill=shade(look["coat"], 0.6))
    if look["skirt"]:
        # A long coat flaring from the waist.
        coat, dark = rgba(look["coat"]), shade(look["coat"], 0.72)
        half = (tx1 - tx0) // 2 if facing in (DOWN, UP) else 5
        for i in range(0, 13):
            r = min(half, 8) + i // 2
            u.line((tcx - r, tbot - 2 + i, tcx + r, tbot - 2 + i), fill=coat)
            u.point((tcx + r, tbot - 2 + i), fill=dark)
        if facing == DOWN:
            u.line((tcx, ttop + 2, tcx, tbot + 9), fill=dark)
    draw_beanie(o, None, cx, htop, w, facing, look)
    hair = draw_boy_hair if not look["scarf"] else draw_girl_hair
    if facing == DOWN or not look["scarf"]:
        hair(o, None, cx, htop, w, facing, look)
    if look["scarf"]:
        scarf, dark = rgba(look["scarf"]), shade(look["scarf"], 0.72)
        o.rectangle((tcx - 6, hbot - 1, tcx + 6, hbot + 2), fill=scarf)
        o.line((tcx - 6, hbot + 2, tcx + 6, hbot + 2), fill=dark)
        if facing == DOWN:
            o.rectangle((tcx + 2, hbot + 2, tcx + 5, hbot + 9), fill=scarf)
            o.line((tcx + 5, hbot + 2, tcx + 5, hbot + 9), fill=dark)
        else:
            hair(o, None, cx, htop, w, facing, look)
    return under, over


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


def sheet(look, anim):
    body = look["body"]
    base = layer("body", body, anim, look["skin"])
    head = layer(look["head"], body, anim, look["skin"])
    face = eyes(anim)
    legs = layer(look["legs"], body, anim, look["trousers"])
    boots = layer(look["boots"], body, anim, look["shoes"])
    top = layer(look["top"], body, anim, look["coat"])
    count = FRAMES[anim]
    out = Image.new("RGBA", (count * 64, 256), (0, 0, 0, 0))
    for row in range(4):
        for f in range(count):
            area = (f * 64, row * 64, (f + 1) * 64, (row + 1) * 64)
            cell = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            for part in (base, legs, boots):
                cell.alpha_composite(part.crop(area))
            h, t = head.crop(area), top.crop(area)
            under, over = paint_frame(h, t, row, look, f)
            coat = t.copy()
            coat.alpha_composite(under)
            cell.alpha_composite(outline(coat))
            cell.alpha_composite(h)
            if face is not None:
                cell.alpha_composite(face.crop(area))
            cell.alpha_composite(outline(over))
            out.alpha_composite(cell, (f * 64, row * 64))
    return out


GREY = (200, 208, 220, 255)
os.makedirs(out_dir, exist_ok=True)


def x4(img):
    return img.resize((img.width * 4, img.height * 4), Image.NEAREST)


rows = []
for name, look in (("boy", BOY), ("girl", GIRL)):
    walk, run = sheet(look, "walk"), sheet(look, "run")
    walk.save(f"{out_dir}/{name}-walk-sheet.png")
    run.save(f"{out_dir}/{name}-run-sheet.png")
    for tag, img in (("walk", walk), ("run", run)):
        bg = Image.new("RGBA", img.size, GREY)
        bg.alpha_composite(img)
        bg.save(f"{out_dir}/{name}-{tag}.png")
        x4(bg).save(f"{out_dir}/{name}-{tag}-x4.png")
    idle = Image.new("RGBA", (64 * 4, 64), GREY)
    for i, r in enumerate((DOWN, LEFT, RIGHT, UP)):
        idle.alpha_composite(walk.crop((0, r * 64, 64, (r + 1) * 64)), (i * 64, 0))
    idle.save(f"{out_dir}/{name}-idle.png")
    x4(idle).save(f"{out_dir}/{name}-idle-x4.png")
    print(name, len(walk.convert("RGBA").getcolors(1 << 20)), "colours")
    rows.append(idle)
board = Image.new("RGBA", (64 * 4, 130), (255, 255, 255, 255))
board.paste(rows[0], (0, 0))
board.paste(rows[1], (0, 66))
x4(board).save(f"{out_dir}/overview-x4.png")
print("sheets ->", out_dir)
