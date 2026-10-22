#ifndef GUARD_SUNDIAL_RECORD_H
#define GUARD_SUNDIAL_RECORD_H

// The daily record: one attempt a day, wins, losses and streaks. Plain C over a
// struct so it can be unit-tested; daily_underdog.c moves it in and out of vars.

#include "constants/sundial.h"

struct SundialRecord
{
    u16 lastDay;    // Sundial_DayNumber of the last daily started; 0 = never
    u16 result;     // SUNDIAL_RESULT_*, for lastDay
    u16 wins;
    u16 losses;
    u16 winStreak;
    u16 playStreak; // days in a row with a daily played
};

u32 Sundial_DayNumber(u32 year, u32 month, u32 day);
bool32 Sundial_StartDaily(struct SundialRecord *record, u32 today);
void Sundial_FinishDaily(struct SundialRecord *record, bool32 won);
u32 Sundial_WinPrize(u32 winStreak);
u32 Sundial_TrophyStars(bool32 won, u32 fainted);

#endif // GUARD_SUNDIAL_RECORD_H
