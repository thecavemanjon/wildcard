#ifndef GUARD_SUNDIAL_SEED_H
#define GUARD_SUNDIAL_SEED_H

// Seeds and teams (DECISIONS "Seeds and recipes"). Plain C, no game state, so the
// same seed gives the same team on every cartridge and in the unit tests.

// Goes on the share card. Bump it whenever a change alters what a seed generates.
#define SUNDIAL_GENERATOR_VERSION 3 // 3: the daily roster cut to 19

// Both sides of every battle.
#define SUNDIAL_LEVEL 50

// One random stream per part of a battle, so changing how one part draws
// doesn't reshuffle the others.
enum SundialPart
{
    SUNDIAL_PART_TEAM = 1,
    SUNDIAL_PART_OPPONENT,
    SUNDIAL_PART_RIVAL, // which starter the rival picked
    SUNDIAL_PART_GAUNTLET_DRAFT = 16, // the gauntlet's (sundial_gauntlet.c)
    SUNDIAL_PART_GAUNTLET_LADDER,
    SUNDIAL_PART_GAUNTLET_TEAM,
    SUNDIAL_PART_RULE,
};

// Weekday tiers: difficulty climbs towards Sunday (design doc "Roster").
enum SundialTier
{
    SUNDIAL_TIER_GYM,      // Mon, Tue
    SUNDIAL_TIER_ELITE,    // Wed, Thu
    SUNDIAL_TIER_VILLAIN,  // Fri
    SUNDIAL_TIER_RIVAL,    // Sat
    SUNDIAL_TIER_CHAMPION, // Sun
};

// The roster: the design doc's 31. Append only, since the order decides who a seed picks.
enum SundialOpponent
{
    SUNDIAL_OPP_ROXANNE,
    SUNDIAL_OPP_BRAWLY,
    SUNDIAL_OPP_WATTSON,
    SUNDIAL_OPP_FLANNERY,
    SUNDIAL_OPP_NORMAN,
    SUNDIAL_OPP_WINONA,
    SUNDIAL_OPP_TATE_AND_LIZA,
    SUNDIAL_OPP_JUAN,
    SUNDIAL_OPP_SIDNEY,
    SUNDIAL_OPP_PHOEBE,
    SUNDIAL_OPP_GLACIA,
    SUNDIAL_OPP_DRAKE,
    SUNDIAL_OPP_MAXIE,
    SUNDIAL_OPP_ARCHIE,
    SUNDIAL_OPP_RIVAL, // Brendan or May, whichever the player isn't
    SUNDIAL_OPP_WALLACE,
    SUNDIAL_OPP_STEVEN,
    SUNDIAL_OPP_BROCK,
    SUNDIAL_OPP_MISTY,
    SUNDIAL_OPP_LT_SURGE,
    SUNDIAL_OPP_ERIKA,
    SUNDIAL_OPP_KOGA,
    SUNDIAL_OPP_SABRINA,
    SUNDIAL_OPP_BLAINE,
    SUNDIAL_OPP_GIOVANNI,
    SUNDIAL_OPP_LORELEI,
    SUNDIAL_OPP_BRUNO,
    SUNDIAL_OPP_AGATHA,
    SUNDIAL_OPP_LANCE,
    SUNDIAL_OPP_BLUE,
    SUNDIAL_OPP_RED,
    SUNDIAL_OPP_COUNT,
};

struct SundialRng
{
    u32 state;
};

struct SundialMon
{
    u16 species;
    u8 nature;
    u8 abilityNum; // 0 or 1; never the hidden ability
};

u32 Sundial_Mix32(u32 x);
u32 Sundial_DateSeed(u32 year, u32 month, u32 day);
u32 Sundial_Weekday(u32 year, u32 month, u32 day); // 0 = Sunday
enum SundialTier Sundial_TierForWeekday(u32 weekday);
enum SundialTier Sundial_OpponentTier(enum SundialOpponent opponent);
bool32 Sundial_IsDailyOpponent(enum SundialOpponent opponent);
enum SundialOpponent Sundial_PickOpponent(u32 seed, enum SundialTier tier);
enum SundialOpponent Sundial_DailyOpponent(u32 year, u32 month, u32 day);
u32 Sundial_WordSeed(const u8 *word);
bool32 Sundial_WordIs(const u8 *typed, const u8 *word);

// Event days replace the daily's opponent and team (same every year).
enum SundialEvent
{
    SUNDIAL_EVENT_NONE,
    SUNDIAL_EVENT_EASTER,
    SUNDIAL_EVENT_HALLOWEEN,
    SUNDIAL_EVENT_CHRISTMAS,
};
// Rule days (DECISIONS 2026-10-19): a twist on top of the weekday's tier.
enum SundialRule
{
    SUNDIAL_RULE_NONE,
    SUNDIAL_RULE_ELECTRIC_TERRAIN,
    SUNDIAL_RULE_GRASSY_TERRAIN,
    SUNDIAL_RULE_MISTY_TERRAIN,
    SUNDIAL_RULE_PSYCHIC_TERRAIN,
    SUNDIAL_RULE_TRICK_ROOM,
    SUNDIAL_RULE_INVERSE,
    SUNDIAL_RULE_COUNT,
};
enum SundialRule Sundial_RuleForDate(u32 year, u32 month, u32 day);

void Sundial_EasterSunday(u32 year, u32 *month, u32 *day);
enum SundialEvent Sundial_EventForDate(u32 year, u32 month, u32 day);
void Sundial_PickMoves(u16 species, u16 *moves);
enum SundialOpponent Sundial_FreePlayOpponent(u32 seed);
void Sundial_RngInit(struct SundialRng *rng, u32 seed, enum SundialPart part);
u32 Sundial_RngNext(struct SundialRng *rng);
u32 Sundial_RngBelow(struct SundialRng *rng, u32 n);

bool32 Sundial_IsInDailyPool(u16 species);
u32 Sundial_DailyPoolSize(void);
void Sundial_GenerateTeam(u32 seed, struct SundialMon *team);

#endif // GUARD_SUNDIAL_SEED_H
