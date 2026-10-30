#include <stdio.h>
#include <string.h>

#include <NEMain.h>
#include <fat.h>
#include <nds.h>

#include "player_pal_bin.h"
#include "player_tex_bin.h"
#include "saltmere.h"
#include "saltmere_bin.h"
#include "saltmere_pal_bin.h"
#include "saltmere_tex_bin.h"

// ---------------------------------------------------------------------------
// Save test: a counter that goes up with A and survives a restart.
// Tries a save file next to the ROM (DLDI/SD, flashcarts and melonDS with DLDI on)
// and falls back to the cartridge save chip (what Delta stores as its .sav).

struct SaveData
{
    u32 magic;
    u32 counter;
};

static const u32 SAVE_MAGIC = 0x56533942; // "B9SV"

enum class Backend { None, File, Cart };

static Backend backend = Backend::None;
static char save_path[256];
static int cart_type = -1;

static void save_init(int argc, char **argv)
{
    if (fatInitDefault())
    {
        if (argc > 0 && argv[0] != NULL && strlen(argv[0]) > 4 && strlen(argv[0]) < sizeof(save_path))
        {
            // Same name as the ROM, with .sav instead of .nds.
            strcpy(save_path, argv[0]);
            strcpy(save_path + strlen(save_path) - 4, ".sav");
        }
        else
        {
            strcpy(save_path, "fat:/beyond-the-nine.sav");
        }
        backend = Backend::File;
        return;
    }

    sysSetCardOwner(true);
    cart_type = cardEepromGetType();
    // If detection finds nothing, assume the 64 KB EEPROM that melonDS gives unknown games.
    if (cart_type <= 0)
        cart_type = 2;
    backend = Backend::Cart;
}

// One byte on the save chip's SPI bus. The last byte of a command goes out with HOLD
// cleared, which ends the command. libnds' cardWriteEeprom() ends commands by turning
// the bus off instead, and melonDS 1.1 (Delta's core) never commits writes ended that way.
static u8 spi_byte(u8 value, bool last)
{
    REG_AUXSPICNT = CARD_ENABLE | CARD_SPI_ENABLE | (last ? 0 : CARD_SPI_HOLD) | CARD_SPI_BAUD_4MHz;
    REG_AUXSPIDATA = value;
    eepromWaitBusy();
    return REG_AUXSPIDATA;
}

// Writes up to one page (32 bytes for EEPROM, 256 for FLASH) at a page-aligned address.
static void cart_write(u32 address, const u8 *data, u32 length)
{
    spi_byte(SPI_EEPROM_WREN, true);

    if (cart_type == 1)
    {
        spi_byte(SPI_EEPROM_PP | ((address & BIT(8)) >> 5), false);
        spi_byte(address & 0xFF, false);
    }
    else
    {
        // FLASH (type 3) uses page write, which erases the page first.
        spi_byte(cart_type == 3 ? SPI_EEPROM_PW : SPI_EEPROM_PP, false);
        if (cart_type == 3)
            spi_byte((address >> 16) & 0xFF, false);
        spi_byte((address >> 8) & 0xFF, false);
        spi_byte(address & 0xFF, false);
    }
    for (u32 i = 0; i < length; i++)
        spi_byte(data[i], i == length - 1);

    u8 status;
    do
    {
        spi_byte(SPI_EEPROM_RDSR, false);
        status = spi_byte(0, true);
    } while (status & 1); // write in progress

    REG_AUXSPICNT = CARD_SPI_HOLD | CARD_SPI_BAUD_4MHz;
}

static bool save_read(SaveData *data)
{
    if (backend == Backend::File)
    {
        FILE *f = fopen(save_path, "rb");
        if (f == NULL)
            return false;
        bool ok = fread(data, sizeof(*data), 1, f) == 1;
        fclose(f);
        return ok && data->magic == SAVE_MAGIC;
    }
    if (backend == Backend::Cart)
    {
        cardReadEeprom(0, (u8 *)data, sizeof(*data), cart_type);
        return data->magic == SAVE_MAGIC;
    }
    return false;
}

static bool save_write(SaveData *data)
{
    if (backend == Backend::File)
    {
        FILE *f = fopen(save_path, "wb");
        if (f == NULL)
            return false;
        bool ok = fwrite(data, sizeof(*data), 1, f) == 1;
        fclose(f);
        return ok;
    }
    if (backend == Backend::Cart)
    {
        cart_write(0, (const u8 *)data, sizeof(*data));
        SaveData check;
        cardReadEeprom(0, (u8 *)&check, sizeof(check), cart_type);
        return check.magic == data->magic && check.counter == data->counter;
    }
    return false;
}

// ---------------------------------------------------------------------------
// Overworld: Port Saltmere block-out with a tile-by-tile player.

// The model is built at 1 tile = 0.25 units, centred on the map (see `make models`).
static const float TILE = 0.25f;
static const int STEP_FRAMES = 12; // frames to walk one tile

enum Dir { DOWN, UP, LEFT, RIGHT };
static const int DX[] = { 0, 0, -1, 1 };
static const int DY[] = { 1, -1, 0, 0 };

struct Player
{
    int tx, ty;  // tile
    int dir;     // also the row in the sprite sheet
    int step;    // frames left in the current step, 0 when standing
    int foot;    // which foot leads this step: walk frame 1 or 2
};

static NE_Camera *camera;
static NE_Model *town;
static NE_Material *player_mat;
static Player player;
static float cam_x, cam_z;

static float tile_x(int tx) { return (tx + 0.5f - SALTMERE_W / 2.0f) * TILE; }
static float tile_z(int ty) { return (ty + 0.5f - SALTMERE_H / 2.0f) * TILE; }

static bool walkable(int tx, int ty)
{
    if (tx < 0 || ty < 0 || tx >= SALTMERE_W || ty >= SALTMERE_H)
        return false;
    char t = saltmere_map[ty][tx];
    return t == '.' || t == ',' || t == 'P';
}

static void player_update(u32 held)
{
    if (player.step > 0)
    {
        player.step--;
        return;
    }

    int dir = -1;
    if (held & KEY_DOWN)
        dir = DOWN;
    else if (held & KEY_UP)
        dir = UP;
    else if (held & KEY_LEFT)
        dir = LEFT;
    else if (held & KEY_RIGHT)
        dir = RIGHT;
    if (dir < 0)
        return;

    player.dir = dir;
    int nx = player.tx + DX[dir];
    int ny = player.ty + DY[dir];
    if (!walkable(nx, ny))
        return;
    player.tx = nx;
    player.ty = ny;
    player.step = STEP_FRAMES;
    player.foot = player.foot == 1 ? 2 : 1;
}

// Where the player is drawn this frame: between the previous and the current tile.
static void player_pos(float *x, float *z)
{
    float t = (float)player.step / STEP_FRAMES;
    *x = tile_x(player.tx) - DX[player.dir] * TILE * t;
    *z = tile_z(player.ty) - DY[player.dir] * TILE * t;
}

static void draw_player(void)
{
    float px, pz;
    player_pos(&px, &pz);

    // Walk frame: the leading foot for the first half of a step, then standing.
    int frame = player.step > STEP_FRAMES / 2 ? player.foot : 0;
    int u0 = frame * 32, v0 = player.dir * 32;

    NE_ViewPush();
    NE_ViewMove(px, 0, pz);
    NE_PolyFormat(31, 1, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_MaterialUse(player_mat);

    // A 32x32 billboard leaning back to face the camera (about 39 degrees down).
    const float w = 0.16f, h = 0.32f, up = 0.78f, back = -0.63f;
    NE_PolyBegin(GL_QUAD);
    NE_PolyColor(RGB15(31, 31, 31));
    NE_PolyTexCoord(u0, v0 + 32);
    NE_PolyVertex(-w, 0, 0);
    NE_PolyTexCoord(u0 + 32, v0 + 32);
    NE_PolyVertex(w, 0, 0);
    NE_PolyTexCoord(u0 + 32, v0);
    NE_PolyVertex(w, h * up, h * back);
    NE_PolyTexCoord(u0, v0);
    NE_PolyVertex(-w, h * up, h * back);
    NE_PolyEnd();

    NE_ViewPop();
}

static void draw_scene(void)
{
    // Black 2 style: high and behind, tilted down at the player.
    NE_CameraSet(camera,
                 cam_x, 1.5f, cam_z + 1.7f,
                 cam_x, 0.0f, cam_z - 0.15f,
                 0, 1, 0);
    NE_CameraUse(camera);

    NE_PolyFormat(31, 0, (NE_LightEnum)0, NE_CULL_NONE, (NE_OtherFormatEnum)0);
    NE_ModelDraw(town);
    draw_player();
}

int main(int argc, char **argv)
{
    irqEnable(IRQ_HBLANK);
    irqSet(IRQ_VBLANK, NE_VBLFunc);
    irqSet(IRQ_HBLANK, NE_HBLFunc);

    NE_Init3D();
    NE_SetFov(50);
    NE_ClearColorSet(RGB15(4, 7, 14), 31, 63); // deep navy sea and sky

    // Bottom screen console on VRAM H, so it can't collide with Nitro Engine's
    // texture banks (A-D).
    PrintConsole bottomScreen;
    videoSetModeSub(MODE_0_2D);
    vramSetBankH(VRAM_H_SUB_BG);
    consoleInit(&bottomScreen, 0, BgType_Text4bpp, BgSize_T_256x256, 2, 1, false, true);

    camera = NE_CameraCreate();
    town = NE_ModelCreate(NE_Static);
    NE_ModelLoadStaticMesh(town, saltmere_bin);

    NE_Material *town_mat = NE_MaterialCreate();
    NE_MaterialTexLoad(town_mat, NE_PAL256, 128, 128, NE_TEXGEN_TEXCOORD, saltmere_tex_bin);
    NE_Palette *town_pal = NE_PaletteCreate();
    NE_PaletteLoad(town_pal, saltmere_pal_bin, saltmere_pal_bin_size / 2, NE_PAL256);
    NE_MaterialSetPalette(town_mat, town_pal);
    NE_ModelSetMaterial(town, town_mat);

    player_mat = NE_MaterialCreate();
    NE_MaterialTexLoad(player_mat, NE_PAL16, 128, 128,
                       (NE_TextureFlags)(NE_TEXGEN_TEXCOORD | NE_TEXTURE_COLOR0_TRANSPARENT),
                       player_tex_bin);
    NE_Palette *player_pal = NE_PaletteCreate();
    NE_PaletteLoad(player_pal, player_pal_bin, 16, NE_PAL16);
    NE_MaterialSetPalette(player_mat, player_pal);

    for (int y = 0; y < SALTMERE_H; y++)
        for (int x = 0; x < SALTMERE_W; x++)
            if (saltmere_map[y][x] == 'P')
                player = { x, y, DOWN, 0, 0, 0 };
    player_pos(&cam_x, &cam_z);

    save_init(argc, argv);
    SaveData data = { SAVE_MAGIC, 0 };
    bool loaded = save_read(&data);
    if (!loaded)
        data = { SAVE_MAGIC, 0 };

    printf("\x1b[1;1HPoke Legends: Beyond the Nine");
    printf("\x1b[3;1HPort Saltmere (block-out)");
    printf("\x1b[4;1HD-pad: walk");
    printf("\x1b[14;1HSave test");
    if (backend == Backend::File)
        printf("\x1b[15;1HSave: file\n %.60s", save_path);
    else if (backend == Backend::Cart)
        printf("\x1b[15;1HSave: cart chip, type %d\n %lu bytes", cart_type, (unsigned long)cardEepromGetSize());
    else
        printf("\x1b[15;1HSave: none found");
    printf("\x1b[18;1H%s", loaded ? "Loaded saved counter" : "No save yet");
    printf("\x1b[20;1HCounter: %lu   ", (unsigned long)data.counter);
    printf("\x1b[23;1HA: add 1 and save");

#ifdef SAVE_SELFTEST
    // Test builds only (make DEFINES=-DSAVE_SELFTEST): act as if A was pressed 3 seconds
    // after boot, like a player would.
    int selftest = 180;
#else
    int selftest = 0;
#endif

    while (1)
    {
        NE_WaitForVBL((NE_UpdateFlags)0);
        scanKeys();
        u32 down = keysDown();

        u32 held = keysHeld();
#ifdef WALK_SELFTEST
        // Test builds only: hold Down for 3 seconds, which walks into the water's edge.
        static int frame;
        if (frame++ < 180)
            held |= KEY_DOWN;
#endif
        player_update(held);
        float px, pz;
        player_pos(&px, &pz);
        cam_x += (px - cam_x) * 0.2f;
        cam_z += (pz - cam_z) * 0.2f;

        printf("\x1b[6;1HTile: %2d,%2d  ", player.tx, player.ty);

        if ((down & KEY_A) || (selftest > 0 && --selftest == 0))
        {
            data.counter++;
            bool ok = save_write(&data);
            printf("\x1b[20;1HCounter: %lu   ", (unsigned long)data.counter);
            printf("\x1b[21;1H%s", ok ? "Saved.      " : "Save FAILED.");
        }

        NE_Process(draw_scene);
    }

    return 0;
}
