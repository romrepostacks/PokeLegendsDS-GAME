#include <stdio.h>

#include <nds.h>

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

    consoleSelect(&bottomScreen);
    printf("\x1b[11;10HPress START");

    while (1)
    {
        swiWaitForVBlank();
        scanKeys();
    }

    return 0;
}
