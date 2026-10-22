#include "global.h"
#include "test/test.h"
#include "sundial_record.h"

TEST("Sundial record: day numbers count from 1 January 2000")
{
    EXPECT_EQ(Sundial_DayNumber(2000, 1, 1), 1);
    EXPECT_EQ(Sundial_DayNumber(2000, 3, 1), 61);      // 2000 was a leap year
    EXPECT_EQ(Sundial_DayNumber(2001, 1, 1), 367);
    EXPECT_EQ(Sundial_DayNumber(2026, 10, 12), 9782);
    EXPECT_EQ(Sundial_DayNumber(2026, 10, 13) - Sundial_DayNumber(2026, 10, 12), 1);
    EXPECT_EQ(Sundial_DayNumber(2027, 1, 1) - Sundial_DayNumber(2026, 12, 31), 1);
    EXPECT_EQ(Sundial_DayNumber(2028, 3, 1) - Sundial_DayNumber(2028, 2, 28), 2); // leap day
    EXPECT_EQ(Sundial_DayNumber(2100, 3, 1) - Sundial_DayNumber(2100, 2, 28), 1); // not a leap year
}

TEST("Sundial record: one attempt per day")
{
    struct SundialRecord r = {0};

    EXPECT(Sundial_StartDaily(&r, 100));
    EXPECT(!Sundial_StartDaily(&r, 100));
    Sundial_FinishDaily(&r, TRUE);
    EXPECT(!Sundial_StartDaily(&r, 100));
    EXPECT(Sundial_StartDaily(&r, 101));
}

TEST("Sundial record: consecutive days build streaks, a missed day resets them")
{
    struct SundialRecord r = {0};

    Sundial_StartDaily(&r, 100); Sundial_FinishDaily(&r, TRUE);
    Sundial_StartDaily(&r, 101); Sundial_FinishDaily(&r, TRUE);
    EXPECT_EQ(r.winStreak, 2);
    EXPECT_EQ(r.playStreak, 2);
    Sundial_StartDaily(&r, 102); Sundial_FinishDaily(&r, FALSE);
    EXPECT_EQ(r.winStreak, 0);
    EXPECT_EQ(r.playStreak, 3);
    Sundial_StartDaily(&r, 103); Sundial_FinishDaily(&r, TRUE);
    Sundial_StartDaily(&r, 105);
    EXPECT_EQ(r.winStreak, 0);
    EXPECT_EQ(r.playStreak, 1);
    EXPECT_EQ(r.wins, 3);
    EXPECT_EQ(r.losses, 1);
}

TEST("Sundial record: an unfinished daily counts as a loss")
{
    struct SundialRecord r = {0};

    Sundial_StartDaily(&r, 100); Sundial_FinishDaily(&r, TRUE);
    Sundial_StartDaily(&r, 101); // reset mid-battle: never finished
    Sundial_StartDaily(&r, 102);
    EXPECT_EQ(r.losses, 1);
    EXPECT_EQ(r.winStreak, 0);
    EXPECT_EQ(r.playStreak, 3);
}

TEST("Sundial record: win prizes climb with the streak and cap at 5000")
{
    EXPECT_EQ(Sundial_WinPrize(0), 0);
    EXPECT_EQ(Sundial_WinPrize(1), 1000);
    EXPECT_EQ(Sundial_WinPrize(2), 1500);
    EXPECT_EQ(Sundial_WinPrize(5), 3000);
    EXPECT_EQ(Sundial_WinPrize(6), 4000);
    EXPECT_EQ(Sundial_WinPrize(7), 5000);
    EXPECT_EQ(Sundial_WinPrize(40), 5000);
}

TEST("Sundial record: trophy stars: a win, two or fewer fainted, flawless")
{
    EXPECT_EQ(Sundial_TrophyStars(FALSE, 0), 0);
    EXPECT_EQ(Sundial_TrophyStars(TRUE, 5), 1);
    EXPECT_EQ(Sundial_TrophyStars(TRUE, 3), 1);
    EXPECT_EQ(Sundial_TrophyStars(TRUE, 2), 2);
    EXPECT_EQ(Sundial_TrophyStars(TRUE, 1), 2);
    EXPECT_EQ(Sundial_TrophyStars(TRUE, 0), 3);
}
