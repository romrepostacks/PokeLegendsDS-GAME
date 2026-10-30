# Converts each chunk OBJ with obj2dl and packs the display lists into one file:
#
#   u32 offsets[cols * rows]   byte offset of chunk (x, y) at [y * cols + x], 0 if empty
#   ...display lists...
#
#   python tools/art/pack_chunks.py OBJ2DL OBJ_DIR COLS ROWS OUT.bin

import os
import struct
import subprocess
import sys

obj2dl, obj_dir, cols, rows, out = sys.argv[1:6]
cols, rows = int(cols), int(rows)

offsets = [0] * (cols * rows)
blob = b""
base = 4 * cols * rows
for name in sorted(os.listdir(obj_dir)):
    if not name.endswith(".obj"):
        continue
    x, y = map(int, name[:-4].split("_"))
    path = os.path.join(obj_dir, name)
    dl = path[:-4] + ".dl"
    subprocess.run([sys.executable, obj2dl, "--input", path, "--output", dl, "--texture", "128", "128",
                    "--use-vertex-color", "--scale", "0.25"], check=True, stdout=subprocess.DEVNULL)
    with open(dl, "rb") as f:
        data = f.read()
    offsets[y * cols + x] = base + len(blob)
    blob += data + b"\0" * (-len(data) % 4)

with open(out, "wb") as f:
    f.write(struct.pack(f"<{cols * rows}I", *offsets) + blob)
print(f"{out}: {sum(1 for o in offsets if o)} chunks, {base + len(blob)} bytes")
