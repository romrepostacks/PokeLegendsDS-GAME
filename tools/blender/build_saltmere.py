# Builds Port Saltmere in Blender from maps/saltmere.h and exports it as an OBJ with UVs
# and vertex colours, ready for Nitro Engine's obj2dl.
#
#   blender -b --factory-startup --python tools/blender/build_saltmere.py -- OUT.obj OUT.blend
#
# Every face maps onto one 32x32 cell of art/textures/saltmere.png (tools/art/make_atlas.py),
# and its vertex colour tints that cell. One tile = 1 Blender unit. Blender X = column,
# -Y = row (north is +Y), Z = height. The model is centred on the origin, because DS
# vertices only reach +-8 units even after obj2dl's scaling (0.25 per tile, so up to 64 tiles).

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
    return t in (".", ",", ":", "r", "P")


def blocks(t):
    """Connected blocks of one tile type, as (r0, c0, r1, c1) bounding boxes."""
    seen, out = set(), []
    for r in range(H):
        for c in range(W):
            if rows[r][c] != t or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if tile(nr, nc) == t and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            rs, cs = [x[0] for x in cells], [x[1] for x in cells]
            out.append((min(rs), min(cs), max(rs), max(cs)))
    return out


def building(r0, c0, r1, c1, i):
    """One building over a rectangle of '#' tiles: walls, a door, one pitched roof."""
    w, d = c1 - c0 + 1, r1 - r0 + 1
    big = w * d >= 20
    tint = TINTS[i % len(TINTS)]
    wall_top = ROOF_Z + (FLOOR if big else 0)
    x0, x1, y0, y1 = c0, c1 + 1, -r1 - 1, -r0  # y0 is the south face
    door_c = (c0 + c1) // 2
    # South and north faces, one panel per tile; doors face south onto open ground.
    for c in range(c0, c1 + 1):
        for r, ya, yb, xa, xb in ((r1 + 1, y0, y0, c, c + 1), (r0 - 1, y1, y1, c + 1, c)):
            n = tile(r, c)
            if n is None or n == "#":
                continue
            ground_cell = DOOR if (r == r1 + 1 and c == door_c and walkable(n)) else WINDOW
            side(xa, ya, xb, yb, 0, FLOOR, ground_cell, tint)
            for z in range(1, int(wall_top) - 1):
                side(xa, ya, xb, yb, z, z + 1, WINDOW, tint)
            side(xa, ya, xb, yb, wall_top - 1, wall_top, EAVES, tint)
    for r in range(r0, r1 + 1):
        for c, xa, ya, yb in ((c0 - 1, x0, -r, -r - 1), (c1 + 1, x1, -r - 1, -r)):
            n = tile(r, c)
            if n is None or n == "#":
                continue
            side(xa, ya, xa, yb, 0, FLOOR, WINDOW, tint)
            for z in range(1, int(wall_top) - 1):
                side(xa, ya, xa, yb, z, z + 1, WINDOW, tint)
            side(xa, ya, xa, yb, wall_top - 1, wall_top, EAVES, tint)
    # Roof: the ridge runs along the long side, gables close the short ends.
    o = 0.15
    top = wall_top + RIDGE * (1.3 if big else 1.0)
    if w >= d:
        ym = (y0 + y1) / 2
        poly([(x0 - o, y0 - o, wall_top), (x1 + o, y0 - o, wall_top), (x1 + o, ym, top), (x0 - o, ym, top)], ROOF)
        poly([(x1 + o, y1 + o, wall_top), (x0 - o, y1 + o, wall_top), (x0 - o, ym, top), (x1 + o, ym, top)], ROOF)
        for x in (x0, x1):
            poly([(x, y0, wall_top), (x, y1, wall_top), (x, ym, top)], WALL, tint, [(0, 0), (1, 0), (0.5, 1)])
    else:
        xm = (x0 + x1) / 2
        poly([(x0 - o, y1 + o, wall_top), (x0 - o, y0 - o, wall_top), (xm, y0 - o, top), (xm, y1 + o, top)], ROOF)
        poly([(x1 + o, y0 - o, wall_top), (x1 + o, y1 + o, wall_top), (xm, y1 + o, top), (xm, y0 - o, top)], ROOF)
        for y in (y0, y1):
            poly([(x0, y, wall_top), (x1, y, wall_top), (xm, y, top)], WALL, tint, [(0, 0), (1, 0), (0.5, 1)])


def ring(cx, cy, rad, a):
    return cx + rad * math.cos(a), cy + rad * math.sin(a)


def band(cx, cy, z0, z1, rad0, rad1, cell, tint=WHITE, sides=8):
    """A ring of quads from radius rad0 at z0 to rad1 at z1 (a cylinder, cone or bowl)."""
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        (ax, ay), (bx, by) = ring(cx, cy, rad0, a0), ring(cx, cy, rad0, a1)
        (qx, qy), (dx, dy) = ring(cx, cy, rad1, a1), ring(cx, cy, rad1, a0)
        poly([(ax, ay, z0), (bx, by, z0), (qx, qy, z1), (dx, dy, z1)], cell, tint)


def disc(cx, cy, z, rad, cell, sides=8):
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        poly([(cx, cy, z), ring(cx, cy, rad, a0) + (z,), ring(cx, cy, rad, a1) + (z,)], cell, WHITE,
             [(0.5, 0.5), (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
              (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1))])


def cone(cx, cy, z0, z1, rad, cell, tint=WHITE, sides=8):
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        poly([ring(cx, cy, rad, a0) + (z0,), ring(cx, cy, rad, a1) + (z0,), (cx, cy, z1)], cell, tint,
             [(0, 0), (1, 0), (0.5, 1)])


def fountain(r0, c0, r1, c1):
    """Tiered fountain, frozen solid: stone basin, column, upper bowl, ice spray."""
    cx, cy = (c0 + c1 + 1) / 2, -(r0 + r1 + 1) / 2
    R = (c1 - c0 + 1) / 2 - 0.1
    stone = (0.92, 0.94, 1.0)
    band(cx, cy, 0.0, 0.45, R, R, QUAY, stone)            # basin wall
    band(cx, cy, 0.45, 0.45, R, R - 0.22, QUAY, stone)    # rim
    disc(cx, cy, 0.35, R - 0.22, ICE)                      # frozen pool
    band(cx, cy, 0.35, 1.5, 0.22, 0.18, QUAY, stone)      # column
    band(cx, cy, 1.2, 1.55, 0.25, 0.75, QUAY, stone)      # upper bowl
    disc(cx, cy, 1.55, 0.75, ICE)
    for i in range(8):                                     # icicles off the bowl
        a = 2 * math.pi * (i + 0.5) / 8
        (ax, ay), (bx, by) = ring(cx, cy, 0.76, a - 0.12), ring(cx, cy, 0.76, a + 0.12)
        mx, my = ring(cx, cy, 0.78, a)
        poly([(ax, ay, 1.55), (bx, by, 1.55), (mx, my, 0.95)], ICE, WHITE, [(0, 1), (1, 1), (0.5, 0)])
    band(cx, cy, 1.55, 2.0, 0.3, 0.12, ICE)               # frozen spray
    cone(cx, cy, 2.0, 2.45, 0.12, ICE)


def lighthouse(c, r):
    ground(c, r, 0.0, QUAY)
    cx, cy = c + 0.5, -r - 0.5
    band(cx, cy, 0.0, 0.35, 0.5, 0.5, QUAY)               # stone plinth
    poly([(cx - 0.5, cy - 0.5, 0.35), (cx + 0.5, cy - 0.5, 0.35), (cx + 0.5, cy + 0.5, 0.35),
          (cx - 0.5, cy + 0.5, 0.35)], SNOW)
    band(cx, cy, 0.35, 1.8, 0.44, 0.37, STRIPES)
    band(cx, cy, 1.8, 3.2, 0.37, 0.30, STRIPES)
    band(cx, cy, 3.2, 3.25, 0.30, 0.42, DARKWOOD)          # gallery
    band(cx, cy, 3.25, 3.8, 0.32, 0.32, LAMP)
    cone(cx, cy, 3.8, 4.35, 0.42, ROOF, (0.9, 0.5, 0.5))


def pine(c, r):
    """Four-sided pine with snow on top. Only trees at the edge of a wood get one; the
    ones behind them would be hidden, so they stay bare snow (saves polygons)."""
    if all(tile(r + dr, c + dc) in ("T", None) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return
    h = zlib.crc32(f"t{c},{r}".encode())
    cx, cy = c + 0.5 + (h % 7 - 3) * 0.03, -r - 0.5 + (h // 7 % 7 - 3) * 0.03
    s = 0.9 + (h % 5) * 0.06
    green = (0.30, 0.52, 0.42)
    for z0, rad in ((0.15, 0.6), (0.75, 0.45), (1.3, 0.32)):
        cone(cx, cy, z0 * s, (z0 + 0.75) * s, rad * s, SNOW, green, 4)
    cone(cx, cy, 1.8 * s, 2.15 * s, 0.12 * s, SNOW, WHITE, 4)  # snow cap


def boulder(c, r):
    h = zlib.crc32(f"b{c},{r}".encode())
    z = 0.5 + (h % 4) * 0.15
    box(c, r, WATER_Z if tile(r, c) == "R" and r >= 19 else 0.0, z, QUAY, SNOW, 0.04 + (h % 3) * 0.04,
        (0.85, 0.87, 0.92))


def lamp(c, r):
    cx, cy = c + 0.5, -r - 0.5
    iron = (0.35, 0.38, 0.45)
    band(cx, cy, 0.0, 1.3, 0.06, 0.05, DARKWOOD, iron, 4)
    band(cx, cy, 1.3, 1.55, 0.13, 0.13, LAMP, WHITE, 4)
    cone(cx, cy, 1.55, 1.75, 0.17, DARKWOOD, iron, 4)


for i, b in enumerate(blocks("#")):
    building(*b, i)
for b in blocks("f"):
    fountain(*b)

for r, row in enumerate(rows):
    for c, t in enumerate(row):
        if t == "~":
            ground(c, r, WATER_Z, WATER)
            continue
        if t == "#":
            continue
        if t == "L":
            lighthouse(c, r)
            continue
        dock = t == ","
        rock = t in "rR" or (t == "L")
        near = [tile(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        if dock:
            ground(c, r, 0.0, PLANK)
        elif rock:
            ground(c, r, 0.0, QUAY, (0.9, 0.92, 0.98))
        elif t in ":T" or "T" in near:
            ground(c, r, 0.0, SNOW)
        elif "#" in near:
            ground(c, r, 0.0, DUSTED)
        else:
            ground(c, r, 0.0, COBBLE)

        if t == "c":
            box(c, r, 0.0, 0.7, CRATE, CRATE, 0.12)
        elif t == "T":
            pine(c, r)
        elif t == "R":
            boulder(c, r)
        elif t == "i":
            lamp(c, r)

        # Edges over the water: quay wall for land, dark boards and posts for docks.
        x0, x1, y0, y1 = bounds(c, r)
        edge = DARKWOOD if dock else QUAY
        for n, a, b in ((tile(r + 1, c), (x0, y0), (x1, y0)),
                        (tile(r, c - 1), (x0, y1), (x0, y0)),
                        (tile(r, c + 1), (x1, y0), (x1, y1)),
                        (tile(r - 1, c), (x1, y1), (x0, y1))):
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
