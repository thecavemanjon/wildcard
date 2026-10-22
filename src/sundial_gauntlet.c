#include "global.h"
#include "pokemon.h"
#include "sundial_gauntlet.h"
#include "constants/pokemon.h"
#include "constants/species.h"

// Weeks run Monday to Sunday. Day 1 (1 January 2000) was a Saturday, so the
// first Monday is day 3 and opens week 1.
u32 Gauntlet_WeekNumber(u32 dayNumber)
{
    return (dayNumber + 4) / 7;
}

u32 Gauntlet_WeekSeed(u32 week)
{
    return Sundial_Mix32(0x6A000000 | week);
}

// Six to draft three from: a daily-style random six from the week's own stream.
void Gauntlet_Draft(u32 seed, struct SundialMon *draft)
{
    Sundial_GenerateTeam(Sundial_Mix32(seed ^ SUNDIAL_PART_GAUNTLET_DRAFT), draft);
}

// The ladder: three of the first four gym leaders, the other three, two of
// Lorelei/Bruno/Agatha, Lance, then Red. After Red, anyone from the crew.
static const u8 sTierGym1[] = { SUNDIAL_OPP_BROCK, SUNDIAL_OPP_MISTY, SUNDIAL_OPP_LT_SURGE, SUNDIAL_OPP_ERIKA };
static const u8 sTierGym2[] = { SUNDIAL_OPP_KOGA, SUNDIAL_OPP_SABRINA, SUNDIAL_OPP_BLAINE };
static const u8 sTierElite[] = { SUNDIAL_OPP_LORELEI, SUNDIAL_OPP_BRUNO, SUNDIAL_OPP_AGATHA };
static const u8 sCrew[] =
{
    SUNDIAL_OPP_BROCK, SUNDIAL_OPP_MISTY, SUNDIAL_OPP_LT_SURGE, SUNDIAL_OPP_ERIKA,
    SUNDIAL_OPP_KOGA, SUNDIAL_OPP_SABRINA, SUNDIAL_OPP_BLAINE,
    SUNDIAL_OPP_LORELEI, SUNDIAL_OPP_BRUNO, SUNDIAL_OPP_AGATHA, SUNDIAL_OPP_LANCE,
};

static void Shuffle(struct SundialRng *rng, u8 *items, u32 count)
{
    u32 i;

    for (i = count - 1; i > 0; i--)
    {
        u32 j = Sundial_RngBelow(rng, i + 1);
        u8 tmp = items[i];

        items[i] = items[j];
        items[j] = tmp;
    }
}

enum SundialOpponent Gauntlet_Opponent(u32 seed, u32 round)
{
    struct SundialRng rng;
    u8 gym1[ARRAY_COUNT(sTierGym1)], gym2[ARRAY_COUNT(sTierGym2)], elite[ARRAY_COUNT(sTierElite)];

    if (round == 0)
        round = 1;
    if (round == GAUNTLET_RED_ROUND)
        return SUNDIAL_OPP_RED;
    if (round == GAUNTLET_RED_ROUND - 1)
        return SUNDIAL_OPP_LANCE;
    if (round > GAUNTLET_RED_ROUND)
    {
        Sundial_RngInit(&rng, seed + round, SUNDIAL_PART_GAUNTLET_LADDER);
        return sCrew[Sundial_RngBelow(&rng, ARRAY_COUNT(sCrew))];
    }
    memcpy(gym1, sTierGym1, sizeof(gym1));
    memcpy(gym2, sTierGym2, sizeof(gym2));
    memcpy(elite, sTierElite, sizeof(elite));
    Sundial_RngInit(&rng, seed, SUNDIAL_PART_GAUNTLET_LADDER);
    Shuffle(&rng, gym1, ARRAY_COUNT(gym1));
    Shuffle(&rng, gym2, ARRAY_COUNT(gym2));
    Shuffle(&rng, elite, ARRAY_COUNT(elite));
    if (round <= 3)
        return gym1[round - 1];
    if (round <= 6)
        return gym2[round - 4];
    return elite[round - 7];
}

enum Type Gauntlet_OpponentType(enum SundialOpponent opponent)
{
    switch (opponent)
    {
    case SUNDIAL_OPP_BROCK:    return TYPE_ROCK;
    case SUNDIAL_OPP_MISTY:    return TYPE_WATER;
    case SUNDIAL_OPP_LT_SURGE: return TYPE_ELECTRIC;
    case SUNDIAL_OPP_ERIKA:    return TYPE_GRASS;
    case SUNDIAL_OPP_KOGA:     return TYPE_POISON;
    case SUNDIAL_OPP_SABRINA:  return TYPE_PSYCHIC;
    case SUNDIAL_OPP_BLAINE:   return TYPE_FIRE;
    case SUNDIAL_OPP_LORELEI:  return TYPE_ICE;
    case SUNDIAL_OPP_BRUNO:    return TYPE_FIGHTING;
    case SUNDIAL_OPP_AGATHA:   return TYPE_GHOST;
    case SUNDIAL_OPP_LANCE:    return TYPE_DRAGON;
    default:                   return TYPE_NONE;
    }
}

u32 Gauntlet_BaseStatTotal(u16 species)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[species];

    return info->baseHP + info->baseAttack + info->baseDefense
         + info->baseSpAttack + info->baseSpDefense + info->baseSpeed;
}

// How strong each round's Pokémon are (base stat total), climbing with the ladder.
static void StrengthBand(u32 round, u32 *low, u32 *high)
{
    if (round <= 3)       { *low = 400; *high = 500; }
    else if (round <= 6)  { *low = 460; *high = 540; }
    else if (round <= 9)  { *low = 500; *high = 600; }
    else                  { *low = 520; *high = 720; }
}

static bool32 FitsRound(u16 species, enum Type type, u32 low, u32 high)
{
    u32 bst;

    if (!Sundial_IsInDailyPool(species))
        return FALSE;
    if (type != TYPE_NONE && !IsSpeciesOfType(species, type))
        return FALSE;
    bst = Gauntlet_BaseStatTotal(species);
    return bst >= low && bst <= high;
}

// Red keeps Pikachu and brings two of his Gold/Silver/Origins regulars.
static const u16 sRedRegulars[] = { SPECIES_CHARIZARD, SPECIES_VENUSAUR, SPECIES_BLASTOISE, SPECIES_SNORLAX, SPECIES_ESPEON, SPECIES_LAPRAS };

// Three different species of the opponent's type in the round's band (the band
// widens until there are enough), each with a nature and ability slot.
void Gauntlet_OpponentTeam(u32 seed, u32 round, struct SundialMon *team)
{
    struct SundialRng rng;
    enum SundialOpponent opponent = Gauntlet_Opponent(seed, round);
    enum Type type = Gauntlet_OpponentType(opponent);
    u32 low, high, count, i, j, species;

    Sundial_RngInit(&rng, seed + round, SUNDIAL_PART_GAUNTLET_TEAM);
    if (opponent == SUNDIAL_OPP_RED)
    {
        u8 picks[ARRAY_COUNT(sRedRegulars)];

        for (i = 0; i < ARRAY_COUNT(picks); i++)
            picks[i] = i;
        Shuffle(&rng, picks, ARRAY_COUNT(picks));
        team[0].species = SPECIES_PIKACHU;
        team[1].species = sRedRegulars[picks[0]];
        team[2].species = sRedRegulars[picks[1]];
    }
    else
    {
        StrengthBand(round, &low, &high);
        for (;;)
        {
            count = 0;
            for (species = 1; species < NUM_SPECIES; species++)
            {
                if (FitsRound(species, type, low, high))
                    count++;
            }
            if (count >= GAUNTLET_TEAM_SIZE * 2 || (low == 0 && high >= 800))
                break;
            low = low > 40 ? low - 40 : 0;
            high += 40;
        }
        for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
        {
            bool32 duplicate;

            do
            {
                u32 pick = Sundial_RngBelow(&rng, count);

                for (species = 1; species < NUM_SPECIES; species++)
                {
                    if (FitsRound(species, type, low, high) && pick-- == 0)
                        break;
                }
                team[i].species = species;
                duplicate = FALSE;
                for (j = 0; j < i; j++)
                {
                    if (team[j].species == team[i].species)
                        duplicate = TRUE;
                }
            } while (duplicate);
        }
    }
    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
    {
        team[i].nature = Sundial_RngBelow(&rng, NUM_NATURES);
        team[i].abilityNum = Sundial_RngBelow(&rng, 2);
        if (gSpeciesInfo[team[i].species].abilities[1] == ABILITY_NONE)
            team[i].abilityNum = 0;
    }
}

// Effort values in the opponents' best attacking stat and Speed: 84 in round 1,
// full (252) from round 5 on.
u32 Gauntlet_EffortForRound(u32 round)
{
    u32 evs = 84 + (round > 0 ? round - 1 : 0) * 42;

    return evs > MAX_PER_STAT_EVS ? MAX_PER_STAT_EVS : evs;
}

bool32 Gauntlet_EarnsReward(u32 roundReached)
{
    return roundReached >= GAUNTLET_REWARD_ROUND;
}
