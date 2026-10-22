#include "global.h"
#include "pokemon.h"
#include "battle_util.h"
#include "move.h"
#include "sundial_seed.h"
#include "constants/characters.h"
#include "constants/pokemon.h"

// lowbias32 (Chris Wellons): a cheap integer hash where every input bit flips
// about half the output bits.
u32 Sundial_Mix32(u32 x)
{
    x ^= x >> 16;
    x *= 0x7FEB352D;
    x ^= x >> 15;
    x *= 0x846CA68B;
    x ^= x >> 16;
    return x;
}

// Hashes YYYYMMDD, so a phone or a website can work out the same seed.
u32 Sundial_DateSeed(u32 year, u32 month, u32 day)
{
    return Sundial_Mix32(year * 10000 + month * 100 + day);
}

// Sakamoto's method; matches the real calendar from 1753 on.
u32 Sundial_Weekday(u32 year, u32 month, u32 day)
{
    static const u8 offsets[] = {0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4};

    if (month < 3)
        year--;
    return (year + year / 4 - year / 100 + year / 400 + offsets[month - 1] + day) % 7;
}

enum SundialTier Sundial_TierForWeekday(u32 weekday)
{
    static const u8 tiers[7] =
    {
        SUNDIAL_TIER_CHAMPION, // Sun
        SUNDIAL_TIER_GYM,      // Mon
        SUNDIAL_TIER_GYM,      // Tue
        SUNDIAL_TIER_ELITE,    // Wed
        SUNDIAL_TIER_ELITE,    // Thu
        SUNDIAL_TIER_VILLAIN,  // Fri
        SUNDIAL_TIER_RIVAL,    // Sat
    };

    return tiers[weekday % 7];
}

static const u8 sOpponentTiers[SUNDIAL_OPP_COUNT] =
{
    [SUNDIAL_OPP_ROXANNE]       = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_BRAWLY]        = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_WATTSON]       = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_FLANNERY]      = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_NORMAN]        = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_WINONA]        = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_TATE_AND_LIZA] = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_JUAN]          = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_SIDNEY]        = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_PHOEBE]        = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_GLACIA]        = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_DRAKE]         = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_MAXIE]         = SUNDIAL_TIER_VILLAIN,
    [SUNDIAL_OPP_ARCHIE]        = SUNDIAL_TIER_VILLAIN,
    [SUNDIAL_OPP_RIVAL]         = SUNDIAL_TIER_RIVAL,
    [SUNDIAL_OPP_WALLACE]       = SUNDIAL_TIER_CHAMPION,
    [SUNDIAL_OPP_STEVEN]        = SUNDIAL_TIER_CHAMPION,
    [SUNDIAL_OPP_BROCK]         = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_MISTY]         = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_LT_SURGE]      = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_ERIKA]         = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_KOGA]          = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_SABRINA]       = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_BLAINE]        = SUNDIAL_TIER_GYM,
    [SUNDIAL_OPP_GIOVANNI]      = SUNDIAL_TIER_VILLAIN,
    [SUNDIAL_OPP_LORELEI]       = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_BRUNO]         = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_AGATHA]        = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_LANCE]         = SUNDIAL_TIER_ELITE,
    [SUNDIAL_OPP_BLUE]          = SUNDIAL_TIER_RIVAL,
    [SUNDIAL_OPP_RED]           = SUNDIAL_TIER_CHAMPION,
};

enum SundialTier Sundial_OpponentTier(enum SundialOpponent opponent)
{
    return sOpponentTiers[opponent];
}

// The daily's 19 (DECISIONS 2026-10-19): Hoenn, plus Blue and Giovanni. The Kanto
// crew and Red are the gauntlet's; Free Play and PRACTICE still have everyone.
bool32 Sundial_IsDailyOpponent(enum SundialOpponent opponent)
{
    switch (opponent)
    {
    case SUNDIAL_OPP_BROCK:
    case SUNDIAL_OPP_MISTY:
    case SUNDIAL_OPP_LT_SURGE:
    case SUNDIAL_OPP_ERIKA:
    case SUNDIAL_OPP_KOGA:
    case SUNDIAL_OPP_SABRINA:
    case SUNDIAL_OPP_BLAINE:
    case SUNDIAL_OPP_LORELEI:
    case SUNDIAL_OPP_BRUNO:
    case SUNDIAL_OPP_AGATHA:
    case SUNDIAL_OPP_LANCE:
    case SUNDIAL_OPP_RED:
        return FALSE;
    default:
        return opponent < SUNDIAL_OPP_COUNT;
    }
}

// Uniform pick among the tier's daily opponents, from the seed's opponent stream.
enum SundialOpponent Sundial_PickOpponent(u32 seed, enum SundialTier tier)
{
    struct SundialRng rng;
    u32 i, count = 0, pick;

    for (i = 0; i < SUNDIAL_OPP_COUNT; i++)
    {
        if (sOpponentTiers[i] == tier && Sundial_IsDailyOpponent(i))
            count++;
    }
    Sundial_RngInit(&rng, seed, SUNDIAL_PART_OPPONENT);
    pick = Sundial_RngBelow(&rng, count);
    for (i = 0; i < SUNDIAL_OPP_COUNT; i++)
    {
        if (sOpponentTiers[i] == tier && Sundial_IsDailyOpponent(i) && pick-- == 0)
            return i;
    }
    return SUNDIAL_OPP_WALLACE;
}

enum SundialOpponent Sundial_DailyOpponent(u32 year, u32 month, u32 day)
{
    return Sundial_PickOpponent(Sundial_DateSeed(year, month, day),
                                Sundial_TierForWeekday(Sundial_Weekday(year, month, day)));
}

// Lowercase counts as uppercase in words, so "bigfish" and "BIGFISH" are one seed.
static u8 FoldCase(u8 c)
{
    if (c >= CHAR_a && c <= CHAR_z)
        c -= CHAR_a - CHAR_A;
    return c;
}

// FNV-1a over the word's bytes (game charmap, EOS-terminated), then mixed.
u32 Sundial_WordSeed(const u8 *word)
{
    u32 hash = 0x811C9DC5;

    for (; *word != EOS; word++)
    {
        hash ^= FoldCase(*word);
        hash *= 0x01000193;
    }
    return Sundial_Mix32(hash);
}

// Same word, ignoring case (for the secret words).
bool32 Sundial_WordIs(const u8 *typed, const u8 *word)
{
    for (; *typed != EOS && *word != EOS; typed++, word++)
    {
        if (FoldCase(*typed) != FoldCase(*word))
            return FALSE;
    }
    return *typed == *word;
}

// Free Play: any of the whole roster, from the seed's opponent stream.
enum SundialOpponent Sundial_FreePlayOpponent(u32 seed)
{
    struct SundialRng rng;

    Sundial_RngInit(&rng, seed, SUNDIAL_PART_OPPONENT);
    return Sundial_RngBelow(&rng, SUNDIAL_OPP_COUNT);
}

void Sundial_RngInit(struct SundialRng *rng, u32 seed, enum SundialPart part)
{
    rng->state = Sundial_Mix32(seed ^ Sundial_Mix32(part));
}

// Weyl sequence through the mixer (the splitmix idea, in 32 bits).
u32 Sundial_RngNext(struct SundialRng *rng)
{
    rng->state += 0x9E3779B9;
    return Sundial_Mix32(rng->state);
}

// Uniform-enough in [0, n) without division.
u32 Sundial_RngBelow(struct SundialRng *rng, u32 n)
{
    return ((u64)Sundial_RngNext(rng) * n) >> 32;
}

// Daily pool: every National Dex base form that isn't a legendary or mythical
// (Ultra Beasts are in). Any evolution stage, no guardrails. Pool order is species ID order.
bool32 Sundial_IsInDailyPool(u16 species)
{
    const struct SpeciesInfo *info;

    if (species == SPECIES_NONE || species >= NUM_SPECIES || !IsSpeciesEnabled(species))
        return FALSE;
    info = &gSpeciesInfo[species];
    return info->natDexNum != 0
        && info->natDexNum <= NATIONAL_DEX_COUNT
        && GET_BASE_SPECIES_ID(species) == species
        && !info->isRestrictedLegendary
        && !info->isSubLegendary
        && !info->isMythical;
}

u32 Sundial_DailyPoolSize(void)
{
    u32 species, count = 0;

    for (species = 1; species < NUM_SPECIES; species++)
    {
        if (Sundial_IsInDailyPool(species))
            count++;
    }
    return count;
}

// Six different species from the pool, each with a nature and ability slot from
// the seed (the game's own RNG would give two players different abilities).
// Draws pool positions first, then finds them all in one pass over the species.
void Sundial_GenerateTeam(u32 seed, struct SundialMon *team)
{
    struct SundialRng rng;
    u32 picks[PARTY_SIZE];
    u32 poolSize = Sundial_DailyPoolSize();
    u32 species, poolIndex = 0;
    u32 i, j;

    Sundial_RngInit(&rng, seed, SUNDIAL_PART_TEAM);
    for (i = 0; i < PARTY_SIZE; i++)
    {
        bool32 duplicate;

        do
        {
            picks[i] = Sundial_RngBelow(&rng, poolSize);
            duplicate = FALSE;
            for (j = 0; j < i; j++)
            {
                if (picks[j] == picks[i])
                    duplicate = TRUE;
            }
        } while (duplicate);
        team[i].nature = Sundial_RngBelow(&rng, NUM_NATURES);
        team[i].abilityNum = Sundial_RngBelow(&rng, 2);
    }

    for (species = 1; species < NUM_SPECIES; species++)
    {
        if (!Sundial_IsInDailyPool(species))
            continue;
        for (i = 0; i < PARTY_SIZE; i++)
        {
            if (picks[i] == poolIndex)
            {
                team[i].species = species;
                if (gSpeciesInfo[species].abilities[1] == ABILITY_NONE)
                    team[i].abilityNum = 0;
            }
        }
        poolIndex++;
    }
}

// Which weekday has which rule: the one table to change. Tuesday's terrain is
// picked by the date. Event days keep their own battle, no rule.
enum SundialRule Sundial_RuleForDate(u32 year, u32 month, u32 day)
{
    struct SundialRng rng;

    if (Sundial_EventForDate(year, month, day) != SUNDIAL_EVENT_NONE)
        return SUNDIAL_RULE_NONE;
    switch (Sundial_Weekday(year, month, day))
    {
    case 2: // Tuesday
        Sundial_RngInit(&rng, Sundial_DateSeed(year, month, day), SUNDIAL_PART_RULE);
        return SUNDIAL_RULE_ELECTRIC_TERRAIN + Sundial_RngBelow(&rng, 4);
    case 3: // Wednesday
        return SUNDIAL_RULE_TRICK_ROOM;
    case 4: // Thursday
        return SUNDIAL_RULE_INVERSE;
    default:
        return SUNDIAL_RULE_NONE;
    }
}

// Western Easter Sunday: the anonymous Gregorian computus (Meeus/Jones/Butcher).
void Sundial_EasterSunday(u32 year, u32 *month, u32 *day)
{
    u32 a = year % 19;
    u32 b = year / 100;
    u32 c = year % 100;
    u32 d = b / 4;
    u32 e = b % 4;
    u32 f = (b + 8) / 25;
    u32 g = (b - f + 1) / 3;
    u32 h = (19 * a + b - d - g + 15) % 30;
    u32 i = c / 4;
    u32 k = c % 4;
    u32 l = (32 + 2 * e + 2 * i - h - k) % 7;
    u32 m = (a + 11 * h + 22 * l) / 451;

    *month = (h + l - 7 * m + 114) / 31;
    *day = (h + l - 7 * m + 114) % 31 + 1;
}

enum SundialEvent Sundial_EventForDate(u32 year, u32 month, u32 day)
{
    u32 easterMonth, easterDay;

    if (month == 10 && day == 31)
        return SUNDIAL_EVENT_HALLOWEEN;
    if (month == 12 && day == 25)
        return SUNDIAL_EVENT_CHRISTMAS;
    Sundial_EasterSunday(year, &easterMonth, &easterDay);
    if (month == easterMonth && day == easterDay)
        return SUNDIAL_EVENT_EASTER;
    return SUNDIAL_EVENT_NONE;
}

// Moves that look strong on paper but waste a turn, need a setup the team
// doesn't have, or knock out the user.
static bool32 IsAwkwardMove(u16 move)
{
    switch (GetMoveEffect(move))
    {
    case EFFECT_TWO_TURNS_ATTACK:
    case EFFECT_SOLAR_BEAM:
    case EFFECT_SKY_DROP:
    case EFFECT_FOCUS_PUNCH:
    case EFFECT_DREAM_EATER:
    case EFFECT_LAST_RESORT:
    case EFFECT_FUTURE_SIGHT:
    case EFFECT_SNORE:
    case EFFECT_FIRST_TURN_ONLY:
    case EFFECT_SYNCHRONOISE:
    case EFFECT_BELCH:
    case EFFECT_SHELL_TRAP:
    case EFFECT_UPPER_HAND:
    case EFFECT_MAX_HP_50_RECOIL:
    case EFFECT_FINAL_GAMBIT:
    case EFFECT_SPIT_UP:
    case EFFECT_OHKO:
        return TRUE;
    default:
        return IsExplosionMove(move) || MoveHasAdditionalEffectSelf(move, MOVE_EFFECT_RECHARGE);
    }
}

// Rough damage per turn: power x accuracy x the attacking stat it uses, with
// STAB. Moves of variable or fixed power (Low Kick, Seismic Toss) score 0.
static u32 ScoreMove(u16 species, u16 move)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[species];
    u32 power = GetMovePower(move);
    u32 accuracy = GetMoveAccuracy(move);
    u32 score;

    if (GetMoveCategory(move) == DAMAGE_CATEGORY_STATUS || power <= 1 || IsAwkwardMove(move))
        return 0;
    if (IsMultiHitMove(move))
        power *= 3;
    else if (GetMoveStrikeCount(move) > 1)
        power *= GetMoveStrikeCount(move);
    score = power * (accuracy == 0 ? 100 : accuracy);
    score *= GetMoveCategory(move) == DAMAGE_CATEGORY_PHYSICAL ? info->baseAttack : info->baseSpAttack;
    if (IsSpeciesOfType(species, GetMoveType(move)))
        score = score * 3 / 2;
    return score;
}

static bool32 HasMove(const u16 *moves, u16 move)
{
    u32 i;

    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (moves[i] == move)
            return TRUE;
    }
    return FALSE;
}

static bool32 HasMoveOfType(const u16 *moves, enum Type type)
{
    u32 i;

    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (moves[i] != MOVE_NONE && GetMoveType(moves[i]) == type)
            return TRUE;
    }
    return FALSE;
}

// The best-scoring move it learns (any level-up level, or TM/tutor) that isn't
// taken yet. typeWanted: only that type; else if newTypeOnly, no type it already has.
static u16 BestMove(u16 species, const u16 *moves, s32 typeWanted, bool32 newTypeOnly)
{
    const struct LevelUpMove *levelUp = GetSpeciesLevelUpLearnset(species);
    const u16 *teachable = GetSpeciesTeachableLearnset(species);
    u16 best = MOVE_NONE;
    u32 bestScore = 0;
    u32 i, pass;

    for (pass = 0; pass < 2; pass++)
    {
        for (i = 0; ; i++)
        {
            u16 move;
            u32 score;

            if (pass == 0 ? levelUp[i].move == LEVEL_UP_MOVE_END : teachable[i] == MOVE_UNAVAILABLE)
                break;
            move = pass == 0 ? levelUp[i].move : teachable[i];
            if (HasMove(moves, move))
                continue;
            if (typeWanted >= 0 && GetMoveType(move) != typeWanted)
                continue;
            if (newTypeOnly && HasMoveOfType(moves, GetMoveType(move)))
                continue;
            score = ScoreMove(species, move);
            if (score > bestScore)
            {
                best = move;
                bestScore = score;
            }
        }
    }
    return best;
}

// Four moves for a team mon, the same for everyone (no seed): the strongest of
// each of its own types, then the strongest that hit new types, then the
// strongest of whatever's left. A mon with fewer than four usable attacks fills
// up with its latest level-up moves (status moves included).
void Sundial_PickMoves(u16 species, u16 *moves)
{
    const struct LevelUpMove *levelUp = GetSpeciesLevelUpLearnset(species);
    u32 count = 0, i, slot;
    s32 j;

    for (i = 0; i < MAX_MON_MOVES; i++)
        moves[i] = MOVE_NONE;

    for (slot = 0; slot < 2; slot++)
    {
        enum Type type = GetSpeciesType(species, slot);

        if (slot == 1 && type == GetSpeciesType(species, 0))
            break;
        if ((moves[count] = BestMove(species, moves, type, FALSE)) != MOVE_NONE)
            count++;
    }
    while (count < MAX_MON_MOVES && (moves[count] = BestMove(species, moves, -1, TRUE)) != MOVE_NONE)
        count++;
    while (count < MAX_MON_MOVES && (moves[count] = BestMove(species, moves, -1, FALSE)) != MOVE_NONE)
        count++;

    for (i = 0; levelUp[i].move != LEVEL_UP_MOVE_END; i++)
        ;
    for (j = i - 1; j >= 0 && count < MAX_MON_MOVES; j--)
    {
        if (!HasMove(moves, levelUp[j].move))
            moves[count++] = levelUp[j].move;
    }
}
