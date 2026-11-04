# Packs the starter screen: the snowy supply crate with three Poke Balls on the bottom screen,
# and for each of the 27 starters its icon, battle sprite, base stats, Lv 5 moves and evolutions.
#
#   python tools/art/make_starters.py art/starters data/textures include/starter_data.h
#
# Battle sprites are the Black/White style front sprites from PokeAPI (art/starters/<dex>.png).
# Stats, moves (Scarlet/Violet, learned by Lv 5) and evolution levels are in art/starters/data.json,
# also from PokeAPI. Each sprite keeps its own 16 colours. Writes:
#   starters.bin           per starter: icon (32x32 4bpp sprite tiles), battle (64x64 4bpp texture),
#                          stats (128x128 4bpp texture), text (256x64 4bpp texture),
#                          palette (16 colours, 0 transparent)
#   starter_top_tex/pal    the top screen stage
#   starter_info_pal       colours for the stats and text panels
#   starter_hint_tex       "Tap a Poke Ball" panel, 256x32
#   starter_crate_*        bottom screen crate: tiles, 32x32 map, palette (bank 12)
#   starter_ball_*         Poke Ball sprite, closed and open frames, and its palette
#   starter_data.h         dex numbers and names, row by row (Grass, Fire, Water), gen 1-9 left to right

import json
import os
import struct
import sys
import urllib.request
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

art_dir, data_dir, header = sys.argv[1:4]
FONT = ImageFont.load_default_imagefont()
URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/{}.png"

# (dex, name, final evolution, flavour), one row per type.
ROWS = [
    ("Grass", [
        (1, "Bulbasaur", "Venusaur", "Carries a seed that grows as it does."),
        (152, "Chikorita", "Meganium", "Its leaf gives off a sweet, calm scent."),
        (252, "Treecko", "Sceptile", "Cool-headed, it climbs any wall."),
        (387, "Turtwig", "Torterra", "Its shell is soil that hardens with age."),
        (495, "Snivy", "Serperior", "Proud and quick, it soaks up the sun."),
        (650, "Chespin", "Chesnaught", "Its soft quills stiffen when on guard."),
        (722, "Rowlet", "Decidueye", "Flies without a sound to catch foes."),
        (810, "Grookey", "Rillaboom", "Keeps a beat with its stick all day."),
        (906, "Sprigatito", "Meowscarada", "Moody but sweet; smells of fresh grass."),
    ]),
    ("Fire", [
        (4, "Charmander", "Charizard", "The flame on its tail shows its mood."),
        (155, "Cyndaquil", "Typhlosion", "Flares up its back when startled."),
        (255, "Torchic", "Blaziken", "Warm to hold; a fire burns inside."),
        (390, "Chimchar", "Infernape", "Its tail flame stays lit even in rain."),
        (498, "Tepig", "Emboar", "Snorts embers when it gets excited."),
        (653, "Fennekin", "Delphox", "Nibbles twigs to keep its ears hot."),
        (725, "Litten", "Incineroar", "Aloof; its groomed fur can catch fire."),
        (813, "Scorbunny", "Cinderace", "Runs hot the moment it starts to sprint."),
        (909, "Fuecoco", "Skeledirge", "Laid-back, with a belly full of fire."),
    ]),
    ("Water", [
        (7, "Squirtle", "Blastoise", "Hides in its shell and fires back water."),
        (158, "Totodile", "Feraligatr", "Snaps at anything that moves."),
        (258, "Mudkip", "Swampert", "Senses the water around it with its fin."),
        (393, "Piplup", "Empoleon", "Proud, and won't admit it needs help."),
        (501, "Oshawott", "Samurott", "Fights with the shell on its stomach."),
        (656, "Froakie", "Greninja", "Wraps itself in bubbles to stay safe."),
        (728, "Popplio", "Primarina", "Blows water balloons to show off."),
        (816, "Sobble", "Inteleon", "Shy; it vanishes into water when scared."),
        (912, "Quaxly", "Quaquaval", "Neat and tidy; its feathers stay dry."),
    ]),
]

SKY0, SKY1 = (22, 44, 78), (70, 120, 170)
HILL, SNOW, FLAKE = (150, 180, 210), (220, 234, 246), (255, 255, 255)
PAD, PAD2 = (120, 170, 210), (170, 210, 236)
PLATE, LINE, PTEXT, GOLD = (16, 34, 60), (110, 200, 240), (232, 246, 255), (255, 216, 90)


def pal15(rgb):
    return (rgb[0] >> 3) | (rgb[1] >> 3) << 5 | (rgb[2] >> 3) << 10


def mask(s):
    w, h = FONT.getbbox(s)[2:]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((0, 0), s, font=FONT, fill=255)
    return m.point(lambda v: 255 if v > 80 else 0)


def nibbles(px):
    """4bpp, low nibble first: the order both DS textures and sprite tiles use."""
    return bytes(px[i] | px[i + 1] << 4 for i in range(0, len(px), 2))


def sprite_tiles(im):
    """A paletted image as 8x8 tiles, left to right then top to bottom (1D sprite mapping)."""
    out = b""
    for ty in range(0, im.height, 8):
        for tx in range(0, im.width, 8):
            out += nibbles(im.crop((tx, ty, tx + 8, ty + 8)).tobytes())
    return out


def lum(c):
    return c[0] * 3 + c[1] * 6 + c[2]


def shrink(im):
    """Half size for the menu icon. Dark outline pixels win a 2x2 block, so edges survive."""
    px = im.load()
    out = Image.new("RGBA", (im.width // 2, im.height // 2), (0, 0, 0, 0))
    o = out.load()
    for y in range(out.height):
        for x in range(out.width):
            block = [px[2 * x + i, 2 * y + j] for j in (0, 1) for i in (0, 1)]
            solid = [c for c in block if c[3]]
            if not solid or (len(solid) == 1 and lum(solid[0]) >= 200):
                continue
            dark = min(solid, key=lum)
            o[x, y] = dark if lum(dark) < 150 or len(solid) == 1 else Counter(solid).most_common(1)[0][0]
    return out


def pixels(im):
    d = im.tobytes()
    return [tuple(d[i:i + 4]) for i in range(0, len(d), 4)]


def indexed(im, colours):
    """RGBA to palette indices, 0 for transparent."""
    return Image.frombytes("P", im.size, bytes(0 if c[3] == 0 else 1 + colours.index(c[:3]) for c in pixels(im)))


# Shared by the stats, text and hint textures.
INFO = [None, PTEXT, GOLD, LINE, PLATE, (240, 128, 64), (240, 208, 72), (120, 210, 110), (8, 18, 34)]
TEXT, NAME, LABEL, BACK, LOW, MID, HIGH, TRACK = range(1, 9)


def stage():
    im = Image.new("RGB", (256, 256), SKY1)
    d = ImageDraw.Draw(im)
    for y in range(192):
        t = (y // 16) / 11
        d.line((0, y, 255, y), fill=tuple(int(SKY0[i] * (1 - t) + SKY1[i] * t) for i in range(3)))
    d.polygon([(0, 84), (50, 70), (110, 82), (180, 64), (256, 78), (256, 192), (0, 192)], fill=HILL)
    d.rectangle((0, 100, 255, 255), fill=SNOW)
    for i in range(60):
        d.point(((i * 97) % 256, (i * 53) % 100), fill=FLAKE)
    d.ellipse((12, 110, 116, 128), fill=PAD)
    d.ellipse((24, 113, 104, 125), fill=PAD2)
    q = im.quantize(16, dither=Image.Dither.NONE)
    p = q.getpalette()[:48]
    colours = [pal15(p[i:i + 3]) for i in range(0, len(p), 3)]
    colours += [0] * (16 - len(colours))
    open(f"{data_dir}/starter_top_tex.bin", "wb").write(nibbles(q.tobytes()))
    open(f"{data_dir}/starter_top_pal.bin", "wb").write(struct.pack("<16H", *colours))


def write(im, x, y, s, col, right=False):
    m = mask(s)
    if right:
        x -= m.width
    assert x >= 0 and x + m.width <= im.width - 4, f"too wide: {s}"
    im.paste(col, (x, y), m)


def plate(im, box):
    ImageDraw.Draw(im).rounded_rectangle(box, 4, fill=BACK, outline=LABEL)


def stats_panel(stats):
    """Base stats with bars, for the right half of the top screen."""
    im = Image.new("P", (128, 128), 0)
    d = ImageDraw.Draw(im)
    plate(im, (2, 2, 125, 125))
    write(im, 8, 6, "BASE STATS", NAME)
    for i, (label, v) in enumerate(zip(("HP", "Atk", "Def", "Sp.Atk", "Sp.Def", "Speed"), stats)):
        y = 22 + i * 15
        write(im, 8, y, label, LABEL)
        write(im, 66, y, str(v), TEXT, right=True)
        d.rectangle((70, y + 3, 119, y + 7), fill=TRACK)
        d.rectangle((70, y + 3, 70 + min(49, v * 49 // 100), y + 7), fill=LOW if v < 50 else MID if v < 65 else HIGH)
    write(im, 8, 110, "Total", LABEL)
    write(im, 66, 110, str(sum(stats)), NAME, right=True)
    return nibbles(im.tobytes())


def title(name):
    return " ".join(w.capitalize() for w in name.split("-"))


def text_panel(typ, name, flavour, moves, evo):
    """Name, flavour line, starting moves and evolution path, under the sprite and stats."""
    im = Image.new("P", (256, 64), 0)
    plate(im, (2, 0, 253, 62))
    write(im, 8, 3, name.upper(), NAME)
    write(im, 247, 3, typ, LABEL, right=True)
    write(im, 8, 14, flavour, TEXT)
    write(im, 8, 26, "Moves", LABEL)
    write(im, 58, 26, ", ".join(title(m) for m in moves), TEXT)
    write(im, 8, 38, "Evolves", LABEL)
    (mid, lv1), (last, lv2) = evo[1], evo[2]
    write(im, 58, 38, f"Lv {lv1}  {title(mid)}", TEXT)
    write(im, 58, 50, f"Lv {lv2}  {title(last)}", TEXT)
    return nibbles(im.tobytes())


def hint():
    im = Image.new("P", (256, 32), 0)
    plate(im, (40, 4, 215, 27))
    m = mask("Tap a Poke Ball to look inside")
    im.paste(TEXT, (128 - m.width // 2, 10), m)
    open(f"{data_dir}/starter_hint_tex.bin", "wb").write(nibbles(im.tobytes()))


# The bottom screen: a supply crate dug out of the snow, three Poke Balls in its straw.
CRATE = dict(
    night=(14, 30, 54), snow0=(150, 180, 210), snow1=(196, 218, 238), snow2=(236, 244, 252),
    wood0=(46, 52, 30), wood1=(74, 82, 44), wood2=(104, 112, 62), wood3=(136, 142, 84),
    metal0=(60, 66, 74), metal1=(120, 128, 138),
    straw0=(120, 96, 48), straw1=(170, 140, 72), straw2=(212, 184, 110), shadow=(26, 34, 40))
BALL_X, BALL_Y = (72, 128, 184), 100  # ball centres, in screen pixels
CRATE_BANK = 12


def crate():
    import random
    C = CRATE
    im = Image.new("RGB", (256, 192), C["night"])
    d = ImageDraw.Draw(im)
    d.rectangle((0, 24, 255, 191), fill=C["snow1"])
    d.rectangle((0, 24, 255, 27), fill=C["snow0"])
    x0, y0, x1, y1, t = 20, 40, 235, 158, 10
    d.rectangle((x0 + 3, y0 + 4, x1 + 3, y1 + 4), fill=C["snow0"])
    d.rectangle((x0, y0, x1, y1), fill=C["wood1"], outline=C["wood0"])
    for box in ((x0, y0, x1, y0 + t), (x0, y1 - t - 6, x1, y1), (x0, y0, x0 + t, y1), (x1 - t, y0, x1, y1)):
        d.rectangle(box, fill=C["wood2"], outline=C["wood0"])
    for x in range(x0 + 16, x1 - 8, 24):
        d.line((x, y0 + 2, x, y0 + t - 2), fill=C["wood1"])
        d.line((x + 8, y1 - t - 4, x + 8, y1 - 2), fill=C["wood1"])
    d.line((x0 + 2, y0 + t // 2, x1 - 2, y0 + t // 2), fill=C["wood3"])
    d.line((x0 + 2, y1 - t // 2 - 3, x1 - 2, y1 - t // 2 - 3), fill=C["wood3"])
    for cx, cy in ((x0, y0), (x1 - 13, y0), (x0, y1 - 13), (x1 - 13, y1 - 13)):
        d.rectangle((cx, cy, cx + 13, cy + 13), fill=C["metal1"], outline=C["metal0"])
        d.point((cx + 3, cy + 3), fill=C["metal0"])
        d.point((cx + 10, cy + 10), fill=C["metal0"])
    ix0, iy0, ix1, iy1 = x0 + t + 1, y0 + t + 1, x1 - t - 1, y1 - t - 7
    d.rectangle((ix0, iy0, ix1, iy1), fill=C["straw1"])
    d.rectangle((ix0, iy0, ix1, iy0 + 5), fill=C["shadow"])
    d.rectangle((ix0, iy0, ix0 + 3, iy1), fill=C["straw0"])
    random.seed(7)
    for _ in range(260):
        x, y, n = random.randrange(ix0 + 4, ix1 - 4), random.randrange(iy0 + 7, iy1 - 1), random.randrange(3, 7)
        d.line((x, y, x + n * random.choice((-1, 1)), y + random.choice((-1, 0, 1))),
               fill=random.choice((C["straw0"], C["straw2"], C["straw2"])))
    for cx in BALL_X:
        d.ellipse((cx - 19, BALL_Y - 17, cx + 19, BALL_Y + 19), fill=C["straw0"])
        d.ellipse((cx - 17, BALL_Y - 15, cx + 17, BALL_Y + 17), fill=C["shadow"])
    m = mask("KAELMOOR EXPEDITION  03")
    m = m.crop(m.getbbox())
    d.bitmap((128 - m.width // 2, y1 - t - 3), m, fill=C["wood0"])

    def mound(pts, top):
        d.polygon(pts, fill=C["snow2"])
        d.line([(x, y + 3) for x, y in top], fill=C["snow1"])
    mound([(0, 118), (10, 112), (22, 116), (30, 130), (40, 150), (56, 166), (60, 191), (0, 191)],
          [(0, 119), (10, 113), (22, 117), (29, 129)])
    mound([(226, 60), (236, 52), (248, 50), (255, 54), (255, 191), (238, 191), (232, 150), (228, 110)],
          [(236, 53), (248, 51), (255, 55)])
    mound([(150, 191), (170, 170), (196, 162), (224, 166), (240, 176), (255, 191)],
          [(170, 171), (196, 163), (224, 167)])
    mound([(0, 191), (0, 176), (30, 168), (70, 172), (96, 182), (104, 191)], [(0, 177), (30, 169), (70, 173)])
    random.seed(11)
    for _ in range(70):
        y = random.choice((random.randrange(y0, y0 + t), random.randrange(y1 - t - 6, y1)))
        d.point((random.randrange(x0, x1), y), fill=C["snow2"])
    for _ in range(40):
        d.point((random.randrange(256), random.randrange(26, 192)), fill=C["snow2"])
    return im


def crate_tiles(first_tile):
    """Tiles (deduplicated, flips included), map and palette for the crate background."""
    im = crate()
    colours = list(CRATE.values())
    assert len(colours) <= 15
    px = im.load()
    tiles, lookup, tmap = [], {}, [0] * (32 * 32)
    for ty in range(24):
        for tx in range(32):
            rows = [[1 + colours.index(px[tx * 8 + x, ty * 8 + y]) for x in range(8)] for y in range(8)]
            key = tuple(sum(rows, []))
            if key not in lookup:
                lookup[key] = (len(tiles), 0)
                tiles.append(key)
                lookup.setdefault(tuple(sum([r[::-1] for r in rows], [])), (len(tiles) - 1, 1))
                lookup.setdefault(tuple(sum(rows[::-1], [])), (len(tiles) - 1, 2))
                lookup.setdefault(tuple(sum([r[::-1] for r in rows[::-1]], [])), (len(tiles) - 1, 3))
            n, flip = lookup[key]
            tmap[ty * 32 + tx] = (first_tile + n) | flip << 10 | CRATE_BANK << 12
    assert first_tile + len(tiles) <= 13 * 2048 // 32, f"{len(tiles)} crate tiles don't fit below the map"
    open(f"{data_dir}/starter_crate_tiles.bin", "wb").write(b"".join(nibbles(t) for t in tiles))
    open(f"{data_dir}/starter_crate_map.bin", "wb").write(struct.pack(f"<{len(tmap)}H", *tmap))
    pal = [0] + [pal15(c) for c in colours]
    pal += [0] * (16 - len(pal))
    open(f"{data_dir}/starter_crate_pal.bin", "wb").write(struct.pack("<16H", *pal))
    return len(tiles)


def balls():
    """A Poke Ball, closed and open: 32x32, two frames."""
    red, dark, white, grey, black, glow = (220, 48, 56), (150, 24, 40), (244, 244, 248), (176, 184, 200), (24, 24, 32), (255, 246, 190)
    shine = (255, 140, 140)
    colours = [red, dark, white, grey, black, glow, shine]
    frames = []
    for opened in (False, True):
        im = Image.new("RGB", (32, 32), (255, 0, 255))
        d = ImageDraw.Draw(im)
        if opened:
            d.chord((4, 0, 27, 16), 180, 360, fill=red, outline=black)   # lid tipped back
            d.ellipse((5, 9, 26, 17), fill=black)
            d.ellipse((7, 10, 24, 16), fill=glow)
            d.chord((4, 6, 27, 29), 0, 180, fill=white, outline=black)
            d.line((4, 17, 27, 17), fill=black)
        else:
            d.ellipse((4, 4, 27, 27), fill=white, outline=black)
            d.chord((4, 4, 27, 27), 180, 360, fill=red, outline=black)
            d.arc((6, 6, 25, 25), 200, 250, fill=shine)
            d.rectangle((5, 15, 26, 16), fill=black)
            d.ellipse((12, 12, 19, 19), fill=white, outline=black)
            d.ellipse((14, 14, 17, 17), fill=grey)
            d.chord((4, 4, 27, 27), 20, 160, fill=None, outline=grey)
        p = Image.frombytes("P", (32, 32), bytes(0 if c == (255, 0, 255) else 1 + colours.index(c) for c in pixels(im.convert("RGBA")) for c in [c[:3]]))
        frames.append(sprite_tiles(p))
    open(f"{data_dir}/starter_ball_tiles.bin", "wb").write(b"".join(frames))
    pal = [0] + [pal15(c) for c in colours]
    pal += [0] * (16 - len(pal))
    open(f"{data_dir}/starter_ball_pal.bin", "wb").write(struct.pack("<16H", *pal))


os.makedirs(art_dir, exist_ok=True)
data = json.load(open(f"{art_dir}/data.json"))
blob = b""
dex_list, names = [], []
for typ, row in ROWS:
    for dex, name, final, flavour in row:
        path = f"{art_dir}/{dex}.png"
        if not os.path.exists(path):
            urllib.request.urlretrieve(URL.format(dex), path)
        im = Image.open(path).convert("RGBA")
        # 64x64 around the sprite, standing on the bottom edge.
        left, top, right, bottom = im.getbbox()
        cx = (left + right) // 2
        crop = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        crop.alpha_composite(im.crop((cx - 32, bottom - 64, cx + 32, bottom)))
        colours = sorted({c[:3] for c in pixels(crop) if c[3]})
        assert len(colours) <= 15, f"{name}: {len(colours)} colours"
        icon = indexed(shrink(crop), colours)
        battle = indexed(crop, colours)
        pal = [0] + [pal15(c) for c in colours]
        pal += [0] * (16 - len(pal))
        blob += sprite_tiles(icon) + nibbles(battle.tobytes()) 
        d = data[str(dex)]
        blob += stats_panel(d["stats"]) + text_panel(typ, name, flavour, d["moves"], d["evo"])
        blob += struct.pack("<16H", *pal)
        dex_list.append(dex)
        names.append(name)

open(f"{data_dir}/starters.bin", "wb").write(blob)
info_pal = [0] + [pal15(c) for c in INFO[1:]]
info_pal += [0] * (16 - len(info_pal))
open(f"{data_dir}/starter_info_pal.bin", "wb").write(struct.pack("<16H", *info_pal))
stage()
hint()
balls()
# The crate's tiles go after the creator's UI tiles, in the same tile block.
ui_tiles = os.path.getsize(f"{data_dir}/ui_tiles.bin") // 32
crate_count = crate_tiles(ui_tiles)

with open(header, "w", newline="\n") as f:
    f.write("// Written by tools/art/make_starters.py.\n#pragma once\n\n")
    f.write(f"#define STARTER_GENS {len(ROWS[0][1])}\n#define STARTER_COUNT {len(dex_list)}\n\n")
    f.write("static const char *const STARTER_TYPES[] = { " + ", ".join(f'"{t}"' for t, _ in ROWS) + " };\n")
    f.write("static const u16 STARTER_DEX[] = { " + ", ".join(map(str, dex_list)) + " };\n")
    f.write(f"#define STARTER_CRATE_TILE {ui_tiles}\n#define STARTER_CRATE_BANK {CRATE_BANK}\n")
    f.write(f"static const int STARTER_BALL_X[] = {{ {', '.join(map(str, BALL_X))} }};\n#define STARTER_BALL_Y {BALL_Y}\n")
    f.write("static const char *const STARTER_NAMES[] = { " + ", ".join(f'"{n}"' for n in names) + " };\n")
print(len(dex_list), "starters,", len(blob), "bytes,", crate_count, "crate tiles")
