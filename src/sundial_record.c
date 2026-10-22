#include "global.h"
#include "sundial_record.h"

// Days since 1 January 2000, counting that day as 1 (0 means "never played").
u32 Sundial_DayNumber(u32 year, u32 month, u32 day)
{
    static const u16 daysBeforeMonth[] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
    u32 y = year - 2000;
    u32 days = y * 365 + (y + 3) / 4 - (y + 99) / 100 + (y + 399) / 400;

    days += daysBeforeMonth[month - 1] + day;
    if (month > 2 && (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)))
        days++;
    return days;
}

// Claims today's attempt. FALSE if today's daily was already started.
// Missing a day breaks both streaks; a daily left unfinished counts as a loss.
bool32 Sundial_StartDaily(struct SundialRecord *record, u32 today)
{
    if (record->lastDay == today)
        return FALSE;

    if (record->result == SUNDIAL_RESULT_IN_PROGRESS)
        Sundial_FinishDaily(record, FALSE);

    if (record->lastDay != 0 && record->lastDay + 1 == today)
    {
        record->playStreak++;
    }
    else
    {
        record->playStreak = 1;
        record->winStreak = 0;
    }
    record->lastDay = today;
    record->result = SUNDIAL_RESULT_IN_PROGRESS;
    return TRUE;
}

void Sundial_FinishDaily(struct SundialRecord *record, bool32 won)
{
    if (won)
    {
        record->wins++;
        record->winStreak++;
        record->result = SUNDIAL_RESULT_WON;
    }
    else
    {
        record->losses++;
        record->winStreak = 0;
        record->result = SUNDIAL_RESULT_LOST;
    }
}

// Money for a won daily, by the win streak including today's win: 1000, 1500,
// 2000, 2500, 3000, 4000, then 5000 a day from the seventh on.
u32 Sundial_WinPrize(u32 winStreak)
{
    static const u16 prizes[] = {1000, 1500, 2000, 2500, 3000, 4000, 5000};

    if (winStreak == 0)
        return 0;
    if (winStreak > ARRAY_COUNT(prizes))
        winStreak = ARRAY_COUNT(prizes);
    return prizes[winStreak - 1];
}

// The trophy wall's rating for one daily: a win is a star, two or fewer of the
// six fainted is two, nobody fainted is three. A loss is none.
u32 Sundial_TrophyStars(bool32 won, u32 fainted)
{
    if (!won)
        return 0;
    if (fainted == 0)
        return 3;
    if (fainted <= 2)
        return 2;
    return 1;
}
