# Builds Port Saltmere in Blender from maps/saltmere.h and exports one OBJ per 8x8-tile
# chunk (UVs and vertex colours), ready for Nitro Engine's obj2dl. The game only draws the
# chunks near the camera, because the DS can't take the whole town in one frame.
#
#   blender -b --factory-startup --python tools/blender/build_saltmere.py -- OUT_DIR OUT.blend
#
# Every face maps onto one 32x32 cell of art/textures/saltmere.png (tools/art/make_atlas.py),
# and its vertex colour tints that cell. One tile = 1 Blender unit. Blender X = column,
# -Y = row (north is +Y), Z = height. The model is centred on the origin, because DS
# vertices only reach +-8 units even after obj2dl's scaling.

import math
import os
import re
import sys
import zlib

import bpy

ROOT = __file__.rsplit("tools", 1)[0]
out_dir, out_blend = sys.argv[sys.argv.index("--") + 1:][:2]

with open(ROOT + "maps/saltmere.h") as f:
    rows = re.findall(r'^\s*"([^"]*)",', f.read(), re.M)
H, W = len(rows), len(rows[0])
CHUNK = 8

# Atlas cells (see make_atlas.py)
COBBLE, DUSTED, SNOW, PLANK, WATER, WALL, WINDOW, DOOR = range(8)
ROOF, EAVES, STRIPES, LAMP, CRATE, DARKWOOD, QUAY, ICE = range(8, 16)

WATER_Z = -0.4
FLOOR = 1.0          # storey height
ROOF_Z = 2.0         # walls go up two storeys
WHITE = (1.0, 1.0, 1.0)
ROCK = (0.72, 0.74, 0.80)
# Pastel house colours: pale blue, cream, pale green, rose
TINTS = [(0.78, 0.88, 1.0), (1.0, 0.94, 0.80), (0.82, 1.0, 0.90), (1.0, 0.84, 0.82)]

chunks = {}          # (cx, cy) -> {"verts", "faces", "uvs", "colors"}
current = (0, 0)


def use_chunk(c, r):
    global current
    current = (int(c) // CHUNK, int(r) // CHUNK)


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
    m = chunks.setdefault(current, {"verts": [], "faces": [], "uvs": [], "colors": []})
    base = len(m["verts"])
    m["verts"].extend((x - W / 2, y + H / 2, z) for x, y, z in corners)
    m["faces"].append(tuple(range(base, base + len(corners))))
    m["uvs"].extend(cell_uv(cell, u, v) for u, v in corner_uv)
    m["colors"].extend([tint] * len(corners))


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


def ring_point(cx, cy, rad, i, sides):
    a = 2 * math.pi * i / sides
    return cx + rad * math.cos(a), cy + rad * math.sin(a)


def cone(cx, cy, z0, z1, rad0, rad1, cell, sides=8, tint=WHITE):
    """One band of a round shape: radius rad0 at z0 narrowing to rad1 at z1."""
    for i in range(sides):
        a, b = ring_point(cx, cy, rad0, i, sides), ring_point(cx, cy, rad0, i + 1, sides)
        c, d = ring_point(cx, cy, rad1, i + 1, sides), ring_point(cx, cy, rad1, i, sides)
        if rad1 == 0:
            poly([(*a, z0), (*b, z0), (cx, cy, z1)], cell, tint, [(0, 0), (1, 0), (0.5, 1)])
        else:
            poly([(*a, z0), (*b, z0), (*c, z1), (*d, z1)], cell, tint)


def disc(cx, cy, z, rad, cell, sides=8, tint=WHITE):
    """Flat round top, a fan of triangles. UVs map the circle into the cell."""
    for i in range(sides):
        a, b = ring_point(cx, cy, rad, i, sides), ring_point(cx, cy, rad, i + 1, sides)
        uv = [((p[0] - cx) / (2 * rad) + 0.5, (p[1] - cy) / (2 * rad) + 0.5) for p in (a, b)]
        poly([(*a, z), (*b, z), (cx, cy, z)], cell, tint, [*uv, (0.5, 0.5)])


def washer(cx, cy, z, inner, outer, cell, sides=8):
    """Flat ring, for the fountain's rim."""
    for i in range(sides):
        a, b = ring_point(cx, cy, outer, i, sides), ring_point(cx, cy, outer, i + 1, sides)
        c, d = ring_point(cx, cy, inner, i + 1, sides), ring_point(cx, cy, inner, i, sides)
        poly([(*a, z), (*b, z), (*c, z), (*d, z)], cell)


def blocks(kind):
    """Finds the solid rectangles of tile `kind`: (column, row, width, height)."""
    seen = set()
    for r, row in enumerate(rows):
        for c, t in enumerate(row):
            if t != kind or (c, r) in seen:
                continue
            w = 1
            while tile(r, c + w) == kind:
                w += 1
            h = 1
            while tile(r + h, c) == kind:
                h += 1
            seen.update((c + x, r + y) for x in range(w) for y in range(h))
            yield c, r, w, h


def house(c0, r0, w, h):
    """One detached house: walls, windows, a door in the street side, and a pitched roof."""
    tint = TINTS[zlib.crc32(f"{c0},{r0}".encode()) % len(TINTS)]
    use_chunk(c0 + w / 2, r0 + h / 2)
    x0, x1, y1, y0 = c0, c0 + w, -r0, -r0 - h
    door = c0 + w // 2
    for c in range(c0, c0 + w):                        # south and north fronts
        side(c, y0, c + 1, y0, 0, FLOOR, DOOR if c == door else WINDOW, tint)
        side(c, y0, c + 1, y0, FLOOR, ROOF_Z, EAVES, tint)
        side(c + 1, y1, c, y1, 0, FLOOR, WINDOW, tint)
        side(c + 1, y1, c, y1, FLOOR, ROOF_Z, EAVES, tint)
    for r in range(r0, r0 + h):                        # west and east ends
        side(x0, -r, x0, -r - 1, 0, FLOOR, WINDOW, tint)
        side(x0, -r, x0, -r - 1, FLOOR, ROOF_Z, EAVES, tint)
        side(x1, -r - 1, x1, -r, 0, FLOOR, WINDOW, tint)
        side(x1, -r - 1, x1, -r, FLOOR, ROOF_Z, EAVES, tint)

    # The ridge runs along the long side; gables close the short ends.
    o = 0.2                                            # overhang
    top = ROOF_Z + min(w, h) * 0.32
    if w >= h:
        ym = (y0 + y1) / 2
        for c in range(c0, c0 + w):
            a, b = c - (o if c == c0 else 0), c + 1 + (o if c == c0 + w - 1 else 0)
            poly([(a, y0 - o, ROOF_Z), (b, y0 - o, ROOF_Z), (b, ym, top), (a, ym, top)], ROOF)
            poly([(b, y1 + o, ROOF_Z), (a, y1 + o, ROOF_Z), (a, ym, top), (b, ym, top)], ROOF)
        for x in (x0, x1):
            poly([(x, y0, ROOF_Z), (x, y1, ROOF_Z), (x, ym, top)], WALL, tint,
                 [(0, 0), (1, 0), (0.5, 1)])
    else:
        xm = (x0 + x1) / 2
        for r in range(r0, r0 + h):
            a, b = -r + (o if r == r0 else 0), -r - 1 - (o if r == r0 + h - 1 else 0)
            poly([(x0 - o, a, ROOF_Z), (x0 - o, b, ROOF_Z), (xm, b, top), (xm, a, top)], ROOF)
            poly([(x1 + o, b, ROOF_Z), (x1 + o, a, ROOF_Z), (xm, a, top), (xm, b, top)], ROOF)
        for y in (y0, y1):
            poly([(x0, y, ROOF_Z), (x1, y, ROOF_Z), (xm, y, top)], WALL, tint,
                 [(0, 0), (1, 0), (0.5, 1)])


def fountain(c0, r0, w, h):
    """Round stone basin with a rim and water, a pedestal, and a smaller bowl on top."""
    use_chunk(c0 + w / 2, r0 + h / 2)
    cx, cy = c0 + w / 2, -r0 - h / 2
    for c in range(c0, c0 + w):
        for r in range(r0, r0 + h):
            ground(c, r, 0.0, COBBLE)
    rim = w / 2 - 0.1
    sides = 12
    cone(cx, cy, 0.0, 0.5, rim, rim, QUAY, sides)            # basin wall
    washer(cx, cy, 0.5, rim - 0.3, rim, COBBLE, sides)       # rim, wide enough to read
    cone(cx, cy, 0.3, 0.5, rim - 0.3, rim - 0.3, QUAY, sides)  # inside of the rim
    disc(cx, cy, 0.3, rim - 0.3, ICE, sides)                 # water
    cone(cx, cy, 0.3, 1.3, 0.42, 0.24, QUAY)                 # pedestal
    cone(cx, cy, 1.3, 1.6, 0.24, 0.8, QUAY)                  # underside of the upper bowl
    washer(cx, cy, 1.6, 0.6, 0.8, COBBLE)
    disc(cx, cy, 1.55, 0.6, ICE)                             # water in the upper bowl
    cone(cx, cy, 1.55, 2.0, 0.14, 0.1, QUAY)                 # spout
    cone(cx, cy, 2.0, 2.25, 0.2, 0, ICE)


def lighthouse(c0, r0, w, h):
    """Stands on the rock headland, on a stone base, well clear of the docks."""
    use_chunk(c0 + w / 2, r0 + h / 2)
    for c in range(c0, c0 + w):
        for r in range(r0, r0 + h):
            ground(c, r, 0.0, DUSTED, ROCK)
    cx, cy = c0 + w / 2, -r0 - h / 2
    cone(cx, cy, 0.0, 0.5, 1.05, 1.0, QUAY)
    washer(cx, cy, 0.5, 0.85, 1.0, SNOW)
    cone(cx, cy, 0.5, 2.0, 0.85, 0.72, STRIPES)
    cone(cx, cy, 2.0, 3.5, 0.72, 0.6, STRIPES)
    cone(cx, cy, 3.5, 5.0, 0.6, 0.5, STRIPES)
    washer(cx, cy, 5.0, 0.5, 0.72, DARKWOOD)                 # gallery
    cone(cx, cy, 5.0, 5.7, 0.46, 0.46, LAMP)
    cone(cx, cy, 5.7, 6.4, 0.6, 0, ROOF, tint=(0.9, 0.5, 0.5))


# Each block is built once, whole, in the chunk that holds its centre.
for block in blocks("#"):
    house(*block)
for block in blocks("f"):
    fountain(*block)
for block in blocks("L"):
    lighthouse(*block)

for r, row in enumerate(rows):
    for c, t in enumerate(row):
        use_chunk(c, r)
        if t == "~":
            ground(c, r, WATER_Z, WATER)
            continue
        if t in "#fL":
            continue
        if t == "x":
            box(c, r, 0.0, 0.7, SNOW, SNOW, 0.0)
            continue

        near = [tile(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        dock = t == "," or (t == "c" and "," in near)
        rock = t == "r"
        if dock:
            ground(c, r, 0.0, PLANK)
        elif rock:
            ground(c, r, 0.0, DUSTED if (r * 7 + c * 3) % 5 else SNOW, ROCK)
        elif "#" in near or "x" in near:
            # Snow piles up against the houses and the edge of the town.
            ground(c, r, 0.0, SNOW if "#" in near[:3] or "x" in near else DUSTED)
        else:
            ground(c, r, 0.0, COBBLE)

        if t == "c":
            box(c, r, 0.0, 0.7, CRATE, CRATE, 0.12)

        # Edges over the water: rock and quay walls on land, dark boards and posts on docks.
        x0, x1, y0, y1 = bounds(c, r)
        edge = DARKWOOD if dock else QUAY
        for n, a, b in ((tile(r + 1, c), (x0, y0), (x1, y0)),
                        (tile(r - 1, c), (x1, y1), (x0, y1)),
                        (tile(r, c - 1), (x0, y1), (x0, y0)),
                        (tile(r, c + 1), (x1, y0), (x1, y1))):
            if n == "~":
                side(*a, *b, WATER_Z, 0.0, edge, ROCK if rock else WHITE)
        if dock:
            for px, side_tile in ((x0, tile(r, c - 1)), (x1 - 0.14, tile(r, c + 1))):
                if side_tile == "~" and r % 2 == 1:
                    px0, py0 = px - 0.03, y0 - 0.03
                    for (ax, ay), (bx, by) in (((0, 0), (0.2, 0)), ((0.2, 0), (0.2, 0.2)),
                                               ((0.2, 0.2), (0, 0.2)), ((0, 0.2), (0, 0))):
                        side(px0 + ax, py0 + ay, px0 + bx, py0 + by, WATER_Z - 0.2, 0.25, DARKWOOD)
                    poly([(px0, py0, 0.25), (px0 + 0.2, py0, 0.25),
                          (px0 + 0.2, py0 + 0.2, 0.25), (px0, py0 + 0.2, 0.25)], SNOW)

bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(out_dir, exist_ok=True)
objs = {}
for (cx, cy), m in chunks.items():
    mesh = bpy.data.meshes.new(f"Saltmere_{cx}_{cy}")
    mesh.from_pydata(m["verts"], [], m["faces"])
    uv_layer = mesh.uv_layers.new(name="UV")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = m["uvs"][loop.vertex_index]
    attr = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, col in enumerate(m["colors"]):
        attr.data[i].color_srgb = (*col, 1.0)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    objs[(cx, cy)] = obj

bpy.ops.wm.save_as_mainfile(filepath=out_blend)
for (cx, cy), obj in objs.items():
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, f"{cx}_{cy}.obj"),
                          export_selected_objects=True, export_colors=True,
                          export_normals=False, export_uv=True, export_materials=False,
                          forward_axis="NEGATIVE_Z", up_axis="Y")
polys = {k: len(m["faces"]) for k, m in chunks.items()}
print(f"Saltmere: {len(polys)} chunks, {sum(polys.values())} polygons, biggest {max(polys.values())}")
