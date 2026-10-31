# Builds character previews from Universal LPC Spritesheet layers, keeping LPC's own layer
# order and credits. The LPC tree stays outside this repo.
#
#   python tools/art/lpc_compose.py LPC_DIR OUT_DIR CREDITS.md
#
# LPC sheets are 64x64 per frame. walk has 9 frames and run has 8, each with rows up, left,
# down, right. A layer is either anim.png (recoloured here) or anim/colour.png.

import colorsys
import csv
import glob
import json
import os
import sys

from PIL import Image

lpc, out_dir, credits_path = sys.argv[1:4]

SKIN = (246, 200, 160)
NAVY = (44, 56, 110)
BROWN = (110, 70, 44)
DARK = (50, 50, 66)

# Each entry: definition file name, colour.
LOOKS = {
    "boy-1-climber": ("male", "heads_human_male", [
        ("hair_spiked", (92, 62, 44)), ("torso_clothes_longsleeve2_buttoned", (214, 74, 52)),
        ("legs_cuffed", (150, 118, 80)), ("feet_boots_fold", BROWN)]),
    "boy-2-guide": ("male", "heads_human_male", [
        ("hair_messy1", (232, 196, 100)), ("torso_clothes_longsleeve2", (78, 130, 90)),
        ("hat_hood_cloth", (60, 100, 76)), ("legs_cuffed", NAVY), ("feet_boots_rim", BROWN)]),
    "boy-3-sailor": ("male", "heads_human_male", [
        ("hair_bedhead", (46, 46, 70)), ("torso_clothes_longsleeve2_cardigan", (56, 90, 160)),
        ("neck_scarf", (226, 216, 190)), ("hat_cap_leather", (56, 90, 160)),
        ("legs_formal", DARK), ("feet_boots_basic", BROWN)]),
    "girl-1-guide": ("female", "heads_human_female", [
        ("hair_wavy", (240, 206, 110)), ("torso_clothes_longsleeve2", (40, 150, 150)),
        ("neck_scarf", (146, 160, 96)), ("legs_leggings", DARK), ("feet_boots_fold", BROWN)]),
    "girl-2-researcher": ("female", "heads_human_female", [
        ("hair_high_ponytail", (190, 88, 50)), ("torso_clothes_longsleeve2_buttoned", (236, 240, 232)),
        ("belt_leather", (70, 150, 96)), ("legs_leggings", DARK), ("feet_boots_rim", (70, 120, 80))]),
    "girl-3-sailor": ("female", "heads_human_female", [
        ("hair_bob", (190, 96, 56)), ("torso_clothes_longsleeve2_cardigan", NAVY),
        ("hat_cap_leather", (206, 58, 76)), ("legs_leggings", DARK), ("feet_boots_fold", BROWN)]),
}


def definition(name):
    found = glob.glob(f"{lpc}/sheet_definitions/**/{name}.json", recursive=True)
    if not found:
        raise SystemExit(f"no definition {name}")
    with open(found[0], encoding="utf8") as f:
        return json.load(f)


def csv_credits(path):
    """Credits for a folder, from LPC's CREDITS.csv."""
    out = {}
    with open(f"{lpc}/CREDITS.csv", encoding="utf8", newline="") as f:
        for row in csv.DictReader(f, skipinitialspace=True):
            if row["filename"].startswith(path):
                key = (row["authors"], row["licenses"])
                out.setdefault(key, row["urls"])
    return [{"file": path, "authors": a.split(","), "licenses": l.split(","), "urls": u.split(",")}
            for (a, l), u in out.items()]


def recolour(img, colour):
    """Maps the layer's shades, darkest to lightest, onto a ramp of the chosen colour."""
    px = img.load()
    shades = sorted({px[x, y][:3] for y in range(img.height) for x in range(img.width)
                     if px[x, y][3] > 0}, key=lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
    if not shades:
        return img
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in colour))
    ramp = {}
    for i, shade in enumerate(shades):
        t = i / max(1, len(shades) - 1)
        val = min(1.0, v * (0.5 + 0.65 * t))
        ramp[shade] = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s * (1.05 - 0.2 * t), val))
    out = img.copy()
    o = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a > 0:
                o[x, y] = (*ramp[(r, g, b)], a)
    return out


def load_layer(path, anim, colour, variants):
    base = f"{lpc}/spritesheets/{path}"
    if os.path.isfile(f"{base}{anim}.png"):
        return recolour(Image.open(f"{base}{anim}.png").convert("RGBA"), colour)
    if os.path.isdir(f"{base}{anim}"):
        name = variants[0].replace(" ", "_") if variants else "white"
        for pick in ("white", name):
            if os.path.isfile(f"{base}{anim}/{pick}.png"):
                return recolour(Image.open(f"{base}{anim}/{pick}.png").convert("RGBA"), colour)
    return None


def compose(body, parts, anim, used):
    layers = []
    for name, colour in parts:
        if name.startswith("path:"):    # a folder with no definition of its own: eyes
            path = name[5:]
            img = load_layer(path, anim, colour, [])
            if img is not None:
                layers.append((105, img))
            used[name] = {"name": path, "credits": csv_credits(path)}
            continue
        d = definition(name)
        got = False
        for key in sorted(k for k in d if k.startswith("layer_")):
            path = d[key].get(body)
            if not path:
                continue
            img = load_layer(path, anim, colour, d.get("variants", []))
            if img is not None:
                layers.append((d[key].get("zPos", 0), img))
                got = True
        if not got:
            print(f"  {name}: no {anim} art for {body}")
        used[name] = d
    size = max(i.size for _, i in layers)
    sheet = Image.new("RGBA", size, (0, 0, 0, 0))
    for _, img in sorted(layers, key=lambda x: x[0]):
        sheet.alpha_composite(img)
    return sheet


GREY = (200, 208, 220, 255)


def frames(sheet, row, count):
    return [sheet.crop((i * 64, row * 64, (i + 1) * 64, (row + 1) * 64)) for i in range(count)]


def strip(images):
    out = Image.new("RGBA", (64 * len(images), 64), GREY)
    for i, img in enumerate(images):
        out.alpha_composite(img, (i * 64, 0))
    return out


os.makedirs(out_dir, exist_ok=True)
used = {}
rows = []
for name, (body, head, parts) in LOOKS.items():
    full = [("body", SKIN), (head, SKIN), ("path:eyes/human/adult/default/", (70, 110, 170))] + parts
    walk = compose(body, full, "walk", used)
    run = compose(body, full, "run", used)
    stills = [frames(walk, 2, 1)[0], frames(walk, 0, 1)[0], frames(walk, 1, 1)[0]]
    line = strip(stills + frames(walk, 1, 9)[1:9:2] + frames(run, 1, 8)[0:8:2])
    colours = len(line.convert("RGB").getcolors(1 << 20))
    print(f"{name}: {colours} colours in the preview strip")
    line.save(f"{out_dir}/{name}.png")
    line.resize((line.width * 4, line.height * 4), Image.NEAREST).save(f"{out_dir}/{name}-x4.png")
    walk.save(f"{out_dir}/{name}-walk-sheet.png")
    run.save(f"{out_dir}/{name}-run-sheet.png")
    rows.append(line)

board = Image.new("RGBA", (rows[0].width, 66 * len(rows)), (255, 255, 255, 255))
for i, row in enumerate(rows):
    board.paste(row, (0, i * 66))
board.save(f"{out_dir}/overview.png")
board.resize((board.width * 2, board.height * 2), Image.NEAREST).save(f"{out_dir}/overview-x2.png")

licences = set()
with open(credits_path, "w", encoding="utf8") as f:
    f.write("# Credits\n\nCharacter art built from the Universal LPC Spritesheet Character Generator "
            "(https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator).\n"
            "Layers below are credited as that project lists them. A layer offered under several "
            "licences lists each one.\n\n")
    for name in sorted(used):
        d = used[name]
        f.write(f"## {d.get('name', name)} (`{name}`)\n\n")
        for c in d.get("credits", []):
            licences.update(c.get("licenses", []))
            f.write(f"- `{c.get('file', '')}`: {', '.join(c.get('authors', []))}. "
                    f"Licences: {', '.join(c.get('licenses', []))}.")
            if c.get("urls"):
                f.write(f" Source: {' '.join(c['urls'])}")
            f.write("\n")
        f.write("\n")
print("licences:", ", ".join(sorted(licences)))
