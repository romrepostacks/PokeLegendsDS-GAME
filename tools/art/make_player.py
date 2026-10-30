# Draws the player's overworld sprite sheet: an original trainer in winter expedition
# gear (red parka with fur hood, green scarf, backpack, boots), in the Kaelmoor palette.
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
    f.rect(12, 24 + ly, 14, 27 + ly, "N")
    f.rect(17, 24 + ry, 19, 27 + ry, "N")
    f.rect(11, 28 + ly, 14, 29 + ly, "B")
    f.rect(11, 30 + ly, 14, 30 + ly, "b")
    f.rect(17, 28 + ry, 20, 29 + ry, "B")
    f.rect(17, 30 + ry, 20, 30 + ry, "b")


def body_front(f, step, back):
    # Parka, flared at the bottom, with a fur hem.
    f.rect(10, 15, 21, 24, "R")
    f.rect(9, 21, 22, 24, "R")
    f.rect(19, 16, 21, 24, "r")
    f.rect(9, 25, 22, 25, "W")
    f.rect(17, 25, 22, 25, "w")
    # Arms swing opposite to the lifted foot.
    la = 1 if step == 2 else 0
    ra = 1 if step == 1 else 0
    f.rect(7, 16 + la, 9, 21 + la, "R")
    f.rect(7, 22 + la, 9, 23 + la, "N")
    f.rect(22, 16 + ra, 24, 21 + ra, "r")
    f.rect(22, 22 + ra, 24, 23 + ra, "N")
    if back:
        f.rect(11, 16, 20, 23, "P")
        f.rect(11, 22, 20, 23, "p")
        f.rect(13, 18, 18, 19, "p")  # pocket
    else:
        f.rect(15, 16, 16, 24, "r")  # zip
        f.dot(13, 19, "r")
        f.dot(18, 19, "r")


def frame_down(step):
    f = Frame()
    legs_front(f, step)
    body_front(f, step, back=False)
    f.rect(10, 14, 21, 15, "G")  # scarf
    f.rect(18, 15, 20, 19, "G")
    f.rect(18, 19, 20, 19, "g")
    f.ellipse(8, 1, 23, 15, "R")  # hood
    f.ellipse(10, 3, 21, 14, "W")  # fur rim
    f.ellipse(18, 4, 21, 13, "w")
    f.ellipse(12, 5, 19, 13, "S")  # face
    f.rect(17, 7, 19, 12, "s")
    f.rect(12, 5, 19, 6, "H")      # fringe
    f.dot(13, 7, "H")
    f.rect(13, 9, 13, 10, "o")     # eyes
    f.rect(18, 9, 18, 10, "o")
    f.dot(15, 12, "s")
    return f.outline()


def frame_up(step):
    f = Frame()
    legs_front(f, step)
    body_front(f, step, back=True)
    f.ellipse(8, 1, 23, 15, "R")   # back of the hood
    f.ellipse(17, 2, 23, 14, "r")
    f.rect(11, 1, 20, 2, "W")      # fur showing over the top
    f.rect(10, 14, 21, 15, "G")    # scarf, tail down the back
    f.rect(15, 15, 16, 20, "G")
    f.rect(15, 20, 16, 21, "g")
    return f.outline()


def frame_left(step):
    f = Frame()
    # Legs: in a stride the front foot reaches left, the back foot trails right.
    if step == 0:
        f.rect(13, 24, 17, 27, "N")
        f.rect(12, 28, 17, 29, "B")
        f.rect(12, 30, 17, 30, "b")
    else:
        front, back = (9, 17) if step == 1 else (10, 16)
        f.rect(front + 2, 24, front + 4, 27, "N")
        f.rect(front, 28, front + 4, 29, "B")
        f.rect(front, 30, front + 4, 30, "b")
        f.rect(back, 24, back + 2, 26, "N")
        f.rect(back, 27, back + 3, 28, "B")
        f.rect(back, 29, back + 3, 29, "b")
    f.rect(11, 15, 20, 24, "R")    # parka
    f.rect(10, 21, 21, 24, "R")
    f.rect(10, 25, 21, 25, "W")
    f.rect(19, 16, 23, 23, "P")    # backpack
    f.rect(21, 16, 23, 23, "p")
    ax = {0: 14, 1: 12, 2: 16}[step]  # arm swings with the stride
    f.rect(ax, 16, ax + 2, 21, "r")
    f.rect(ax, 22, ax + 2, 23, "N")
    f.rect(11, 14, 19, 15, "G")    # scarf, end flying back
    f.rect(19, 14, 21, 16, "g")
    f.ellipse(9, 1, 22, 15, "R")   # hood
    f.ellipse(9, 4, 15, 14, "W")   # fur rim around the face
    f.ellipse(9, 5, 14, 13, "S")   # face in profile
    f.rect(10, 5, 15, 6, "H")
    f.rect(11, 9, 11, 10, "o")     # eye
    f.dot(9, 11, "s")              # nose
    f.ellipse(17, 3, 22, 14, "r")
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
