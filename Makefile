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

# Send the ROM to the iPhone over PairDrop. Prints a pair code if the phone isn't paired.
# node is the Windows install, which the MSYS2 shell doesn't have on PATH.
NODE		?= /c/Program\ Files/nodejs/node.exe

.PHONY: send
send: $(ROM)
	$(NODE) tools/send-to-phone.mjs $(ROM)
