# SPDX-License-Identifier: CC0-1.0
#
# Uses the BlocksDS default ARM9-only ROM makefile. Run from the Wonderful
# Toolchain Shell so BLOCKSDS is set.

BLOCKSDS	?= /opt/wonderful/thirdparty/blocksds/core

NAME		:= PokeLegendsofNine-DS
GAME_TITLE	:= Poke Legends
GAME_SUBTITLE	:= Beyond the Nine
GAME_AUTHOR	:= Kyle

SOURCEDIRS	:= src
INCLUDEDIRS	:= include maps
BINDIRS		:= data/models data/textures

LIBS		:= -lNE -lnds9
LIBDIRS		:= $(BLOCKSDSEXT)/nitro-engine

include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile

# Our own game code. With the homebrew default (####), melonDS and Delta give the ROM no
# save chip, so saves have nowhere to go.
NDSTOOL_ARGS	+= -g B9NE

# 3D models: Blender builds the map model, obj2dl turns it into a DS display list.
# The .bin files are committed, so a plain `make` doesn't need Blender.
BLENDER		?= /c/Program\ Files/Blender\ Foundation/Blender\ 5.2/blender.exe
PYTHON		?= /c/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe
OBJ2DL		:= $(BLOCKSDSEXT)/nitro-engine/tools/obj2dl/obj2dl.py

IMG2DS		:= $(BLOCKSDSEXT)/nitro-engine/tools/img2ds/img2ds.py

.PHONY: models textures
models: data/models/saltmere.bin
textures: data/textures/player_tex.bin data/textures/saltmere_tex.bin

data/models/saltmere.bin: maps/saltmere.h tools/blender/build_saltmere.py
	@mkdir -p build
	$(BLENDER) -b --factory-startup --python tools/blender/build_saltmere.py -- \
		$$(cygpath -w build/saltmere.obj) $$(cygpath -w art/models/saltmere.blend)
	$(PYTHON) $$(cygpath -w $(OBJ2DL)) --input build/saltmere.obj --output $@ \
		--texture 128 128 --use-vertex-color --scale 0.25

# Pixel art is drawn by scripts, then converted to paletted DS textures.
art/sprites/player.png: tools/art/make_player.py
	$(PYTHON) -I $< $@

art/textures/saltmere.png: tools/art/make_atlas.py
	$(PYTHON) -I $< $@

data/textures/player_tex.bin: art/sprites/player.png
	$(PYTHON) $$(cygpath -w $(IMG2DS)) --input $< --name player --output data/textures --format PAL16

data/textures/saltmere_tex.bin: art/textures/saltmere.png
	$(PYTHON) $$(cygpath -w $(IMG2DS)) --input $< --name saltmere --output data/textures --format PAL256

# Send the ROM to the iPhone over PairDrop. Prints a pair code if the phone isn't paired.
# node is the Windows install, which the MSYS2 shell doesn't have on PATH.
NODE		?= /c/Program\ Files/nodejs/node.exe

.PHONY: send
send: $(ROM)
	$(NODE) tools/send-to-phone.mjs $(ROM) $(if $(PAIR),--pair)
