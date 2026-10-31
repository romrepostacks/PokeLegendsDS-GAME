# Draws the Port Saltmere texture atlas: 256x256, sixteen 48x48 cells, one per surface.
# Art is laid out on a 32-unit grid and drawn at 1.5 texels per unit.
# The Blender script maps each face onto one cell (see CELLS in build_saltmere.py), and
# vertex colours tint the plain walls per building. Kaelmoor palette: pale stone, snow,
# cold water, warm wood.
#
#   python tools/art/make_atlas.py art/textures/saltmere.png
#
# Colours are snapped to the DS's 15-bit range, and the sheet stays under 256 colours,
# so it converts to an 8bpp paletted texture (64 KB of VRAM).

import random
import sys

from PIL import Image

C = 32       # art units per cell
SIZE = 48    # texels per cell
img = Image.new("RGB", (256, 256))
rng = random.Random(9)


def snap(c):
    return tuple((v >> 3) << 3 for v in c)


def put(cell, x, y, c):
    for ty in range(y * SIZE // C, (y + 1) * SIZE // C):
        for tx in range(x * SIZE // C, (x + 1) * SIZE // C):
            img.putpixel(((cell % 4) * SIZE + tx, (cell // 4) * SIZE + ty), snap(c))


def fill(cell, shades, weights=None):
    """Flat base colour. No per-pixel noise: with no mipmaps on the DS, noise shimmers
    ("scratchy") as soon as the camera moves, so detail comes from large shapes only."""
    rect(cell, 0, 0, C - 1, C - 1, shades[0])


def rect(cell, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(cell, x, y, c)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# Ground cells use big shapes and soft 2-texel joints. Thin lines swim as the camera
# moves, because the DS has no mipmaps.
# 0: plaza slabs, two rows of two.
STONE = (200, 208, 220)
JOINT = (186, 194, 208)
rect(0, 0, 0, C - 1, C - 1, STONE)
rect(0, 0, 0, C - 1, 1, JOINT)
rect(0, 0, 16, C - 1, 17, JOINT)
rect(0, 0, 0, 1, 15, JOINT)
rect(0, 16, 16, 17, C - 1, JOINT)

# 1: cobbles under a thin dusting of snow
for y in range(C):
    for x in range(C):
        c = img.getpixel((x * SIZE // C, y * SIZE // C))
        stone = (x + (4 if (y // 8) % 2 else 0)) // 8 + y // 8
        put(1, x, y, (236, 242, 250) if stone % 3 else c)  # snow on two stones in three

# 2: snow drift
fill(2, [(240, 244, 250), (228, 236, 246), (250, 252, 255)], [5, 3, 2])
rect(2, 4, 20, 13, 21, (226, 234, 246))  # soft drift shadows
rect(2, 18, 9, 27, 10, (226, 234, 246))

# 3: dock planks, two boards across the tile
WOOD = (150, 108, 72)
rect(3, 0, 0, C - 1, C - 1, WOOD)
rect(3, 0, 0, C - 1, 1, (128, 92, 62))
rect(3, 0, 16, C - 1, 17, (128, 92, 62))

# 4: sea water, flat with one wide, soft ripple
rect(4, 0, 0, C - 1, C - 1, (52, 100, 150))
rect(4, 6, 10, 21, 11, (60, 110, 160))
rect(4, 18, 24, 29, 25, (60, 110, 160))

# 5: plain plaster wall (white, so vertex colours tint it)
PLASTER = (236, 236, 236)
fill(5, [PLASTER, shade(PLASTER, 0.96)], [4, 1])
rect(5, 0, C - 2, C - 1, C - 1, (150, 150, 160))  # base course


def window(cell):
    fill(cell, [PLASTER, shade(PLASTER, 0.96)], [4, 1])
    rect(cell, 8, 6, 23, 23, (70, 60, 56))       # frame
    rect(cell, 10, 8, 21, 21, (140, 190, 230))    # glass
    rect(cell, 10, 8, 21, 11, (190, 220, 245))    # sky reflection
    rect(cell, 15, 8, 16, 21, (70, 60, 56))       # mullion
    rect(cell, 10, 14, 21, 15, (70, 60, 56))
    rect(cell, 7, 24, 24, 25, (246, 250, 255))    # snow on the sill


# 6: wall with a window
window(6)
rect(6, 0, C - 2, C - 1, C - 1, (150, 150, 160))

# 7: wall with a door
fill(7, [PLASTER, shade(PLASTER, 0.96)], [4, 1])
rect(7, 9, 6, 22, C - 1, (70, 46, 34))
rect(7, 11, 8, 20, C - 1, (128, 82, 54))
rect(7, 15, 8, 16, C - 1, (98, 64, 44))
put(7, 19, 20, (230, 200, 90))                    # handle
rect(7, 7, 4, 24, 5, (246, 250, 255))             # snow on the canopy

# 8: snowy roof slope, eave at the bottom of the cell
fill(8, [(242, 246, 252), (226, 234, 246)], [3, 1])
for x in range(C):
    edge = C - 6 - (1 if (x // 4) % 2 else 0)     # scalloped snow edge over the slate
    rect(8, x, edge, x, C - 4, (64, 72, 96))
rect(8, 0, C - 3, C - 1, C - 1, (44, 48, 70))     # eave

# 9: icicles hanging under the eaves (upper wall band)
fill(9, [PLASTER, shade(PLASTER, 0.96)], [4, 1])
rect(9, 0, 0, C - 1, 2, (44, 48, 70))
for x in range(1, C, 3):
    rect(9, x, 3, x, 3 + rng.randrange(2, 7), (200, 230, 250))

# 10: lighthouse tower, red and white bands
for y in range(C):
    band = (210, 60, 52) if (y // 8) % 2 == 0 else (240, 240, 244)
    for x in range(C):
        put(10, x, y, band)

# 11: lighthouse lamp room, glass with frames and a warm light
fill(11, [(255, 230, 140), (250, 214, 110)])
for x in range(0, C, 8):
    rect(11, x, 0, x + 1, C - 1, (40, 44, 60))
rect(11, 0, 0, C - 1, 2, (40, 44, 60))
rect(11, 0, C - 3, C - 1, C - 1, (40, 44, 60))

# 12: crate
fill(12, [(176, 128, 80), (166, 120, 74)])
rect(12, 0, 0, C - 1, 2, (110, 74, 46))
rect(12, 0, C - 3, C - 1, C - 1, (110, 74, 46))
rect(12, 0, 0, 2, C - 1, (110, 74, 46))
rect(12, C - 3, 0, C - 1, C - 1, (110, 74, 46))
for i in range(3, C - 3):
    rect(12, i, i, i + 1, i, (120, 82, 50))

# 13: dark wet wood (posts, dock sides)
fill(13, [(84, 60, 44), (74, 52, 38), (94, 68, 50)])
for y0 in range(0, C, 8):
    rect(13, 0, y0, C - 1, y0, (66, 48, 36))

# 14: quay wall, large blocks of darker stone
fill(14, [(130, 140, 158), (122, 132, 150)])
for y0 in range(0, C, 10):
    rect(14, 0, y0, C - 1, y0, (104, 112, 130))
    off = 8 if (y0 // 10) % 2 else 0
    for x in range(off, C, 16):
        rect(14, x, y0, x, min(C - 1, y0 + 9), (104, 112, 130))

# 15: fountain water, frozen at the edges
fill(15, [(150, 200, 236), (170, 214, 244), (130, 186, 228)], [4, 2, 1])
for i in range(C):
    for j in (0, 1, C - 2, C - 1):
        put(15, i, j, (226, 240, 252))
        put(15, j, i, (226, 240, 252))

colours = len(img.getcolors(1 << 16))
assert colours <= 256, f"{colours} colours: too many for an 8bpp texture"
img.save(sys.argv[1])
print(f"saltmere atlas -> {sys.argv[1]} ({colours} colours)")
