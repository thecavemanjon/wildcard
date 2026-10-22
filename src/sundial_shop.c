#include "global.h"
#include "daily_underdog.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "main.h"
#include "menu.h"
#include "money.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "script.h"
#include "sound.h"
#include "sprite.h"
#include "string_util.h"
#include "sundial_prices.h"
#include "sundial_shop.h"
#include "task.h"
#include "text.h"
#include "window.h"
#include "constants/characters.h"
#include "constants/songs.h"
#include "constants/vars.h"

// The follower picker, after the debug menu's Pokémon picker: one Pokémon at a
// time with its party icon. Up/down add or take the step; left/right change the
// step (+1, +10, +100), shown as in the debug menu. Two modes:
//   shop: every Pokémon; A buys it. Buying marks it caught in the Pokédex, and
//         caught is what "owned" means (gifted battle teams don't touch the dex).
//   follower: only owned Pokémon (plus "no follower"), stepping 1/10/100
//         places through them; A picks the follower.
// A new purchase follows you if nobody is, else takes an empty spot.

#define ICON_TAG 0x5D01
#define ICON_X 196
#define ICON_Y 60

enum
{
    PICKER_SHOP,
    PICKER_FOLLOWER,
};

static const struct WindowTemplate sPickerWindow =
{
    .bg = 0,
    .tilemapLeft = 1,
    .tilemapTop = 5, // clear of the money box's frame
    .width = 26,
    .height = 6,
    .paletteNum = 15,
    .baseBlock = 0x40,
};

static const u8 sTextColors[] = {TEXT_COLOR_WHITE, TEXT_COLOR_DARK_GRAY, TEXT_COLOR_LIGHT_GRAY};

#define tMode     data[0]
#define tDexNum   data[1] // 0 = no follower (follower mode only)
#define tWindowId data[2]
#define tSpriteId data[3]
#define tStep     data[4] // index into sSteps

static const u16 sSteps[] = {1, 10, 100};

static void Task_Picker(u8 taskId);

static bool32 IsOwned(u32 dexNum)
{
    return dexNum != 0 && GetSetPokedexFlag(dexNum, FLAG_GET_CAUGHT);
}

// Can walk behind you indoors: has an overworld sprite no bigger than 32x32.
static bool32 CanFollowIndoors(u16 species)
{
    const struct ObjectEventGraphicsInfo *info = SpeciesToGraphicsInfo(species, FALSE, FALSE);

    return info != NULL && info->oam->size <= ST_OAM_SIZE_2;
}

static u32 CurrentPrice(u16 species)
{
    if (GetNationalPokedexCount(FLAG_GET_CAUGHT) == 0)
        return 0; // the first one is on us
    return Sundial_FollowerPrice(species);
}

static void DestroyIcon(u8 taskId)
{
    if (gTasks[taskId].tSpriteId != MAX_SPRITES)
    {
        FreeSpriteTilesByTag(ICON_TAG);
        FreeSpritePaletteByTag(ICON_TAG);
        DestroySprite(&gSprites[gTasks[taskId].tSpriteId]);
        gTasks[taskId].tSpriteId = MAX_SPRITES;
    }
}

static void Print(u8 windowId, const u8 *str, u32 x, u32 y)
{
    AddTextPrinterParameterized4(windowId, FONT_NORMAL, x, y, 0, 0, sTextColors, TEXT_SKIP_DRAW, str);
}

// Redraws the window and icon; status is an extra line (or NULL for the usual).
static void Redraw(u8 taskId, const u8 *status)
{
    u8 windowId = gTasks[taskId].tWindowId;
    u32 dexNum = gTasks[taskId].tDexNum;
    u16 species = dexNum != 0 ? NationalPokedexNumToSpecies(dexNum) : SPECIES_NONE;
    u8 line[32];
    u8 *end;

    FillWindowPixelBuffer(windowId, PIXEL_FILL(1));
    DestroyIcon(taskId);

    if (species == SPECIES_NONE)
    {
        Print(windowId, COMPOUND_STRING("No follower"), 0, 0);
    }
    else
    {
        end = StringCopy(line, COMPOUND_STRING("{NO}"));
        end = ConvertIntToDecimalStringN(end, dexNum, STR_CONV_MODE_LEADING_ZEROS, 4);
        *end++ = CHAR_SPACE;
        StringCopy(end, GetSpeciesName(species));
        Print(windowId, line, 0, 0);

        if (status == NULL)
        {
            if (IsOwned(dexNum))
                status = gTasks[taskId].tMode == PICKER_SHOP ? COMPOUND_STRING("You have this one") : COMPOUND_STRING("In your collection");
            else if (!CanFollowIndoors(species))
                status = COMPOUND_STRING("Too big to bring indoors");
            else if (CurrentPrice(species) == 0)
                status = COMPOUND_STRING("Free: your first one");
            else
            {
                end = StringCopy(line, COMPOUND_STRING("Price: "));
                *end++ = CHAR_CURRENCY;
                ConvertIntToDecimalStringN(end, CurrentPrice(species), STR_CONV_MODE_LEFT_ALIGN, 6);
                status = line;
            }
        }
        gTasks[taskId].tSpriteId = CreateTaggedMonIcon(ICON_TAG, ICON_TAG, species);
        if (gTasks[taskId].tSpriteId != MAX_SPRITES)
        {
            gSprites[gTasks[taskId].tSpriteId].callback = SpriteCB_MonIcon;
            gSprites[gTasks[taskId].tSpriteId].x = ICON_X;
            gSprites[gTasks[taskId].tSpriteId].y = ICON_Y;
            gSprites[gTasks[taskId].tSpriteId].oam.priority = 0;
        }
    }
    if (status != NULL)
        Print(windowId, status, 0, 16);
    // The button guide, with the step size as in the debug menu.
    if (gTasks[taskId].tMode == PICKER_SHOP)
        end = StringCopy(line, COMPOUND_STRING("{A_BUTTON} Buy  {B_BUTTON} Back  {LEFT_ARROW}+"));
    else
        end = StringCopy(line, COMPOUND_STRING("{A_BUTTON} Choose  {B_BUTTON} Back  {LEFT_ARROW}+"));
    end = ConvertIntToDecimalStringN(end, sSteps[gTasks[taskId].tStep], STR_CONV_MODE_LEFT_ALIGN, 3);
    StringCopy(end, COMPOUND_STRING("{RIGHT_ARROW}"));
    Print(windowId, line, 0, 32);
    CopyWindowToVram(windowId, COPYWIN_FULL);
}

static u32 ClampDex(s32 dexNum)
{
    if (dexNum < 1)
        return 1;
    if (dexNum > NATIONAL_DEX_COUNT)
        return NATIONAL_DEX_COUNT;
    return dexNum;
}

// Follower mode: the next owned Pokémon (or "no follower", 0) in that direction.
static u32 StepOwned(u32 dexNum, s32 dir)
{
    u32 i;

    for (i = 0; i <= NATIONAL_DEX_COUNT; i++)
    {
        dexNum = (dexNum + NATIONAL_DEX_COUNT + 1 + dir) % (NATIONAL_DEX_COUNT + 1);
        if (dexNum == 0 || IsOwned(dexNum))
            return dexNum;
    }
    return 0;
}

// Up/down: the step through the dex (shop), or through your Pokémon (follower).
static void Move(u8 taskId, s32 dir)
{
    u32 i;

    if (gTasks[taskId].tMode != PICKER_SHOP)
    {
        // At most one lap of the collection (plus "no follower"): each step scans the dex.
        u32 steps = sSteps[gTasks[taskId].tStep] % (GetNationalPokedexCount(FLAG_GET_CAUGHT) + 1);

        for (i = 0; i < steps; i++)
            gTasks[taskId].tDexNum = StepOwned(gTasks[taskId].tDexNum, dir);
    }
    else
        gTasks[taskId].tDexNum = ClampDex(gTasks[taskId].tDexNum + dir * sSteps[gTasks[taskId].tStep]);
    PlaySE(SE_SELECT);
    Redraw(taskId, NULL);
}

// Left/right: the step size.
static void ChangeStep(u8 taskId, s32 dir)
{
    s32 step = gTasks[taskId].tStep + dir;

    if (step < 0 || step >= (s32)ARRAY_COUNT(sSteps))
        return;
    gTasks[taskId].tStep = step;
    PlaySE(SE_SELECT);
    Redraw(taskId, NULL);
}

static void Close(u8 taskId)
{
    DestroyIcon(taskId);
    ClearStdWindowAndFrame(gTasks[taskId].tWindowId, TRUE);
    RemoveWindow(gTasks[taskId].tWindowId);
    DestroyTask(taskId);
    ScriptContext_Enable();
}

static void TryBuy(u8 taskId)
{
    u32 dexNum = gTasks[taskId].tDexNum;
    u16 species = NationalPokedexNumToSpecies(dexNum);
    u32 price = CurrentPrice(species);

    if (IsOwned(dexNum) || !CanFollowIndoors(species))
    {
        PlaySE(SE_FAILURE);
        return;
    }
    if (!IsEnoughMoney(&gSaveBlock1Ptr->money, price))
    {
        PlaySE(SE_FAILURE);
        Redraw(taskId, COMPOUND_STRING("Not enough money yet"));
        return;
    }
    RemoveMoney(&gSaveBlock1Ptr->money, price);
    ChangeAmountInMoneyBox(GetMoney(&gSaveBlock1Ptr->money));
    gSpecialVar_Result = TRUE; // bought something: the script saves
    GetSetPokedexFlag(dexNum, FLAG_SET_SEEN);
    GetSetPokedexFlag(dexNum, FLAG_SET_CAUGHT);
    PlaySE(SE_SHOP);
    switch (DailyUnderdog_WelcomeNewMon(species))
    {
    case WELCOME_FOLLOWING:
        Redraw(taskId, COMPOUND_STRING("Yours! It's following you"));
        break;
    case WELCOME_IN_ROOM:
        Redraw(taskId, COMPOUND_STRING("Yours! It's in your room"));
        break;
    default:
        Redraw(taskId, COMPOUND_STRING("Yours! Pick it at the GameCube"));
        break;
    }
}

static void Task_Picker(u8 taskId)
{
    if (JOY_NEW(DPAD_UP))
        Move(taskId, 1);
    else if (JOY_NEW(DPAD_DOWN))
        Move(taskId, -1);
    else if (JOY_NEW(DPAD_RIGHT))
        ChangeStep(taskId, 1);
    else if (JOY_NEW(DPAD_LEFT))
        ChangeStep(taskId, -1);
    else if (JOY_NEW(A_BUTTON))
    {
        if (gTasks[taskId].tMode == PICKER_SHOP)
        {
            TryBuy(taskId);
        }
        else
        {
            u32 dexNum = gTasks[taskId].tDexNum;
            u16 species = dexNum != 0 ? NationalPokedexNumToSpecies(dexNum) : SPECIES_NONE;

            PlaySE(SE_SELECT);
            gSpecialVar_Result = TRUE;
            Close(taskId);
            DailyUnderdog_MakeFollower(species);
        }
    }
    else if (JOY_NEW(B_BUTTON))
    {
        PlaySE(SE_SELECT);
        if (gTasks[taskId].tMode != PICKER_SHOP) // the shop keeps "bought something"
            gSpecialVar_Result = FALSE;
        Close(taskId);
    }
}

static void OpenPicker(u32 mode, u32 dexNum)
{
    u8 taskId = CreateTask(Task_Picker, 80);

    gTasks[taskId].tMode = mode;
    gTasks[taskId].tDexNum = dexNum;
    gTasks[taskId].tSpriteId = MAX_SPRITES;
    gTasks[taskId].tStep = 0;
    gTasks[taskId].tWindowId = AddWindow(&sPickerWindow);
    DrawStdWindowFrame(gTasks[taskId].tWindowId, FALSE);
    Redraw(taskId, NULL);
}

// PC -> SHOP. The script shows the money box first and waits (waitstate).
// VAR_RESULT: TRUE if anything was bought.
void DailyUnderdog_OpenShop(void)
{
    gSpecialVar_Result = FALSE;
    OpenPicker(PICKER_SHOP, 1);
}

// GameCube. VAR_RESULT: TRUE if a follower (or none) was picked, FALSE on B.
void DailyUnderdog_OpenFollowerPicker(void)
{
    u16 species = VarGet(VAR_UNDERDOG_FOLLOWER);

    OpenPicker(PICKER_FOLLOWER, species != SPECIES_NONE ? SpeciesToNationalPokedexNum(species) : 0);
}

#undef tMode
#undef tDexNum
#undef tWindowId
#undef tSpriteId
#undef tStep
