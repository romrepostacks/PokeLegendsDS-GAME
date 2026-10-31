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


COLOURS = [c[0] for c in colours()]
assert len(COLOURS) == 30

# Skin tones, light to deep.
SKINS = [(252, 216, 184), (246, 200, 160), (232, 180, 136), (214, 156, 110),
         (186, 128, 86), (150, 100, 66), (116, 74, 50), (82, 52, 38)]

# Eye colours: blue, green, brown, hazel, grey, violet, amber, black.
EYES = [(70, 110, 170), (70, 140, 90), (96, 60, 36), (130, 110, 50), (120, 126, 136),
        (120, 80, 170), (200, 140, 40), (36, 32, 40)]

# 30 hair colours: 14 natural shades, then 16 bright ones.
HAIR_COLOURS = [(30, 28, 36), (52, 40, 40), (80, 52, 40), (112, 70, 44), (140, 92, 54), (168, 116, 66),
                (196, 146, 84), (222, 180, 110), (240, 210, 140), (248, 232, 180), (170, 80, 48),
                (200, 100, 56), (150, 150, 156), (220, 220, 226),
                (232, 96, 96), (232, 130, 170), (240, 170, 200), (190, 110, 220), (130, 90, 200),
                (80, 90, 200), (70, 140, 230), (110, 190, 240), (60, 180, 180), (70, 180, 120),
                (140, 200, 90), (230, 220, 90), (240, 170, 70), (230, 120, 50), (120, 60, 90), (40, 80, 90)]
assert len(HAIR_COLOURS) == 30
