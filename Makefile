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
BINDIRS		:= data/models

LIBS		:= -lNE -lnds9
LIBDIRS		:= $(BLOCKSDSEXT)/nitro-engine

include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile

# 3D models: Blender builds the map model, obj2dl turns it into a DS display list.
# The .bin files are committed, so a plain `make` doesn't need Blender.
BLENDER		?= /c/Program\ Files/Blender\ Foundation/Blender\ 5.2/blender.exe
PYTHON		?= /c/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe
OBJ2DL		:= $(BLOCKSDSEXT)/nitro-engine/tools/obj2dl/obj2dl.py

.PHONY: models
models: data/models/saltmere.bin

data/models/saltmere.bin: maps/saltmere.h tools/blender/build_saltmere.py
	@mkdir -p build
	$(BLENDER) -b --factory-startup --python tools/blender/build_saltmere.py -- \
		$$(cygpath -w build/saltmere.obj) $$(cygpath -w art/models/saltmere.blend)
	$(PYTHON) $$(cygpath -w $(OBJ2DL)) --input build/saltmere.obj --output $@ \
		--texture 32 32 --use-vertex-color --scale 0.25

# Send the ROM to the iPhone over PairDrop. Prints a pair code if the phone isn't paired.
# node is the Windows install, which the MSYS2 shell doesn't have on PATH.
NODE		?= /c/Program\ Files/nodejs/node.exe

.PHONY: send
send: $(ROM)
	$(NODE) tools/send-to-phone.mjs $(ROM)
