#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "look.h"
#include "look_bin.h"
#include "look_data.h"
#include "look_ramps_bin.h"

// ---------------------------------------------------------------------------
// Combining layers. The layer data is written by tools/art/make_look.py.

static const int FRAME_BYTES = 64 * 64;
static const int FOOT_SHIFT = 2; // LPC feet end above the frame's bottom edge

static NE_Material *material;
static NE_Palette *palette;
static u8 pixels[FRAME_BYTES] __attribute__((aligned(32)));
static u16 colours[256] __attribute__((aligned(32)));
static bool new_pixels, new_colours;

// Option numbers that the rules below care about.
enum { HAIR_SHORT = 0, HAIR_SPIKY = 2, HAT_NONE = 0, HAT_HOOD = 4, HAT_EARMUFFS = 5, BOTTOMS_SHORTS = 2 };

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

static void blit(int body, int layer, int row, int frame)
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
            if (*src && y < 64)
                pixels[y * 64 + x] = *src;
    }
}

void look_compose(const Look *look, int row, int frame)
{
    int body = look->body;
    memset(pixels, 0, sizeof(pixels));
    blit(body, LAYER_BODY, row, frame);
    bool over_leggings = look->bottoms >= BOTTOMS_SHORTS;
    blit(body, over_leggings ? LAYER_LEGS_UNDER : LAYER_LEGS + look->bottoms, row, frame);
    blit(body, LAYER_FEET + look->shoes, row, frame);
    if (over_leggings)
        blit(body, LAYER_BOTTOMS + look->bottoms - BOTTOMS_SHORTS, row, frame);
    blit(body, LAYER_TOP + look->top, row, frame);
    blit(body, LAYER_HEAD, row, frame);
    if (look->hat != HAT_HOOD)
    {
        // Spikes only show with nothing on top; under a hat, spiky hair is short hair.
        bool flat = look->hair == HAIR_SPIKY && look->hat != HAT_NONE && look->hat != HAT_EARMUFFS;
        blit(body, LAYER_HAIR + (flat ? HAIR_SHORT : look->hair), row, frame);
    }
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
// The creator: the trainer turns and walks on the top screen, with touch tabs below.
// The screen is 32x24 text cells, and a tap is worked out by cell.

static const char *const HAIR_NAMES[] = { "Short", "Crop", "Spiky", "Shaggy", "Wavy", "Ponytail", "Bob", "Braids" };
static const char *const HAT_NAMES[] = { "None", "Beanie", "Knit cap", "Ball cap", "Hood", "Earmuffs" };
static const char *const TOP_NAMES[] = { "Jacket", "Parka", "Vest", "Long coat" };
static const char *const BOTTOM_NAMES[] = { "Trousers", "Leggings", "Shorts", "Skirt" };
static const char *const SHOE_NAMES[] = { "Snow boots", "Tall boots", "Sneakers" };
static const char *const BODY_NAMES[] = { "Boy", "Girl" };
static const char *const SCARF_NAMES[] = { "Off", "On" };

struct Tab
{
    const char *label;
    int x, y;                    // label cell
    const char *const *names;    // shape choices, if any
    int name_count;
    size_t shape;                // Look field the shapes set
    size_t colour;               // Look field the swatches set, if swatch_count
    int ramp, swatch_count;
};

#define FIELD(f) offsetof(Look, f)
static const Tab TABS[] = {
    { "Body", 1, 2, BODY_NAMES, 2, FIELD(body), 0, 0, 0 },
    { "Hair", 7, 2, HAIR_NAMES, 8, FIELD(hair), FIELD(hair_colour), RAMP_HAIR, COUNT_COLOURS },
    { "Hat", 13, 2, HAT_NAMES, 6, FIELD(hat), FIELD(hat_colour), RAMP_COLOURS, COUNT_COLOURS },
    { "Top", 18, 2, TOP_NAMES, 4, FIELD(top), FIELD(top_colour), RAMP_COLOURS, COUNT_COLOURS },
    { "Scarf", 23, 2, SCARF_NAMES, 2, FIELD(scarf), FIELD(scarf_colour), RAMP_COLOURS, COUNT_COLOURS },
    { "Bottoms", 1, 4, BOTTOM_NAMES, 4, FIELD(bottoms), FIELD(bottoms_colour), RAMP_COLOURS, COUNT_COLOURS },
    { "Shoes", 10, 4, SHOE_NAMES, 3, FIELD(shoes), FIELD(shoe_colour), RAMP_COLOURS, COUNT_COLOURS },
    { "Skin", 17, 4, NULL, 0, 0, FIELD(skin), RAMP_SKIN, COUNT_SKIN },
    { "Eyes", 23, 4, NULL, 0, 0, FIELD(eyes), RAMP_EYES, COUNT_EYES },
};
static const int TAB_COUNT = sizeof(TABS) / sizeof(TABS[0]);

static void randomise(Look *look)
{
    u8 version = look->version;
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
    look->version = version;
}

// The controls work on items, so a new skin only replaces the drawing below. Each tab's items
// run in order: its shapes, its colours, Random, Confirm. Touch and the d-pad both end up here.
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
    c->cursor = t.name_count ? ((const u8 *)look)[t.shape] : ((const u8 *)look)[t.colour];
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

// --- Drawing and tap areas: the part a new skin replaces. ---

static const int OPTIONS_ROW = 6, SWATCH_ROW = 15, BUTTON_ROW = 22;
// Solid tiles past the console font, one per colour number in a palette bank. The console only
// uses entry 15 of each bank, so entries 1-14 are free for swatches.
static const int SOLID_TILE = 300, BANK_COLOURS = 14;

static void swatch_cell(int x, int y, int i)
{
    u16 *map = (u16 *)BG_MAP_RAM_SUB(2);
    map[y * 32 + x] = (SOLID_TILE + i % BANK_COLOURS) | ((1 + i / BANK_COLOURS) << 12);
}

static void creator_draw(const Look *look, const Creator *c)
{
    const Tab &t = TABS[c->tab];
    const u8 *fields = (const u8 *)look;
    const int random_item = t.name_count + t.swatch_count;
    consoleClear();
    printf("\x1b[0;1HCreate your trainer");
    for (int i = 0; i < TAB_COUNT; i++)
    {
        printf("\x1b[%d;%dH%s", TABS[i].y, TABS[i].x, TABS[i].label);
        if (i == c->tab)
            printf("\x1b[%d;%dH%.*s", TABS[i].y + 1, TABS[i].x, (int)strlen(TABS[i].label), "-------");
    }
    for (int i = 0; i < t.name_count; i++)
    {
        char mark = c->cursor == i ? '>' : fields[t.shape] == i ? '*' : ' ';
        printf("\x1b[%d;%dH%c%s", OPTIONS_ROW + 1 + (i / 2) * 2, 1 + (i % 2) * 15, mark, t.names[i]);
    }
    for (int i = 0; i < t.swatch_count; i++)
    {
        const u16 *shades = (const u16 *)look_ramps_bin + (t.ramp + i) * LOOK_SHADES;
        BG_PALETTE_SUB[(1 + i / BANK_COLOURS) * 16 + 1 + i % BANK_COLOURS] = shades[LOOK_SWATCH_SHADE];
        int x = 2 + (i % 10) * 3, y = SWATCH_ROW + (i / 10) * 2;
        for (int yy = 0; yy < 2; yy++)
            for (int xx = 0; xx < 2; xx++)
                swatch_cell(x + xx, y + yy, i);
        if (c->cursor == t.name_count + i)
            printf("\x1b[%d;%dH>", y, x - 1);
        else if (fields[t.colour] == i)
            printf("\x1b[%d;%dH*", y, x - 1);
    }
    printf("\x1b[%d;1H%c[ Random ]", BUTTON_ROW, c->cursor == random_item ? '>' : ' ');
    printf("\x1b[%d;18H%c[ Confirm ]", BUTTON_ROW, c->cursor == random_item + 1 ? '>' : ' ');
    printf("\x1b[23;1HX random  Start confirm  B back");
}

// The item under a tap, or -1. A tap on a tab opens it instead.
static int creator_tap(Creator *c, const Look *look, int cx, int cy)
{
    const Tab &t = TABS[c->tab];
    if (cy >= 1 && cy <= 4)
    {
        // Each tab reaches from its label to the next tab's.
        int row = cy <= 2 ? 2 : 4;
        for (int i = TAB_COUNT - 1; i >= 0; i--)
        {
            if (TABS[i].y == row && cx >= TABS[i].x - 1)
            {
                open_tab(c, look, i);
                break;
            }
        }
    }
    else if (cy >= OPTIONS_ROW && cy < SWATCH_ROW - 1)
    {
        int i = (cy - OPTIONS_ROW) / 2 * 2 + (cx >= 16 ? 1 : 0);
        if (i < t.name_count)
            return i;
    }
    else if (cy >= SWATCH_ROW && cy < SWATCH_ROW + 6)
    {
        int i = (cy - SWATCH_ROW) / 2 * 10 + (cx - 1) / 3;
        if (cx >= 1 && cx < 31 && i < t.swatch_count)
            return t.name_count + i;
    }
    else if (cy >= BUTTON_ROW - 1)
    {
        return t.name_count + t.swatch_count + (cx >= 16 ? 1 : 0);
    }
    return -1;
}

static void creator_scene(void)
{
    NE_2DViewInit();
    NE_PolyFormat(31, 0, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_2DDrawTexturedQuad(64, 32, 192, 160, 0, material);
}

void creator_run(Look *look)
{
    // One solid tile per colour number.
    u32 *tiles = (u32 *)BG_TILE_RAM_SUB(1) + SOLID_TILE * 8;
    for (int i = 0; i < BANK_COLOURS; i++)
        for (int w = 0; w < 8; w++)
            tiles[i * 8 + w] = 0x11111111u * (i + 1);

    Creator c = { 0, 0 };
    open_tab(&c, look, 1);
    int tick = 0;
    bool confirmed = false;
    keysSetRepeat(20, 6);
    creator_draw(look, &c);
    look_apply(look);
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
            tap_x = taps[next_tap][0] * 8;
            tap_y = taps[next_tap][1] * 8;
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
            int item = creator_tap(&c, look, tap_x / 8, tap_y / 8);
            if (item >= 0)
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
        {
            creator_draw(look, &c);
            look_apply(look);
        }

        // Stand, then walk, facing each way in turn: down, left, up, right.
        static const int ROWS[] = { 2, 1, 0, 3 };
        const int STAND = 30, STRIDE = 6;
        int t = tick % (STAND + STRIDE * 8);
        int row = ROWS[(tick / (STAND + STRIDE * 8)) % 4];
        look_compose(look, row, t < STAND ? 0 : 1 + (t - STAND) / STRIDE);
        NE_Process(creator_scene);
    }
    consoleClear();
}
