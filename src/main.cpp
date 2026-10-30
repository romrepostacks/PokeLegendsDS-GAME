#include <stdio.h>
#include <string.h>

#include <fat.h>
#include <nds.h>

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
        if (argc > 0 && argv[0] != NULL && strlen(argv[0]) > 4)
        {
            // Same name as the ROM, with .sav instead of .nds.
            snprintf(save_path, sizeof(save_path), "%s", argv[0]);
            strcpy(save_path + strlen(save_path) - 4, ".sav");
        }
        else
        {
            snprintf(save_path, sizeof(save_path), "fat:/beyond-the-nine.sav");
        }
        backend = Backend::File;
        return;
    }

    sysSetCardOwner(true);
    cart_type = cardEepromGetType();
    if (cart_type > 0)
        backend = Backend::Cart;
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
        if (cart_type == 3) // FLASH must be erased before writing
            cardEepromSectorErase(0);
        cardWriteEeprom(0, (u8 *)data, sizeof(*data), cart_type);
        SaveData check;
        cardReadEeprom(0, (u8 *)&check, sizeof(check), cart_type);
        return check.magic == data->magic && check.counter == data->counter;
    }
    return false;
}

int main(int argc, char **argv)
{
    PrintConsole topScreen;
    PrintConsole bottomScreen;

    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);

    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);

    consoleInit(&topScreen, 3, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottomScreen, 3, BgType_Text4bpp, BgSize_T_256x256, 31, 0, false, true);

    consoleSelect(&topScreen);
    printf("\x1b[10;10HPoke Legends\x1b[12;8HBeyond the Nine");

    save_init(argc, argv);

    SaveData data = { SAVE_MAGIC, 0 };
    bool loaded = save_read(&data);
    if (!loaded)
        data = { SAVE_MAGIC, 0 };

    consoleSelect(&bottomScreen);
    printf("\x1b[2;1HSave test");
    if (backend == Backend::File)
        printf("\x1b[4;1HSave: file\n %.60s", save_path);
    else if (backend == Backend::Cart)
        printf("\x1b[4;1HSave: cart chip, type %d\n %lu bytes", cart_type, (unsigned long)cardEepromGetSize());
    else
        printf("\x1b[4;1HSave: none found");
    printf("\x1b[8;1H%s", loaded ? "Loaded saved counter" : "No save yet");
    printf("\x1b[11;1HCounter: %lu   ", (unsigned long)data.counter);
    printf("\x1b[20;1HA: add 1 and save");
    printf("\x1b[22;10HPress START");

#ifdef SAVE_SELFTEST
    // Test builds only (make DEFINES=-DSAVE_SELFTEST): act as if A was pressed at boot.
    bool selftest = true;
#else
    bool selftest = false;
#endif

    while (1)
    {
        swiWaitForVBlank();
        scanKeys();

        if ((keysDown() & KEY_A) || selftest)
        {
            selftest = false;
            data.counter++;
            bool ok = save_write(&data);
            printf("\x1b[11;1HCounter: %lu   ", (unsigned long)data.counter);
            printf("\x1b[13;1H%s", ok ? "Saved.      " : "Save FAILED.");
        }
    }

    return 0;
}
