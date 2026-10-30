// Port Saltmere block-out: the plaza and the docks.
//
// One character per tile, row 0 is north. The game reads this for collision, and
// tools/blender/build_saltmere.py reads it to build the 3D model, so edit it here and
// run `make models` to rebuild the model.
//
//   #  building      c  crate        f  fountain     L  lighthouse
//   .  stone plaza   ,  dock planks  ~  water
//   P  player start (plaza)

#pragma once

static const int SALTMERE_W = 16;
static const int SALTMERE_H = 20;

static const char *const saltmere_map[SALTMERE_H] = {
    "################",
    "##...######...##",
    "#..............#",
    "#..cc......c...#",
    "#......ff......#",
    "#......ff......#",
    "#..............#",
    "##.....P......##",
    "#..............#",
    "#c.............#",
    "~~~~,,,~~~~,,,~~",
    "~~~~,,,~~~~,,,~~",
    "~~~~,,,~~~~,,,~~",
    "~~~~,,,~~~~,,,~~",
    "~~~~,c,~~~~,,,~~",
    "~~~~,,,~~~~,,,~~",
    "~~~~~~~~~~~,L,~~",
    "~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~",
};
