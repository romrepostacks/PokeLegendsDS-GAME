# The 30 colours offered for each outfit part: 12 hues in a strong and a soft version,
# plus 6 neutrals. Each option is (base, shade), the two palette entries it replaces.

import colorsys

NEUTRALS = [(238, 240, 244), (168, 174, 186), (92, 96, 108), (44, 46, 58), (120, 84, 60), (196, 170, 130)]


def option(rgb):
    return tuple(rgb), tuple(int(v * 0.7) for v in rgb)


def colours():
    out = []
    for i in range(12):
        hue = i / 12
        for sat, val in ((0.72, 0.85), (0.38, 0.95)):
            rgb = colorsys.hsv_to_rgb(hue, sat, val)
            out.append(option(tuple(int(v * 255) for v in rgb)))
    out.extend(option(c) for c in NEUTRALS)
    return out


COLOURS = colours()
assert len(COLOURS) == 30
