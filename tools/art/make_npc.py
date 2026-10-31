# Packs an NPC's four idle frames from a 64x64-per-frame LPC character sheet.
#
#   python tools/art/make_npc.py art/player/kyle-player-lpc.png art/sprites/npc.png
#
# Walk rows 8-11 are up, left, down, right; the first frame of each is the idle pose. Each is
# cropped to 32x60, which holds all the art, into a 128x64 sheet in that order.

import sys

from PIL import Image

CROP = (16, 4, 48, 64)

src = Image.open(sys.argv[1]).convert("RGBA")
sheet = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
for i, row in enumerate(range(8, 12)):
    y = row * 64
    sheet.paste(src.crop((CROP[0], y + CROP[1], CROP[2], y + CROP[3])), (i * 32, 0))
sheet.save(sys.argv[2])
print(f"npc sheet -> {sys.argv[2]}")
