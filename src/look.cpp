#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "look.h"
#include "look_bin.h"
#include "look_clips_bin.h"
#include "look_data.h"
#include "look_ramps_bin.h"
#include "ui_boy_pal_bin.h"
#include "ui_boy_tex_bin.h"
#include "ui_data.h"
#include "ui_girl_pal_bin.h"
#include "ui_girl_tex_bin.h"
#include "ui_pal_bin.h"
#include "ui_tiles_bin.h"
#include "ui_top_pal_bin.h"
#include "ui_top_tex_bin.h"

// ---------------------------------------------------------------------------
// Combining layers. The layer data is written by tools/art/make_look.py.

static const int FRAME_BYTES = 64 * 64;
static const int FOOT_SHIFT = 2; // LPC feet end above the frame's bottom edge

static NE_Material *material;
static NE_Palette *palette;
static u8 pixels[FRAME_BYTES] __attribute__((aligned(32)));
static u16 colours[256] __attribute__((aligned(32)));
static bool new_pixels, new_colours;
static u8 *target = pixels; // where look_compose draws

// Option numbers that the rules below care about.
enum { HAT_NONE = 0, HAT_CAP = 3, HAT_HOOD = 4, BOTTOMS_SHORTS = 2 };

void look_init(void)
{
    material = NE_MaterialCreate();
    NE_MaterialTexLoad(material, NE_PAL256, 64, 64,
                       (NE_TextureFlags)(NE_TEXGEN_TEXCOORD | NE_TEXTURE_COLOR0_TRANSPARENT), pixels);
    palette = NE_PaletteCreate();
    NE_PaletteLoad(palette, colours, 256, NE_PAL256);
    NE_MaterialSetPalette(material, palette);
}

void look_default(Look *look)
{
    *look = {};
    look->hat = 1;
    look->hair_colour = DEFAULT_HAIR_COLOUR;
    look->hat_colour = DEFAULT_HAT_COLOUR;
    look->top_colour = DEFAULT_TOP_COLOUR;
    look->bottoms_colour = DEFAULT_BOTTOMS_COLOUR;
    look->shoe_colour = DEFAULT_SHOE_COLOUR;
    look->scarf_colour = DEFAULT_SCARF_COLOUR;
}

NE_Material *look_material(void)
{
    return material;
}

static void set_slot(int slot, int ramp)
{
    const u16 *shades = (const u16 *)look_ramps_bin + ramp * LOOK_SHADES;
    memcpy(colours + 2 + slot * LOOK_SHADES, shades, LOOK_SHADES * 2);
}

void look_apply(const Look *look)
{
    colours[1] = RGB15(3, 3, 6);
    set_slot(SLOT_SKIN, RAMP_SKIN + look->skin);
    set_slot(SLOT_EYES, RAMP_EYES + look->eyes);
    set_slot(SLOT_HAIR, RAMP_HAIR + look->hair_colour);
    set_slot(SLOT_HAT, RAMP_COLOURS + look->hat_colour);
    set_slot(SLOT_POMPOM, RAMP_FIXED + 2);
    set_slot(SLOT_TOP, RAMP_COLOURS + look->top_colour);
    set_slot(SLOT_TRIM, RAMP_FIXED + look->body);
    set_slot(SLOT_BOTTOMS, RAMP_COLOURS + look->bottoms_colour);
    set_slot(SLOT_UNDER, RAMP_FIXED + 3);
    set_slot(SLOT_SHOE, RAMP_COLOURS + look->shoe_colour);
    set_slot(SLOT_SCARF, RAMP_COLOURS + look->scarf_colour);
    new_colours = true;
}

// Rows of the layer above clip_y are left out.
static void blit(int body, int layer, int row, int frame, int clip_y = 0)
{
    const u32 *offsets = (const u32 *)look_bin;
    u32 offset = offsets[(body * LOOK_LAYERS + layer) * 4 * LOOK_FRAMES + row * LOOK_FRAMES + frame];
    if (offset == 0)
        return;
    const u8 *rec = look_bin + offset;
    int x0 = rec[0], y0 = rec[1] + FOOT_SHIFT, w = rec[2], h = rec[3];
    const u8 *src = rec + 4;
    for (int y = y0; y < y0 + h; y++)
    {
        for (int x = x0; x < x0 + w; x++, src++)
            if (*src && y < 64 && y - FOOT_SHIFT >= clip_y)
                target[y * 64 + x] = *src;
    }
}

void look_compose(const Look *look, int row, int frame)
{
    int body = look->body;
    memset(target, 0, FRAME_BYTES);
    // Beanies and caps hide the hair on top of the head; the hood hides it all.
    int clip = 0;
    if (look->hat != HAT_NONE && look->hat <= HAT_CAP)
        clip = look_clips_bin[(body * 4 + row) * LOOK_FRAMES + frame];
    if (look->hat != HAT_HOOD)
        blit(body, LAYER_HAIRBACK + look->hair, row, frame, clip);
    blit(body, LAYER_BODY, row, frame);
    bool over_leggings = look->bottoms >= BOTTOMS_SHORTS;
    blit(body, over_leggings ? LAYER_LEGS_UNDER : LAYER_LEGS + look->bottoms, row, frame);
    blit(body, LAYER_FEET + look->shoes, row, frame);
    if (over_leggings)
        blit(body, LAYER_BOTTOMS + look->bottoms - BOTTOMS_SHORTS, row, frame);
    blit(body, LAYER_TOP + look->top, row, frame);
    blit(body, LAYER_HEAD, row, frame);
    if (look->hat != HAT_HOOD)
        blit(body, LAYER_HAIR + look->hair, row, frame, clip);
    if (look->scarf)
        blit(body, LAYER_SCARF, row, frame);
    if (look->hat != HAT_NONE)
        blit(body, LAYER_HAT + look->hat - 1, row, frame);
    new_pixels = true;
}

void look_upload(void)
{
    if (new_pixels)
    {
        DC_FlushRange(pixels, sizeof(pixels));
        void *vram = NE_TextureDrawingStart(material);
        dmaCopy(pixels, vram, sizeof(pixels));
        NE_TextureDrawingEnd();
        new_pixels = false;
    }
    if (new_colours)
    {
        DC_FlushRange(colours, sizeof(colours));
        void *vram = NE_PaletteModificationStart(palette);
        dmaCopy(colours, vram, sizeof(colours));
        NE_PaletteModificationEnd();
        new_colours = false;
    }
}

// ---------------------------------------------------------------------------
// The creator: the trainer on a snowy stage on the top screen, with touch tabs below.

static const char *const HAIR_NAMES[] = { "Short", "Spiky", "Wavy", "High pony", "Side pony", "Braid", "Bob", "Long" };
static const char *const HAT_NAMES[] = { "None", "Beanie", "Knit cap", "Ball cap", "Hood", "Earmuff" };
static const char *const TOP_NAMES[] = { "Jacket", "Parka", "Vest", "Long coat" };
static const char *const BOTTOM_NAMES[] = { "Trousers", "Leggings", "Shorts", "Skirt" };
static const char *const SHOE_NAMES[] = { "Snow boots", "Tall boots", "Sneakers" };
static const char *const BODY_NAMES[] = { "Boy", "Girl" };
static const char *const SCARF_NAMES[] = { "Off", "On" };

struct Tab
{
    const char *label;
    const char *const *names;    // shape choices, if any
    int name_count;
    size_t shape;                // Look field the shapes set
    size_t colour;               // Look field the swatches set, if swatch_count
    int ramp, swatch_count;
    int preview_y;               // top row of the frame shown in the option tiles
};

#define FIELD(f) offsetof(Look, f)
static const Tab TABS[] = {
    { "BODY", BODY_NAMES, 2, FIELD(body), 0, 0, 0, 4 },
    { "HAIR", HAIR_NAMES, 8, FIELD(hair), FIELD(hair_colour), RAMP_HAIR, COUNT_COLOURS, 8 },
    { "HAT", HAT_NAMES, 6, FIELD(hat), FIELD(hat_colour), RAMP_COLOURS, COUNT_COLOURS, 4 },
    { "TOP", TOP_NAMES, 4, FIELD(top), FIELD(top_colour), RAMP_COLOURS, COUNT_COLOURS, 22 },
    { "SCARF", SCARF_NAMES, 2, FIELD(scarf), FIELD(scarf_colour), RAMP_COLOURS, COUNT_COLOURS, 16 },
    { "LEGS", BOTTOM_NAMES, 4, FIELD(bottoms), FIELD(bottoms_colour), RAMP_COLOURS, COUNT_COLOURS, 32 },
    { "SHOES", SHOE_NAMES, 3, FIELD(shoes), FIELD(shoe_colour), RAMP_COLOURS, COUNT_COLOURS, 34 },
    { "SKIN", NULL, 0, 0, FIELD(skin), RAMP_SKIN, COUNT_SKIN, 0 },
    { "EYES", NULL, 0, 0, FIELD(eyes), RAMP_EYES, COUNT_EYES, 0 },
};
static const int TAB_COUNT = sizeof(TABS) / sizeof(TABS[0]);

static void randomise(Look *look)
{
    look->body = rand() % 2;
    look->hair = rand() % 8;
    look->hat = rand() % 6;
    look->top = rand() % 4;
    look->scarf = rand() % 2;
    look->bottoms = rand() % 4;
    look->shoes = rand() % 3;
    look->skin = rand() % COUNT_SKIN;
    look->eyes = rand() % COUNT_EYES;
    look->hair_colour = rand() % COUNT_COLOURS;
    look->hat_colour = rand() % COUNT_COLOURS;
    look->top_colour = rand() % COUNT_COLOURS;
    look->bottoms_colour = rand() % COUNT_COLOURS;
    look->shoe_colour = rand() % COUNT_COLOURS;
    look->scarf_colour = rand() % COUNT_COLOURS;
}

// The controls work on items, apart from the drawing below. Each tab's items run in order:
// its shapes, its colours, Random, Confirm. Touch and the d-pad both end up here.
struct Creator
{
    int tab;
    int cursor;  // item the d-pad is on
};

static int item_count(const Tab &t)
{
    return t.name_count + t.swatch_count + 2;
}

static void open_tab(Creator *c, const Look *look, int tab)
{
    c->tab = (tab + TAB_COUNT) % TAB_COUNT;
    const Tab &t = TABS[c->tab];
    const u8 *fields = (const u8 *)look;
    c->cursor = t.name_count ? fields[t.shape] : fields[t.colour];
}

// Returns true when the player confirmed.
static bool creator_pick(Look *look, const Creator *c, int item)
{
    u8 *fields = (u8 *)look;
    const Tab &t = TABS[c->tab];
    if (item < t.name_count)
        fields[t.shape] = item;
    else if (item < t.name_count + t.swatch_count)
        fields[t.colour] = item - t.name_count;
    else if (item == t.name_count + t.swatch_count)
        randomise(look);
    else
        return true;
    return false;
}

// --- Drawing and tap areas: the Frost Night skin, art from tools/art/make_ui.py. ---

// The screen is laid out in 8-pixel cells, shifted to centre 31 columns and 22 rows.
static const int SHIFT = 4, SHIFT_Y = 8, COLUMNS = 31;
static const int TAB_X = 2, TAB_W = 3, TITLE_ROW = 3, GRID_ROW = 5, TILE_W = 7, TILE_H = 6, TILE_PITCH = 8;
static const int STRIP_ROW = 17, STRIP_X = 2, STRIP_SHOWN = 14, BUTTON_ROW = 20;
static const int RANDOM_END = 10, BACK_END = 17;
static const int MAP_TEXT = 14, MAP_PANELS = 15;
static const int TAP_BACK = -2;

static u16 *text_map(void) { return (u16 *)BG_MAP_RAM_SUB(MAP_TEXT); }
static u16 *panel_map(void) { return (u16 *)BG_MAP_RAM_SUB(MAP_PANELS); }

static void text(int x, int y, const char *s, int bank)
{
    u16 *map = text_map();
    for (; *s; s++, x++)
    {
        int tile = UI_TILE_FONT + (*s - 32) * 2;
        map[y * 32 + x] = tile | (bank << 12);
        map[(y + 1) * 32 + x] = (tile + 1) | (bank << 12);
    }
}

static void panel(int x, int y, int w, int h, int bank)
{
    u16 *map = panel_map();
    for (int yy = 0; yy < h; yy++)
    {
        int row = yy == 0 ? 0 : yy == h - 1 ? 2 : 1;
        for (int xx = 0; xx < w; xx++)
        {
            int col = xx == 0 ? 0 : xx == w - 1 ? 2 : 1;
            map[(y + yy) * 32 + x + xx] = (UI_TILE_PANEL + row * 3 + col) | (bank << 12);
        }
    }
}

// Option tiles show the frame as sprites: 8bpp 64x32, the two screens' palettes kept the same.
static const int SHOWN_ROWS = 32;
static u16 *preview_gfx[8];
static u8 preview_tiles[64 * SHOWN_ROWS] __attribute__((aligned(32)));
static u8 preview_frame[FRAME_BYTES];

static void draw_preview(const Look *look, int i, int top_row)
{
    u8 *saved = target;
    target = preview_frame;
    look_compose(look, 2, 0);
    target = saved;
    new_pixels = false;
    // Sprites are stored as 8x8 tiles.
    u8 *out = preview_tiles;
    for (int ty = 0; ty < SHOWN_ROWS / 8; ty++)
        for (int tx = 0; tx < 8; tx++)
            for (int y = 0; y < 8; y++, out += 8)
                memcpy(out, preview_frame + (top_row + ty * 8 + y) * 64 + tx * 8, 8);
    DC_FlushRange(preview_tiles, sizeof(preview_tiles));
    dmaCopy(preview_tiles, preview_gfx[i], sizeof(preview_tiles));
}

static int strip_first(const Look *look, const Creator *c)
{
    const Tab &t = TABS[c->tab];
    bool on_strip = c->cursor >= t.name_count && c->cursor < t.name_count + t.swatch_count;
    int shown = on_strip ? c->cursor - t.name_count : ((const u8 *)look)[t.colour];
    int first = shown - STRIP_SHOWN / 2;
    if (first > t.swatch_count - STRIP_SHOWN)
        first = t.swatch_count - STRIP_SHOWN;
    return first < 0 ? 0 : first;
}

static void creator_draw(const Look *look, const Creator *c)
{
    const Tab &t = TABS[c->tab];
    const u8 *fields = (const u8 *)look;
    const int random_item = t.name_count + t.swatch_count;
    dmaFillHalfWords(0, text_map(), 2048);
    dmaFillHalfWords(0, panel_map(), 2048);

    for (int i = 0; i < TAB_COUNT; i++)
    {
        int x = TAB_X + i * TAB_W;
        panel(x, 0, TAB_W, TAB_W, i == c->tab ? BANK_SELECTED : BANK_PANEL);
        for (int yy = 0; yy < 3; yy++)
            for (int xx = 0; xx < 3; xx++)
                text_map()[yy * 32 + x + xx] = (UI_TILE_ICON + i * 9 + yy * 3 + xx) |
                                               ((i == c->tab ? BANK_ICON_ON : BANK_ICON) << 12);
    }

    panel(0, TITLE_ROW, COLUMNS, 2, BANK_PANEL);
    text(1, TITLE_ROW, t.label, BANK_GOLD_TEXT);
    if (t.name_count)
    {
        char line[16];
        sprintf(line, "Style %d of %d", fields[t.shape] + 1, t.name_count);
        text(8, TITLE_ROW, line, BANK_TEXT);
        const char *name = t.names[fields[t.shape]];
        text(COLUMNS - 1 - strlen(name), TITLE_ROW, name, BANK_TEXT);
    }
    else
    {
        text(8, TITLE_ROW, "Pick a colour", BANK_TEXT);
    }

    for (int i = 0; i < 8; i++)
    {
        if (i >= t.name_count)
        {
            oamSetHidden(&oamSub, i, true);
            continue;
        }
        int x = (i % 4) * TILE_PITCH, y = GRID_ROW + (i / 4) * TILE_H;
        bool selected = fields[t.shape] == i;
        panel(x, y, TILE_W, TILE_H, c->cursor == i ? BANK_FOCUS : selected ? BANK_SELECTED : BANK_PANEL);
        if (selected)
        {
            // The bar fits 7 letters: the first word here, the full name in the title.
            char word[TILE_W + 1];
            snprintf(word, sizeof(word), "%s", t.names[i]);
            word[strcspn(word, " ")] = 0;
            panel(x, y + TILE_H - 2, TILE_W, 2, BANK_SOLID);
            text(x + (TILE_W - strlen(word)) / 2, y + TILE_H - 2, word, BANK_DARK_TEXT);
        }
        Look shown = *look;
        ((u8 *)&shown)[t.shape] = i;
        if (c->tab == 1)
            shown.hat = 0; // hair shows without a hat
        draw_preview(&shown, i, t.preview_y);
        oamSet(&oamSub, i, x * 8 + SHIFT + (TILE_W * 8 - 64) / 2, y * 8 + SHIFT_Y + 3, 0, 0, SpriteSize_64x32,
               SpriteColorFormat_256Color, preview_gfx[i], -1, false, false, false, false, false);
    }

    int first = strip_first(look, c);
    for (int n = 0; n < STRIP_SHOWN && first + n < t.swatch_count; n++)
    {
        int i = first + n;
        const u16 *shades = (const u16 *)look_ramps_bin + (t.ramp + i) * LOOK_SHADES;
        int bank = BANK_SWATCH + n / 12, k = 1 + n % 12;
        BG_PALETTE_SUB[bank * 16 + k] = shades[LOOK_SWATCH_SHADE];
        BG_PALETTE_SUB[bank * 16 + 13] = UI_ICE;
        BG_PALETTE_SUB[bank * 16 + 14] = UI_WHITE;
        BG_PALETTE_SUB[bank * 16 + 15] = UI_GOLD;
        int border = c->cursor == t.name_count + i ? 2 : fields[t.colour] == i ? 1 : 0;
        int tile = UI_TILE_SWATCH + ((k - 1) * 3 + border) * 4;
        for (int q = 0; q < 4; q++)
            text_map()[(STRIP_ROW + q / 2) * 32 + STRIP_X + n * 2 + q % 2] = (tile + q) | (bank << 12);
    }
    if (t.swatch_count > STRIP_SHOWN)
    {
        text(1, STRIP_ROW, "<", first ? BANK_TEXT : BANK_ICON);
        text(COLUMNS - 1, STRIP_ROW, ">", first + STRIP_SHOWN < t.swatch_count ? BANK_TEXT : BANK_ICON);
    }

    panel(0, BUTTON_ROW, RANDOM_END - 1, 2, c->cursor == random_item ? BANK_FOCUS : BANK_PANEL);
    text(1, BUTTON_ROW, "X", BANK_GOLD_TEXT);
    text(3, BUTTON_ROW, "Random", BANK_TEXT);
    panel(RANDOM_END, BUTTON_ROW, BACK_END - RANDOM_END - 1, 2, BANK_PANEL);
    text(RANDOM_END + 1, BUTTON_ROW, "B Back", BANK_TEXT);
    text(RANDOM_END + 1, BUTTON_ROW, "B", BANK_GOLD_TEXT);
    bool on_confirm = c->cursor == random_item + 1;
    panel(BACK_END, BUTTON_ROW, COLUMNS - BACK_END, 2, on_confirm ? BANK_FOCUS : BANK_SOLID);
    text(BACK_END + 1, BUTTON_ROW, "START Confirm", on_confirm ? BANK_TEXT : BANK_DARK_TEXT);
    oamUpdate(&oamSub);
}

// The item under a tap, TAP_BACK, or -1. A tap on a tab opens it instead.
static int creator_tap(Creator *c, const Look *look, int px, int py)
{
    const Tab &t = TABS[c->tab];
    int cx = (px - SHIFT) / 8, cy = (py - SHIFT_Y) / 8;
    if (cy < TITLE_ROW)
    {
        int i = (cx - TAB_X) / TAB_W;
        if (cx >= TAB_X && i < TAB_COUNT)
            open_tab(c, look, i);
    }
    else if (cy >= GRID_ROW && cy < STRIP_ROW)
    {
        int i = cx / TILE_PITCH + (cy - GRID_ROW) / TILE_H * 4;
        if (i < t.name_count)
            return i;
    }
    else if (cy >= STRIP_ROW && cy < STRIP_ROW + 2)
    {
        int first = strip_first(look, c);
        int colour = ((const u8 *)look)[t.colour];
        if (cx < STRIP_X)
            colour--;
        else if (cx >= STRIP_X + STRIP_SHOWN * 2)
            colour++;
        else
            colour = first + (cx - STRIP_X) / 2;
        if (colour >= 0 && colour < t.swatch_count)
            return t.name_count + colour;
    }
    else if (cy >= BUTTON_ROW - 1)
    {
        int random_item = t.name_count + t.swatch_count;
        return cx < RANDOM_END ? random_item : cx < BACK_END ? TAP_BACK : random_item + 1;
    }
    return -1;
}

// Top screen.
static NE_Material *stage_mat, *boy_mat, *girl_mat;
static NE_Palette *stage_pal, *boy_pal, *girl_pal;
static bool stage_girl;

static const int FLAKES = 24;
static s16 flake_x[FLAKES], flake_y[FLAKES];

static NE_Material *stage_texture(int size_y, int size_x, const void *tex, const void *pal, NE_Palette **out)
{
    NE_Material *m = NE_MaterialCreate();
    NE_MaterialTexLoad(m, NE_PAL16, size_x, size_y, NE_TEXGEN_TEXCOORD, tex);
    *out = NE_PaletteCreate();
    NE_PaletteLoad(*out, pal, 16, NE_PAL16);
    NE_MaterialSetPalette(m, *out);
    return m;
}

static void creator_scene(void)
{
    NE_2DViewInit();
    NE_PolyFormat(31, 0, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_2DDrawTexturedQuad(0, 0, 256, 256, 3, stage_mat);
    NE_2DDrawTexturedQuad(181, 7, 245, 23, 2, stage_girl ? girl_mat : boy_mat);
    for (int i = 0; i < FLAKES; i++)
        NE_2DDrawQuad(flake_x[i], flake_y[i], flake_x[i] + 2, flake_y[i] + 2, 2, NE_White);
    NE_2DDrawTexturedQuad(64, 32, 192, 160, 1, material);
}

static void bottom_screen_start(void)
{
    vramSetBankI(VRAM_I_SUB_SPRITE);
    videoSetModeSub(MODE_0_2D);
    bgInitSub(0, BgType_Text4bpp, BgSize_T_256x256, MAP_TEXT, 0);
    bgInitSub(1, BgType_Text4bpp, BgSize_T_256x256, MAP_PANELS, 0);
    REG_BG0HOFS_SUB = -SHIFT;
    REG_BG1HOFS_SUB = -SHIFT;
    REG_BG0VOFS_SUB = -SHIFT_Y;
    REG_BG1VOFS_SUB = -SHIFT_Y;
    dmaCopy(ui_tiles_bin, BG_TILE_RAM_SUB(0), ui_tiles_bin_size);
    dmaCopy(ui_pal_bin, BG_PALETTE_SUB, ui_pal_bin_size);
    oamInit(&oamSub, SpriteMapping_1D_32, false);
    for (int i = 0; i < 8; i++)
        preview_gfx[i] = oamAllocateGfx(&oamSub, SpriteSize_64x32, SpriteColorFormat_256Color);
}

static void bottom_screen_stop(void)
{
    for (int i = 0; i < 8; i++)
        oamFreeGfx(&oamSub, preview_gfx[i]);
    oamClear(&oamSub, 0, 0);
    oamUpdate(&oamSub);
    oamDisable(&oamSub);
    REG_BG0HOFS_SUB = 0;
    REG_BG1HOFS_SUB = 0;
    REG_BG0VOFS_SUB = 0;
    REG_BG1VOFS_SUB = 0;
}

static void creator_refresh(const Look *look, const Creator *c)
{
    look_apply(look);
    DC_FlushRange(colours, sizeof(colours));
    dmaCopy(colours, SPRITE_PALETTE_SUB, sizeof(colours));
    creator_draw(look, c);
    stage_girl = look->body != 0;
}

void creator_run(Look *look)
{
    bottom_screen_start();
    stage_mat = stage_texture(256, 256, ui_top_tex_bin, ui_top_pal_bin, &stage_pal);
    boy_mat = stage_texture(16, 64, ui_boy_tex_bin, ui_boy_pal_bin, &boy_pal);
    girl_mat = stage_texture(16, 64, ui_girl_tex_bin, ui_girl_pal_bin, &girl_pal);
    for (int i = 0; i < FLAKES; i++)
    {
        flake_x[i] = rand() % 256;
        flake_y[i] = rand() % 192;
    }

    Creator c = { 0, 0 };
    open_tab(&c, look, 1);
    int tick = 0, facing = 0;
    bool confirmed = false, walking = false;
    keysSetRepeat(20, 6);
    creator_refresh(look, &c);
#ifdef TEST_TAPS
    static const u8 taps[][2] = TEST_TAPS;
    unsigned next_tap = 0;
#endif
#ifdef TEST_PRESSES
    static const u32 presses[] = TEST_PRESSES;
    unsigned next_press = 0;
#endif

    while (!confirmed)
    {
        NE_WaitForVBL((NE_UpdateFlags)0);
        look_upload();
        scanKeys();
        u32 down = keysDown();
        u32 repeat = keysDownRepeat();
        touchPosition touch;
        touchRead(&touch);
        int tap_x = touch.px, tap_y = touch.py;
        tick++;
#ifdef TEST_TAPS
        if (tick % 45 == 0 && next_tap < sizeof(taps) / sizeof(taps[0]))
        {
            down |= KEY_TOUCH;
            tap_x = taps[next_tap][0];
            tap_y = taps[next_tap][1];
            next_tap++;
        }
#endif
#ifdef TEST_PRESSES
        if (tick % 30 == 0 && next_press < sizeof(presses) / sizeof(presses[0]))
        {
            down |= presses[next_press];
            repeat |= presses[next_press];
            next_press++;
        }
#endif
        int count = item_count(TABS[c.tab]);
        bool changed = true;
        if (down & KEY_TOUCH)
        {
            int item = creator_tap(&c, look, tap_x, tap_y);
            if (item == TAP_BACK)
            {
                open_tab(&c, look, c.tab - 1);
            }
            else if (item >= 0)
            {
                c.cursor = item;
                confirmed = creator_pick(look, &c, item);
            }
        }
        else if (repeat & KEY_LEFT)
            open_tab(&c, look, c.tab - 1);
        else if (repeat & KEY_RIGHT)
            open_tab(&c, look, c.tab + 1);
        else if (repeat & KEY_UP)
            c.cursor = (c.cursor + count - 1) % count;
        else if (repeat & KEY_DOWN)
            c.cursor = (c.cursor + 1) % count;
        else if (down & KEY_A)
            confirmed = creator_pick(look, &c, c.cursor);
        else if (down & KEY_B)
            open_tab(&c, look, c.tab - 1);
        else if (down & KEY_X)
            randomise(look);
        else if (down & KEY_START)
            confirmed = true;
        else
            changed = false;
        if (changed)
            creator_refresh(look, &c);

        if (down & KEY_L)
            facing = (facing + 3) % 4;
        if (down & KEY_R)
            facing = (facing + 1) % 4;
        if (down & KEY_Y)
            walking = !walking;

        for (int i = 0; i < FLAKES; i++)
        {
            if (tick % (1 + i % 3) == 0)
                flake_y[i]++;
            if (flake_y[i] > 140)
            {
                flake_y[i] = 0;
                flake_x[i] = rand() % 256;
            }
        }

        static const int ROWS[] = { 2, 1, 0, 3 }; // down, left, up, right
        const int STRIDE = 6;
        look_compose(look, ROWS[facing], walking ? 1 + (tick / STRIDE) % 8 : 0);
        NE_Process(creator_scene);
    }

    NE_MaterialDelete(stage_mat);
    NE_MaterialDelete(boy_mat);
    NE_MaterialDelete(girl_mat);
    NE_PaletteDelete(stage_pal);
    NE_PaletteDelete(boy_pal);
    NE_PaletteDelete(girl_pal);
    bottom_screen_stop();
}
