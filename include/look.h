#pragma once

#include <NEMain.h>
#include <nds.h>

// The player's choices, stored in the save. Option numbers follow the lists in
// tools/art/paint_character.py; colours index the rows in tools/art/colour_options.py.
struct Look
{
    u8 version;
    u8 body, hair, hat, top, scarf, bottoms, shoes;
    u8 skin, eyes, hair_colour, hat_colour, top_colour, bottoms_colour, shoe_colour, scarf_colour, bike_colour;
};

void look_init(void);
void look_default(Look *look);
NE_Material *look_material(void);
// Rebuilds the palette from the look's colours.
void look_apply(const Look *look);
// Combines one 64x64 frame in RAM. row: 0 up, 1 left, 2 down, 3 right.
void look_compose(const Look *look, int row, int frame);
// Copies a new frame and palette to video memory. Call right after NE_WaitForVBL().
void look_upload(void);
// The touch screen creator. Returns when the player confirms.
void creator_run(Look *look);

// The creator's Frost night skin on the bottom screen, shared with the starter screen.
// Map coordinates are in tiles; the layers sit UI_SHIFT, UI_SHIFT_Y pixels in from the corner.
static const int UI_SHIFT = 4, UI_SHIFT_Y = 8;
void ui_bottom_start(void);
void ui_bottom_stop(void);
u16 *ui_text_map(void);
u16 *ui_panel_map(void);
void ui_text(int x, int y, const char *s, int bank); // two tiles tall
void ui_panel(int x, int y, int w, int h, int bank);

// The starter screen. Returns the chosen starter's National Dex number.
u16 starter_run(void);
// The name of a starter, or NULL if dex isn't one.
const char *starter_name(u16 dex);
