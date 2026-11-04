// The starter screen: a supply crate dug out of the snow, with three Poke Balls in its straw.
// The crate holds all 27 starters, one generation's three at a time over 9 pages (Grass, Fire,
// Water, left to right). Tapping a ball opens it: the starter peeks out on the bottom screen and
// the top screen shows it large with base stats, Lv 5 moves and evolutions.
// Art comes from tools/art/make_starters.py.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <NEMain.h>
#include <nds.h>

#include "look.h"
#include "starter_ball_pal_bin.h"
#include "starter_ball_tiles_bin.h"
#include "starter_crate_map_bin.h"
#include "starter_crate_pal_bin.h"
#include "starter_crate_tiles_bin.h"
#include "starter_data.h"
#include "starter_hint_tex_bin.h"
#include "starter_info_pal_bin.h"
#include "starter_top_pal_bin.h"
#include "starter_top_tex_bin.h"
#include "starters_bin.h"
#include "ui_data.h"

struct StarterArt
{
    u8 icon[32 * 32 / 2];   // 4bpp sprite tiles
    u8 battle[64 * 64 / 2]; // 4bpp texture, shown at 2x
    u8 stats[128 * 128 / 2]; // 4bpp texture: base stats panel
    u8 text[256 * 64 / 2];   // 4bpp texture: name, type, flavour, moves, evolutions
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

// Bottom screen layout, in tiles (the UI layers sit UI_SHIFT, UI_SHIFT_Y in from the corner).
static const int PAGE_ROW = 0, NAME_ROW = 14, BUTTON_ROW = 20;
static const int COLUMNS = 31, CHOOSE_X = 8, CHOOSE_W = 15, YES_END = 15;
static const int CRATE_MAP = 13; // below the creator's two maps (14, 15)
static const int BALL_PAL = 3, ICON_PAL = 4, ICON_SPRITE = 3;

struct Picker
{
    int page;    // generation, 0-8
    int ball;    // open ball (0 Grass, 1 Fire, 2 Water), or -1
    bool asking; // "Choose X?" is up
};

static int picked(const Picker *p) { return p->ball * STARTER_GENS + p->page; }

static u16 *ball_gfx[2], *icon_gfx; // closed and open frames

static void picker_draw(const Picker *p)
{
    dmaFillHalfWords(0, ui_text_map(), 2048);
    dmaFillHalfWords(0, ui_panel_map(), 2048);
    char line[32];

    ui_panel(0, PAGE_ROW, COLUMNS, 2, BANK_PANEL);
    if (p->asking)
    {
        snprintf(line, sizeof(line), "Choose %s?", STARTER_NAMES[picked(p)]);
        ui_text(1, PAGE_ROW, line, BANK_GOLD_TEXT);
    }
    else
    {
        // Greyed out at the ends, like the creator's colour strip arrows.
        ui_text(7, PAGE_ROW, "<", p->page > 0 ? BANK_TEXT : BANK_ICON);
        snprintf(line, sizeof(line), "Page %d of %d", p->page + 1, STARTER_GENS);
        ui_text(10, PAGE_ROW, line, BANK_TEXT);
        ui_text(23, PAGE_ROW, ">", p->page < STARTER_GENS - 1 ? BANK_TEXT : BANK_ICON);
    }

    for (int b = 0; b < 3; b++)
        oamSet(&oamSub, b, STARTER_BALL_X[b] - 16, STARTER_BALL_Y - 16, 1, BALL_PAL, SpriteSize_32x32,
               SpriteColorFormat_16Color, ball_gfx[b == p->ball], -1, false, false, false, false, false);
    oamSetHidden(&oamSub, ICON_SPRITE, p->ball < 0);
    if (p->ball >= 0)
    {
        // The starter peeks out of its ball, with its name on a plate underneath.
        int i = picked(p);
        dmaCopy(art(i)->icon, icon_gfx, sizeof(art(i)->icon));
        dmaCopy(art(i)->palette, SPRITE_PALETTE_SUB + ICON_PAL * 16, sizeof(art(i)->palette));
        int len = strlen(STARTER_NAMES[i]), x = (STARTER_BALL_X[p->ball] - UI_SHIFT) / 8 - (len + 2) / 2;
        if (x < 0)
            x = 0;
        if (x > COLUMNS - len - 2)
            x = COLUMNS - len - 2;
        ui_panel(x, NAME_ROW, len + 2, 2, BANK_FOCUS);
        ui_text(x + 1, NAME_ROW, STARTER_NAMES[i], BANK_TEXT);
    }

    if (p->asking)
    {
        ui_panel(0, BUTTON_ROW, YES_END, 2, BANK_SELECTED);
        ui_text(1, BUTTON_ROW, "A", BANK_GOLD_TEXT);
        ui_text(3, BUTTON_ROW, "Yes", BANK_TEXT);
        ui_panel(YES_END + 1, BUTTON_ROW, COLUMNS - YES_END - 1, 2, BANK_PANEL);
        ui_text(YES_END + 2, BUTTON_ROW, "B", BANK_GOLD_TEXT);
        ui_text(YES_END + 4, BUTTON_ROW, "No", BANK_TEXT);
    }
    else if (p->ball >= 0)
    {
        ui_panel(CHOOSE_X, BUTTON_ROW, CHOOSE_W, 2, BANK_SOLID);
        ui_text(CHOOSE_X + 3, BUTTON_ROW, "A Choose", BANK_DARK_TEXT);
    }
}

// The name plate pulses by changing BANK_FOCUS itself. The creator isn't affected:
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

// Top screen: the snowy stage, then either the hint or the open ball's starter at 2x with its
// stats and text panels.
static NE_Material *stage_mat, *hint_mat, *battle_mat, *stats_mat, *text_mat;
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

// i: starter index, or -1 for none.
static void show(int i)
{
    if (i == shown)
        return;
    if (shown >= 0)
    {
        NE_MaterialDelete(battle_mat);
        NE_MaterialDelete(stats_mat);
        NE_MaterialDelete(text_mat);
        NE_PaletteDelete(battle_pal);
    }
    shown = i;
    if (i < 0)
        return;
    battle_pal = palette(art(i)->palette);
    battle_mat = texture(64, 64, art(i)->battle, battle_pal, true);
    stats_mat = texture(128, 128, art(i)->stats, info_pal, true);
    text_mat = texture(256, 64, art(i)->text, info_pal, true);
}

static void starter_scene(void)
{
    NE_2DViewInit();
    NE_PolyFormat(31, 0, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_2DDrawTexturedQuad(0, 0, 256, 256, 3, stage_mat);
    if (shown < 0)
    {
        NE_2DDrawTexturedQuad(0, 80, 256, 112, 1, hint_mat);
        return;
    }
    NE_2DDrawTexturedQuad(0, -6, 128, 122, 1, battle_mat);
    NE_2DDrawTexturedQuad(128, 0, 256, 128, 1, stats_mat);
    NE_2DDrawTexturedQuad(0, 128, 256, 192, 1, text_mat);
}

// The crate, on a third layer under the creator's text and panels. Its tiles follow the UI's.
static int crate_start(void)
{
    int bg = bgInitSub(2, BgType_Text4bpp, BgSize_T_256x256, CRATE_MAP, 0);
    dmaCopy(starter_crate_tiles_bin, (u8 *)BG_TILE_RAM_SUB(0) + STARTER_CRATE_TILE * 32, starter_crate_tiles_bin_size);
    dmaCopy(starter_crate_map_bin, BG_MAP_RAM_SUB(CRATE_MAP), starter_crate_map_bin_size);
    dmaCopy(starter_crate_pal_bin, BG_PALETTE_SUB + STARTER_CRATE_BANK * 16, starter_crate_pal_bin_size);
    bgSetPriority(bg, 3);
    REG_BG2HOFS_SUB = 0;
    REG_BG2VOFS_SUB = 0;
    return bg;
}

u16 starter_run(void)
{
    ui_bottom_start();
    int crate_bg = crate_start();
    for (int f = 0; f < 2; f++)
    {
        ball_gfx[f] = oamAllocateGfx(&oamSub, SpriteSize_32x32, SpriteColorFormat_16Color);
        dmaCopy(starter_ball_tiles_bin + f * 512, ball_gfx[f], 512);
    }
    dmaCopy(starter_ball_pal_bin, SPRITE_PALETTE_SUB + BALL_PAL * 16, starter_ball_pal_bin_size);
    icon_gfx = oamAllocateGfx(&oamSub, SpriteSize_32x32, SpriteColorFormat_16Color);
    oamSet(&oamSub, ICON_SPRITE, 0, 0, 0, ICON_PAL, SpriteSize_32x32, SpriteColorFormat_16Color, icon_gfx, -1,
           false, true, false, false, false);
    stage_pal = palette(starter_top_pal_bin);
    stage_mat = texture(256, 256, starter_top_tex_bin, stage_pal, false);
    info_pal = palette(starter_info_pal_bin);
    hint_mat = texture(256, 32, starter_hint_tex_bin, info_pal, true);
    shown = -1;

    const u16 focus_fill = BG_PALETTE_SUB[BANK_FOCUS * 16 + 2];
    Picker p = { 0, -1, false };
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
        Picker was = p;
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
            int hit = -1;
            for (int b = 0; b < 3; b++)
                if (abs(touch.px - STARTER_BALL_X[b]) < 18 && abs(touch.py - STARTER_BALL_Y) < 20)
                    hit = b;
            if (cy < PAGE_ROW + 2)
            {
                int page = p.page + (cx < COLUMNS / 2 ? -1 : 1);
                if (page >= 0 && page < STARTER_GENS)
                    p = { page, -1, false };
            }
            else if (hit >= 0)
            {
                // A tap opens a ball; tapping the open one again picks it.
                p.asking = hit == p.ball;
                p.ball = hit;
            }
            else if (cy >= BUTTON_ROW && p.ball >= 0)
                p.asking = true;
        }
        else if ((down & KEY_A) && p.ball >= 0)
            p.asking = true;
        else if (down & KEY_B)
            p.ball = -1;
        else if (repeat & KEY_LEFT)
        {
            // Past the left ball is the previous page's right one.
            if (p.ball < 0)
                p.ball = 1;
            else if (p.ball > 0)
                p.ball--;
            else if (p.page > 0)
                p = { p.page - 1, 2, false };
        }
        else if (repeat & KEY_RIGHT)
        {
            if (p.ball < 0)
                p.ball = 1;
            else if (p.ball < 2)
                p.ball++;
            else if (p.page < STARTER_GENS - 1)
                p = { p.page + 1, 0, false };
        }

        if (p.page != was.page || p.ball != was.ball || p.asking != was.asking)
        {
            show(p.ball < 0 ? -1 : picked(&p));
            picker_draw(&p);
        }
        if (p.ball >= 0)
        {
            // The starter hops on top of its open ball.
            int hop = (tick / 12) % 2 ? 2 : 0;
            oamSetXY(&oamSub, ICON_SPRITE, STARTER_BALL_X[p.ball] - 16, STARTER_BALL_Y - 44 - hop);
        }
        oamUpdate(&oamSub);
        pulse(tick, focus_fill);
        NE_Process(starter_scene);
    }

    show(-1);
    NE_MaterialDelete(stage_mat);
    NE_MaterialDelete(hint_mat);
    NE_PaletteDelete(stage_pal);
    NE_PaletteDelete(info_pal);
    for (int f = 0; f < 2; f++)
        oamFreeGfx(&oamSub, ball_gfx[f]);
    oamFreeGfx(&oamSub, icon_gfx);
    bgHide(crate_bg);
    ui_bottom_stop();
    return STARTER_DEX[picked(&p)];
}
