#include "global.h"
#include "test/test.h"
#include "sundial_gauntlet.h"
#include "sundial_record.h"
#include "constants/species.h"

TEST("Gauntlet: weeks run Monday to Sunday")
{
    u32 monday = Sundial_DayNumber(2026, 10, 19);  // a Monday
    u32 sunday = Sundial_DayNumber(2026, 10, 25);

    EXPECT_EQ(Gauntlet_WeekNumber(monday), Gauntlet_WeekNumber(sunday));
    EXPECT_EQ(Gauntlet_WeekNumber(monday) - 1, Gauntlet_WeekNumber(monday - 1));
    EXPECT_EQ(Gauntlet_WeekNumber(sunday) + 1, Gauntlet_WeekNumber(sunday + 1));
    EXPECT_EQ(Gauntlet_WeekNumber(Sundial_DayNumber(2000, 1, 3)), 1); // the first Monday
}

TEST("Gauntlet: the draft is six different species, the same all week")
{
    struct SundialMon a[GAUNTLET_DRAFT_SIZE], b[GAUNTLET_DRAFT_SIZE];
    u32 i, j, seed = Gauntlet_WeekSeed(1400);

    Gauntlet_Draft(seed, a);
    Gauntlet_Draft(seed, b);
    for (i = 0; i < GAUNTLET_DRAFT_SIZE; i++)
    {
        EXPECT_EQ(a[i].species, b[i].species);
        EXPECT(Sundial_IsInDailyPool(a[i].species));
        for (j = 0; j < i; j++)
            EXPECT_NE(a[i].species, a[j].species);
    }
}

TEST("Gauntlet: the ladder climbs gym leaders, Elite Four, Lance, then Red")
{
    u32 week, round;

    for (week = 1; week < 60; week++)
    {
        u32 seed = Gauntlet_WeekSeed(week);
        bool8 seen[SUNDIAL_OPP_COUNT] = {0};

        for (round = 1; round <= 3; round++)
        {
            enum SundialOpponent opp = Gauntlet_Opponent(seed, round);
            EXPECT(opp == SUNDIAL_OPP_BROCK || opp == SUNDIAL_OPP_MISTY || opp == SUNDIAL_OPP_LT_SURGE || opp == SUNDIAL_OPP_ERIKA);
        }
        for (round = 4; round <= 6; round++)
        {
            enum SundialOpponent opp = Gauntlet_Opponent(seed, round);
            EXPECT(opp == SUNDIAL_OPP_KOGA || opp == SUNDIAL_OPP_SABRINA || opp == SUNDIAL_OPP_BLAINE);
        }
        for (round = 7; round <= 8; round++)
        {
            enum SundialOpponent opp = Gauntlet_Opponent(seed, round);
            EXPECT(opp == SUNDIAL_OPP_LORELEI || opp == SUNDIAL_OPP_BRUNO || opp == SUNDIAL_OPP_AGATHA);
        }
        EXPECT_EQ(Gauntlet_Opponent(seed, 9), SUNDIAL_OPP_LANCE);
        EXPECT_EQ(Gauntlet_Opponent(seed, GAUNTLET_RED_ROUND), SUNDIAL_OPP_RED);
        for (round = 1; round <= GAUNTLET_RED_ROUND; round++)  // nobody twice before Red
        {
            enum SundialOpponent opp = Gauntlet_Opponent(seed, round);
            EXPECT(!seen[opp]);
            seen[opp] = TRUE;
        }
        for (round = GAUNTLET_RED_ROUND + 1; round < 30; round++)
            EXPECT_NE(Gauntlet_OpponentType(Gauntlet_Opponent(seed, round)), TYPE_NONE);
    }
}

TEST("Gauntlet: opponents field three of their own type, stronger as the rounds go")
{
    u32 week, round, i, j;

    for (week = 1; week < 25; week++)
    {
        u32 seed = Gauntlet_WeekSeed(week);
        u32 firstTotal = 0, laterTotal = 0;

        for (round = 1; round <= 14; round++)
        {
            struct SundialMon team[GAUNTLET_TEAM_SIZE];
            enum SundialOpponent opp = Gauntlet_Opponent(seed, round);

            Gauntlet_OpponentTeam(seed, round, team);
            for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
            {
                EXPECT_NE(team[i].species, SPECIES_NONE);
                if (opp != SUNDIAL_OPP_RED)
                    EXPECT(IsSpeciesOfType(team[i].species, Gauntlet_OpponentType(opp)));
                for (j = 0; j < i; j++)
                    EXPECT_NE(team[i].species, team[j].species);
                if (round == 1) firstTotal += Gauntlet_BaseStatTotal(team[i].species);
                if (round == 8) laterTotal += Gauntlet_BaseStatTotal(team[i].species);
            }
            if (opp == SUNDIAL_OPP_RED)
                EXPECT_EQ(team[0].species, SPECIES_PIKACHU);
        }
        EXPECT_LT(firstTotal, laterTotal);
    }
}

TEST("Gauntlet: effort grows to the cap; rewards from round 5")
{
    EXPECT_GT(Gauntlet_EffortForRound(1), 0);
    EXPECT_LT(Gauntlet_EffortForRound(3), Gauntlet_EffortForRound(5));
    EXPECT_EQ(Gauntlet_EffortForRound(5), MAX_PER_STAT_EVS);
    EXPECT_EQ(Gauntlet_EffortForRound(40), MAX_PER_STAT_EVS);
    EXPECT(!Gauntlet_EarnsReward(4));
    EXPECT(Gauntlet_EarnsReward(5));
}
