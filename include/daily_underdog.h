#ifndef GUARD_DAILY_UNDERDOG_H
#define GUARD_DAILY_UNDERDOG_H

#include "sundial_seed.h"

void DailyUnderdog_GiveTestTeam(void);
void DailyUnderdog_GetToday(u32 *year, u32 *month, u32 *day);
void DailyUnderdog_GetTeamDate(u32 *year, u32 *month, u32 *day); // PRACTICE follows TEST DAY
u32 DailyUnderdog_TodayNumber(void);
void DailyUnderdog_SetArenaOpponent(u32 seed, enum SundialOpponent opponent);
void DailyUnderdog_ApplyBattleRule(void);
u32 DailyUnderdog_TrophyStars(enum SundialOpponent opponent);
const u8 *DailyUnderdog_OpponentName(enum SundialOpponent opponent);
const u8 *DailyUnderdog_RuleName(enum SundialRule rule); // NULL on a day without one
void DailyUnderdog_TryStartDaily(void);
void DailyUnderdog_RecordResult(void);
void DailyUnderdog_Save(void);
void DailyUnderdog_EnterSeedWord(void);
void DailyUnderdog_StartFreePlay(void);
void DailyUnderdog_WarpToArena(void);
void DailyUnderdog_PushOpponentChoices(void);
void DailyUnderdog_GiveTeamVsChosenOpponent(void);
void DailyUnderdog_NextTestDay(void);
void DailyUnderdog_EnterHallOfFame(void);
void DailyUnderdog_GiveFollowerParty(void);
void DailyUnderdog_PushCostumeChoices(void);
void DailyUnderdog_PushFreeCostumes(void);
void DailyUnderdog_SetCostume(void);

// Costume look-ups. Each returns the costume's value, or `fallback` when no costume is worn.
u16 DailyUnderdog_CostumeTrainerPic(u16 fallback);
u16 DailyUnderdog_CostumeOverworldGfx(u8 avatarState, u16 fallback);
u16 DailyUnderdog_CostumePaletteTag(u16 fallback);
void DailyUnderdog_RenamePlayer(void);

u16 DailyUnderdog_OpponentTrainerPic(u32 opponent);
u16 DailyUnderdog_WardrobePreviewPic(u32 id);
void DailyUnderdog_MakeFollower(u16 species);
u32 DailyUnderdog_RoomWindowView(void);
void DailyUnderdog_SetUpDaily(void);
void DailyUnderdog_SetUpPractice(void);
void DailyUnderdog_PlaceInRoom(u32 spot, u16 species);
void DailyUnderdog_ApplyRoomTheme(bool32 skipFaded);
enum
{
    WELCOME_FOLLOWING,
    WELCOME_IN_ROOM,
    WELCOME_COLLECTION, // room full: swap it in from a spot or the GameCube
};
u32 DailyUnderdog_WelcomeNewMon(u16 species);

#endif // GUARD_DAILY_UNDERDOG_H
