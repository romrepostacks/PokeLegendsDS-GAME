# Packs the 27 starters for the starter screen: menu icons, battle sprites and top screen text.
#
#   python tools/art/make_starters.py art/starters data/textures include/starter_data.h
#
# Battle sprites are the Black/White style front sprites from PokeAPI (art/starters/<dex>.png);
# a missing one is downloaded. Each sprite keeps its own 16 colours. Writes:
#   starters.bin           per starter: icon (32x32 4bpp sprite tiles), battle (64x64 4bpp texture),
#                          info (256x32 4bpp texture), palette (16 colours, 0 transparent)
#   starter_top_tex/pal    the top screen stage
#   starter_info_pal       the info text colours
#   starter_data.h         dex numbers and names, row by row (Grass, Fire, Water), gen 1-9 left to right

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


def stage():
    im = Image.new("RGB", (256, 256), SKY1)
    d = ImageDraw.Draw(im)
    for y in range(192):
        t = (y // 16) / 11
        d.line((0, y, 255, y), fill=tuple(int(SKY0[i] * (1 - t) + SKY1[i] * t) for i in range(3)))
    d.polygon([(0, 110), (60, 92), (120, 106), (190, 88), (256, 102), (256, 192), (0, 192)], fill=HILL)
    d.rectangle((0, 128, 255, 255), fill=SNOW)
    for i in range(60):
        d.point(((i * 97) % 256, (i * 53) % 128), fill=FLAKE)
    d.ellipse((76, 132, 180, 152), fill=PAD)
    d.ellipse((88, 135, 168, 149), fill=PAD2)
    d.rounded_rectangle((6, 6, 150, 24), 4, fill=PLATE, outline=LINE)
    m = mask("CHOOSE YOUR PARTNER")
    d.bitmap((78 - m.width // 2, 10), m, fill=PTEXT)
    d.rounded_rectangle((2, 151, 253, 189), 4, fill=PLATE, outline=LINE)
    q = im.quantize(16, dither=Image.Dither.NONE)
    p = q.getpalette()[:48]
    colours = [pal15(p[i:i + 3]) for i in range(0, len(p), 3)]
    colours += [0] * (16 - len(colours))
    open(f"{data_dir}/starter_top_tex.bin", "wb").write(nibbles(q.tobytes()))
    open(f"{data_dir}/starter_top_pal.bin", "wb").write(struct.pack("<16H", *colours))


def info(typ, name, final, flavour):
    """Three lines for the plate under the sprite. Colours: 1 white, 2 gold, 3 ice."""
    im = Image.new("P", (256, 32), 0)
    lines = [((6, 0), name.upper(), 2), ((96, 0), typ, 3),
             ((6, 11), flavour, 1), ((6, 22), f"Evolves into {final}", 3)]
    for (x, y), s, col in lines:
        m = mask(s)
        assert x + m.width <= 250, f"too wide: {s}"
        im.paste(col, (x, y), m)
    return nibbles(im.tobytes())


os.makedirs(art_dir, exist_ok=True)
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
        blob += sprite_tiles(icon) + nibbles(battle.tobytes()) + info(typ, name, final, flavour)
        blob += struct.pack("<16H", *pal)
        dex_list.append(dex)
        names.append(name)

open(f"{data_dir}/starters.bin", "wb").write(blob)
info_pal = [0, pal15(PTEXT), pal15(GOLD), pal15(LINE)] + [0] * 12
open(f"{data_dir}/starter_info_pal.bin", "wb").write(struct.pack("<16H", *info_pal))
stage()

with open(header, "w", newline="\n") as f:
    f.write("// Written by tools/art/make_starters.py.\n#pragma once\n\n")
    f.write(f"#define STARTER_GENS {len(ROWS[0][1])}\n#define STARTER_COUNT {len(dex_list)}\n\n")
    f.write("static const char *const STARTER_TYPES[] = { " + ", ".join(f'"{t}"' for t, _ in ROWS) + " };\n")
    f.write("static const u16 STARTER_DEX[] = { " + ", ".join(map(str, dex_list)) + " };\n")
    f.write("static const char *const STARTER_NAMES[] = { " + ", ".join(f'"{n}"' for n in names) + " };\n")
print(len(dex_list), "starters,", len(blob), "bytes")
