# Builds Port Saltmere in Blender from maps/saltmere.h and exports it as an OBJ with UVs
# and vertex colours, ready for Nitro Engine's obj2dl.
#
#   blender -b --factory-startup --python tools/blender/build_saltmere.py -- OUT.obj OUT.blend
#
# Every face maps onto one 32x32 cell of art/textures/saltmere.png (tools/art/make_atlas.py),
# and its vertex colour tints that cell. One tile = 1 Blender unit. Blender X = column,
# -Y = row (north is +Y), Z = height. The model is centred on the origin, because DS
# vertices only reach +-8 units even after obj2dl's scaling.

import math
import re
import sys
import zlib

import bpy

ROOT = __file__.rsplit("tools", 1)[0]
out_obj, out_blend = sys.argv[sys.argv.index("--") + 1:][:2]

with open(ROOT + "maps/saltmere.h") as f:
    rows = re.findall(r'^\s*"([^"]*)",', f.read(), re.M)
H, W = len(rows), len(rows[0])

# Atlas cells (see make_atlas.py)
COBBLE, DUSTED, SNOW, PLANK, WATER, WALL, WINDOW, DOOR = range(8)
ROOF, EAVES, STRIPES, LAMP, CRATE, DARKWOOD, QUAY, ICE = range(8, 16)

WATER_Z = -0.4
FLOOR = 1.0          # storey height
ROOF_Z = 2.0         # walls go up two storeys
RIDGE = 0.9          # roof height above the walls
WHITE = (1.0, 1.0, 1.0)
# Pastel house colours: pale blue, cream, pale green, rose
TINTS = [(0.78, 0.88, 1.0), (1.0, 0.94, 0.80), (0.82, 1.0, 0.90), (1.0, 0.84, 0.82)]

verts, faces, uvs, colors = [], [], [], []


def cell_uv(cell, u, v):
    """(u, v) in 0-1 inside a cell -> atlas UV, inset half a texel so cells don't bleed."""
    cx, cy = cell % 4, cell // 4
    x = cx * 32 + 0.5 + u * 31
    y = cy * 32 + 0.5 + (1 - v) * 31
    return (x / 128, 1 - y / 128)


def poly(corners, cell, tint=WHITE, corner_uv=None):
    """A quad or triangle with its own vertices, so faces keep their own UVs and tint."""
    if corner_uv is None:
        corner_uv = [(0, 0), (1, 0), (1, 1), (0, 1)][:len(corners)]
    base = len(verts)
    verts.extend((x - W / 2, y + H / 2, z) for x, y, z in corners)
    faces.append(tuple(range(base, base + len(corners))))
    uvs.extend(cell_uv(cell, u, v) for u, v in corner_uv)
    colors.extend([tint] * len(corners))


def tile(r, c):
    if 0 <= r < H and 0 <= c < W:
        return rows[r][c]
    return None


def bounds(c, r, inset=0.0):
    return c + inset, c + 1 - inset, -r - 1 + inset, -r - inset  # x0, x1, y0 (south), y1 (north)


def ground(c, r, z, cell, tint=WHITE):
    x0, x1, y0, y1 = bounds(c, r)
    poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], cell, tint)


def side(x0, y0, x1, y1, z0, z1, cell, tint=WHITE):
    """A vertical face from (x0, y0) to (x1, y1), seen from its right-hand side."""
    poly([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], cell, tint)


def box(c, r, z0, z1, cell_side, cell_top, inset, tint=WHITE):
    x0, x1, y0, y1 = bounds(c, r, inset)
    side(x0, y0, x1, y0, z0, z1, cell_side, tint)
    side(x1, y1, x0, y1, z0, z1, cell_side, tint)
    side(x0, y1, x0, y0, z0, z1, cell_side, tint)
    side(x1, y0, x1, y1, z0, z1, cell_side, tint)
    poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], cell_top, tint)


def walkable(t):
    return t in (".", ",", "P")


def house(c, r):
    tint = TINTS[(c // 3 + r) % len(TINTS)]
    x0, x1, y0, y1 = bounds(c, r)
    h = zlib.crc32(f"{c},{r}".encode())
    # Walls, only where they face open ground (the rest is hidden by other houses).
    for dc, dr, a, b in ((0, 1, (x0, y0), (x1, y0)), (0, -1, (x1, y1), (x0, y1)),
                         (-1, 0, (x0, y1), (x0, y0)), (1, 0, (x1, y0), (x1, y1))):
        n = tile(r + dr, c + dc)
        if n is None or n == "#":
            continue
        ground_cell = DOOR if (dr == 1 and h % 4 == 0) else WINDOW
        side(*a, *b, 0, FLOOR, ground_cell if walkable(n) else WALL, tint)
        side(*a, *b, FLOOR, ROOF_Z, EAVES, tint)
    # Pitched roof: the ridge runs along the row of houses, gables close the ends.
    ew = tile(r, c - 1) == "#" or tile(r, c + 1) == "#"
    top = ROOF_Z + RIDGE
    o = 0.12  # overhang
    if ew:
        ym = (y0 + y1) / 2
        poly([(x0, y0 - o, ROOF_Z), (x1, y0 - o, ROOF_Z), (x1, ym, top), (x0, ym, top)], ROOF)
        poly([(x1, y1 + o, ROOF_Z), (x0, y1 + o, ROOF_Z), (x0, ym, top), (x1, ym, top)], ROOF)
        for x, n in ((x0, tile(r, c - 1)), (x1, tile(r, c + 1))):
            if n != "#":
                poly([(x, y0, ROOF_Z), (x, y1, ROOF_Z), (x, ym, top)], WALL, tint,
                     [(0, 0), (1, 0), (0.5, 1)])
    else:
        xm = (x0 + x1) / 2
        poly([(x0 - o, y1, ROOF_Z), (x0 - o, y0, ROOF_Z), (xm, y0, top), (xm, y1, top)], ROOF)
        poly([(x1 + o, y0, ROOF_Z), (x1 + o, y1, ROOF_Z), (xm, y1, top), (xm, y0, top)], ROOF)
        for y, n in ((y0, tile(r + 1, c)), (y1, tile(r - 1, c))):
            if n != "#":
                poly([(x0, y, ROOF_Z), (x1, y, ROOF_Z), (xm, y, top)], WALL, tint,
                     [(0, 0), (1, 0), (0.5, 1)])


def lighthouse(c, r):
    ground(c, r, 0.0, PLANK)
    cx, cy = c + 0.5, -r - 0.5
    sides = 8

    def ring(rad, a):
        return cx + rad * math.cos(a), cy + rad * math.sin(a)

    def band(z0, z1, rad0, rad1, cell):
        for i in range(sides):
            a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
            (ax, ay), (bx, by) = ring(rad0, a0), ring(rad0, a1)
            (cx1, cy1), (dx, dy) = ring(rad1, a1), ring(rad1, a0)
            poly([(ax, ay, z0), (bx, by, z0), (cx1, cy1, z1), (dx, dy, z1)], cell)

    band(0.0, 1.2, 0.42, 0.36, STRIPES)
    band(1.2, 2.4, 0.36, 0.30, STRIPES)
    band(2.4, 2.9, 0.34, 0.34, LAMP)
    for i in range(sides):  # cone roof
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        (ax, ay), (bx, by) = ring(0.42, a0), ring(0.42, a1)
        poly([(ax, ay, 2.9), (bx, by, 2.9), (cx, cy, 3.4)], ROOF, (0.9, 0.5, 0.5),
             [(0, 0), (1, 0), (0.5, 1)])


for r, row in enumerate(rows):
    for c, t in enumerate(row):
        if t == "~":
            ground(c, r, WATER_Z, WATER)
            continue
        if t == "#":
            house(c, r)
            continue
        if t == "L":
            lighthouse(c, r)
            continue

        dock = t == "," or r >= 10
        if dock:
            ground(c, r, 0.0, PLANK)
        else:
            # Snow piles up against the houses and the edge of the map.
            near = [tile(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
            if "#" in near or None in near:
                ground(c, r, 0.0, SNOW if "#" in near[:3] else DUSTED)
            else:
                ground(c, r, 0.0, COBBLE)

        if t == "c":
            box(c, r, 0.0, 0.7, CRATE, CRATE, 0.12)
        elif t == "f":
            box(c, r, 0.0, 0.35, QUAY, ICE, 0.04)

        # Edges over the water: quay wall for the plaza, dark boards and posts for docks.
        x0, x1, y0, y1 = bounds(c, r)
        edge = DARKWOOD if dock else QUAY
        for n, a, b in ((tile(r + 1, c), (x0, y0), (x1, y0)),
                        (tile(r, c - 1), (x0, y1), (x0, y0)),
                        (tile(r, c + 1), (x1, y0), (x1, y1))):
            if n == "~":
                side(*a, *b, WATER_Z, 0.0, edge)
        if dock:
            for px, side_tile in ((x0, tile(r, c - 1)), (x1 - 0.14, tile(r, c + 1))):
                if side_tile == "~" and r % 2 == 1:
                    post_c = (px - 0.03, y0 - 0.03)
                    for (ax, ay), (bx, by) in (((0, 0), (0.2, 0)), ((0.2, 0), (0.2, 0.2)),
                                               ((0.2, 0.2), (0, 0.2)), ((0, 0.2), (0, 0))):
                        side(post_c[0] + ax, post_c[1] + ay, post_c[0] + bx, post_c[1] + by,
                             WATER_Z - 0.2, 0.25, DARKWOOD)
                    poly([(post_c[0], post_c[1], 0.25), (post_c[0] + 0.2, post_c[1], 0.25),
                          (post_c[0] + 0.2, post_c[1] + 0.2, 0.25), (post_c[0], post_c[1] + 0.2, 0.25)],
                         SNOW)

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("Saltmere")
mesh.from_pydata(verts, [], faces)
uv_layer = mesh.uv_layers.new(name="UV")
for loop in mesh.loops:
    uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
attr = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
for i, col in enumerate(colors):
    attr.data[i].color_srgb = (*col, 1.0)
obj = bpy.data.objects.new("Saltmere", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.wm.save_as_mainfile(filepath=out_blend)
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_colors=True,
                      export_normals=False, export_uv=True, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y")
quads = sum(1 for f in faces if len(f) == 4)
print(f"Saltmere: {quads} quads, {len(faces) - quads} triangles -> {out_obj}")
