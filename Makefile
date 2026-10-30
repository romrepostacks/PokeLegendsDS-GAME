# SPDX-License-Identifier: CC0-1.0
#
# Uses the BlocksDS default ARM9-only ROM makefile. Run from the Wonderful
# Toolchain Shell so BLOCKSDS is set.

BLOCKSDS	?= /opt/wonderful/thirdparty/blocksds/core

NAME		:= PokeLegendsofNine-DS
GAME_TITLE	:= PokeLegendsofNine DS
GAME_SUBTITLE	:= Legends of 9
GAME_AUTHOR	:= Kyle

SOURCEDIRS	:= src
INCLUDEDIRS	:= include

include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
