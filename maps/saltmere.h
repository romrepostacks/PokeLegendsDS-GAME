// Port Saltmere town centre: station, plaza, harbour and the lighthouse point.
//
// One character per tile, row 0 is north. The game reads this for collision, and
// tools/blender/build_saltmere.py reads it to build the 3D model, so edit it here and
// run `make models` to rebuild the model.
//
//   #  building (each connected block is one building)
//   .  stone plaza   :  snow          ,  dock planks   r  rocky ground   ~  water
//   c  crate         f  fountain      i  lamp post     T  pine tree      R  boulder
//   L  lighthouse    P  player start
//
// Buildings, north to south: rail station (top centre), four houses either side of it,
// healing centre and mart (west), expedition HQ and two houses (east), water gym (on the
// quay, west). Two piers run south; the lighthouse stands on the rocky point (east).

#pragma once

static const int SALTMERE_W = 32;
static const int SALTMERE_H = 32;

static const char *const saltmere_map[SALTMERE_H] = {
    "TTTTTTTTTTTT########TTTTTTTTTTTT",
    "TTTTTTTTTTTT########TTTTTTTTTTTT",
    "TT:###:###::########::###:###:TT",
    "TT:###:###::########::###:###:TT",
    "TT::::::::i..........i::::::::TT",
    "TT:..........................:TT",
    "TT:#####...............######:TT",
    "TT:#####....i.....i....######:TT",
    "TT:#####...............######:TT",
    "TT:#####......fff......######:TT",
    "TT:...........fff......######:TT",
    "TT:####.......fff............:TT",
    "TT:####.................###..:TT",
    "TT:####.....i.....i.....###..:TT",
    "TT:..........................:TT",
    "TT:######..cc......c.....###.:TT",
    "TT:######..c...P...cc....###.:TT",
    "TT:######....................:TT",
    "TT:######....................:TT",
    "TT......................rrrrrrrT",
    "RRR~~~~~~~,,,~~~~,,,~~~~rrrrrrR~",
    "RRR~~~~~~~,,,~~~~,,,~~~~RrrrrrR~",
    "RRR~~~~~~~,,,~~~~,,,~~~~~Rrrrr~~",
    "RRR~~~~~~~,,,~~~~,,,~~~~~~rrrR~~",
    "RR~~~~~~~~,,,~~~~,,,~~~~~~Rrrr~~",
    "RR~~~~~~~~,c,~~~~,,,~~~~~~~rrr~~",
    "~~~~~~~~~~,,,~~~~~~~~~~~~~~rLR~~",
    "~~~~~~~~~~,,,~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
};
