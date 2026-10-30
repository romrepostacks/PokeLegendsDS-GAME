# Builds the Port Saltmere block-out in Blender from maps/saltmere.h and exports it as
# an OBJ with vertex colors, ready for Nitro Engine's obj2dl.
#
#   blender -b --factory-startup --python tools/blender/build_saltmere.py -- OUT.obj OUT.blend
#
# One tile = 1 Blender unit. Blender X = column, -Y = row (north is +Y), Z = height.

import re
import sys

import bpy

ROOT = __file__.rsplit("tools", 1)[0]
out_obj, out_blend = sys.argv[sys.argv.index("--") + 1:][:2]

with open(ROOT + "maps/saltmere.h") as f:
    rows = re.findall(r'^\s*"([^"]*)",', f.read(), re.M)

SALTMERE_H = len(rows)
SALTMERE_W = len(rows[0])
WATER_Z = -0.4

# Block-out colours (0-1 RGB), in the Kaelmoor palette: pale stone, cold water.
STONE = (0.78, 0.80, 0.84)
STONE_DARK = (0.66, 0.69, 0.74)
PLANK = (0.55, 0.40, 0.27)
WATER = (0.22, 0.42, 0.62)
QUAY = (0.50, 0.53, 0.58)
CRATE = (0.62, 0.46, 0.28)
FOUNTAIN = (0.70, 0.74, 0.80)
FOUNTAIN_TOP = (0.45, 0.70, 0.90)
BUILDINGS = [(0.36, 0.45, 0.60), (0.55, 0.36, 0.33), (0.40, 0.52, 0.47), (0.60, 0.58, 0.50)]
ROOF = (0.25, 0.28, 0.36)

verts, faces, colors = [], [], []


def quad(corners, color):
    """Adds one quad with its own 4 vertices, so each face keeps a flat colour."""
    base = len(verts)
    # Centre the map on the origin: DS vertices only reach +-8 units even after scaling.
    verts.extend((x - SALTMERE_W / 2, y + SALTMERE_H / 2, z) for x, y, z in corners)
    colors.extend([color] * 4)
    faces.append((base, base + 1, base + 2, base + 3))


def top(x, y, z, color, inset=0.0):
    x0, x1 = x + inset, x + 1 - inset
    y0, y1 = -y - 1 + inset, -y - inset
    quad([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], color)


def box(x, y, z0, z1, side, roof, inset=0.0):
    x0, x1 = x + inset, x + 1 - inset
    y0, y1 = -y - 1 + inset, -y - inset
    quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], side)  # south
    quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], side)  # north
    quad([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], side)  # west
    quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side)  # east
    top(x, y, z1, roof, inset)


def tile(r, c):
    if 0 <= r < len(rows) and 0 <= c < len(rows[r]):
        return rows[r][c]
    return "~"


for r, row in enumerate(rows):
    for c, t in enumerate(row):
        if t == "~":
            top(c, r, WATER_Z, WATER)
            continue

        dock = r >= 10
        ground = PLANK if dock or t == "," else (STONE if (r + c) % 2 else STONE_DARK)
        if t == "#":
            colour = BUILDINGS[(c // 3 + r) % len(BUILDINGS)]
            box(c, r, 0.0, 2.5, colour, ROOF)
            continue
        top(c, r, 0.0, ground)
        if t == "c":
            box(c, r, 0.0, 0.8, CRATE, CRATE, inset=0.1)
        elif t == "f":
            box(c, r, 0.0, 0.5, FOUNTAIN, FOUNTAIN_TOP, inset=0.05)

        # Quay and dock edges: a face down to the water on sides that border water.
        x0, x1, y0, y1 = c, c + 1, -r - 1, -r
        edge = PLANK if dock else QUAY
        if tile(r + 1, c) == "~":
            quad([(x0, y0, WATER_Z), (x1, y0, WATER_Z), (x1, y0, 0), (x0, y0, 0)], edge)
        if tile(r, c - 1) == "~":
            quad([(x0, y1, WATER_Z), (x0, y0, WATER_Z), (x0, y0, 0), (x0, y1, 0)], edge)
        if tile(r, c + 1) == "~":
            quad([(x1, y0, WATER_Z), (x1, y1, WATER_Z), (x1, y1, 0), (x1, y0, 0)], edge)

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("Saltmere")
mesh.from_pydata(verts, [], faces)
attr = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
for i, col in enumerate(colors):
    attr.data[i].color_srgb = (*col, 1.0)
obj = bpy.data.objects.new("Saltmere", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.wm.save_as_mainfile(filepath=out_blend)
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_colors=True,
                      export_normals=False, export_uv=False, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y")
print(f"Saltmere: {len(faces)} quads -> {out_obj}")
