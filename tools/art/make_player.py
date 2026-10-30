# Draws the player's overworld sprite sheet: an original trainer in winter expedition
# gear (green knit cap, red parka with fur collar, backpack, boots), in the Kaelmoor palette.
#
#   python tools/art/make_player.py art/sprites/player.png
#
# Sheet: 128x128, frames are 32x32. Columns: stand, step 1, step 2. Rows: down, up,
# left, right (right is the left row mirrored). 15 colours + transparent, so it converts
# to a 4bpp (16 colour) DS texture.

import sys

from PIL import Image

PAL = {
    "o": (24, 28, 48),     # outline
    "R": (196, 64, 56),    # parka
    "r": (140, 40, 40),    # parka shade
    "W": (238, 242, 246),  # fur
    "w": (180, 192, 208),  # fur shade
    "S": (244, 200, 160),  # skin
    "s": (214, 156, 120),  # skin shade
    "H": (80, 52, 40),     # hair
    "G": (64, 190, 140),   # scarf (aurora green)
    "g": (40, 130, 100),   # scarf shade
    "N": (44, 58, 92),     # trousers, mittens
    "B": (96, 62, 40),     # boots
    "b": (60, 38, 24),     # boot soles
    "P": (58, 110, 140),   # backpack
    "p": (36, 74, 100),    # backpack shade
}


class Frame:
    def __init__(self):
        self.px = [[None] * 32 for _ in range(32)]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < 32 and 0 <= y < 32:
                    self.px[y][x] = c

    def ellipse(self, x0, y0, x1, y1, c):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) / 2 + 0.5, (y1 - y0) / 2 + 0.5
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.px[y][x] = c

    def dot(self, x, y, c):
        self.px[y][x] = c

    def outline(self):
        """Dark outline around the silhouette, like Black 2's overworld sprites."""
        add = []
        for y in range(32):
            for x in range(32):
                if self.px[y][x] is None:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 32 and 0 <= ny < 32 and self.px[ny][nx] not in (None, "o"):
                            add.append((x, y))
                            break
        for x, y in add:
            self.px[y][x] = "o"
        return self


def legs_front(f, step):
    # step: 0 stand, 1 left foot lifted, 2 right foot lifted
    ly = -1 if step == 1 else 0
    ry = -1 if step == 2 else 0
    f.rect(12, 23, 14, 28 + ly, "N")
    f.rect(17, 23, 19, 28 + ry, "N")
    f.rect(12, 29 + ly, 14, 30 + ly, "B")
    f.rect(17, 29 + ry, 19, 30 + ry, "B")


def arms_front(f, step):
    la = 1 if step == 2 else 0  # arms swing opposite to the lifted foot
    ra = 1 if step == 1 else 0
    f.rect(8, 15, 10, 20 + la, "R")    # sleeves: lit edge out, shaded edge in
    f.rect(10, 16, 10, 20 + la, "r")
    f.rect(8, 21 + la, 10, 22 + la, "N")
    f.rect(21, 15, 23, 20 + ra, "r")
    f.rect(21, 16, 21, 20 + ra, "R")
    f.rect(21, 21 + ra, 23, 22 + ra, "N")


def arm_seams(f):
    """Dark line between each arm and the body, so the arms read as arms."""
    f.rect(11, 16, 11, 21, "o")
    f.rect(20, 16, 20, 21, "o")


def cap(f, x0, x1):
    """Knit cap in aurora green with a fold-up band and a white pompom."""
    f.ellipse(x0, 2, x1, 9, "G")
    f.rect(x0, 7, x1, 8, "g")
    m = (x0 + x1) // 2
    f.ellipse(m - 1, 0, m + 2, 2, "W")


def frame_down(step):
    f = Frame()
    legs_front(f, step)
    arms_front(f, step)
    f.rect(11, 15, 20, 22, "R")    # parka, hip length
    f.rect(18, 15, 20, 22, "r")
    f.rect(15, 16, 15, 22, "r")    # zip
    arm_seams(f)
    f.rect(12, 15, 12, 19, "P")    # backpack straps
    f.rect(19, 15, 19, 19, "p")
    f.rect(11, 14, 20, 15, "W")    # fur collar
    f.rect(18, 14, 20, 15, "w")
    f.rect(12, 9, 19, 13, "S")     # face
    f.rect(18, 9, 19, 13, "s")
    f.rect(11, 9, 11, 12, "H")     # hair at the sides
    f.rect(20, 9, 20, 12, "H")
    cap(f, 11, 20)
    f.rect(13, 10, 13, 11, "o")    # eyes
    f.rect(17, 10, 17, 11, "o")
    return f.outline()


def frame_up(step):
    f = Frame()
    legs_front(f, step)
    arms_front(f, step)
    f.rect(11, 15, 20, 22, "R")
    f.rect(18, 15, 20, 22, "r")
    arm_seams(f)
    f.rect(12, 15, 19, 21, "P")    # backpack
    f.rect(17, 15, 19, 21, "p")
    f.rect(12, 15, 19, 16, "p")    # flap
    f.rect(11, 14, 20, 14, "W")    # collar
    f.rect(11, 9, 20, 13, "H")     # hair
    cap(f, 11, 20)
    return f.outline()


def frame_left(step):
    f = Frame()
    # Legs: in a stride the front foot reaches left, the back foot trails right.
    if step == 0:
        f.rect(14, 23, 17, 28, "N")
        f.rect(13, 29, 17, 30, "B")
    else:
        front, back = (11, 17) if step == 1 else (12, 16)
        f.rect(back, 23, back + 2, 27, "N")
        f.rect(back, 28, back + 3, 29, "B")
        f.rect(front + 1, 23, front + 3, 28, "N")
        f.rect(front, 29, front + 3, 30, "B")
    f.rect(18, 15, 21, 21, "P")    # backpack
    f.rect(20, 15, 21, 21, "p")
    f.rect(12, 15, 18, 22, "R")    # parka
    f.rect(17, 15, 18, 22, "r")
    f.rect(12, 14, 18, 15, "W")    # collar
    ax = {0: 14, 1: 12, 2: 16}[step]  # arm swings with the stride
    f.rect(ax - 1, 15, ax + 2, 22, "o")  # outline round the sleeve
    f.rect(ax, 15, ax + 1, 21, "R")
    f.rect(ax + 1, 16, ax + 1, 21, "r")
    f.rect(ax, 22, ax + 1, 22, "N")
    f.rect(14, 9, 19, 13, "H")     # hair at the back
    f.rect(11, 9, 15, 13, "S")     # face in profile
    f.rect(15, 10, 15, 13, "s")
    cap(f, 11, 19)
    f.rect(12, 10, 12, 11, "o")    # eye
    return f.outline()


def to_image(frame, mirror=False):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            c = frame.px[y][31 - x if mirror else x]
            if c is not None:
                img.putpixel((x, y), (*PAL[c], 255))
    return img


def main(out):
    sheet = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    rows = [
        [frame_down(s) for s in range(3)],
        [frame_up(s) for s in range(3)],
        [frame_left(s) for s in range(3)],
    ]
    for r, frames in enumerate(rows):
        for c, frame in enumerate(frames):
            sheet.paste(to_image(frame), (c * 32, r * 32))
    for c, frame in enumerate(rows[2]):
        sheet.paste(to_image(frame, mirror=True), (c * 32, 96))
    sheet.save(out)
    print(f"player sheet -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
