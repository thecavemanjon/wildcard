#include "global.h"
#include "battle_util.h"
#include "move.h"
#include "test/test.h"
#include "sundial_seed.h"
#include "constants/species.h"

// Golden values come from a Python port; a website or share-card checker must match them.
TEST("Sundial: hash and date seed match the reference values")
{
    EXPECT_EQ(Sundial_Mix32(0), 0);
    EXPECT_EQ(Sundial_Mix32(1), 0x688990C0);
    EXPECT_EQ(Sundial_DateSeed(2026, 10, 12), 0xD0E8F232);
}

TEST("Sundial: random stream matches the reference values")
{
    struct SundialRng rng;

    Sundial_RngInit(&rng, Sundial_DateSeed(2026, 10, 12), SUNDIAL_PART_TEAM);
    EXPECT_EQ(Sundial_RngNext(&rng), 0xE678B57F);
    EXPECT_EQ(Sundial_RngNext(&rng), 0xEE0A9E79);
    EXPECT_EQ(Sundial_RngNext(&rng), 0x70C32DC9);
}

TEST("Sundial: word seeds differ by word and repeat for the same word")
{
    static const u8 splash[] = _("SPLASH");
    static const u8 splosh[] = _("SPLOSH");

    static const u8 splashLower[] = _("splash");

    EXPECT_EQ(Sundial_WordSeed(splash), Sundial_WordSeed(splash));
    EXPECT_NE(Sundial_WordSeed(splash), Sundial_WordSeed(splosh));
    EXPECT_EQ(Sundial_WordSeed(splash), Sundial_WordSeed(splashLower));
}

TEST("Sundial: secret words match whatever the case, and only the whole word")
{
    static const u8 jonno[] = _("JONNO");
    static const u8 typed[] = _("jOnNo");
    static const u8 longer[] = _("JONNOS");
    static const u8 shorter[] = _("JONN");

    EXPECT(Sundial_WordIs(typed, jonno));
    EXPECT(!Sundial_WordIs(longer, jonno));
    EXPECT(!Sundial_WordIs(shorter, jonno));
}

TEST("Sundial: Free Play opponents come from the whole roster, same word same opponent")
{
    bool8 seen[SUNDIAL_OPP_COUNT] = {0};
    u32 i, seed;

    for (i = 0; i < 400; i++)
    {
        seed = Sundial_Mix32(i + 7);
        EXPECT_LT(Sundial_FreePlayOpponent(seed), SUNDIAL_OPP_COUNT);
        EXPECT_EQ(Sundial_FreePlayOpponent(seed), Sundial_FreePlayOpponent(seed));
        seen[Sundial_FreePlayOpponent(seed)] = TRUE;
    }
    for (i = 0; i < SUNDIAL_OPP_COUNT; i++)
        EXPECT(seen[i]);
}

TEST("Sundial: RngBelow covers its range evenly")
{
    struct SundialRng rng;
    u32 counts[6] = {0};
    u32 i;

    Sundial_RngInit(&rng, 12345, SUNDIAL_PART_TEAM);
    for (i = 0; i < 6000; i++)
        counts[Sundial_RngBelow(&rng, 6)]++;
    for (i = 0; i < 6; i++)
    {
        EXPECT_GT(counts[i], 900);
        EXPECT_LT(counts[i], 1100);
    }
}

TEST("Sundial: daily pool bans legendaries and mythicals only")
{
    EXPECT(!Sundial_IsInDailyPool(SPECIES_NONE));
    EXPECT(!Sundial_IsInDailyPool(SPECIES_MEWTWO));
    EXPECT(!Sundial_IsInDailyPool(SPECIES_MEW));
    EXPECT(!Sundial_IsInDailyPool(SPECIES_ZAPDOS));
    EXPECT(Sundial_IsInDailyPool(SPECIES_NIHILEGO));
    EXPECT(Sundial_IsInDailyPool(SPECIES_MAGIKARP));
    EXPECT(Sundial_IsInDailyPool(SPECIES_CATERPIE));
    EXPECT(Sundial_IsInDailyPool(SPECIES_GARCHOMP));
    EXPECT(Sundial_IsInDailyPool(SPECIES_SLAKING));
    EXPECT_GT(Sundial_DailyPoolSize(), 800);
}

TEST("Sundial: same date gives the same team; teams are six different pool species")
{
    struct SundialMon a[PARTY_SIZE], b[PARTY_SIZE];
    u32 i, j, day;

    for (day = 1; day <= 28; day++)
    {
        Sundial_GenerateTeam(Sundial_DateSeed(2026, 10, day), a);
        Sundial_GenerateTeam(Sundial_DateSeed(2026, 10, day), b);
        for (i = 0; i < PARTY_SIZE; i++)
        {
            EXPECT_EQ(a[i].species, b[i].species);
            EXPECT_EQ(a[i].nature, b[i].nature);
            EXPECT_EQ(a[i].abilityNum, b[i].abilityNum);
            EXPECT(Sundial_IsInDailyPool(a[i].species));
            EXPECT_LT(a[i].nature, NUM_NATURES);
            EXPECT_LT(a[i].abilityNum, 2);
            for (j = 0; j < i; j++)
                EXPECT_NE(a[i].species, a[j].species);
        }
    }
}

TEST("Sundial: consecutive days give different teams")
{
    struct SundialMon a[PARTY_SIZE], b[PARTY_SIZE];

    Sundial_GenerateTeam(Sundial_DateSeed(2026, 10, 12), a);
    Sundial_GenerateTeam(Sundial_DateSeed(2026, 10, 13), b);
    EXPECT_NE(a[0].species, b[0].species);
}

TEST("Sundial: weekday matches the real calendar")
{
    EXPECT_EQ(Sundial_Weekday(2026, 10, 12), 1); // Monday
    EXPECT_EQ(Sundial_Weekday(2000, 1, 1), 6);   // Saturday
    EXPECT_EQ(Sundial_Weekday(2024, 2, 29), 4);  // Thursday, leap day
    EXPECT_EQ(Sundial_Weekday(2027, 1, 3), 0);   // Sunday
}

TEST("Sundial: every tier has an opponent")
{
    u32 tier, opp, count;

    for (tier = SUNDIAL_TIER_GYM; tier <= SUNDIAL_TIER_CHAMPION; tier++)
    {
        count = 0;
        for (opp = 0; opp < SUNDIAL_OPP_COUNT; opp++)
        {
            if (Sundial_OpponentTier(opp) == tier)
                count++;
        }
        EXPECT_GT(count, 0);
    }
}

TEST("Sundial: each day's opponent comes from its weekday's tier, same date same opponent")
{
    u32 day;

    for (day = 1; day <= 31; day++)
    {
        enum SundialOpponent opp = Sundial_DailyOpponent(2026, 10, day);

        EXPECT_LT(opp, SUNDIAL_OPP_COUNT);
        EXPECT_EQ(Sundial_OpponentTier(opp), Sundial_TierForWeekday(Sundial_Weekday(2026, 10, day)));
        EXPECT(Sundial_IsDailyOpponent(opp));
        EXPECT_EQ(opp, Sundial_DailyOpponent(2026, 10, day));
    }
}

TEST("Sundial: every daily gym leader turns up over a few months of Mondays and Tuesdays")
{
    bool8 seen[SUNDIAL_OPP_COUNT] = {0};
    u32 i, seed;

    for (i = 0; i < 120; i++)
    {
        seed = Sundial_Mix32(i + 1);
        seen[Sundial_PickOpponent(seed, SUNDIAL_TIER_GYM)] = TRUE;
    }
    for (i = 0; i < SUNDIAL_OPP_COUNT; i++)
    {
        if (Sundial_OpponentTier(i) == SUNDIAL_TIER_GYM)
            EXPECT_EQ(seen[i], Sundial_IsDailyOpponent(i));
    }
}

TEST("Sundial: the daily roster is 19: Hoenn, Blue and Giovanni; Red and the Kanto crew are the gauntlet's")
{
    u32 opp, count = 0, counts[SUNDIAL_TIER_CHAMPION + 1] = {0};

    for (opp = 0; opp < SUNDIAL_OPP_COUNT; opp++)
    {
        if (Sundial_IsDailyOpponent(opp))
        {
            count++;
            counts[Sundial_OpponentTier(opp)]++;
        }
    }
    EXPECT_EQ(count, 19);
    EXPECT_EQ(counts[SUNDIAL_TIER_GYM], 8);
    EXPECT_EQ(counts[SUNDIAL_TIER_ELITE], 4);
    EXPECT_EQ(counts[SUNDIAL_TIER_VILLAIN], 3);
    EXPECT_EQ(counts[SUNDIAL_TIER_RIVAL], 2);
    EXPECT_EQ(counts[SUNDIAL_TIER_CHAMPION], 2);
    EXPECT(!Sundial_IsDailyOpponent(SUNDIAL_OPP_RED));
    EXPECT(Sundial_IsDailyOpponent(SUNDIAL_OPP_GIOVANNI));
    EXPECT(Sundial_IsDailyOpponent(SUNDIAL_OPP_BLUE));
}

TEST("Sundial: the roster is the design doc's 31")
{
    u32 opp, counts[SUNDIAL_TIER_CHAMPION + 1] = {0};

    EXPECT_EQ(SUNDIAL_OPP_COUNT, 31);
    for (opp = 0; opp < SUNDIAL_OPP_COUNT; opp++)
        counts[Sundial_OpponentTier(opp)]++;
    EXPECT_EQ(counts[SUNDIAL_TIER_GYM], 15);
    EXPECT_EQ(counts[SUNDIAL_TIER_ELITE], 8);
    EXPECT_EQ(counts[SUNDIAL_TIER_VILLAIN], 3);
    EXPECT_EQ(counts[SUNDIAL_TIER_RIVAL], 2);
    EXPECT_EQ(counts[SUNDIAL_TIER_CHAMPION], 3);
}

TEST("Sundial: picked moves are four different moves, own types first")
{
    u16 moves[MAX_MON_MOVES];

    Sundial_PickMoves(SPECIES_GRENINJA, moves);
    EXPECT_EQ(GetMoveType(moves[0]), TYPE_WATER);
    EXPECT_EQ(GetMoveType(moves[1]), TYPE_DARK);
    EXPECT_NE(GetMoveCategory(moves[0]), DAMAGE_CATEGORY_PHYSICAL); // Sp. Atk is its better stat
    EXPECT_NE(moves[2], moves[3]);
}

TEST("Sundial: picked moves skip Explosion and recharge moves")
{
    u16 moves[MAX_MON_MOVES];
    u32 i;

    Sundial_PickMoves(SPECIES_SNORLAX, moves);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        EXPECT(!IsExplosionMove(moves[i]));
        EXPECT(!MoveHasAdditionalEffectSelf(moves[i], MOVE_EFFECT_RECHARGE));
    }
}

TEST("Sundial: every pool mon gets moves, and Magikarp all three it knows")
{
    u16 moves[MAX_MON_MOVES];
    u32 species, i, j;

    for (species = 1; species < NUM_SPECIES; species += 5)
    {
        if (!Sundial_IsInDailyPool(species))
            continue;
        Sundial_PickMoves(species, moves);
        EXPECT_NE(moves[0], MOVE_NONE);
        for (i = 0; i < MAX_MON_MOVES; i++)
        {
            for (j = i + 1; j < MAX_MON_MOVES; j++)
                EXPECT(moves[i] == MOVE_NONE || moves[i] != moves[j]);
        }
    }
    Sundial_PickMoves(SPECIES_MAGIKARP, moves); // Tackle, then Flail and Splash
    EXPECT_EQ(moves[0], MOVE_TACKLE);
    EXPECT_NE(moves[2], MOVE_NONE);
    EXPECT_EQ(moves[3], MOVE_NONE);
}

TEST("Sundial: Easter Sunday matches the calendar")
{
    u32 month, day;

    Sundial_EasterSunday(2025, &month, &day);
    EXPECT_EQ(month, 4); EXPECT_EQ(day, 20);
    Sundial_EasterSunday(2026, &month, &day);
    EXPECT_EQ(month, 4); EXPECT_EQ(day, 5);
    Sundial_EasterSunday(2027, &month, &day);
    EXPECT_EQ(month, 3); EXPECT_EQ(day, 28);
    Sundial_EasterSunday(2038, &month, &day);
    EXPECT_EQ(month, 4); EXPECT_EQ(day, 25);
}

TEST("Sundial: event days fall on Halloween, Christmas and Easter only")
{
    EXPECT_EQ(Sundial_EventForDate(2026, 10, 31), SUNDIAL_EVENT_HALLOWEEN);
    EXPECT_EQ(Sundial_EventForDate(2026, 12, 25), SUNDIAL_EVENT_CHRISTMAS);
    EXPECT_EQ(Sundial_EventForDate(2027, 3, 28), SUNDIAL_EVENT_EASTER);
    EXPECT_EQ(Sundial_EventForDate(2026, 3, 28), SUNDIAL_EVENT_NONE);
    EXPECT_EQ(Sundial_EventForDate(2026, 10, 30), SUNDIAL_EVENT_NONE);
    EXPECT_EQ(Sundial_EventForDate(2026, 12, 24), SUNDIAL_EVENT_NONE);
}

TEST("Sundial: rule days: a terrain on Tuesdays, Trick Room on Wednesdays, Inverse on Thursdays")
{
    bool8 terrains[SUNDIAL_RULE_COUNT] = {0};
    u32 y, m, day, i;

    EXPECT_EQ(Sundial_RuleForDate(2026, 10, 19), SUNDIAL_RULE_NONE);       // Monday
    EXPECT_EQ(Sundial_RuleForDate(2026, 10, 21), SUNDIAL_RULE_TRICK_ROOM); // Wednesday
    EXPECT_EQ(Sundial_RuleForDate(2026, 10, 22), SUNDIAL_RULE_INVERSE);    // Thursday
    EXPECT_EQ(Sundial_RuleForDate(2026, 10, 25), SUNDIAL_RULE_NONE);       // Sunday
    EXPECT_EQ(Sundial_RuleForDate(2026, 12, 25), SUNDIAL_RULE_NONE);       // Christmas (a Friday anyway)
    EXPECT_EQ(Sundial_RuleForDate(2025, 12, 25), SUNDIAL_RULE_NONE);       // Christmas on a Thursday: the event wins
    for (y = 2026; y <= 2027; y++) // every Tuesday has a terrain, and all four turn up
    {
        for (m = 1; m <= 12; m++)
        {
            static const u8 lengths[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

            for (day = 1; day <= lengths[m - 1]; day++)
            {
                enum SundialRule rule = Sundial_RuleForDate(y, m, day);

                if (Sundial_Weekday(y, m, day) != 2 || Sundial_EventForDate(y, m, day) != SUNDIAL_EVENT_NONE)
                    continue;
                EXPECT(rule >= SUNDIAL_RULE_ELECTRIC_TERRAIN && rule <= SUNDIAL_RULE_PSYCHIC_TERRAIN);
                terrains[rule] = TRUE;
            }
        }
    }
    for (i = SUNDIAL_RULE_ELECTRIC_TERRAIN; i <= SUNDIAL_RULE_PSYCHIC_TERRAIN; i++)
        EXPECT(terrains[i]);
}
