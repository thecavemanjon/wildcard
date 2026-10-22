#include "global.h"
#include "battle.h"
#include "bg.h"
#include "daily_underdog.h"
#include "data.h"
#include "event_data.h"
#include "gpu_regs.h"
#include "graphics.h"
#include "main.h"
#include "menu.h"
#include "overworld.h"
#include "palette.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "scanline_effect.h"
#include "sprite.h"
#include "string_util.h"
#include "sundial_card.h"
#include "sundial_record.h"
#include "sundial_seed.h"
#include "task.h"
#include "text.h"
#include "trainer_pokemon_sprites.h"
#include "window.h"
#include "constants/characters.h"
#include "constants/rgb.h"
#include "constants/sundial.h"
#include "constants/vars.h"

// The results card: one screen after a daily, made to be screenshotted (a GBA
// can't copy text to a clipboard). Layout follows the design doc's share card.
// Dailies show their number and date; Free Play shows its seed word instead.

// Day #1 for the card's number: LAUNCH_* in constants/sundial.h (move to the real launch date when it ships).

#define ICON_Y        92 // middle of the icon strip (the art sits low in its 32x32)
#define ICON_X_FIRST  36
#define ICON_X_STEP   34
#define TRAINER_PIC_X 188
#define TRAINER_PIC_Y 56
#define TRAINER_PIC_PAL_SLOT 15

struct ResultsCard
{
    u8 seedWord[CODE_NAME_LENGTH + 1]; // Free Play's word; empty for a daily
    u16 trainerId;
    u16 year;
    u8 month;
    u8 day;
    u8 turns;
    u8 faintedMask; // bit n: party slot n fainted
    bool8 won;
    u16 prize; // money for a won daily; 0 otherwise
    u8 arenaSlot; // whose colours the card wears
    bool8 practice; // PRACTICE (a chosen opponent): never on the record
    u16 gauntletWeek; // a gauntlet run's card: its week (from launch), the round it ended in, the week's best
    u8 gauntletRound;
    u8 gauntletBest;
};

EWRAM_DATA static struct ResultsCard sCard = {0};

static const u8 *const sMonthNames[] =
{
    COMPOUND_STRING("JAN"), COMPOUND_STRING("FEB"), COMPOUND_STRING("MAR"), COMPOUND_STRING("APR"),
    COMPOUND_STRING("MAY"), COMPOUND_STRING("JUN"), COMPOUND_STRING("JUL"), COMPOUND_STRING("AUG"),
    COMPOUND_STRING("SEP"), COMPOUND_STRING("OCT"), COMPOUND_STRING("NOV"), COMPOUND_STRING("DEC"),
};

static const struct BgTemplate sBgTemplates[] =
{
    {
        .bg = 0,
        .charBaseIndex = 1,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    },
};

enum
{
    WIN_TEXT,
};

static const struct WindowTemplate sWindowTemplates[] =
{
    [WIN_TEXT] =
    {
        .bg = 0,
        .tilemapLeft = 1,
        .tilemapTop = 1,
        .width = 28,
        .height = 18,
        .paletteNum = 15,
        .baseBlock = 1,
    },
    DUMMY_WIN_TEMPLATE,
};

// The card's own palette (BG palette 15), so it can be more than white text.
enum
{
    CARD_CLEAR,
    CARD_WHITE,
    CARD_SHADOW,
    CARD_GOLD,
    CARD_GOLD_SHADOW,
    CARD_GREEN,
    CARD_GREEN_SHADOW,
    CARD_RED,
    CARD_RED_SHADOW,
    CARD_BAND,  // header band
    CARD_PANEL, // behind the party icons
    CARD_GREY,  // the trophy wall's not-yet-beaten
};

static const u16 sCardPalette[16] =
{
    [CARD_CLEAR]        = RGB(0, 0, 0),
    [CARD_WHITE]        = RGB(31, 31, 31),
    [CARD_SHADOW]       = RGB(5, 5, 8),
    [CARD_GOLD]         = RGB(31, 25, 6),
    [CARD_GOLD_SHADOW]  = RGB(12, 8, 1),
    [CARD_GREEN]        = RGB(14, 30, 12),
    [CARD_GREEN_SHADOW] = RGB(2, 4, 2), // dark, so WON! and LOST stand out on any card colour
    [CARD_RED]          = RGB(31, 11, 10),
    [CARD_RED_SHADOW]   = RGB(5, 1, 2),
    [CARD_GREY]         = RGB(13, 14, 18),
    // CARD_BAND and CARD_PANEL come from the opponent's colour (SetCardColours)
};

// Each arena slot's card colour (roughly the opponent's type), as 5-bit RGB.
// The header band is a darker shade, the icon strip a lighter one.
static const u8 sSlotColours[][3] =
{
    [ 0] = {12, 9, 5},  // Roxanne: rock
    [ 1] = {12, 6, 2},  // Brawly: fighting
    [ 2] = {10, 8, 1},  // Wattson: electric
    [ 3] = {12, 3, 2},  // Flannery: fire
    [ 4] = {10, 9, 8},  // Norman: normal
    [ 5] = {6, 10, 15}, // Winona: flying
    [ 6] = {14, 5, 10}, // Tate & Liza: psychic
    [ 7] = {3, 8, 14},  // Juan: water
    [ 8] = {6, 5, 6},   // Sidney: dark
    [ 9] = {8, 5, 12},  // Phoebe: ghost
    [10] = {5, 11, 14}, // Glacia: ice
    [11] = {3, 10, 10}, // Drake: dragon
    [12] = {11, 2, 4},  // Maxie: magma
    [13] = {2, 6, 13},  // Archie: aqua
    [14] = {4, 11, 13}, // Wallace
    [15] = {8, 9, 11},  // Steven: steel
    [16] = {5, 9, 9},   // Brendan
    [17] = {5, 9, 9},
    [18] = {5, 9, 9},
    [19] = {5, 9, 9},   // May
    [20] = {5, 9, 9},
    [21] = {5, 9, 9},
    [22] = {10, 8, 5},  // Brock: rock
    [23] = {3, 9, 15},  // Misty: water
    [24] = {9, 8, 1},   // Lt. Surge: electric
    [25] = {5, 10, 4},  // Erika: grass
    [26] = {10, 4, 12}, // Koga: poison
    [27] = {14, 4, 12}, // Sabrina: psychic
    [28] = {13, 5, 1},  // Blaine: fire
    [29] = {7, 6, 4},   // Giovanni: ground
    [30] = {6, 10, 15}, // Lorelei: ice
    [31] = {12, 7, 4},  // Bruno: fighting
    [32] = {8, 5, 12},  // Agatha: ghost
    [33] = {8, 4, 15},  // Lance: dragon
    [34] = {9, 10, 13}, // Red: the summit
    [35] = {6, 7, 12},  // Blue
    [36] = {6, 7, 12},
    [37] = {6, 7, 12},
    [38] = {9, 10, 13}, // Red, Origins
};

static const u8 sBandWhite[] = {CARD_BAND, CARD_WHITE, CARD_SHADOW};
static const u8 sBandGold[]  = {CARD_BAND, CARD_GOLD, CARD_GOLD_SHADOW};
static const u8 sWhite[]     = {CARD_CLEAR, CARD_WHITE, CARD_SHADOW};
static const u8 sGold[]      = {CARD_CLEAR, CARD_GOLD, CARD_GOLD_SHADOW};
static const u8 sGreen[]     = {CARD_CLEAR, CARD_GREEN, CARD_GREEN_SHADOW};
static const u8 sRed[]       = {CARD_CLEAR, CARD_RED, CARD_RED_SHADOW};

static void Task_CardFadeIn(u8 taskId);
static void Task_CardWaitForKey(u8 taskId);
static void Task_CardFadeOut(u8 taskId);

// Called straight after the battle, before the party is healed.
void SundialCard_Capture(u16 trainerId, bool32 won, const u8 *seedWord, u32 year, u32 month, u32 day)
{
    u32 i;

    if (seedWord != NULL)
        StringCopy(sCard.seedWord, seedWord);
    else
        sCard.seedWord[0] = EOS;
    sCard.trainerId = trainerId;
    sCard.won = won;
    sCard.year = year;
    sCard.month = month;
    sCard.day = day;
    sCard.turns = gBattleResults.battleTurnCounter;
    sCard.prize = 0;
    sCard.arenaSlot = VarGet(VAR_UNDERDOG_ARENA_SLOT);
    sCard.faintedMask = 0;
    sCard.practice = FALSE;
    sCard.gauntletRound = 0;
    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) != SPECIES_NONE
         && GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_HP) == 0)
            sCard.faintedMask |= 1 << i;
    }
}

// Called after Capture, for a PRACTICE battle.
void SundialCard_SetPractice(void)
{
    sCard.practice = TRUE;
}

// Called after Capture, when a gauntlet run ends.
void SundialCard_SetGauntlet(u32 week, u32 round, u32 best)
{
    sCard.gauntletWeek = week;
    sCard.gauntletRound = round;
    sCard.gauntletBest = best;
}

// Called after Capture, for a won daily.
void SundialCard_SetPrize(u32 prize)
{
    sCard.prize = prize;
}

static void VBlankCB_Card(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void CB2_Card(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static bool32 IsFreePlay(void)
{
    return sCard.seedWord[0] != EOS;
}

static bool32 IsGauntlet(void)
{
    return sCard.gauntletRound != 0;
}

static bool32 IsDaily(void)
{
    return !IsFreePlay() && !sCard.practice && !IsGauntlet();
}

static void Print(const u8 *str, u32 x, u32 y, const u8 *colors)
{
    AddTextPrinterParameterized3(WIN_TEXT, FONT_NORMAL, x, y, colors, TEXT_SKIP_DRAW, str);
}

// The backdrop colour is the card, in the opponent's colour; the header band
// is a darker shade and the icon strip a lighter one. WON!/LOST say the result.
static void SetCardColours(void)
{
    u32 slot = sCard.arenaSlot < ARRAY_COUNT(sSlotColours) ? sCard.arenaSlot : 0;
    u32 r = sSlotColours[slot][0], g = sSlotColours[slot][1], b = sSlotColours[slot][2];

    gPlttBufferUnfaded[0] = RGB(r, g, b);
    gPlttBufferFaded[0] = gPlttBufferUnfaded[0];
    gPlttBufferUnfaded[BG_PLTT_ID(15) + CARD_BAND] = RGB(r / 2, g / 2, b / 2);
    gPlttBufferUnfaded[BG_PLTT_ID(15) + CARD_PANEL] = RGB(min(31, r * 27 / 20 + 2), min(31, g * 27 / 20 + 2), min(31, b * 27 / 20 + 2));
}

static u8 *AppendNumber(u8 *dest, u32 value)
{
    return ConvertIntToDecimalStringN(dest, value, STR_CONV_MODE_LEFT_ALIGN, 5);
}

static void PrintCard(void)
{
    u8 line[64];
    u8 *end;
    u32 i;
    u32 number = Sundial_DayNumber(sCard.year, sCard.month, sCard.day)
               - Sundial_DayNumber(LAUNCH_YEAR, LAUNCH_MONTH, LAUNCH_DAY) + 1;

    FillWindowPixelBuffer(WIN_TEXT, PIXEL_FILL(CARD_CLEAR));
    FillWindowPixelRect(WIN_TEXT, PIXEL_FILL(CARD_BAND), 0, 0, 224, 32);
    FillWindowPixelRect(WIN_TEXT, PIXEL_FILL(CARD_PANEL), 0, 70, 224, 36);

    if (IsGauntlet())
    {
        Print(COMPOUND_STRING("POKéMON WILD CARD"), 4, 0, sBandWhite);
        end = StringCopy(line, COMPOUND_STRING("GAUNTLET, WEEK "));
        AppendNumber(end, sCard.gauntletWeek);
        Print(line, 4, 16, sBandGold);
    }
    else if (IsFreePlay())
    {
        // Free Play: the word is the share line, and there's no day number.
        Print(COMPOUND_STRING("POKéMON WILD CARD"), 4, 0, sBandWhite);
        end = StringCopy(line, COMPOUND_STRING("SEED: "));
        StringCopy(end, sCard.seedWord);
        Print(line, 4, 16, sBandGold);
    }
    else if (sCard.practice)
    {
        Print(COMPOUND_STRING("POKéMON WILD CARD"), 4, 0, sBandWhite);
        Print(COMPOUND_STRING("PRACTICE"), 4, 16, sBandGold);
    }
    else
    {
        end = StringCopy(line, COMPOUND_STRING("POKéMON WILD CARD {NO}"));
        AppendNumber(end, number);
        Print(line, 4, 0, sBandWhite);

        end = AppendNumber(line, sCard.day);
        *end++ = CHAR_SPACE;
        end = StringCopy(end, sMonthNames[sCard.month - 1]);
        *end++ = CHAR_SPACE;
        end = AppendNumber(end, sCard.year);
        if (DailyUnderdog_RuleName(Sundial_RuleForDate(sCard.year, sCard.month, sCard.day)) != NULL)
        {
            end = StringCopy(end, COMPOUND_STRING("   "));
            StringCopy(end, DailyUnderdog_RuleName(Sundial_RuleForDate(sCard.year, sCard.month, sCard.day)));
        }
        Print(line, 4, 16, sBandGold);
    }

    end = StringCopy(line, COMPOUND_STRING("vs "));
    end = StringCopy(end, GetTrainerClassNameFromId(sCard.trainerId));
    *end++ = CHAR_SPACE;
    StringCopy(end, GetTrainerNameFromId(sCard.trainerId));
    Print(line, 0, 36, sWhite);

    Print(sCard.won ? COMPOUND_STRING("WON!") : COMPOUND_STRING("LOST"), 0, 52, sCard.won ? sGreen : sRed);
    if (IsGauntlet())
    {
        end = StringCopy(line, COMPOUND_STRING("in ROUND "));
        AppendNumber(end, sCard.gauntletRound);
        Print(line, 40, 52, sGold);
    }
    if (sCard.prize != 0)
    {
        end = line;
        *end++ = CHAR_PLUS;
        *end++ = CHAR_CURRENCY;
        AppendNumber(end, sCard.prize);
        Print(line, 40, 52, sGold);
    }

    // The share line: one mark per party slot, standing or fainted, then turns.
    end = line;
    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) == SPECIES_NONE)
            continue;
        end = StringCopy(end, (sCard.faintedMask & (1 << i)) ? COMPOUND_STRING("{BIG_MULT_X}") : COMPOUND_STRING("{CIRCLE_DOT}"));
    }
    end = StringCopy(end, COMPOUND_STRING(" in "));
    end = AppendNumber(end, sCard.turns);
    StringCopy(end, sCard.turns == 1 ? COMPOUND_STRING(" turn") : COMPOUND_STRING(" turns"));
    Print(line, 0, 108, sWhite);

    if (IsGauntlet())
    {
        end = StringCopy(line, COMPOUND_STRING("Best this week: ROUND "));
        AppendNumber(end, sCard.gauntletBest);
        Print(line, 0, 124, sGold);
    }
    else if (IsFreePlay())
    {
        Print(COMPOUND_STRING("FREE PLAY: not on your record"), 0, 124, sGold);
    }
    else if (sCard.practice)
    {
        Print(COMPOUND_STRING("PRACTICE: not on your record"), 0, 124, sGold);
    }
    else
    {
        end = StringCopy(line, COMPOUND_STRING("Win streak: "));
        end = AppendNumber(end, VarGet(VAR_UNDERDOG_WIN_STREAK));
        end = StringCopy(end, COMPOUND_STRING("   Days in a row: "));
        AppendNumber(end, VarGet(VAR_UNDERDOG_PLAY_STREAK));
        Print(line, 0, 124, sGold);
    }

    PutWindowTilemap(WIN_TEXT);
    CopyWindowToVram(WIN_TEXT, COPYWIN_FULL);
}

#define TAG_GREY_ICON_PAL 0xD000 // grey copies of the six icon palettes, for fainted Pokémon

// Fainted Pokémon get a grey copy of their icon palette: still clear on the
// icon strip, obviously knocked out.
static void LoadGreyIconPalettes(void)
{
    u32 k, c;

    for (k = 0; k < 6; k++)
    {
        u16 grey[16];
        struct SpritePalette pal = {grey, TAG_GREY_ICON_PAL + k};

        for (c = 0; c < 16; c++)
        {
            u16 rgb = gMonIconPalettes[k][c];
            u32 lum = ((rgb & 0x1F) * 30 + ((rgb >> 5) & 0x1F) * 59 + ((rgb >> 10) & 0x1F) * 11) / 100;

            lum = 8 + lum / 2; // a soft mid grey, so outlines still read
            grey[c] = RGB(lum, lum, lum);
        }
        LoadSpritePalette(&pal);
    }
}

static void FreeGreyIconPalettes(void)
{
    u32 k;

    for (k = 0; k < 6; k++)
        FreeSpritePaletteByTag(TAG_GREY_ICON_PAL + k);
}

static void CreateCardSprites(void)
{
    u32 i;

    CreateTrainerPicSprite(GetTrainerPicFromId(sCard.trainerId), TRUE,
                           TRAINER_PIC_X, TRAINER_PIC_Y, TRAINER_PIC_PAL_SLOT, TAG_NONE);

    LoadMonIconPalettes();
    LoadGreyIconPalettes();
    for (i = 0; i < PARTY_SIZE; i++)
    {
        u16 species = GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES);
        u8 spriteId;

        if (species == SPECIES_NONE)
            continue;
        spriteId = CreateMonIcon(species, SpriteCallbackDummy, ICON_X_FIRST + i * ICON_X_STEP, ICON_Y, 0,
                                 GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_PERSONALITY));
        gSprites[spriteId].oam.priority = 0; // icons default to 1, under the panel on BG0
        if (sCard.faintedMask & (1 << i))
            gSprites[spriteId].oam.paletteNum = IndexOfSpritePaletteTag(TAG_GREY_ICON_PAL + GetValidMonIconPalIndex(species));
    }
}

// Script special after a daily or Free Play. Takes over the screen; leaves for
// the Hall of Fame after a won daily, otherwise the bedroom.
void DailyUnderdog_ShowResultsCard(void)
{
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_0);
    DmaFill16(3, 0, VRAM, VRAM_SIZE);
    DmaFill32(3, 0, OAM, OAM_SIZE);
    DmaFill16(3, 0, PLTT, PLTT_SIZE);
    ScanlineEffect_Stop();
    ResetTasks();
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();

    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    LoadPalette(sCardPalette, BG_PLTT_ID(15), PLTT_SIZE_4BPP);
    SetCardColours();

    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP);
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    ShowBg(0);

    PrintCard();
    CreateCardSprites();

    BlendPalettes(PALETTES_ALL, 16, RGB_BLACK);
    BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
    EnableInterrupts(INTR_FLAG_VBLANK);
    SetVBlankCallback(VBlankCB_Card);
    SetMainCallback2(CB2_Card);
    CreateTask(Task_CardFadeIn, 0);
}

static void Task_CardFadeIn(u8 taskId)
{
    if (!gPaletteFade.active)
        gTasks[taskId].func = Task_CardWaitForKey;
}

static void Task_CardWaitForKey(u8 taskId)
{
    if (JOY_NEW(A_BUTTON | B_BUTTON))
    {
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        gTasks[taskId].func = Task_CardFadeOut;
    }
}

static void Task_CardFadeOut(u8 taskId)
{
    if (gPaletteFade.active)
        return;
    DestroyTask(taskId);
    FreeMonIconPalettes();
    FreeGreyIconPalettes();
    FreeAllWindowBuffers();
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    if (sCard.won && IsDaily()) // the Hall of Fame is for dailies
        DailyUnderdog_EnterHallOfFame();
    else
        SetMainCallback2(CB2_ReturnToBedroomHub);
}

// The trophy wall (from the notebook): the daily's 19, each with your best stars
// against them (DailyUnderdog_TrophyStars). Same window and palette as the card.
static const u8 sTrophyOrder[] =
{
    SUNDIAL_OPP_ROXANNE, SUNDIAL_OPP_BRAWLY, SUNDIAL_OPP_WATTSON, SUNDIAL_OPP_FLANNERY,
    SUNDIAL_OPP_NORMAN, SUNDIAL_OPP_WINONA, SUNDIAL_OPP_TATE_AND_LIZA, SUNDIAL_OPP_JUAN,
    SUNDIAL_OPP_SIDNEY, SUNDIAL_OPP_PHOEBE, SUNDIAL_OPP_GLACIA, SUNDIAL_OPP_DRAKE,
    SUNDIAL_OPP_MAXIE, SUNDIAL_OPP_ARCHIE, SUNDIAL_OPP_GIOVANNI,
    SUNDIAL_OPP_RIVAL, SUNDIAL_OPP_BLUE, SUNDIAL_OPP_WALLACE, SUNDIAL_OPP_STEVEN,
};

static const u8 sDimStar[] = {CARD_CLEAR, CARD_GREY, CARD_CLEAR};

static void Task_TrophyWaitForKey(u8 taskId);
static void Task_TrophyFadeOut(u8 taskId);

static void PrintTrophyWall(void)
{
    u8 line[48];
    u8 *end;
    u32 i, j, beaten = 0, stars = 0;

    FillWindowPixelBuffer(WIN_TEXT, PIXEL_FILL(CARD_CLEAR));
    FillWindowPixelRect(WIN_TEXT, PIXEL_FILL(CARD_BAND), 0, 0, 224, 18);
    for (i = 0; i < ARRAY_COUNT(sTrophyOrder); i++)
    {
        u32 got = DailyUnderdog_TrophyStars(sTrophyOrder[i]);
        u32 x = (i < 10) ? 0 : 114, y = 20 + (i % 10) * 12;

        stars += got;
        beaten += got > 0;
        Print(DailyUnderdog_OpponentName(sTrophyOrder[i]), x, y, got ? sWhite : sDimStar);
        for (j = 0; j < 3; j++)
            Print(COMPOUND_STRING("{STAR}"), x + 70 + j * 10, y, j < got ? sGold : sDimStar);
    }
    end = StringCopy(line, COMPOUND_STRING("TROPHY WALL   "));
    end = AppendNumber(end, beaten);
    end = StringCopy(end, COMPOUND_STRING("/19 beaten, "));
    end = AppendNumber(end, stars);
    StringCopy(end, COMPOUND_STRING("/57 {STAR}"));
    Print(line, 4, 1, sBandGold);
    PutWindowTilemap(WIN_TEXT);
    CopyWindowToVram(WIN_TEXT, COPYWIN_FULL);
}

// Script special (waitstate): shows the wall until A or B, then back to the script.
void DailyUnderdog_ShowTrophyWall(void)
{
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_0);
    DmaFill16(3, 0, VRAM, VRAM_SIZE);
    DmaFill32(3, 0, OAM, OAM_SIZE);
    DmaFill16(3, 0, PLTT, PLTT_SIZE);
    ScanlineEffect_Stop();
    ResetTasks();
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();

    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    LoadPalette(sCardPalette, BG_PLTT_ID(15), PLTT_SIZE_4BPP);
    gPlttBufferUnfaded[0] = RGB(4, 6, 12);
    gPlttBufferFaded[0] = gPlttBufferUnfaded[0];
    gPlttBufferUnfaded[BG_PLTT_ID(15) + CARD_BAND] = RGB(2, 3, 7);

    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP);
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    ShowBg(0);

    PrintTrophyWall();

    BlendPalettes(PALETTES_ALL, 16, RGB_BLACK);
    BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
    EnableInterrupts(INTR_FLAG_VBLANK);
    SetVBlankCallback(VBlankCB_Card);
    SetMainCallback2(CB2_Card);
    CreateTask(Task_TrophyWaitForKey, 0);
}

static void Task_TrophyWaitForKey(u8 taskId)
{
    if (!gPaletteFade.active && JOY_NEW(A_BUTTON | B_BUTTON))
    {
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        gTasks[taskId].func = Task_TrophyFadeOut;
    }
}

static void Task_TrophyFadeOut(u8 taskId)
{
    if (gPaletteFade.active)
        return;
    DestroyTask(taskId);
    FreeAllWindowBuffers();
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}
