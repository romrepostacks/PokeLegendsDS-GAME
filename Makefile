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
INCLUDEDIRS	:= include

include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile

# Copy the ROM to iCloud Drive so it can be opened in Delta on the iPhone.
# Local only: the .nds stays gitignored.
PHONEDIR	?= /c/Users/ADMIN/iCloudDrive/Delta

.PHONY: phone
phone: $(ROM)
	@mkdir -p "$(PHONEDIR)"
	cp $(ROM) "$(PHONEDIR)/"
