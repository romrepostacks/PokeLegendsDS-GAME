# Draws the player's overworld sprites: an original trainer in winter expedition gear
# (green knit cap, red parka with fur collar, backpack, boots), in the Kaelmoor palette.
#
#   python tools/art/make_player.py art/sprites/player.png
#
# Sheet: 128x256, frames are 32x32, three columns per row.
#   Rows 0-3: walk  (down, up, left, right)   columns: stand, step 1, step 2
#   Rows 4-7: run   (down, up, left, right)   columns: passing, stride 1, stride 2
#   Rows 8-11: bike (down, up, left, right)   columns: coast, pedal 1, pedal 2
# Right is always the left row mirrored. 15 colours + transparent, so it converts to a
# 4bpp (16 colour) DS texture.

import sys

from PIL import Image

PAL = {
    "o": (24, 28, 48),     # outline, tyres
    "R": (196, 64, 56),    # parka
    "r": (140, 40, 40),    # parka shade
    "W": (238, 242, 246),  # fur
    "w": (180, 192, 208),  # fur shade
    "S": (244, 200, 160),  # skin
    "s": (214, 156, 120),  # skin shade
    "H": (80, 52, 40),     # hair
    "G": (64, 190, 140),   # cap, bike frame (aurora green)
    "g": (40, 130, 100),   # cap and frame shade
    "N": (44, 58, 92),     # trousers, mittens
    "B": (96, 62, 40),     # boots
    "b": (150, 160, 176),  # bike metal (bars, spokes)
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
                    self.rect(x, y, x, y, c)

    def ring(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if abs(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 - r) < 0.75:
                    self.rect(x, y, x, y, c)

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


# --- Parts -------------------------------------------------------------------------

def cap(f, x0, x1, dy=0):
    """Knit cap with a fold-up band and a white pompom."""
    f.ellipse(x0, 2 + dy, x1, 9 + dy, "G")
    f.rect(x0, 7 + dy, x1, 8 + dy, "g")
    m = (x0 + x1) // 2
    f.ellipse(m - 1, 0 + dy, m + 2, 2 + dy, "W")


def head_front(f, dy=0):
    f.rect(12, 9 + dy, 19, 13 + dy, "S")
    f.rect(18, 9 + dy, 19, 13 + dy, "s")
    f.rect(11, 9 + dy, 11, 12 + dy, "H")
    f.rect(20, 9 + dy, 20, 12 + dy, "H")
    cap(f, 11, 20, dy)
    f.rect(13, 10 + dy, 13, 11 + dy, "o")
    f.rect(17, 10 + dy, 17, 11 + dy, "o")


def head_back(f, dy=0):
    f.rect(11, 9 + dy, 20, 13 + dy, "H")
    cap(f, 11, 20, dy)


def head_side(f, dx=0, dy=0):
    f.rect(14 + dx, 9 + dy, 19 + dx, 13 + dy, "H")
    f.rect(11 + dx, 9 + dy, 15 + dx, 13 + dy, "S")
    f.rect(15 + dx, 10 + dy, 15 + dx, 13 + dy, "s")
    cap(f, 11 + dx, 19 + dx, dy)
    f.rect(12 + dx, 10 + dy, 12 + dx, 11 + dy, "o")


def torso_front(f, back, dy=0, bottom=22):
    f.rect(11, 15 + dy, 20, bottom + dy, "R")
    f.rect(18, 15 + dy, 20, bottom + dy, "r")
    f.rect(11, 16 + dy, 11, bottom - 1 + dy, "o")  # seams keep the arms readable
    f.rect(20, 16 + dy, 20, bottom - 1 + dy, "o")
    if back:
        f.rect(12, 15 + dy, 19, 21 + dy, "P")
        f.rect(17, 15 + dy, 19, 21 + dy, "p")
        f.rect(12, 15 + dy, 19, 16 + dy, "p")
        f.rect(11, 14 + dy, 20, 14 + dy, "W")
    else:
        f.rect(15, 16 + dy, 15, bottom + dy, "r")
        f.rect(12, 15 + dy, 12, 19 + dy, "P")
        f.rect(19, 15 + dy, 19, 19 + dy, "p")
        f.rect(11, 14 + dy, 20, 15 + dy, "W")
        f.rect(18, 14 + dy, 20, 15 + dy, "w")


def arm_front(f, side, top, bottom):
    """A sleeve on the left (side=-1) or right (+1) of the body, mitten at the bottom.
    Moving the bottom up or down is what makes the swing visible from the front."""
    x0 = 8 if side < 0 else 21
    lit, shade = ("R", "r") if side < 0 else ("r", "R")
    inner = x0 + 2 if side < 0 else x0
    f.rect(x0, top, x0 + 2, bottom - 2, lit)
    f.rect(inner, top + 1, inner, bottom - 2, shade)
    f.rect(x0, bottom - 1, x0 + 2, bottom, "N")


def legs_front(f, lift_l, lift_r, top=23):
    f.rect(12, top, 14, 28 - lift_l, "N")
    f.rect(17, top, 19, 28 - lift_r, "N")
    f.rect(12, 29 - lift_l, 14, 30 - lift_l, "B")
    f.rect(17, 29 - lift_r, 19, 30 - lift_r, "B")


def arm_side(f, x, top, bottom, bent=False):
    """Sleeve seen from the side, outlined so it reads over the parka."""
    if bent:  # forearm reaching forward (left), as in a run
        f.rect(x - 1, top - 1, x + 2, top + 4, "o")
        f.rect(x - 4, top + 2, x - 1, top + 5, "o")
        f.rect(x, top, x + 1, top + 3, "R")
        f.rect(x - 3, top + 3, x - 1, top + 4, "R")
        f.rect(x - 3, top + 3, x - 3, top + 4, "N")
        return
    f.rect(x - 1, top - 1, x + 2, bottom + 1, "o")
    f.rect(x, top, x + 1, bottom - 1, "R")
    f.rect(x + 1, top + 1, x + 1, bottom - 1, "r")
    f.rect(x, bottom, x + 1, bottom, "N")


def body_side(f, dx=0, dy=0, bottom=22):
    f.rect(18 + dx, 15 + dy, 21 + dx, 21 + dy, "P")
    f.rect(20 + dx, 15 + dy, 21 + dx, 21 + dy, "p")
    f.rect(12 + dx, 15 + dy, 18 + dx, bottom + dy, "R")
    f.rect(17 + dx, 15 + dy, 18 + dx, bottom + dy, "r")
    f.rect(12 + dx, 14 + dy, 18 + dx, 15 + dy, "W")


# --- Walk --------------------------------------------------------------------------

def walk_down(step, back=False):
    f = Frame()
    # Opposite arm and leg: the arm on the side of the lifted foot swings back (shorter
    # from the front), the other swings forward (longer).
    lift = {0: (0, 0), 1: (1, 0), 2: (0, 1)}[step]
    swing = {0: (0, 0), 1: (-2, 2), 2: (2, -2)}[step]
    legs_front(f, *lift)
    torso_front(f, back)
    arm_front(f, -1, 15, 22 + swing[0])
    arm_front(f, 1, 15, 22 + swing[1])
    (head_back if back else head_front)(f)
    return f.outline()


def walk_left(step):
    f = Frame()
    if step == 0:
        f.rect(14, 23, 17, 28, "N")
        f.rect(13, 29, 17, 30, "B")
    else:
        front, back = (11, 17) if step == 1 else (12, 16)
        f.rect(back, 23, back + 2, 27, "N")
        f.rect(back, 28, back + 3, 29, "B")
        f.rect(front + 1, 23, front + 3, 28, "N")
        f.rect(front, 29, front + 3, 30, "B")
    body_side(f)
    ax = {0: 14, 1: 11, 2: 17}[step]  # arm swings opposite the front leg
    arm_side(f, ax, 15, 22)
    head_side(f)
    return f.outline()


# --- Run: longer strides, a bob, arms bent and pumping ------------------------------

def run_down(step, back=False):
    f = Frame()
    dy = 0 if step == 0 else 1  # body dips on each stride
    lift = {0: (0, 0), 1: (3, 0), 2: (0, 3)}[step]
    legs_front(f, *lift, top=23 + dy)
    torso_front(f, back, dy)
    # Bent arms: the forward arm's mitten comes up to the chest, the other drops back.
    arms = {0: (21, 21), 1: (18, 23), 2: (23, 18)}[step]
    arm_front(f, -1, 15 + dy, arms[0] + dy)
    arm_front(f, 1, 15 + dy, arms[1] + dy)
    (head_back if back else head_front)(f, dy)
    return f.outline()


def run_left(step):
    f = Frame()
    dy = 0 if step == 0 else 1
    if step == 0:  # passing: one leg under the body, the other bent just behind it
        f.rect(16, 23, 18, 26, "N")
        f.rect(17, 26, 19, 27, "N")
        f.rect(17, 28, 20, 28, "B")
        f.rect(13, 23, 15, 28, "N")
        f.rect(12, 29, 15, 30, "B")
    else:
        # Stride: legs open at an angle, the back foot just off the ground. Kept well
        # short of horizontal so it reads as a jog, not a kick.
        f.rect(16, 23 + dy, 18, 25 + dy, "N")   # back thigh
        f.rect(17, 26, 19, 27, "N")             # back shin, angled down
        f.rect(18, 28, 21, 28, "B")
        f.rect(12, 23 + dy, 14, 27, "N")        # front leg reaching forward
        f.rect(11, 28, 13, 28, "N")
        f.rect(10, 29, 13, 30, "B")
    body_side(f, -1, dy)  # leaning into the run
    if step == 0:
        arm_side(f, 14, 15 + dy, 21 + dy)
    else:
        arm_side(f, 13 if step == 1 else 16, 15 + dy, 21 + dy, bent=step == 1)
    head_side(f, -1, dy)
    return f.outline()


# --- Bike: rider seated, pedals turning ---------------------------------------------

def bike_down(step, back=False):
    f = Frame()
    # Front wheel and fork (rear wheel from behind), handlebars across.
    f.rect(15, 22, 16, 31, "o")
    f.rect(15, 23, 16, 29, "b")
    f.rect(14, 18, 17, 22, "G")
    f.rect(16, 18, 17, 22, "g")
    # Legs on the pedals: one knee up, one down.
    knees = {0: (0, 0), 1: (2, 0), 2: (0, 2)}[step]
    for x, k in ((11, knees[0]), (18, knees[1])):
        f.rect(x, 21, x + 2, 27 - k, "N")
        f.rect(x, 28 - k, x + 2, 29 - k, "B")
    torso_front(f, back, -1, bottom=20)
    if not back:
        f.rect(8, 18, 23, 18, "b")  # handlebars in front of the body
    for x in (7, 22):  # arms out to the grips
        f.rect(x + 1, 14, x + 2, 16, "R" if x == 7 else "r")
        f.rect(x, 17, x + 2, 19, "N")
    (head_back if back else head_front)(f, -1)
    return f.outline()


def bike_left(step):
    f = Frame()
    f.ring(7, 25, 5, "o")    # front wheel (facing left)
    f.ring(24, 25, 5, "o")   # back wheel
    for cx in (7, 24):
        f.rect(cx, 21, cx, 29, "b")
        f.rect(cx - 4, 25, cx + 4, 25, "b")
    f.rect(8, 18, 9, 25, "G")       # fork
    f.rect(9, 23, 23, 24, "G")      # down tube
    f.rect(17, 19, 18, 24, "g")     # seat tube
    f.rect(16, 20, 20, 20, "o")     # saddle
    f.rect(7, 16, 10, 17, "b")      # handlebar
    # Pedals and leg: knee up on one beat, extended on the other.
    if step == 1:
        f.rect(13, 19, 17, 21, "N")
        f.rect(13, 22, 14, 25, "N")
        f.rect(12, 26, 15, 27, "B")
    elif step == 2:
        f.rect(15, 19, 18, 21, "N")
        f.rect(16, 22, 18, 27, "N")
        f.rect(16, 28, 19, 29, "B")
    else:
        f.rect(14, 19, 18, 21, "N")
        f.rect(14, 22, 16, 26, "N")
        f.rect(13, 27, 16, 28, "B")
    # Rider sitting tall, leaning a little over the bars.
    f.rect(19, 14, 22, 19, "P")
    f.rect(21, 14, 22, 19, "p")
    f.rect(14, 14, 20, 20, "R")
    f.rect(19, 14, 20, 20, "r")
    f.rect(14, 14, 19, 14, "W")
    f.rect(9, 15, 16, 18, "o")      # arm reaching to the bar
    f.rect(10, 16, 15, 17, "R")
    f.rect(8, 15, 11, 18, "o")
    f.rect(9, 16, 10, 17, "N")
    head_side(f, 1, 0)
    return f.outline()


# --- Sheet -------------------------------------------------------------------------

def to_image(frame, mirror=False):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            c = frame.px[y][31 - x if mirror else x]
            if c is not None:
                img.putpixel((x, y), (*PAL[c], 255))
    return img


def main(out):
    sheet = Image.new("RGBA", (128, 512), (0, 0, 0, 0))
    sets = [(walk_down, walk_left), (run_down, run_left), (bike_down, bike_left)]
    for i, (down, left) in enumerate(sets):
        rows = [
            [down(s) for s in range(3)],
            [down(s, back=True) for s in range(3)],
            [left(s) for s in range(3)],
        ]
        for r, frames in enumerate(rows):
            for c, frame in enumerate(frames):
                sheet.paste(to_image(frame), (c * 32, (i * 4 + r) * 32))
        for c, frame in enumerate(rows[2]):
            sheet.paste(to_image(frame, mirror=True), (c * 32, (i * 4 + 3) * 32))
    sheet.save(out)
    print(f"player sheet -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
