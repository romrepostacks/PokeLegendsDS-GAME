// The starter screen: all 27 starters on the bottom screen in three rows (Grass, Fire, Water),
// Gen 1 to 9 from left to right, five generations at a time. The top screen shows the one
// under the cursor. Art comes from tools/art/make_starters.py.

#include <stdio.h>
#include <string.h>

#include <NEMain.h>
#include <nds.h>

#include "look.h"
#include "starter_data.h"
#include "starter_info_pal_bin.h"
#include "starter_top_pal_bin.h"
#include "starter_top_tex_bin.h"
#include "starters_bin.h"
#include "ui_data.h"

struct StarterArt
{
    u8 icon[32 * 32 / 2];   // 4bpp sprite tiles
    u8 battle[64 * 64 / 2]; // 4bpp texture, shown at 2x
    u8 info[256 * 32 / 2];  // 4bpp texture: name, type, flavour line, final evolution
    u16 palette[16];        // icon and battle sprite; 0 is transparent
};

static const StarterArt *art(int i) { return (const StarterArt *)starters_bin + i; }

const char *starter_name(u16 dex)
{
    for (int i = 0; i < STARTER_COUNT; i++)
        if (STARTER_DEX[i] == dex)
            return STARTER_NAMES[i];
    return NULL;
}

// Bottom screen layout, in tiles.
static const int SHOWN = 5;             // generations on screen at once
static const int CELL_W = 5, PITCH = 6; // a cell and the gap after it
static const int CELL_H = 5, ROW_PITCH = 6;
static const int GEN_ROW = 0, GRID_X = 1, GRID_ROW = 2, BUTTON_ROW = 20;
static const int LEFT_END = 7, RIGHT_START = 24, YES_END = 15;

struct Picker
{
    int cursor; // row * STARTER_GENS + gen
    int first;  // first generation on screen
    bool asking; // "Choose X?" is up
};

static u16 *icon_gfx[3 * SHOWN];

static int row_of(int i) { return i / STARTER_GENS; }
static int gen_of(int i) { return i % STARTER_GENS; }
static int cell_x(int c) { return GRID_X + c * PITCH; }
static int cell_y(int r) { return GRID_ROW + r * ROW_PITCH; }

// Scrolls so the cursor's generation is on screen.
static void follow(Picker *p)
{
    int gen = gen_of(p->cursor);
    if (gen < p->first)
        p->first = gen;
    if (gen >= p->first + SHOWN)
        p->first = gen - SHOWN + 1;
}

// Scrolls one generation, taking the cursor along if it would go off screen.
static void scroll(Picker *p, int step)
{
    p->first += step;
    if (p->first < 0)
        p->first = 0;
    if (p->first > STARTER_GENS - SHOWN)
        p->first = STARTER_GENS - SHOWN;
    int gen = gen_of(p->cursor);
    if (gen < p->first)
        p->cursor += p->first - gen;
    if (gen >= p->first + SHOWN)
        p->cursor -= gen - (p->first + SHOWN - 1);
}

static void picker_draw(const Picker *p)
{
    dmaFillHalfWords(0, ui_text_map(), 2048);
    dmaFillHalfWords(0, ui_panel_map(), 2048);
    char line[32];

    if (p->asking)
    {
        ui_panel(0, GEN_ROW, 31, 2, BANK_PANEL);
        snprintf(line, sizeof(line), "Choose %s?", STARTER_NAMES[p->cursor]);
        ui_text(1, GEN_ROW, line, BANK_GOLD_TEXT);
    }

    for (int c = 0; c < SHOWN; c++)
    {
        if (!p->asking)
        {
            snprintf(line, sizeof(line), "Gen %d", p->first + c + 1);
            ui_text(cell_x(c), GEN_ROW, line, p->first + c == gen_of(p->cursor) ? BANK_GOLD_TEXT : BANK_TEXT);
        }
        for (int r = 0; r < 3; r++)
        {
            int i = r * STARTER_GENS + p->first + c, slot = r * SHOWN + c;
            int x = cell_x(c), y = cell_y(r);
            ui_panel(x, y, CELL_W, CELL_H, i == p->cursor ? BANK_FOCUS : BANK_PANEL);
            dmaCopy(art(i)->icon, icon_gfx[slot], sizeof(art(i)->icon));
            dmaCopy(art(i)->palette, SPRITE_PALETTE_SUB + slot * 16, sizeof(art(i)->palette));
            oamSet(&oamSub, slot, x * 8 + UI_SHIFT + 4, y * 8 + UI_SHIFT_Y + 4, 0, slot, SpriteSize_32x32,
                   SpriteColorFormat_16Color, icon_gfx[slot], -1, false, false, false, false, false);
        }
    }

    if (p->asking)
    {
        ui_panel(0, BUTTON_ROW, YES_END, 2, BANK_SELECTED);
        ui_text(1, BUTTON_ROW, "A", BANK_GOLD_TEXT);
        ui_text(3, BUTTON_ROW, "Yes", BANK_TEXT);
        ui_panel(YES_END + 1, BUTTON_ROW, 31 - YES_END - 1, 2, BANK_PANEL);
        ui_text(YES_END + 2, BUTTON_ROW, "B", BANK_GOLD_TEXT);
        ui_text(YES_END + 4, BUTTON_ROW, "No", BANK_TEXT);
    }
    else
    {
        // Greyed out at the ends, like the creator's colour strip arrows.
        ui_panel(0, BUTTON_ROW, LEFT_END, 2, BANK_PANEL);
        ui_text(1, BUTTON_ROW, "< L", p->first > 0 ? BANK_TEXT : BANK_ICON);
        ui_panel(LEFT_END + 1, BUTTON_ROW, RIGHT_START - LEFT_END - 2, 2, BANK_SOLID);
        ui_text(LEFT_END + 4, BUTTON_ROW, "A Choose", BANK_DARK_TEXT);
        ui_panel(RIGHT_START, BUTTON_ROW, 31 - RIGHT_START, 2, BANK_PANEL);
        ui_text(RIGHT_START + 3, BUTTON_ROW, "R >", p->first < STARTER_GENS - SHOWN ? BANK_TEXT : BANK_ICON);
    }
}

// The highlighted box pulses by changing BANK_FOCUS itself. The creator isn't affected:
// ui_bottom_start() reloads the palette.
static u16 blend(u16 a, u16 b, int t, int of)
{
    u16 out = 0;
    for (int shift = 0; shift < 15; shift += 5)
    {
        int from = (a >> shift) & 31, to = (b >> shift) & 31;
        out |= (from + (to - from) * t / of) << shift;
    }
    return out;
}

static void pulse(int tick, u16 fill)
{
    int t = tick % 120;
    if (t > 60)
        t = 120 - t;
    BG_PALETTE_SUB[BANK_FOCUS * 16 + 1] = UI_ICE;
    BG_PALETTE_SUB[BANK_FOCUS * 16 + 2] = blend(fill, UI_ICE, t, 80); // stops short of the border colour
}

// Top screen: the stage, the sprite at 2x and the info plate.
static NE_Material *stage_mat, *battle_mat, *info_mat;
static NE_Palette *stage_pal, *battle_pal, *info_pal;
static int shown = -1;

static NE_Material *texture(int w, int h, const void *tex, NE_Palette *pal, bool transparent)
{
    NE_Material *m = NE_MaterialCreate();
    NE_MaterialTexLoad(m, NE_PAL16, w, h,
                       (NE_TextureFlags)(NE_TEXGEN_TEXCOORD | (transparent ? NE_TEXTURE_COLOR0_TRANSPARENT : 0)), tex);
    NE_MaterialSetPalette(m, pal);
    return m;
}

static NE_Palette *palette(const void *colours)
{
    NE_Palette *p = NE_PaletteCreate();
    NE_PaletteLoad(p, colours, 16, NE_PAL16);
    return p;
}

static void show(int i)
{
    if (i == shown)
        return;
    if (shown >= 0)
    {
        NE_MaterialDelete(battle_mat);
        NE_MaterialDelete(info_mat);
        NE_PaletteDelete(battle_pal);
    }
    shown = i;
    battle_pal = palette(art(i)->palette);
    battle_mat = texture(64, 64, art(i)->battle, battle_pal, true);
    info_mat = texture(256, 32, art(i)->info, info_pal, true);
}

static void starter_scene(void)
{
    NE_2DViewInit();
    NE_PolyFormat(31, 0, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_2DDrawTexturedQuad(0, 0, 256, 256, 3, stage_mat);
    NE_2DDrawTexturedQuad(64, 16, 192, 144, 1, battle_mat);
    NE_2DDrawTexturedQuad(0, 154, 256, 186, 1, info_mat);
}

u16 starter_run(void)
{
    ui_bottom_start();
    for (int i = 0; i < 3 * SHOWN; i++)
        icon_gfx[i] = oamAllocateGfx(&oamSub, SpriteSize_32x32, SpriteColorFormat_16Color);
    stage_pal = palette(starter_top_pal_bin);
    stage_mat = texture(256, 256, starter_top_tex_bin, stage_pal, false);
    info_pal = palette(starter_info_pal_bin);
    shown = -1;

    const u16 focus_fill = BG_PALETTE_SUB[BANK_FOCUS * 16 + 2];
    Picker p = { 0, 0, false };
    show(p.cursor);
    picker_draw(&p);
    keysSetRepeat(20, 6);
    int tick = 0;
    bool chosen = false;
#ifdef STARTER_PRESSES
    // Test builds only: a press every half second, for screenshots.
    static const u32 presses[] = STARTER_PRESSES;
    unsigned next_press = 0;
#endif

    while (!chosen)
    {
        NE_WaitForVBL((NE_UpdateFlags)0);
        scanKeys();
        u32 down = keysDown(), repeat = keysDownRepeat();
        touchPosition touch;
        touchRead(&touch);
        tick++;
#ifdef STARTER_PRESSES
        if (tick % 30 == 0 && next_press < sizeof(presses) / sizeof(presses[0]))
        {
            down |= presses[next_press];
            repeat |= presses[next_press];
            next_press++;
        }
#endif
        int was = p.cursor, first = p.first;
        bool asking = p.asking;
        int cx = (touch.px - UI_SHIFT) / 8, cy = (touch.py - UI_SHIFT_Y) / 8;

        if (p.asking)
        {
            if ((down & KEY_A) || ((down & KEY_TOUCH) && cy >= BUTTON_ROW && cx < YES_END))
                chosen = true;
            else if (down & (KEY_B | KEY_TOUCH))
                p.asking = false;
        }
        else if (down & KEY_TOUCH)
        {
            int gx = cx - GRID_X, gy = cy - GRID_ROW;
            int c = gx / PITCH, r = gy / ROW_PITCH;
            if (gx >= 0 && gy >= 0 && r < 3 && c < SHOWN && gx % PITCH < CELL_W && gy % ROW_PITCH < CELL_H)
            {
                // A tap highlights; tapping the highlighted one again picks it.
                int i = r * STARTER_GENS + p.first + c;
                p.asking = i == p.cursor;
                p.cursor = i;
            }
            else if (cy >= BUTTON_ROW)
            {
                if (cx < LEFT_END)
                    scroll(&p, -1);
                else if (cx >= RIGHT_START)
                    scroll(&p, 1);
                else
                    p.asking = true;
            }
        }
        else if (down & KEY_A)
            p.asking = true;
        else if ((repeat & KEY_LEFT) && gen_of(p.cursor) > 0)
            p.cursor--;
        else if ((repeat & KEY_RIGHT) && gen_of(p.cursor) < STARTER_GENS - 1)
            p.cursor++;
        else if ((repeat & KEY_UP) && row_of(p.cursor) > 0)
            p.cursor -= STARTER_GENS;
        else if ((repeat & KEY_DOWN) && row_of(p.cursor) < 2)
            p.cursor += STARTER_GENS;
        else if (repeat & KEY_L)
            scroll(&p, -1);
        else if (repeat & KEY_R)
            scroll(&p, 1);
        follow(&p);

        if (p.cursor != was || p.first != first || p.asking != asking)
        {
            show(p.cursor);
            picker_draw(&p);
        }
        // The highlighted icon hops, like the party icons in the old games.
        int c = gen_of(p.cursor) - p.first, r = row_of(p.cursor);
        int hop = (tick / 12) % 2 ? 2 : 0;
        oamSetXY(&oamSub, r * SHOWN + c, cell_x(c) * 8 + UI_SHIFT + 4, cell_y(r) * 8 + UI_SHIFT_Y + 4 - hop);
        oamUpdate(&oamSub);
        pulse(tick, focus_fill);
        NE_Process(starter_scene);
    }

    NE_MaterialDelete(stage_mat);
    NE_MaterialDelete(battle_mat);
    NE_MaterialDelete(info_mat);
    NE_PaletteDelete(stage_pal);
    NE_PaletteDelete(battle_pal);
    NE_PaletteDelete(info_pal);
    for (int i = 0; i < 3 * SHOWN; i++)
        oamFreeGfx(&oamSub, icon_gfx[i]);
    ui_bottom_stop();
    return STARTER_DEX[p.cursor];
}
