# Draws the creator's Frost Night skin: the top screen scene and the bottom screen's tiles.
#
#   python tools/art/make_ui.py data/textures include/ui_data.h
#
# Bottom screen tiles are 4bpp. Colours come from palette banks, so one set of tiles can be
# blue or gold (see the BANK_ names written to the header). Tile 0 stays empty.

import random
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

data_dir, header = sys.argv[1:3]
FONT = ImageFont.load_default_imagefont()

SKY0, SKY1 = (22, 44, 78), (70, 120, 170)
HILL, SNOW, FLAKE = (150, 180, 210), (220, 234, 246), (255, 255, 255)
PAD, PAD2 = (120, 170, 210), (170, 210, 236)
PLATE, LINE, PTEXT, HINT = (16, 34, 60), (110, 200, 240), (232, 246, 255), (30, 50, 80)
BG, PANEL, TILE, TILE_ON = (14, 30, 54), (24, 48, 80), (24, 52, 86), (36, 84, 128)
GOLD, TEXT, DARK = (255, 216, 90), (220, 238, 255), (20, 30, 50)
ICON_OFF = (120, 170, 210)


def text(d, x, y, s, fill, scale=1):
    """Pixel font text centred on x, y."""
    w, h = d.textbbox((0, 0), s, font=FONT)[2:]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((0, 0), s, font=FONT, fill=255)
    mask = mask.point(lambda v: 255 if v > 80 else 0).resize((w * scale, h * scale), Image.NEAREST)
    d.bitmap((x - w * scale // 2, y - h * scale // 2), mask, fill=fill)


def top_screen():
    im = Image.new("RGB", (256, 256), SKY1)
    d = ImageDraw.Draw(im)
    for y in range(192):
        t = (y // 16) / 11
        d.line((0, y, 255, y), fill=tuple(int(SKY0[i] * (1 - t) + SKY1[i] * t) for i in range(3)))
    d.polygon([(0, 120), (50, 100), (110, 116), (170, 96), (256, 112), (256, 192), (0, 192)], fill=HILL)
    d.rectangle((0, 140, 255, 255), fill=SNOW)
    random.seed(3)
    for _ in range(60):
        d.point((random.randrange(256), random.randrange(140)), fill=FLAKE)
    d.ellipse((88, 150, 168, 166), fill=PAD)
    d.ellipse((96, 152, 160, 163), fill=PAD2)
    d.rounded_rectangle((6, 6, 120, 24), 4, fill=PLATE, outline=LINE)
    text(d, 63, 15, "TRAINER", PTEXT)
    d.rounded_rectangle((176, 6, 250, 24), 4, fill=PLATE, outline=LINE)
    for x, s in ((24, "<"), (232, ">")):
        d.rounded_rectangle((x - 9, 88, x + 9, 106), 4, fill=PLATE, outline=LINE)
        text(d, x, 97, s, PTEXT)
    text(d, 128, 178, "L / R  turn     Y  walk", HINT)
    return im


def pal15(rgb):
    return (rgb[0] >> 3) | (rgb[1] >> 3) << 5 | (rgb[2] >> 3) << 10


def pal16_texture(im, name):
    """A 4bpp texture and palette, as the DS wants them."""
    q = im.quantize(16, dither=Image.Dither.NONE)
    p = q.getpalette()[:48]
    px = q.tobytes()
    out = bytearray((px[i] & 15) | (px[i + 1] & 15) << 4 for i in range(0, len(px), 2))
    open(f"{data_dir}/{name}_tex.bin", "wb").write(out)
    colours = [pal15(p[i:i + 3]) for i in range(0, len(p) - 2, 3)]
    colours += [0] * (16 - len(colours))
    open(f"{data_dir}/{name}_pal.bin", "wb").write(struct.pack("<16H", *colours))


def label(s, name):
    """White text on the plate colour, for the plate that changes."""
    im = Image.new("RGB", (64, 16), PLATE)
    text(ImageDraw.Draw(im), 32, 8, s, PTEXT)
    pal16_texture(im, name)


tiles = [bytes(64)]  # one byte per pixel until the end


def add(rows):
    tiles.append(bytes(v for row in rows for v in row))
    return len(tiles) - 1


def from_image(im, ox, oy):
    return add([[im.getpixel((ox + x, oy + y)) for x in range(8)] for y in range(8)])


# Rounded panel, 3x3 tiles: border 1, fill 2.
im = Image.new("P", (24, 24), 0)
d = ImageDraw.Draw(im)
d.rounded_rectangle((0, 0, 23, 23), 4, fill=2, outline=1)
PANEL_TILE = len(tiles)
for y in range(3):
    for x in range(3):
        from_image(im, x * 8, y * 8)

# Font: 95 characters, two tiles tall, one row of shadow.
FONT_TILE = len(tiles)
for c in range(32, 127):
    mask = Image.new("L", (8, 16), 0)
    ImageDraw.Draw(mask).text((1, 2), chr(c), font=FONT, fill=255)
    im = Image.new("P", (8, 16), 0)
    m = mask.load()
    for y in range(16):
        for x in range(8):
            if m[x, y] > 80:
                if y + 1 < 16:
                    im.putpixel((x, y + 1), 2)
    for y in range(16):
        for x in range(8):
            if m[x, y] > 80:
                im.putpixel((x, y), 1)
    from_image(im, 0, 0)
    from_image(im, 0, 8)


# Tab icons, 3x3 tiles: body, hair, hat, top, scarf, legs, shoes, skin, eyes, bike.
def icon(d, x, y, k):
    col = 1
    if k == 0:
        d.ellipse((x + 3, y, x + 8, y + 5), fill=col)
        d.rectangle((x + 2, y + 6, x + 9, y + 11), fill=col)
    elif k == 1:
        d.pieslice((x, y, x + 11, y + 12), 180, 360, fill=col)
        d.rectangle((x, y + 6, x + 2, y + 11), fill=col)
        d.rectangle((x + 9, y + 6, x + 11, y + 11), fill=col)
    elif k == 2:
        d.pieslice((x + 1, y + 2, x + 10, y + 14), 180, 360, fill=col)
        d.rectangle((x, y + 7, x + 11, y + 9), fill=col)
        d.ellipse((x + 4, y, x + 7, y + 3), fill=col)
    elif k == 3:
        d.polygon([(x, y + 3), (x + 3, y), (x + 8, y), (x + 11, y + 3), (x + 9, y + 5), (x + 9, y + 11),
                   (x + 2, y + 11), (x + 2, y + 5)], fill=col)
    elif k == 4:
        d.rectangle((x, y + 2, x + 11, y + 5), fill=col)
        d.rectangle((x + 7, y + 5, x + 10, y + 11), fill=col)
    elif k == 5:
        d.polygon([(x + 1, y), (x + 10, y), (x + 11, y + 11), (x + 7, y + 11), (x + 6, y + 4), (x + 5, y + 4),
                   (x + 4, y + 11), (x, y + 11)], fill=col)
    elif k == 6:
        d.rectangle((x + 2, y + 1, x + 6, y + 8), fill=col)
        d.rectangle((x + 2, y + 7, x + 11, y + 11), fill=col)
    elif k == 7:
        d.ellipse((x + 1, y + 1, x + 10, y + 10), fill=col)
    elif k == 9:
        d.ellipse((x - 1, y + 4, x + 5, y + 10), outline=col)
        d.ellipse((x + 6, y + 4, x + 12, y + 10), outline=col)
        d.line((x + 2, y + 7, x + 5, y + 2, x + 9, y + 7), fill=col)
    elif k == 8:
        d.ellipse((x, y + 3, x + 11, y + 9), fill=col)
        d.ellipse((x + 4, y + 4, x + 7, y + 8), fill=0)


ICON_TILE = len(tiles)
for k in range(10):
    im = Image.new("P", (24, 24), 0)
    icon(ImageDraw.Draw(im), 6, 6, k)
    for y in range(3):
        for x in range(3):
            from_image(im, x * 8, y * 8)

# Swatches, 2x2 tiles: colour numbers 1-12, each with three borders (13 ice, 14 white, 15 gold).
SWATCH_TILE = len(tiles)
for k in range(1, 13):
    for border in (13, 14, 15):
        im = Image.new("P", (16, 16), 0)
        ImageDraw.Draw(im).rectangle((1, 1, 14, 14), fill=k, outline=border)
        for y in range(2):
            for x in range(2):
                from_image(im, x * 8, y * 8)


packed = bytearray()
for t in tiles:
    for i in range(0, 64, 2):
        packed.append(t[i] | t[i + 1] << 4)
open(f"{data_dir}/ui_tiles.bin", "wb").write(packed)


def bank(*colours):
    row = [0] + [pal15(c) for c in colours]
    return row + [0] * (16 - len(row))


BANKS = [("TEXT", bank(TEXT, BG)), ("GOLD_TEXT", bank(GOLD, BG)), ("DARK_TEXT", bank(DARK, GOLD)),
         ("PANEL", bank(LINE, TILE)), ("SELECTED", bank(LINE, TILE_ON)), ("FOCUS", bank(GOLD, TILE_ON)),
         ("SOLID", bank(GOLD, GOLD)), ("ICON", bank(ICON_OFF)), ("ICON_ON", bank(GOLD))]
palette = [pal15(BG)] + [0] * 15
for _, row in BANKS:
    palette += row
palette += [0] * (256 - len(palette))
open(f"{data_dir}/ui_pal.bin", "wb").write(struct.pack(f"<{len(palette)}H", *palette))

pal16_texture(top_screen(), "ui_top")
label("Boy", "ui_boy")
label("Girl", "ui_girl")

with open(header, "w", newline="\n") as f:
    f.write("// Written by tools/art/make_ui.py.\n#pragma once\n\n")
    for name, v in (("PANEL", PANEL_TILE), ("FONT", FONT_TILE), ("ICON", ICON_TILE), ("SWATCH", SWATCH_TILE)):
        f.write(f"#define UI_TILE_{name} {v}\n")
    for i, (name, _) in enumerate(BANKS):
        f.write(f"#define BANK_{name} {i + 1}\n")
    f.write(f"#define BANK_SWATCH {len(BANKS) + 1}\n")
    f.write(f"#define UI_ICE {pal15(LINE)}\n#define UI_WHITE {pal15(PTEXT)}\n#define UI_GOLD {pal15(GOLD)}\n")
print(len(tiles), "tiles,", len(packed), "bytes")
