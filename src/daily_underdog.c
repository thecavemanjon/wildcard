#include "global.h"
#include "tileset_anims.h"
#include "field_camera.h"
#include "daily_underdog.h"
#include "wildcard_sim.h"
#include "battle.h"
#include "battle_setup.h"
#include "battle_util.h"
#include "hall_of_fame.h"
#include "item.h"
#include "load_save.h"
#include "main.h"
#include "overworld.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "field_screen_effect.h"
#include "fieldmap.h"
#include "malloc.h"
#include "money.h"
#include "naming_screen.h"
#include "palette.h"
#include "pokedex.h"
#include "pokemon.h"
#include "save.h"
#include "rtc.h"
#include "script_menu.h"
#include "script_pokemon_util.h"
#include "string_util.h"
#include "sundial_card.h"
#include "sundial_record.h"
#include "sundial_seed.h"
#include "wildcard_gauntlet.h"
#include "constants/script_menu.h"
#include "constants/rgb.h"
#include "constants/event_objects.h"
#include "constants/items.h"
#include "constants/map_groups.h"
#include "constants/moves.h"
#include "constants/species.h"
#include "constants/trainers.h"
#include "constants/vars.h"
#include "constants/wildcard_bedroom.h"

// The fixed OP team below is for testing; the PC gives the daily team.
#define TEAM_LEVEL SUNDIAL_LEVEL

// Free Play's word, kept for the results card.
EWRAM_DATA static u8 sSeedWord[CODE_NAME_LENGTH + 1] = {0};

struct TestTeamMon
{
    u16 species;
    u16 heldItem;
    u8 nature;
    bool8 hiddenAbility;
    bool8 physical; // 252 Atk / 252 Spe if TRUE, 252 SpA / 252 Spe if FALSE
    u16 moves[MAX_MON_MOVES];
};

// Grass and Electric, built to flatten Wallace while we test the Hall of Fame.
static const struct TestTeamMon sTestTeam[PARTY_SIZE] =
{
    { SPECIES_RILLABOOM, ITEM_CHOICE_BAND, NATURE_ADAMANT, TRUE,  TRUE,  { MOVE_GRASSY_GLIDE, MOVE_WOOD_HAMMER,    MOVE_KNOCK_OFF,     MOVE_HIGH_HORSEPOWER } },
    { SPECIES_ZAPDOS,    ITEM_LEFTOVERS,   NATURE_TIMID,   FALSE, FALSE, { MOVE_THUNDERBOLT,  MOVE_HURRICANE,      MOVE_HEAT_WAVE,     MOVE_ROOST } },
    { SPECIES_TAPU_KOKO, ITEM_LIFE_ORB,    NATURE_TIMID,   FALSE, FALSE, { MOVE_THUNDERBOLT,  MOVE_DAZZLING_GLEAM, MOVE_GRASS_KNOT,    MOVE_VOLT_SWITCH } },
    { SPECIES_KARTANA,   ITEM_FOCUS_SASH,  NATURE_JOLLY,   FALSE, TRUE,  { MOVE_LEAF_BLADE,   MOVE_SACRED_SWORD,   MOVE_SMART_STRIKE,  MOVE_SWORDS_DANCE } },
    { SPECIES_REGIELEKI, ITEM_LIFE_ORB,    NATURE_JOLLY,   FALSE, TRUE,  { MOVE_THUNDERBOLT,  MOVE_EXTREME_SPEED,  MOVE_VOLT_SWITCH,   MOVE_EXPLOSION } },
    { SPECIES_SERPERIOR, ITEM_LEFTOVERS,   NATURE_TIMID,   TRUE,  FALSE, { MOVE_LEAF_STORM,   MOVE_DRAGON_PULSE,   MOVE_GLARE,         MOVE_SYNTHESIS } },
};

// Replaces the player's party with the test team, fully healed.
void DailyUnderdog_GiveTestTeam(void)
{
    u32 i, j;

    ZeroPlayerPartyMons();
    for (i = 0; i < PARTY_SIZE; i++)
    {
        struct PokemonTemplate mon = {0};

        mon.species = sTestTeam[i].species;
        mon.heldItem = sTestTeam[i].heldItem;
        mon.level = TEAM_LEVEL;
        mon.nature = sTestTeam[i].nature;
        mon.gender = MON_GENDER_RANDOM;
        mon.origin = GIFTMON_ORIGIN;
        if (sTestTeam[i].hiddenAbility)
        {
            mon.abilityNum = 2;
            mon.doNotUseDefaultAbility = TRUE;
        }
        for (j = 0; j < NUM_STATS; j++)
            mon.ivs[j] = MAX_PER_STAT_IVS; // matches Wallace's perfect IVs
        mon.evs[STAT_HP] = 4;
        mon.evs[STAT_SPEED] = 252;
        mon.evs[sTestTeam[i].physical ? STAT_ATK : STAT_SPATK] = 252;
        for (j = 0; j < MAX_MON_MOVES; j++)
            mon.moves[j] = sTestTeam[i].moves[j];
        ScriptGiveMonParameterized(B_SIDE_PLAYER, PARTY_SIZE, &mon);
    }
}

// Arena slots: the case numbers in data/maps/UnderdogArena_Wallace/scripts.inc.
// Rivals take three slots in a row, one per starter, picked by the seed.
#define RIVAL_VARIANTS 3

static const struct
{
    u8 slot;
    u16 gfx;
} sArenaOpponents[SUNDIAL_OPP_COUNT] =
{
    [SUNDIAL_OPP_ROXANNE]       = {  0, OBJ_EVENT_GFX_ROXANNE },
    [SUNDIAL_OPP_BRAWLY]        = {  1, OBJ_EVENT_GFX_BRAWLY },
    [SUNDIAL_OPP_WATTSON]       = {  2, OBJ_EVENT_GFX_WATTSON },
    [SUNDIAL_OPP_FLANNERY]      = {  3, OBJ_EVENT_GFX_FLANNERY },
    [SUNDIAL_OPP_NORMAN]        = {  4, OBJ_EVENT_GFX_NORMAN },
    [SUNDIAL_OPP_WINONA]        = {  5, OBJ_EVENT_GFX_WINONA },
    [SUNDIAL_OPP_TATE_AND_LIZA] = {  6, OBJ_EVENT_GFX_TATE }, // Liza is a second object
    [SUNDIAL_OPP_JUAN]          = {  7, OBJ_EVENT_GFX_JUAN },
    [SUNDIAL_OPP_SIDNEY]        = {  8, OBJ_EVENT_GFX_SIDNEY },
    [SUNDIAL_OPP_PHOEBE]        = {  9, OBJ_EVENT_GFX_PHOEBE },
    [SUNDIAL_OPP_GLACIA]        = { 10, OBJ_EVENT_GFX_GLACIA },
    [SUNDIAL_OPP_DRAKE]         = { 11, OBJ_EVENT_GFX_DRAKE },
    [SUNDIAL_OPP_MAXIE]         = { 12, OBJ_EVENT_GFX_MAXIE },
    [SUNDIAL_OPP_ARCHIE]        = { 13, OBJ_EVENT_GFX_ARCHIE },
    [SUNDIAL_OPP_WALLACE]       = { 14, OBJ_EVENT_GFX_WALLACE },
    [SUNDIAL_OPP_STEVEN]        = { 15, OBJ_EVENT_GFX_STEVEN },
    [SUNDIAL_OPP_RIVAL]         = { 19, OBJ_EVENT_GFX_MAY_NORMAL }, // Brendan (16) for a female player
    [SUNDIAL_OPP_BROCK]         = { 22, OBJ_EVENT_GFX_BROCK },
    [SUNDIAL_OPP_MISTY]         = { 23, OBJ_EVENT_GFX_MISTY },
    [SUNDIAL_OPP_LT_SURGE]      = { 24, OBJ_EVENT_GFX_LT_SURGE },
    [SUNDIAL_OPP_ERIKA]         = { 25, OBJ_EVENT_GFX_ERIKA },
    [SUNDIAL_OPP_KOGA]          = { 26, OBJ_EVENT_GFX_KOGA },
    [SUNDIAL_OPP_SABRINA]       = { 27, OBJ_EVENT_GFX_SABRINA },
    [SUNDIAL_OPP_BLAINE]        = { 28, OBJ_EVENT_GFX_BLAINE },
    [SUNDIAL_OPP_GIOVANNI]      = { 29, OBJ_EVENT_GFX_GIOVANNI },
    [SUNDIAL_OPP_LORELEI]       = { 30, OBJ_EVENT_GFX_LORELEI },
    [SUNDIAL_OPP_BRUNO]         = { 31, OBJ_EVENT_GFX_BRUNO },
    [SUNDIAL_OPP_AGATHA]        = { 32, OBJ_EVENT_GFX_AGATHA },
    [SUNDIAL_OPP_LANCE]         = { 33, OBJ_EVENT_GFX_LANCE },
    [SUNDIAL_OPP_RED]           = { 34, OBJ_EVENT_GFX_RED_NORMAL },
    [SUNDIAL_OPP_BLUE]          = { 35, OBJ_EVENT_GFX_BLUE },
};

#define ARENA_SLOT_BRENDAN 16
#define ARENA_SLOT_RED_ORIGINS 38

// Home turf: each arena slot's room and where you walk in. Hoenn opponents fight in
// their own rooms; Kanto ones (whose FRLG rooms can't load in an Emerald build) get
// arenas of their own: type amphitheatres, the dojo, the pool, Blue's stadium and
// Red's summit (wildcard/art/arenas/build_arenas.py; DECISIONS 2026-10-16).
// Puzzle gyms put you a few steps from the leader, since their puzzles need
// Emerald's own scripts.
static const struct
{
    u16 map;
    u8 x;
    u8 y;
} sArenaRooms[] =
{
    [ 0] = { MAP_UNDERDOG_ARENA_QUARRY,       10,  8 }, // Roxanne: Quarry stadium
    [ 1] = { MAP_UNDERDOG_ARENA_DOJO_HALL,    10,  8 }, // Brawly: DojoHall stadium
    [ 2] = { MAP_UNDERDOG_ARENA_NEON_ELECTRIC, 10,  8 }, // Wattson: NeonElectric stadium
    [ 3] = { MAP_UNDERDOG_ARENA_VOLCANO,      10,  8 }, // Flannery: Volcano stadium
    [ 4] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Norman: Grand stadium
    [ 5] = { MAP_UNDERDOG_ARENA_SKY,          10,  8 }, // Winona: Sky stadium
    [ 6] = { MAP_UNDERDOG_ARENA_NEON_SYNTH_TATE_AND_LIZA, 10,  8 }, // Tate & Liza: NeonSynth stadium
    [ 7] = { MAP_UNDERDOG_ARENA_AQUA,         10,  8 }, // Juan: Aqua stadium
    [ 8] = { MAP_UNDERDOG_ARENA_NEON_TOXIC,   10,  8 }, // Sidney: NeonToxic stadium
    [ 9] = { MAP_UNDERDOG_ARENA_MOONLIT,      10,  8 }, // Phoebe: Moonlit stadium
    [10] = { MAP_UNDERDOG_ARENA_RINK,         10,  8 }, // Glacia: Rink stadium
    [11] = { MAP_UNDERDOG_ARENA_SKY,          10,  8 }, // Drake: Sky stadium
    [12] = { MAP_UNDERDOG_ARENA_VOLCANO,      10,  8 }, // Maxie: Volcano stadium
    [13] = { MAP_UNDERDOG_ARENA_AQUA,         10,  8 }, // Archie: Aqua stadium
    [14] = { MAP_UNDERDOG_ARENA_AQUA,         10,  8 }, // Wallace: Aqua stadium
    [15] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Steven: Grand stadium
    [16] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Brendan: Grand stadium
    [17] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Brendan: Grand stadium
    [18] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Brendan: Grand stadium
    [19] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // May: Grand stadium
    [20] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // May: Grand stadium
    [21] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // May: Grand stadium
    [22] = { MAP_UNDERDOG_ARENA_QUARRY,       10,  8 }, // Brock: Quarry stadium
    [23] = { MAP_UNDERDOG_ARENA_AQUA,         10,  8 }, // Misty: Aqua stadium
    [24] = { MAP_UNDERDOG_ARENA_NEON_ELECTRIC, 10,  8 }, // Lt. Surge: NeonElectric stadium
    [25] = { MAP_UNDERDOG_ARENA_GARDEN,       10,  8 }, // Erika: Garden stadium
    [26] = { MAP_UNDERDOG_ARENA_NEON_TOXIC,   10,  8 }, // Koga: NeonToxic stadium
    [27] = { MAP_UNDERDOG_ARENA_NEON_SYNTH,   10,  8 }, // Sabrina: NeonSynth stadium
    [28] = { MAP_UNDERDOG_ARENA_VOLCANO,      10,  8 }, // Blaine: Volcano stadium
    [29] = { MAP_UNDERDOG_ARENA_QUARRY,       10,  8 }, // Giovanni: Quarry stadium
    [30] = { MAP_UNDERDOG_ARENA_RINK,         10,  8 }, // Lorelei: Rink stadium
    [31] = { MAP_UNDERDOG_ARENA_DOJO_HALL,    10,  8 }, // Bruno: DojoHall stadium
    [32] = { MAP_UNDERDOG_ARENA_MOONLIT,      10,  8 }, // Agatha: Moonlit stadium
    [33] = { MAP_UNDERDOG_ARENA_SKY,          10,  8 }, // Lance: Sky stadium
    [34] = { MAP_UNDERDOG_ARENA_RED,            10,  9 }, // Red, on the Mt. Silver summit
    [35] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Blue: Grand stadium
    [36] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Blue: Grand stadium
    [37] = { MAP_UNDERDOG_ARENA_GRAND,        10,  8 }, // Blue: Grand stadium
    [38] = { MAP_UNDERDOG_ARENA_RED,            10,  9 }, // Red, Origins team (ORIGINS)
};

// Puts today's opponent in the arena: which script case runs, and their sprite.
static void SetArenaOpponent(u32 seed, enum SundialOpponent opponent)
{
    u32 slot = sArenaOpponents[opponent].slot;
    u16 gfx = sArenaOpponents[opponent].gfx;

    if (opponent == SUNDIAL_OPP_RIVAL || opponent == SUNDIAL_OPP_BLUE)
    {
        struct SundialRng rng;

        Sundial_RngInit(&rng, seed, SUNDIAL_PART_RIVAL);
        if (opponent == SUNDIAL_OPP_RIVAL && gSaveBlock2Ptr->playerGender != MALE)
        {
            slot = ARENA_SLOT_BRENDAN;
            gfx = OBJ_EVENT_GFX_BRENDAN_NORMAL;
        }
        slot += Sundial_RngBelow(&rng, RIVAL_VARIANTS);
    }
    VarSet(VAR_UNDERDOG_ARENA_SLOT, slot);
    VarSet(VAR_OBJ_GFX_ID_0, gfx);
}

// For the gauntlet (src/wildcard_gauntlet.c).
void DailyUnderdog_SetArenaOpponent(u32 seed, enum SundialOpponent opponent)
{
    SetArenaOpponent(seed, opponent);
}

struct SecretMon
{
    u16 species;
    u16 heldItem;
    u16 moves[MAX_MON_MOVES]; // left empty: the usual last four level-up moves
};

// A secret word picks the opponent and team by hand instead of by seed.
struct SecretWord
{
    const u8 *word;
    enum SundialOpponent opponent;
    u8 arenaSlot; // an opponent outside the roster (0: the opponent's own slot)
    struct SecretMon team[PARTY_SIZE];
};

// Today's opponent and team from the cartridge clock's date (DECISIONS "Seeds and recipes"):
// six random pool species at level 50, perfect IVs like the opponents, no EVs or
// items, best four moves (Sundial_PickMoves). A secret word swaps in its own six (natures
// still come from the seed).
static void GiveTeam(u32 seed, const struct SecretWord *secret)
{
    struct SundialMon team[PARTY_SIZE];
    u32 i, j;

    Sundial_GenerateTeam(seed, team);
    ZeroPlayerPartyMons();
    for (i = 0; i < PARTY_SIZE; i++)
    {
        struct PokemonTemplate mon = {0};

        mon.species = team[i].species;
        mon.level = TEAM_LEVEL;
        mon.nature = team[i].nature;
        mon.abilityNum = team[i].abilityNum;
        if (secret != NULL)
        {
            mon.species = secret->team[i].species;
            mon.heldItem = secret->team[i].heldItem;
            if (gSpeciesInfo[mon.species].abilities[1] == ABILITY_NONE)
                mon.abilityNum = 0;
        }
        mon.doNotUseDefaultAbility = TRUE;
        mon.gender = MON_GENDER_RANDOM;
        mon.origin = GIFTMON_ORIGIN;
        for (j = 0; j < NUM_STATS; j++)
            mon.ivs[j] = MAX_PER_STAT_IVS;
        Sundial_PickMoves(mon.species, mon.moves);
        if (secret != NULL && secret->team[i].moves[0] != MOVE_NONE)
        {
            for (j = 0; j < MAX_MON_MOVES; j++)
                mon.moves[j] = secret->team[i].moves[j];
        }
        ScriptGiveMonParameterized(B_SIDE_PLAYER, PARTY_SIZE, &mon);
    }
}

struct Date
{
    u32 year, month, day;
};

// Today's date straight from the cartridge clock. Not GetFullYear()/GetDay():
// upstream counts 1 Jan 2000 as day 1 and then adds it to an epoch that is
// already 1 Jan 2000, so those run a day ahead.
static struct Date Today(void)
{
    struct SiiRtcInfo rtc;
    struct Date date;

    if (WildcardSim_GetDate(&date.year, &date.month, &date.day)) // the balance sim's pretend date
        return date;
    RtcGetInfo(&rtc);
    date.year = 2000 + ConvertBcdToBinary(rtc.year);
    date.month = ConvertBcdToBinary(rtc.month);
    date.day = ConvertBcdToBinary(rtc.day);
    return date;
}

void DailyUnderdog_GetToday(u32 *year, u32 *month, u32 *day)
{
    struct Date today = Today();

    *year = today.year;
    *month = today.month;
    *day = today.day;
}

u32 DailyUnderdog_TodayNumber(void)
{
    struct Date today = Today();

    return Sundial_DayNumber(today.year, today.month, today.day);
}

static u32 TodaysSeed(void)
{
    struct Date today = Today();

    return Sundial_DateSeed(today.year, today.month, today.day);
}

static void LoadRecord(struct SundialRecord *record)
{
    record->lastDay = VarGet(VAR_UNDERDOG_LAST_DAILY);
    record->result = VarGet(VAR_UNDERDOG_LAST_RESULT);
    record->wins = VarGet(VAR_UNDERDOG_WINS);
    record->losses = VarGet(VAR_UNDERDOG_LOSSES);
    record->winStreak = VarGet(VAR_UNDERDOG_WIN_STREAK);
    record->playStreak = VarGet(VAR_UNDERDOG_PLAY_STREAK);
}

static void StoreRecord(const struct SundialRecord *record)
{
    VarSet(VAR_UNDERDOG_LAST_DAILY, record->lastDay);
    VarSet(VAR_UNDERDOG_LAST_RESULT, record->result);
    VarSet(VAR_UNDERDOG_WINS, record->wins);
    VarSet(VAR_UNDERDOG_LOSSES, record->losses);
    VarSet(VAR_UNDERDOG_WIN_STREAK, record->winStreak);
    VarSet(VAR_UNDERDOG_PLAY_STREAK, record->playStreak);
}

// PC -> DAILY BATTLE. If today's daily is still free, claims it and hands out the
// team; the script then saves (DailyUnderdog_Save) before the warp, so resetting
// mid-battle can't buy a second try. VAR_RESULT:
// SUNDIAL_RESULT_NONE when the battle is on, otherwise how today's attempt went.
static const struct SecretWord *EventBattle(enum SundialEvent event);

void DailyUnderdog_TryStartDaily(void)
{
    struct SundialRecord record;
    struct Date today = Today();

    LoadRecord(&record);
    if (!Sundial_StartDaily(&record, Sundial_DayNumber(today.year, today.month, today.day)))
    {
        gSpecialVar_Result = record.result;
        return;
    }
    StoreRecord(&record);
    DailyUnderdog_SetUpDaily();
    gSpecialVar_Result = SUNDIAL_RESULT_NONE;
}

// Today's opponent in the arena and your six, without touching the record (the
// balance sim calls this directly).
void DailyUnderdog_SetUpDaily(void)
{
    struct Date today = Today();
    const struct SecretWord *special = EventBattle(Sundial_EventForDate(today.year, today.month, today.day));

    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_DAILY);
    // Event days swap in their own opponent and six; natures still come from the date.
    SetArenaOpponent(TodaysSeed(), special != NULL ? special->opponent : Sundial_DailyOpponent(today.year, today.month, today.day));
    GiveTeam(TodaysSeed(), special);
}

// The balance sim's PRACTICE: the date's team with no event team or rule (the sim
// puts the opponent in the arena itself).
void DailyUnderdog_SetUpPractice(void)
{
    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_PRACTICE);
    GiveTeam(TodaysSeed(), NULL);
}

// Rule days (Sundial_RuleForDate): names and what they do, for the PC and the TV.
static const struct
{
    const u8 *name;
    const u8 *what;
    u8 startingStatus;
} sRules[SUNDIAL_RULE_COUNT] =
{
    [SUNDIAL_RULE_ELECTRIC_TERRAIN] = { COMPOUND_STRING("ELECTRIC TERRAIN"), COMPOUND_STRING("Electric moves hit harder and nobody\ncan fall asleep, all battle."), STARTING_STATUS_ELECTRIC_TERRAIN },
    [SUNDIAL_RULE_GRASSY_TERRAIN]   = { COMPOUND_STRING("GRASSY TERRAIN"), COMPOUND_STRING("Grass moves hit harder and everyone\nheals a little each turn, all battle."), STARTING_STATUS_GRASSY_TERRAIN },
    [SUNDIAL_RULE_MISTY_TERRAIN]    = { COMPOUND_STRING("MISTY TERRAIN"), COMPOUND_STRING("Dragon moves are halved and nobody\ngets a status, all battle."), STARTING_STATUS_MISTY_TERRAIN },
    [SUNDIAL_RULE_PSYCHIC_TERRAIN]  = { COMPOUND_STRING("PSYCHIC TERRAIN"), COMPOUND_STRING("Psychic moves hit harder and priority\nmoves fail, all battle."), STARTING_STATUS_PSYCHIC_TERRAIN },
    [SUNDIAL_RULE_TRICK_ROOM]       = { COMPOUND_STRING("TRICK ROOM"), COMPOUND_STRING("The slowest POKéMON move first,\nall battle."), STARTING_STATUS_TRICK_ROOM },
    [SUNDIAL_RULE_INVERSE]          = { COMPOUND_STRING("INVERSE BATTLE"), COMPOUND_STRING("The type chart is flipped: super\neffective becomes not very effective."), 0 },
};

static enum SundialRule TodaysRule(void)
{
    struct Date today = Today();

    return Sundial_RuleForDate(today.year, today.month, today.day);
}

// From DoTrainerBattle, before every trainer battle: clear any rule left over,
// then set today's if this is the daily.
void DailyUnderdog_ApplyBattleRule(void)
{
    enum SundialRule rule;

    ResetStartingStatuses();
    FlagClear(FLAG_DAILY_INVERSE);
    if (VarGet(VAR_UNDERDOG_BATTLE_KIND) != SUNDIAL_BATTLE_DAILY)
        return;
    rule = TodaysRule();
    if (rule == SUNDIAL_RULE_INVERSE)
        FlagSet(FLAG_DAILY_INVERSE);
    else if (rule != SUNDIAL_RULE_NONE)
        SetStartingStatus(sRules[rule].startingStatus);
}

const u8 *DailyUnderdog_RuleName(enum SundialRule rule)
{
    return rule < SUNDIAL_RULE_COUNT ? sRules[rule].name : NULL;
}

// VAR_RESULT TRUE if today has a rule: STR_VAR_2 its name, STR_VAR_3 what it does.
void DailyUnderdog_BufferRule(void)
{
    enum SundialRule rule = TodaysRule();

    gSpecialVar_Result = rule != SUNDIAL_RULE_NONE;
    if (rule == SUNDIAL_RULE_NONE)
        return;
    StringCopy(gStringVar2, sRules[rule].name);
    StringCopy(gStringVar3, sRules[rule].what);
}

// The trophy wall: today's opponent keeps your best stars against them (before
// the party is healed, so the fainted count is still there).
static enum SundialOpponent TodaysOpponent(void);
STATIC_ASSERT(ARRAY_COUNT(((struct BattleFrontier *)0)->wildcardTrophies) >= SUNDIAL_OPP_COUNT, TrophiesFitTheRoster);

static void RecordTrophy(bool32 won)
{
    enum SundialOpponent opponent = TodaysOpponent();
    u8 *best = &gSaveBlock2Ptr->frontier.wildcardTrophies[opponent];
    u32 i, fainted = 0, stars;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) != SPECIES_NONE
         && GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_HP) == 0)
            fainted++;
    }
    stars = Sundial_TrophyStars(won, fainted);
    if (stars > *best)
        *best = stars;
}

u32 DailyUnderdog_TrophyStars(enum SundialOpponent opponent)
{
    return opponent < SUNDIAL_OPP_COUNT ? gSaveBlock2Ptr->frontier.wildcardTrophies[opponent] : 0;
}

// After any arena battle (the script has faded to black). A daily goes on the
// record; a lost one is saved here (resuming in the bedroom), a won one by the
// Hall of Fame. Free Play and PRACTICE get a card but no record, money or save.
void DailyUnderdog_RecordResult(void)
{
    struct SundialRecord record;
    struct Date today = Today();
    bool32 won = (gBattleOutcome == B_OUTCOME_WON);
    u16 kind = VarGet(VAR_UNDERDOG_BATTLE_KIND);

    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_PRACTICE);
    SundialCard_Capture(TRAINER_BATTLE_PARAM.opponentA, won, kind == SUNDIAL_BATTLE_FREE_PLAY ? sSeedWord : NULL,
                        today.year, today.month, today.day);
    if (kind == SUNDIAL_BATTLE_PRACTICE)
        SundialCard_SetPractice();
    if (kind != SUNDIAL_BATTLE_DAILY)
        return;
    LoadRecord(&record);
    Sundial_FinishDaily(&record, won);
    StoreRecord(&record);
    VarSet(VAR_UNDERDOG_LAST_CARD, SundialCard_ShareBits());
    RecordTrophy(won);
    if (won) // the only money in the game; the Hall of Fame saves it
    {
        u32 prize = Sundial_WinPrize(record.winStreak);

        AddMoney(&gSaveBlock1Ptr->money, prize);
        SundialCard_SetPrize(prize);
    }
    if (!won)
    {
        SetContinueGameWarpToBedroomHub();
        SetContinueGameWarpStatus();
        TrySavingData(SAVE_NORMAL);
    }
}

// Each stadium's two sideline Pokémon: the last two objects in its map.json,
// drawing from VAR_OBJ_GFX_ID_1/2 (the bedroom sets its own on the way back in).
struct StadiumMascots
{
    u16 map;
    u16 species[2];
    u8 floating; // bit 0: the first hovers instead of walking in place; bit 1: the second
};

#include "data/wildcard_stadium_mascots.h"

static void SetStadiumMascots(u16 map)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sStadiumMascots); i++)
    {
        if (sStadiumMascots[i].map == map)
        {
            VarSet(VAR_OBJ_GFX_ID_1, GetGraphicsIdForMon(sStadiumMascots[i].species[0], FALSE, FALSE));
            VarSet(VAR_OBJ_GFX_ID_2, GetGraphicsIdForMon(sStadiumMascots[i].species[1], FALSE, FALSE));
            return;
        }
    }
}

// Called on arrival in a stadium: flying and swimming mascots bob up and down.
// A task does it every frame rather than a one-off levitate, because a mascot
// that starts off-screen only spawns once the camera nears it.
static void Task_FloatMascots(u8 taskId)
{
    s16 *data = gTasks[taskId].data;
    u32 count = gMapHeader.events->objectEventCount;
    u32 j;

    data[1]++;
    for (j = 0; j < 2; j++)
    {
        u8 id = GetObjectEventIdByLocalId(count - 1 + j);
        u32 phase = ((data[1] + j * 24) / 6) % 8;

        if ((data[0] >> j & 1) && id < OBJECT_EVENTS_COUNT && gObjectEvents[id].active)
            gSprites[gObjectEvents[id].spriteId].y2 = phase < 4 ? -phase : phase - 8;
    }
}

void DailyUnderdog_FloatMascots(void)
{
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sStadiumMascots); i++)
    {
        if (sStadiumMascots[i].map == map && sStadiumMascots[i].floating && !FuncIsActiveTask(Task_FloatMascots))
            gTasks[CreateTask(Task_FloatMascots, 80)].data[0] = sStadiumMascots[i].floating;
    }
}

// Warps to today's opponent's room. The script waits (waitstate) for the warp.
void DailyUnderdog_WarpToArena(void)
{
    u16 slot = VarGet(VAR_UNDERDOG_ARENA_SLOT);
    u16 map = MAP_UNDERDOG_ARENA_WALLACE;
    u8 x = 6, y = 11;

    if (slot < ARRAY_COUNT(sArenaRooms))
    {
        map = sArenaRooms[slot].map;
        x = sArenaRooms[slot].x;
        y = sArenaRooms[slot].y;
    }
    SetStadiumMascots(map);
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, x, y);
    DoWarp();
    ResetInitialPlayerAvatarState();
}

// A silent save. Writing flash freezes the game for about a second, so scripts
// fade to black first and the pause hides inside the transition.
void DailyUnderdog_Save(void)
{
    TrySavingData(SAVE_NORMAL);
}

// Free Play: a typed word is the seed for both the opponent and the team.

#define KARP(m1, m2, m3, m4) { SPECIES_MAGIKARP, ITEM_NONE, { MOVE_##m1, MOVE_##m2, MOVE_##m3, MOVE_##m4 } }

static const struct SecretWord sSecretWords[] =
{
    {
        .word = COMPOUND_STRING("JONNO"),
        .opponent = SUNDIAL_OPP_RED,
        .team =
        {
            { SPECIES_GRENINJA,   ITEM_GRENINJITE },
            { SPECIES_SNOM,       ITEM_NONE, { MOVE_FAIRY_WIND, MOVE_ICE_BEAM, MOVE_BUG_BUZZ, MOVE_ICY_WIND } },
            { SPECIES_OSHAWOTT,   ITEM_NONE },
            { SPECIES_PIPLUP,     ITEM_NONE },
            { SPECIES_GROOKEY,    ITEM_NONE },
            { SPECIES_CYNDAQUIL,  ITEM_NONE },
        },
    },
    {
        // Six Magikarp, each hiding one answer to Red's six (shuffled).
        .word = COMPOUND_STRING("SPLASH"),
        .opponent = SUNDIAL_OPP_RED,
        .team =
        {
            KARP(SPLASH, THUNDERBOLT, TACKLE, FLAIL),    // Blastoise
            KARP(PSYCHIC, SPLASH, FLAIL, TACKLE),        // Venusaur
            KARP(SPLASH, TACKLE, FLAIL, CRUNCH),         // Espeon
            KARP(TACKLE, SPLASH, STONE_EDGE, FLAIL),     // Charizard
            KARP(FLAIL, CLOSE_COMBAT, SPLASH, TACKLE),   // Snorlax
            KARP(SPLASH, FLAIL, TACKLE, EARTHQUAKE),     // Pikachu
        },
    },
    {
        .word = COMPOUND_STRING("PIKAPIKA"),
        .opponent = SUNDIAL_OPP_LT_SURGE,
        .team =
        {
            { SPECIES_PIKACHU },
            { SPECIES_PLUSLE },
            { SPECIES_EMOLGA },
            { SPECIES_DEDENNE },
            { SPECIES_TOGEDEMARU },
            { SPECIES_MORPEKO },
        },
    },
    {
        // Youngster Joey's top percentage, times six.
        .word = COMPOUND_STRING("JOEY"),
        .opponent = SUNDIAL_OPP_BROCK,
        .team =
        {
            { SPECIES_RATTATA }, { SPECIES_RATTATA }, { SPECIES_RATTATA },
            { SPECIES_RATTATA }, { SPECIES_RATTATA }, { SPECIES_RATTATA },
        },
    },
    {
        // A friend's team, against Blue (Tyranitar and Heracross make him the harder
        // matchup). Smeargle gets a proper Sketch set; it only learns Sketch by level.
        .word = COMPOUND_STRING("FLARGY"),
        .opponent = SUNDIAL_OPP_BLUE,
        .team =
        {
            { SPECIES_SMEARGLE, ITEM_NONE, { MOVE_SPORE, MOVE_SHELL_SMASH, MOVE_BOOMBURST, MOVE_PROTECT } },
            { SPECIES_GOLURK },
            { SPECIES_ROGGENROLA },
            { SPECIES_SABLEYE },
            { SPECIES_NATU },
            { SPECIES_NECROZMA_DUSK_MANE },
        },
    },
    {
        // Red's team by the end of Pokémon Origins; the player gets the word's random six.
        .word = COMPOUND_STRING("ORIGINS"),
        .opponent = SUNDIAL_OPP_RED,
        .arenaSlot = ARENA_SLOT_RED_ORIGINS,
    },
    // Event days (sEventWords). Also typeable in Free Play, for testing.
    {
        .word = COMPOUND_STRING("HALLOWEEN"),
        .opponent = SUNDIAL_OPP_PHOEBE,
        .team =
        {
            { SPECIES_GOURGEIST },
            { SPECIES_MIMIKYU },
            { SPECIES_CHANDELURE },
            { SPECIES_GENGAR },
            { SPECIES_BANETTE },
            { SPECIES_SABLEYE },
        },
    },
    {
        .word = COMPOUND_STRING("CHRISTMAS"),
        .opponent = SUNDIAL_OPP_GLACIA,
        .team =
        {
            { SPECIES_DELIBIRD },
            { SPECIES_STANTLER },
            { SPECIES_ABOMASNOW },
            { SPECIES_CRYOGONAL },
            { SPECIES_ALCREMIE },
            { SPECIES_SNORLAX },
        },
    },
    {
        .word = COMPOUND_STRING("EASTER"),
        .opponent = SUNDIAL_OPP_ERIKA,
        .team =
        {
            { SPECIES_LOPUNNY },
            { SPECIES_TOGEKISS },
            { SPECIES_CHANSEY },
            { SPECIES_EXEGGUTOR },
            { SPECIES_TORCHIC },
            { SPECIES_DIGGERSBY },
        },
    },
};

#undef KARP

static const u8 *const sEventWords[] =
{
    [SUNDIAL_EVENT_EASTER]    = COMPOUND_STRING("EASTER"),
    [SUNDIAL_EVENT_HALLOWEEN] = COMPOUND_STRING("HALLOWEEN"),
    [SUNDIAL_EVENT_CHRISTMAS] = COMPOUND_STRING("CHRISTMAS"),
};

static const struct SecretWord *FindSecretWord(const u8 *typed)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sSecretWords); i++)
    {
        if (Sundial_WordIs(typed, sSecretWords[i].word))
            return &sSecretWords[i];
    }
    return NULL;
}

static const struct SecretWord *EventBattle(enum SundialEvent event)
{
    return event != SUNDIAL_EVENT_NONE ? FindSecretWord(sEventWords[event]) : NULL;
}

// PC -> FREE PLAY: the word entry screen (the script fades out, then waits).
void DailyUnderdog_EnterSeedWord(void)
{
    sSeedWord[0] = EOS;
    DoNamingScreen(NAMING_SCREEN_CODE, sSeedWord, 0, 0, 0, CB2_ReturnToFieldContinueScript);
}

// After the word screen. VAR_RESULT: FALSE if no word was typed.
void DailyUnderdog_StartFreePlay(void)
{
    const struct SecretWord *secret;
    u32 seed;

    gSpecialVar_Result = FALSE;
    if (sSeedWord[0] == EOS)
        return;
    seed = Sundial_WordSeed(sSeedWord);
    secret = FindSecretWord(sSeedWord);
    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_FREE_PLAY);
    SetArenaOpponent(seed, secret != NULL ? secret->opponent : Sundial_FreePlayOpponent(seed));
    if (secret != NULL && secret->arenaSlot != 0)
        VarSet(VAR_UNDERDOG_ARENA_SLOT, secret->arenaSlot);
    if (secret != NULL && secret->team[0].species == SPECIES_NONE)
        secret = NULL; // a word that only picks the opponent
    GiveTeam(seed, secret);
    if (!CheckBagHasItem(ITEM_MEGA_RING, 1)) // no Mega Evolution without it (JONNO)
        AddBagItem(ITEM_MEGA_RING, 1);
    StringCopy(gStringVar1, sSeedWord);
    gSpecialVar_Result = TRUE;
}

// Testing: CHOOSE OPPONENT on the PC lists the whole roster.
static const u8 *const sOpponentNames[SUNDIAL_OPP_COUNT] =
{
    [SUNDIAL_OPP_ROXANNE]       = COMPOUND_STRING("ROXANNE"),
    [SUNDIAL_OPP_BRAWLY]        = COMPOUND_STRING("BRAWLY"),
    [SUNDIAL_OPP_WATTSON]       = COMPOUND_STRING("WATTSON"),
    [SUNDIAL_OPP_FLANNERY]      = COMPOUND_STRING("FLANNERY"),
    [SUNDIAL_OPP_NORMAN]        = COMPOUND_STRING("NORMAN"),
    [SUNDIAL_OPP_WINONA]        = COMPOUND_STRING("WINONA"),
    [SUNDIAL_OPP_TATE_AND_LIZA] = COMPOUND_STRING("TATE & LIZA"),
    [SUNDIAL_OPP_JUAN]          = COMPOUND_STRING("JUAN"),
    [SUNDIAL_OPP_SIDNEY]        = COMPOUND_STRING("SIDNEY"),
    [SUNDIAL_OPP_PHOEBE]        = COMPOUND_STRING("PHOEBE"),
    [SUNDIAL_OPP_GLACIA]        = COMPOUND_STRING("GLACIA"),
    [SUNDIAL_OPP_DRAKE]         = COMPOUND_STRING("DRAKE"),
    [SUNDIAL_OPP_MAXIE]         = COMPOUND_STRING("MAXIE"),
    [SUNDIAL_OPP_ARCHIE]        = COMPOUND_STRING("ARCHIE"),
    [SUNDIAL_OPP_RIVAL]         = COMPOUND_STRING("RIVAL"),
    [SUNDIAL_OPP_WALLACE]       = COMPOUND_STRING("WALLACE"),
    [SUNDIAL_OPP_STEVEN]        = COMPOUND_STRING("STEVEN"),
    [SUNDIAL_OPP_BROCK]         = COMPOUND_STRING("BROCK"),
    [SUNDIAL_OPP_MISTY]         = COMPOUND_STRING("MISTY"),
    [SUNDIAL_OPP_LT_SURGE]      = COMPOUND_STRING("LT. SURGE"),
    [SUNDIAL_OPP_ERIKA]         = COMPOUND_STRING("ERIKA"),
    [SUNDIAL_OPP_KOGA]          = COMPOUND_STRING("KOGA"),
    [SUNDIAL_OPP_SABRINA]       = COMPOUND_STRING("SABRINA"),
    [SUNDIAL_OPP_BLAINE]        = COMPOUND_STRING("BLAINE"),
    [SUNDIAL_OPP_GIOVANNI]      = COMPOUND_STRING("GIOVANNI"),
    [SUNDIAL_OPP_LORELEI]       = COMPOUND_STRING("LORELEI"),
    [SUNDIAL_OPP_BRUNO]         = COMPOUND_STRING("BRUNO"),
    [SUNDIAL_OPP_AGATHA]        = COMPOUND_STRING("AGATHA"),
    [SUNDIAL_OPP_LANCE]         = COMPOUND_STRING("LANCE"),
    [SUNDIAL_OPP_BLUE]          = COMPOUND_STRING("BLUE"),
    [SUNDIAL_OPP_RED]           = COMPOUND_STRING("RED"),
};

// Easy in (DECISIONS "Daily Red and Daily Battle"): coming into the bedroom with
// today's daily unplayed offers it straight away, once per power-on.
static EWRAM_DATA bool8 sOfferedDailyThisBoot = FALSE;

// Today's opponent (an event day's own, else the date's), name in dest.
static enum SundialOpponent TodaysOpponent(void)
{
    struct Date today = Today();
    const struct SecretWord *special = EventBattle(Sundial_EventForDate(today.year, today.month, today.day));

    return special != NULL ? special->opponent : Sundial_DailyOpponent(today.year, today.month, today.day);
}

const u8 *DailyUnderdog_OpponentName(enum SundialOpponent opponent)
{
    if (opponent == SUNDIAL_OPP_RIVAL) // whichever of the two you aren't
        return gSaveBlock2Ptr->playerGender == MALE ? COMPOUND_STRING("MAY") : COMPOUND_STRING("BRENDAN");
    return opponent < SUNDIAL_OPP_COUNT ? sOpponentNames[opponent] : COMPOUND_STRING("???");
}

static enum SundialOpponent BufferTodaysOpponent(u8 *dest)
{
    enum SundialOpponent opponent = TodaysOpponent();

    if (opponent == SUNDIAL_OPP_RIVAL)
        StringCopy(dest, gSaveBlock2Ptr->playerGender == MALE ? COMPOUND_STRING("MAY") : COMPOUND_STRING("BRENDAN"));
    else
        StringCopy(dest, sOpponentNames[opponent]);
    return opponent;
}

// The TV: today's POKéMON WILD CARD broadcast. VAR_RESULT: TV_* below. VAR_0x8005:
// today's event (enum SundialEvent: 0 none, 1 Easter, 2 Halloween, 3 Christmas).
// STR_VAR_1: today's opponent; STR_VAR_2: win streak; STR_VAR_3: time to the next daily.
void DailyUnderdog_BufferTimeToNextDaily(void);

enum
{
    TV_COMING_UP,
    TV_COMING_UP_CHAMPION,
    TV_YOU_WON,
    TV_YOU_LOST,
};

void DailyUnderdog_TVBroadcast(void)
{
    struct SundialRecord record;
    struct Date today = Today();
    enum SundialOpponent opponent = BufferTodaysOpponent(gStringVar1);

    LoadRecord(&record);
    gSpecialVar_0x8005 = Sundial_EventForDate(today.year, today.month, today.day);
    ConvertIntToDecimalStringN(gStringVar2, record.winStreak, STR_CONV_MODE_LEFT_ALIGN, 5);
    DailyUnderdog_BufferTimeToNextDaily();
    if (record.lastDay != Sundial_DayNumber(today.year, today.month, today.day) || record.result == SUNDIAL_RESULT_NONE)
        gSpecialVar_Result = Sundial_OpponentTier(opponent) == SUNDIAL_TIER_CHAMPION ? TV_COMING_UP_CHAMPION : TV_COMING_UP;
    else if (record.result == SUNDIAL_RESULT_WON)
        gSpecialVar_Result = TV_YOU_WON;
    else // lost, or a reset mid-battle (the attempt still counts)
        gSpecialVar_Result = TV_YOU_LOST;
}

// VAR_RESULT: TRUE to offer today's daily. Buffers the opponent's name (STR_VAR_1).
void DailyUnderdog_ShouldOfferDaily(void)
{
    struct SundialRecord record;
    struct Date today = Today();

    gSpecialVar_Result = FALSE;
    LoadRecord(&record);
    if (sOfferedDailyThisBoot || record.lastDay == Sundial_DayNumber(today.year, today.month, today.day))
        return;
    sOfferedDailyThisBoot = TRUE;
    BufferTodaysOpponent(gStringVar1);
    gSpecialVar_Result = TRUE;
}

// "5h 42m" until midnight on the cartridge clock, in STR_VAR_3.
void DailyUnderdog_BufferTimeToNextDaily(void)
{
    struct SiiRtcInfo rtc;
    u32 minutes;
    u8 *end = gStringVar3;

    RtcGetInfo(&rtc);
    minutes = 24 * 60 - (ConvertBcdToBinary(rtc.hour) * 60 + ConvertBcdToBinary(rtc.minute));
    if (minutes >= 60)
    {
        end = ConvertIntToDecimalStringN(end, minutes / 60, STR_CONV_MODE_LEFT_ALIGN, 2);
        end = StringCopy(end, COMPOUND_STRING("h "));
    }
    end = ConvertIntToDecimalStringN(end, minutes % 60, STR_CONV_MODE_LEFT_ALIGN, 2);
    StringCopy(end, COMPOUND_STRING("m"));
}

// Portraits for CHOOSE OPPONENT (DYN_MULTICHOICE_CB_SHOW_TRAINER in script_menu.c).
static const u16 sOpponentPics[SUNDIAL_OPP_COUNT] =
{
    [SUNDIAL_OPP_ROXANNE]       = TRAINER_PIC_LEADER_ROXANNE,
    [SUNDIAL_OPP_BRAWLY]        = TRAINER_PIC_LEADER_BRAWLY,
    [SUNDIAL_OPP_WATTSON]       = TRAINER_PIC_LEADER_WATTSON,
    [SUNDIAL_OPP_FLANNERY]      = TRAINER_PIC_LEADER_FLANNERY,
    [SUNDIAL_OPP_NORMAN]        = TRAINER_PIC_LEADER_NORMAN,
    [SUNDIAL_OPP_WINONA]        = TRAINER_PIC_LEADER_WINONA,
    [SUNDIAL_OPP_TATE_AND_LIZA] = TRAINER_PIC_LEADER_TATE_AND_LIZA,
    [SUNDIAL_OPP_JUAN]          = TRAINER_PIC_LEADER_JUAN,
    [SUNDIAL_OPP_SIDNEY]        = TRAINER_PIC_ELITE_FOUR_SIDNEY,
    [SUNDIAL_OPP_PHOEBE]        = TRAINER_PIC_ELITE_FOUR_PHOEBE,
    [SUNDIAL_OPP_GLACIA]        = TRAINER_PIC_ELITE_FOUR_GLACIA,
    [SUNDIAL_OPP_DRAKE]         = TRAINER_PIC_ELITE_FOUR_DRAKE,
    [SUNDIAL_OPP_MAXIE]         = TRAINER_PIC_MAGMA_LEADER_MAXIE,
    [SUNDIAL_OPP_ARCHIE]        = TRAINER_PIC_AQUA_LEADER_ARCHIE,
    [SUNDIAL_OPP_RIVAL]         = TRAINER_PIC_MAY, // Brendan for a girl player, below
    [SUNDIAL_OPP_WALLACE]       = TRAINER_PIC_CHAMPION_WALLACE,
    [SUNDIAL_OPP_STEVEN]        = TRAINER_PIC_STEVEN,
    [SUNDIAL_OPP_BROCK]         = TRAINER_PIC_LEADER_BROCK_FRLG,
    [SUNDIAL_OPP_MISTY]         = TRAINER_PIC_LEADER_MISTY_FRLG,
    [SUNDIAL_OPP_LT_SURGE]      = TRAINER_PIC_LEADER_LT_SURGE_FRLG,
    [SUNDIAL_OPP_ERIKA]         = TRAINER_PIC_LEADER_ERIKA_FRLG,
    [SUNDIAL_OPP_KOGA]          = TRAINER_PIC_LEADER_KOGA_FRLG,
    [SUNDIAL_OPP_SABRINA]       = TRAINER_PIC_LEADER_SABRINA_FRLG,
    [SUNDIAL_OPP_BLAINE]        = TRAINER_PIC_LEADER_BLAINE_FRLG,
    [SUNDIAL_OPP_GIOVANNI]      = TRAINER_PIC_LEADER_GIOVANNI_FRLG,
    [SUNDIAL_OPP_LORELEI]       = TRAINER_PIC_ELITE_FOUR_LORELEI_FRLG,
    [SUNDIAL_OPP_BRUNO]         = TRAINER_PIC_ELITE_FOUR_BRUNO_FRLG,
    [SUNDIAL_OPP_AGATHA]        = TRAINER_PIC_ELITE_FOUR_AGATHA_FRLG,
    [SUNDIAL_OPP_LANCE]         = TRAINER_PIC_ELITE_FOUR_LANCE_FRLG,
    [SUNDIAL_OPP_BLUE]          = TRAINER_PIC_CHAMPION_RIVAL_FRLG,
    [SUNDIAL_OPP_RED]           = TRAINER_PIC_RED,
};

u16 DailyUnderdog_OpponentTrainerPic(u32 opponent)
{
    if (opponent == SUNDIAL_OPP_RIVAL && gSaveBlock2Ptr->playerGender != MALE)
        return TRAINER_PIC_BRENDAN;
    return sOpponentPics[opponent];
}

void DailyUnderdog_PushOpponentChoices(void)
{
    u32 i;

    for (i = 0; i < SUNDIAL_OPP_COUNT; i++)
    {
        struct ListMenuItem item;
        u8 *name = Alloc(StringLength(sOpponentNames[i]) + 1); // the menu frees item names when it closes

        StringCopy(name, sOpponentNames[i]);
        item.name = name;
        item.id = i;
        MultichoiceDynamic_PushElement(item);
    }
}

// Testing only, remove before launch (STATUS): MORE -> TEST DAY moves PRACTICE onto a
// later day's team, so a playtest can meet several teams in one sitting. Not saved.
static EWRAM_DATA u8 sPracticeDaysAhead = 0;

static struct Date PracticeDate(void)
{
    static const u8 daysInMonth[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    struct Date date = Today();
    u32 i;

    for (i = 0; i < sPracticeDaysAhead; i++)
    {
        u32 length = daysInMonth[date.month - 1] + (date.month == 2 && date.year % 4 == 0);

        if (++date.day > length)
        {
            date.day = 1;
            if (++date.month > 12)
            {
                date.month = 1;
                date.year++;
            }
        }
    }
    return date;
}

// The date whose team this battle uses: PRACTICE follows TEST DAY, everything else is today
// (for the battle log, src/wildcard_sim.c).
void DailyUnderdog_GetTeamDate(u32 *year, u32 *month, u32 *day)
{
    struct Date date = VarGet(VAR_UNDERDOG_BATTLE_KIND) == SUNDIAL_BATTLE_PRACTICE ? PracticeDate() : Today();

    *year = date.year;
    *month = date.month;
    *day = date.day;
}

// STR_VAR_1 the new practice date (day/month).
void DailyUnderdog_NextTestDay(void)
{
    struct Date date;
    u8 *end;

    sPracticeDaysAhead++;
    date = PracticeDate();
    end = ConvertIntToDecimalStringN(gStringVar1, date.day, STR_CONV_MODE_LEFT_ALIGN, 2);
    *end++ = CHAR_SLASH;
    ConvertIntToDecimalStringN(end, date.month, STR_CONV_MODE_LEFT_ALIGN, 2);
}

// VAR_RESULT holds the picked opponent. Today's team (or TEST DAY's), against them instead.
void DailyUnderdog_GiveTeamVsChosenOpponent(void)
{
    struct Date date = PracticeDate();
    u32 seed = Sundial_DateSeed(date.year, date.month, date.day);

    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_PRACTICE);
    SetArenaOpponent(seed, gSpecialVar_Result);
    GiveTeam(seed, NULL);
}

// A win: Hall of Fame screen (which saves), then home. The continue warp makes that
// save resume in the bedroom, not back in the arena for a free second attempt.
void DailyUnderdog_EnterHallOfFame(void)
{
    SetContinueGameWarpToBedroomHub();
    SetContinueGameWarpStatus();
    SetMainCallback2(CB2_DoHallOfFameScreen);
}

// The room: five of your Pokémon lounge around the bedroom (objects 2-6 in its
// map.json, sprites from VAR_OBJ_GFX_ID_1-5, hidden by FLAG_TEMP_11-15 when a
// spot is empty). Each spot's species is a save var.
#define ROOM_SPOTS 5
#define ROOM_FIRST_LOCAL_ID 2 // object 1 is the stairs box

// Decorations stand on three fixed tiles (map.json objects 7-9): a big doll or an
// extra by the bed (7, 4), a doll at (0, 4), a cushion or doll at (1, 3).
enum
{
    DECOR_BY_BED,
    DECOR_CORNER,
    DECOR_BY_TV,
    DECOR_SLOTS,
};
#define DECOR_FIRST_LOCAL_ID 7

static const u16 sRoomVars[ROOM_SPOTS] =
{
    VAR_UNDERDOG_ROOM_1, VAR_UNDERDOG_ROOM_2, VAR_UNDERDOG_ROOM_3, VAR_UNDERDOG_ROOM_4, VAR_UNDERDOG_ROOM_5,
};

static bool32 OwnsSpecies(u16 species)
{
    return species != SPECIES_NONE && GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_CAUGHT);
}

// Sets each spot's sprite and visibility. The bedroom's ON_TRANSITION calls this
// before objects spawn; RefreshRoom respawns them afterwards.
static void SetUpRoomDecor(void);

void DailyUnderdog_SetUpRoom(void)
{
    u32 i;

    for (i = 0; i < ROOM_SPOTS; i++)
    {
        u16 species = VarGet(sRoomVars[i]);

        if (OwnsSpecies(species))
        {
            VarSet(VAR_OBJ_GFX_ID_1 + i, GetGraphicsIdForMon(species, Wildcard_ShowsShiny(species), FALSE));
            FlagClear(FLAG_TEMP_11 + i);
        }
        else
        {
            FlagSet(FLAG_TEMP_11 + i);
        }
    }
    SetUpRoomDecor();
}

static void RefreshRoom(void)
{
    u8 mapNum = gSaveBlock1Ptr->location.mapNum;
    u8 mapGroup = gSaveBlock1Ptr->location.mapGroup;
    u32 i;

    if (mapGroup != MAP_GROUP(MAP_UNDERDOG_BEDROOM) || mapNum != MAP_NUM(MAP_UNDERDOG_BEDROOM))
        return;
    // Remove first: removing sets the spot's hide flag, which SetUpRoom then corrects.
    for (i = 0; i < ROOM_SPOTS; i++)
        RemoveObjectEventByLocalIdAndMap(ROOM_FIRST_LOCAL_ID + i, mapNum, mapGroup);
    for (i = 0; i < DECOR_SLOTS; i++)
        RemoveObjectEventByLocalIdAndMap(DECOR_FIRST_LOCAL_ID + i, mapNum, mapGroup);
    DailyUnderdog_SetUpRoom();
    for (i = 0; i < ROOM_SPOTS; i++)
    {
        if (!FlagGet(FLAG_TEMP_11 + i))
            TrySpawnObjectEvent(ROOM_FIRST_LOCAL_ID + i, mapNum, mapGroup);
    }
    for (i = 0; i < DECOR_SLOTS; i++)
    {
        if (!FlagGet(FLAG_TEMP_16 + i))
            TrySpawnObjectEvent(DECOR_FIRST_LOCAL_ID + i, mapNum, mapGroup);
    }
}

// Makes species the follower. If it was lounging in a spot, the old follower takes that spot.
void DailyUnderdog_MakeFollower(u16 species)
{
    u16 old = VarGet(VAR_UNDERDOG_FOLLOWER);
    u32 i;

    for (i = 0; i < ROOM_SPOTS; i++)
    {
        if (species != SPECIES_NONE && VarGet(sRoomVars[i]) == species)
            VarSet(sRoomVars[i], old);
    }
    VarSet(VAR_UNDERDOG_FOLLOWER, species);
    DailyUnderdog_GiveFollowerParty();
    RefreshRoom();
}

// Puts species in a spot. If it was following you or lounging elsewhere, it swaps places.
void DailyUnderdog_PlaceInRoom(u32 spot, u16 species)
{
    u16 old = VarGet(sRoomVars[spot]);
    u32 i;

    if (species != SPECIES_NONE && VarGet(VAR_UNDERDOG_FOLLOWER) == species)
    {
        VarSet(VAR_UNDERDOG_FOLLOWER, old);
        DailyUnderdog_GiveFollowerParty();
    }
    for (i = 0; i < ROOM_SPOTS; i++)
    {
        if (i != spot && species != SPECIES_NONE && VarGet(sRoomVars[i]) == species)
            VarSet(sRoomVars[i], old);
    }
    VarSet(sRoomVars[spot], species);
    RefreshRoom();
}

// A new purchase: follows you if nobody is, else takes the first empty spot,
// else just joins the collection. Returns where it went (WELCOME_*).
u32 DailyUnderdog_WelcomeNewMon(u16 species)
{
    u32 i;

    if (VarGet(VAR_UNDERDOG_FOLLOWER) == SPECIES_NONE)
    {
        DailyUnderdog_MakeFollower(species);
        return WELCOME_FOLLOWING;
    }
    for (i = 0; i < ROOM_SPOTS; i++)
    {
        if (!OwnsSpecies(VarGet(sRoomVars[i])) || VarGet(sRoomVars[i]) == species)
        {
            DailyUnderdog_PlaceInRoom(i, species);
            return WELCOME_IN_ROOM;
        }
    }
    return WELCOME_COLLECTION;
}

// Talking to a spot's Pokémon. VAR_0x8004: the spot (0-4). Buffers its name and
// leaves the species in VAR_0x8005 for the cry.
void DailyUnderdog_BufferRoomMon(void)
{
    gSpecialVar_0x8005 = VarGet(sRoomVars[gSpecialVar_0x8004]);
    StringCopy(gStringVar1, GetSpeciesName(gSpecialVar_0x8005));
}

// FOLLOW ME: the spot's Pokémon swaps places with your follower.
void DailyUnderdog_RoomMonFollow(void)
{
    DailyUnderdog_MakeFollower(VarGet(sRoomVars[gSpecialVar_0x8004]));
}

// In the bedroom your party is just your buddy, so it's the one following you.
void DailyUnderdog_GiveFollowerParty(void)
{
    u16 species = VarGet(VAR_UNDERDOG_FOLLOWER);

    ZeroPlayerPartyMons();
    if (species != SPECIES_NONE)
    {
        struct PokemonTemplate mon = {0};

        mon.species = species;
        mon.level = TEAM_LEVEL;
        if (Wildcard_ShowsShiny(species)) // a gauntlet reward, unless switched off at the GameCube
        {
            mon.isShiny = SHINY_MODE_ALWAYS;
            mon.doNotUseDefaultShinyness = TRUE;
        }
        mon.nature = NATURE_RANDOM;
        mon.gender = MON_GENDER_RANDOM;
        mon.origin = GIFTMON_ORIGIN;
        for (u32 i = 0; i < NUM_STATS; i++)
            mon.ivs[i] = USE_RANDOM_IVS;
        for (u32 i = 0; i < MAX_MON_MOVES; i++)
            mon.moves[i] = MOVE_DEFAULT;
        ScriptGiveMonParameterized(B_SIDE_PLAYER, PARTY_SIZE, &mon);
    }
    UpdateFollowingPokemon();
}

// Wardrobe costumes. A costume is a full look: overworld sprite, trainer pic (front and
// battle back view in one) and a gender for the game's text. VAR_UNDERDOG_COSTUME holds
// its index; 0 means none, so the vanilla gender look applies (and old saves are unaffected).
struct Costume
{
    const u8 *name;
    u8 gender;
    u16 trainerPic;
    u16 overworldGfx;
    u16 paletteTag;
    u16 price; // 0: everyone has it
};

#define COSTUME_PRICE     3000
#define COSTUME_PRICE_RED 20000 // the trophy costume

// Wardrobe: free looks first, then the ones bought with daily winnings.
static const struct Costume sCostumes[] =
{
    [1]  = { COMPOUND_STRING("BOY 1"),  MALE,   TRAINER_PIC_HILBERT, OBJ_EVENT_GFX_HILBERT,        OBJ_EVENT_PAL_TAG_HILBERT,      0 },
    [2]  = { COMPOUND_STRING("BOY 2"),  MALE,   TRAINER_PIC_BRENDAN, OBJ_EVENT_GFX_BRENDAN_NORMAL, OBJ_EVENT_PAL_TAG_BRENDAN,      0 },
    [3]  = { COMPOUND_STRING("BOY 3"),  MALE,   TRAINER_PIC_ETHAN,   OBJ_EVENT_GFX_ETHAN,          OBJ_EVENT_PAL_TAG_ETHAN,        0 },
    [4]  = { COMPOUND_STRING("GIRL 1"), FEMALE, TRAINER_PIC_MAY,     OBJ_EVENT_GFX_MAY_NORMAL,     OBJ_EVENT_PAL_TAG_MAY,          0 },
    [5]  = { COMPOUND_STRING("GIRL 2"), FEMALE, TRAINER_PIC_LEAF,    OBJ_EVENT_GFX_GREEN_NORMAL,   OBJ_EVENT_PAL_TAG_PLAYER_GREEN, 0 },
    [6]  = { COMPOUND_STRING("GIRL 3"), FEMALE, TRAINER_PIC_SERENA,  OBJ_EVENT_GFX_SERENA,         OBJ_EVENT_PAL_TAG_SERENA,       0 },
    [7]  = { COMPOUND_STRING("BOY 4"),  MALE,   TRAINER_PIC_LUCAS,   OBJ_EVENT_GFX_LUCAS,          OBJ_EVENT_PAL_TAG_LUCAS,        COSTUME_PRICE },
    [8]  = { COMPOUND_STRING("BOY 5"),  MALE,   TRAINER_PIC_CALEM,   OBJ_EVENT_GFX_CALEM,          OBJ_EVENT_PAL_TAG_CALEM,        COSTUME_PRICE },
    [9]  = { COMPOUND_STRING("GIRL 4"), FEMALE, TRAINER_PIC_LYRA,    OBJ_EVENT_GFX_LYRA,           OBJ_EVENT_PAL_TAG_LYRA,         COSTUME_PRICE },
    [10] = { COMPOUND_STRING("GIRL 5"), FEMALE, TRAINER_PIC_KRIS,    OBJ_EVENT_GFX_KRIS,           OBJ_EVENT_PAL_TAG_KRIS,         COSTUME_PRICE },
    [11] = { COMPOUND_STRING("RED"),    MALE,   TRAINER_PIC_RED,     OBJ_EVENT_GFX_RED_NORMAL,     OBJ_EVENT_PAL_TAG_PLAYER_RED,   COSTUME_PRICE_RED },
};

STATIC_ASSERT(ARRAY_COUNT(sCostumes) <= 16, CostumesFitTheOwnedBitfield);

static bool32 IsCostumeOwned(u32 id)
{
    return sCostumes[id].price == 0 || (VarGet(VAR_UNDERDOG_COSTUMES_OWNED) & (1 << id));
}

// The wardrobe's preview (DYN_MULTICHOICE_CB_SHOW_COSTUME); nothing for CHANGE NAME.
u16 DailyUnderdog_WardrobePreviewPic(u32 id)
{
    if (id == 0 || id >= ARRAY_COUNT(sCostumes))
        return TRAINER_PIC_NONE;
    return sCostumes[id].trainerPic;
}

static const struct Costume *GetCostume(void)
{
    u16 id = VarGet(VAR_UNDERDOG_COSTUME);

    if (id == 0 || id >= ARRAY_COUNT(sCostumes))
        return NULL;
    return &sCostumes[id];
}

u16 DailyUnderdog_CostumeTrainerPic(u16 fallback)
{
    const struct Costume *costume = GetCostume();
    return costume ? costume->trainerPic : fallback;
}

// Only the walking/running sprite is costumed; bikes, surfing etc. never happen here.
u16 DailyUnderdog_CostumeOverworldGfx(u8 avatarState, u16 fallback)
{
    const struct Costume *costume = GetCostume();
    return (costume && avatarState == PLAYER_AVATAR_STATE_NORMAL) ? costume->overworldGfx : fallback;
}

u16 DailyUnderdog_CostumePaletteTag(u16 fallback)
{
    const struct Costume *costume = GetCostume();
    return costume ? costume->paletteTag : fallback;
}

// Unowned costumes show their price; freeOnly lists just the ones everyone has.
static void PushCostumes(bool32 freeOnly)
{
    u32 i;

    for (i = 1; i < ARRAY_COUNT(sCostumes); i++)
    {
        struct ListMenuItem item;
        u8 *name;
        u8 *end;

        if (freeOnly && sCostumes[i].price != 0)
            continue;
        name = Alloc(20); // the menu frees item names when it closes
        end = StringCopy(name, sCostumes[i].name);

        if (!IsCostumeOwned(i))
        {
            *end++ = CHAR_SPACE;
            *end++ = CHAR_CURRENCY;
            ConvertIntToDecimalStringN(end, sCostumes[i].price, STR_CONV_MODE_LEFT_ALIGN, 5);
        }
        item.name = name;
        item.id = i;
        MultichoiceDynamic_PushElement(item);
    }
}

void DailyUnderdog_PushCostumeChoices(void)
{
    PushCostumes(FALSE);
}

// First boot: pick a look from the free ones.
void DailyUnderdog_PushFreeCostumes(void)
{
    PushCostumes(TRUE);
}

// VAR_0x8004 holds a costume index. VAR_RESULT: TRUE if owned. Buffers its name
// (STR_VAR_1) and price (STR_VAR_2) for the buy prompt.
void DailyUnderdog_CheckCostume(void)
{
    u32 id = gSpecialVar_0x8004;

    gSpecialVar_Result = IsCostumeOwned(id);
    StringCopy(gStringVar1, sCostumes[id].name);
    ConvertIntToDecimalStringN(gStringVar2, sCostumes[id].price, STR_CONV_MODE_LEFT_ALIGN, 5);
}

// VAR_0x8004 holds a costume index. VAR_RESULT: TRUE if bought.
void DailyUnderdog_BuyCostume(void)
{
    u32 id = gSpecialVar_0x8004;

    gSpecialVar_Result = FALSE;
    if (!IsEnoughMoney(&gSaveBlock1Ptr->money, sCostumes[id].price))
        return;
    RemoveMoney(&gSaveBlock1Ptr->money, sCostumes[id].price);
    VarSet(VAR_UNDERDOG_COSTUMES_OWNED, VarGet(VAR_UNDERDOG_COSTUMES_OWNED) | (1 << id));
    gSpecialVar_Result = TRUE;
}

// VAR_RESULT holds the costume index. Swaps the player's sprite on the spot.
void DailyUnderdog_SetCostume(void)
{
    if (gSpecialVar_Result == 0 || gSpecialVar_Result >= ARRAY_COUNT(sCostumes) || !IsCostumeOwned(gSpecialVar_Result))
        return;
    VarSet(VAR_UNDERDOG_COSTUME, gSpecialVar_Result);
    gSaveBlock2Ptr->playerGender = sCostumes[gSpecialVar_Result].gender;
    gPlayerAvatar.gender = sCostumes[gSpecialVar_Result].gender;
    ObjectEventSetGraphicsId(&gObjectEvents[gPlayerAvatar.objectEventId],
                             GetPlayerAvatarGraphicsIdByStateIdAndGender(PLAYER_AVATAR_STATE_NORMAL, gPlayerAvatar.gender));
}

// Room colours: palette swaps of the bedroom's floor, wall and rug (DECISIONS
// "Bedroom layout B, room colours sold in the shop"). The TV stand and the
// headboard share some of those colours, so they change too. Halloween and
// Christmas aren't sold: they take over the room on their event days.
#define ROOM_PRICE      2000
#define ROOM_EVENT_ONLY 0xFFFF

enum
{
    ROOM_HONEY,
    ROOM_WALNUT,
    ROOM_OCEAN,
    ROOM_NIGHT,
    ROOM_HALLOWEEN,
    ROOM_CHRISTMAS,
    // Themed rooms (DECISIONS 2026-10-20): colours plus Emerald's dolls and cushions
    ROOM_COSY_ATTIC,
    ROOM_GAMER_DEN,
    ROOM_SNOW_LODGE,
    ROOM_SEASIDE,
    ROOM_FOREST_NOOK,
    ROOM_CHAMPION,
    ROOM_STARGAZER,
    ROOM_JOHTO,
    ROOM_AQUARIUM,
    ROOM_GARDEN,
    ROOM_MAGMA_DEN,
    ROOM_SKY_LOFT,
    ROOM_THEME_COUNT,
};


struct RoomTheme
{
    const u8 *name;
    u16 price; // 0: everyone has it
    u16 floor[4]; // darkest first
    u16 wall[2];  // 0: the tileset's own
    u16 rug[3];
    u16 decor[DECOR_SLOTS]; // object graphics; 0: nothing there
};

#define ROOM_THEMED_PRICE   3000
#define ROOM_CHAMPION_PRICE 5000

static const struct RoomTheme sRoomThemes[ROOM_THEME_COUNT] =
{
    [ROOM_HONEY] = { COMPOUND_STRING("HONEY"), 0 }, // the tileset's own colours
    [ROOM_WALNUT] = { COMPOUND_STRING("WALNUT"), ROOM_PRICE,
        { RGB(11, 7, 4), RGB(14, 9, 5), RGB(17, 12, 7), RGB(20, 14, 8) },
        { RGB(18, 21, 17), RGB(23, 25, 21) },
        { RGB(18, 5, 5), RGB(24, 8, 8), RGB(29, 15, 13) } },
    [ROOM_OCEAN] = { COMPOUND_STRING("OCEAN"), ROOM_PRICE,
        { RGB(18, 17, 15), RGB(22, 21, 18), RGB(25, 24, 22), RGB(28, 27, 25) },
        { RGB(16, 22, 28), RGB(22, 27, 30) },
        { RGB(3, 6, 13), RGB(6, 10, 19), RGB(12, 16, 25) } },
    [ROOM_NIGHT] = { COMPOUND_STRING("NIGHT"), ROOM_PRICE,
        { RGB(8, 5, 4), RGB(12, 7, 5), RGB(15, 10, 6), RGB(17, 12, 8) },
        { RGB(6, 7, 13), RGB(9, 11, 17) },
        { RGB(22, 16, 3), RGB(27, 21, 6), RGB(30, 26, 13) } },
    [ROOM_HALLOWEEN] = { COMPOUND_STRING("HALLOWEEN"), ROOM_EVENT_ONLY,
        { RGB(4, 3, 5), RGB(6, 5, 7), RGB(9, 7, 10), RGB(11, 9, 12) },
        { RGB(10, 6, 15), RGB(15, 10, 20) },
        { RGB(24, 11, 2), RGB(30, 16, 3), RGB(31, 23, 10) } },
    [ROOM_CHRISTMAS] = { COMPOUND_STRING("CHRISTMAS"), ROOM_EVENT_ONLY,
        { RGB(10, 7, 4), RGB(13, 9, 6), RGB(17, 12, 8), RGB(19, 14, 10) },
        { RGB(20, 5, 5), RGB(25, 8, 8) },
        { RGB(3, 12, 6), RGB(6, 17, 8), RGB(13, 23, 15) } },
    // Generated from wildcard/art/rooms/og_rooms.py (its ROOMS table); keep the two in step.
    [ROOM_COSY_ATTIC] = { COMPOUND_STRING("COSY ATTIC"), ROOM_THEMED_PRICE,
        { RGB(26, 18, 10), RGB(21, 14, 8), RGB(28, 21, 13), RGB(24, 17, 10) }, { 0 },
        { RGB(24, 11, 9), RGB(29, 15, 12), RGB(31, 24, 16) },
        { 0, OBJ_EVENT_GFX_PIKACHU_DOLL, OBJ_EVENT_GFX_ROUND_CUSHION } },
    [ROOM_GAMER_DEN] = { COMPOUND_STRING("GAMER DEN"), ROOM_THEMED_PRICE,
        { RGB(5, 4, 9), RGB(8, 6, 12), RGB(10, 8, 15), RGB(12, 10, 17) }, { RGB(9, 8, 16), RGB(12, 11, 20) },
        { RGB(20, 4, 4), RGB(26, 8, 8), RGB(30, 28, 28) },
        { OBJ_EVENT_GFX_BALL_CUSHION, OBJ_EVENT_GFX_UNUSED_PORYGON2_DOLL, OBJ_EVENT_GFX_SPIN_CUSHION } },
    [ROOM_SNOW_LODGE] = { COMPOUND_STRING("SNOW LODGE"), ROOM_THEMED_PRICE,
        { RGB(11, 7, 4), RGB(14, 9, 5), RGB(17, 12, 7), RGB(20, 14, 8) }, { RGB(19, 15, 11), RGB(23, 19, 14) },
        { RGB(18, 4, 4), RGB(24, 7, 7), RGB(29, 14, 12) },
        { OBJ_EVENT_GFX_BIG_SNORLAX_DOLL, 0, OBJ_EVENT_GFX_FIRE_CUSHION } },
    [ROOM_SEASIDE] = { COMPOUND_STRING("SEASIDE"), ROOM_THEMED_PRICE,
        { RGB(24, 21, 15), RGB(27, 24, 18), RGB(29, 27, 21), RGB(30, 28, 23) }, { RGB(20, 26, 30), RGB(25, 29, 31) },
        { RGB(4, 14, 22), RGB(8, 19, 27), RGB(17, 26, 30) },
        { OBJ_EVENT_GFX_BIG_WAILMER_DOLL, OBJ_EVENT_GFX_MUDKIP_DOLL, OBJ_EVENT_GFX_WATER_CUSHION } },
    [ROOM_FOREST_NOOK] = { COMPOUND_STRING("FOREST NOOK"), ROOM_THEMED_PRICE,
        { RGB(16, 11, 6), RGB(20, 14, 8), RGB(23, 17, 10), RGB(26, 20, 12) }, { RGB(17, 23, 14), RGB(22, 27, 18) },
        { RGB(8, 16, 6), RGB(12, 21, 9), RGB(20, 27, 14) },
        { 0, OBJ_EVENT_GFX_TREECKO_DOLL, OBJ_EVENT_GFX_GRASS_CUSHION } },
    [ROOM_CHAMPION] = { COMPOUND_STRING("CHAMPION"), ROOM_CHAMPION_PRICE,
        { RGB(22, 20, 17), RGB(25, 23, 20), RGB(28, 27, 24), RGB(30, 29, 27) }, { RGB(29, 26, 18), RGB(31, 29, 22) },
        { RGB(16, 3, 4), RGB(22, 5, 6), RGB(29, 23, 8) },
        { OBJ_EVENT_GFX_BIG_RHYDON_DOLL, 0, OBJ_EVENT_GFX_DIAMOND_CUSHION } },
    [ROOM_STARGAZER] = { COMPOUND_STRING("STARGAZER"), ROOM_THEMED_PRICE,
        { RGB(12, 13, 15), RGB(15, 16, 18), RGB(18, 19, 21), RGB(21, 22, 24) }, { RGB(5, 6, 13), RGB(8, 9, 17) },
        { RGB(4, 6, 12), RGB(7, 9, 17), RGB(24, 26, 8) },
        { OBJ_EVENT_GFX_ZIGZAG_CUSHION, OBJ_EVENT_GFX_CLEFAIRY_DOLL, OBJ_EVENT_GFX_SWABLU_DOLL } },
    [ROOM_JOHTO] = { COMPOUND_STRING("JOHTO ROOM"), ROOM_THEMED_PRICE,
        { RGB(20, 19, 10), RGB(23, 22, 12), RGB(25, 24, 15), RGB(27, 26, 17) }, { RGB(29, 28, 25), RGB(31, 30, 27) },
        { RGB(4, 7, 16), RGB(7, 11, 21), RGB(14, 18, 26) },
        { OBJ_EVENT_GFX_TOTODILE_DOLL, OBJ_EVENT_GFX_CYNDAQUIL_DOLL, OBJ_EVENT_GFX_CHIKORITA_DOLL } },
    [ROOM_AQUARIUM] = { COMPOUND_STRING("AQUARIUM"), ROOM_THEMED_PRICE,
        { RGB(9, 13, 20), RGB(11, 15, 22), RGB(13, 18, 25), RGB(15, 20, 27) }, { RGB(14, 21, 28), RGB(19, 25, 30) },
        { RGB(4, 15, 20), RGB(8, 20, 25), RGB(18, 27, 30) },
        { OBJ_EVENT_GFX_BIG_LAPRAS_DOLL, OBJ_EVENT_GFX_MARILL_DOLL, OBJ_EVENT_GFX_LOTAD_DOLL } },
    [ROOM_GARDEN] = { COMPOUND_STRING("GARDEN ROOM"), ROOM_THEMED_PRICE,
        { RGB(20, 12, 8), RGB(24, 15, 10), RGB(27, 18, 12), RGB(29, 21, 15) }, { RGB(22, 28, 22), RGB(26, 30, 26) },
        { RGB(8, 18, 8), RGB(12, 23, 11), RGB(22, 28, 16) },
        { 0, OBJ_EVENT_GFX_SEEDOT_DOLL, OBJ_EVENT_GFX_GRASS_CUSHION } },
    [ROOM_MAGMA_DEN] = { COMPOUND_STRING("MAGMA DEN"), ROOM_THEMED_PRICE,
        { RGB(6, 4, 4), RGB(8, 6, 6), RGB(10, 8, 8), RGB(12, 9, 9) }, { RGB(14, 5, 4), RGB(18, 8, 6) },
        { RGB(18, 6, 2), RGB(25, 10, 3), RGB(30, 20, 6) },
        { OBJ_EVENT_GFX_BIG_REGIROCK_DOLL, OBJ_EVENT_GFX_TORCHIC_DOLL, OBJ_EVENT_GFX_FIRE_CUSHION } },
    [ROOM_SKY_LOFT] = { COMPOUND_STRING("SKY LOFT"), ROOM_THEMED_PRICE,
        { RGB(25, 25, 27), RGB(27, 27, 29), RGB(29, 29, 30), RGB(31, 31, 31) }, { RGB(22, 27, 31), RGB(26, 29, 31) },
        { RGB(22, 18, 6), RGB(27, 23, 10), RGB(30, 28, 18) },
        { OBJ_EVENT_GFX_KISS_CUSHION, OBJ_EVENT_GFX_SWABLU_DOLL, OBJ_EVENT_GFX_TOGEPI_DOLL } },
};

// Each room's window view and its potted plants (wildcard/art/rooms/build_bedroom.py
// draws both; og_rooms.py is the mockup).
#define PLANT_BY_BED_CORNER (1 << 0) // (0, 6)
#define PLANT_BY_STAIRS     (1 << 1) // (8, 3)

static const u8 sRoomWindows[ROOM_THEME_COUNT][2] =
{
    [ROOM_HONEY]       = { WINDOW_VIEW_SKY, 0 },
    [ROOM_WALNUT]      = { WINDOW_VIEW_SKY, 0 },
    [ROOM_OCEAN]       = { WINDOW_VIEW_SEA, 0 },
    [ROOM_NIGHT]       = { WINDOW_VIEW_STARS, 0 },
    [ROOM_HALLOWEEN]   = { WINDOW_VIEW_STARS, 0 },
    [ROOM_CHRISTMAS]   = { WINDOW_VIEW_SNOW, 0 },
    [ROOM_COSY_ATTIC]  = { WINDOW_VIEW_POSTER, PLANT_BY_BED_CORNER },
    [ROOM_GAMER_DEN]   = { WINDOW_VIEW_STARS, 0 },
    [ROOM_SNOW_LODGE]  = { WINDOW_VIEW_SNOW, PLANT_BY_BED_CORNER },
    [ROOM_SEASIDE]     = { WINDOW_VIEW_SEA, PLANT_BY_BED_CORNER },
    [ROOM_FOREST_NOOK] = { WINDOW_VIEW_LEAVES, PLANT_BY_BED_CORNER | PLANT_BY_STAIRS },
    [ROOM_CHAMPION]    = { WINDOW_VIEW_CITY, PLANT_BY_BED_CORNER },
    [ROOM_STARGAZER]   = { WINDOW_VIEW_STARS, 0 },
    [ROOM_JOHTO]       = { WINDOW_VIEW_BLOSSOM, PLANT_BY_BED_CORNER },
    [ROOM_AQUARIUM]    = { WINDOW_VIEW_FISH, 0 },
    [ROOM_GARDEN]      = { WINDOW_VIEW_SKY, PLANT_BY_BED_CORNER | PLANT_BY_STAIRS },
    [ROOM_MAGMA_DEN]   = { WINDOW_VIEW_LAVA, 0 },
    [ROOM_SKY_LOFT]    = { WINDOW_VIEW_SKY, 0 },
};

// Owned: the first 16 in VAR_UNDERDOG_ROOMS_OWNED, the rest in the save's spare frontier space.
STATIC_ASSERT(ROOM_THEME_COUNT <= 16 + 8 * sizeof(gSaveBlock2Ptr->frontier.wildcardRoomsOwned), RoomThemesFitTheOwnedBitfields);

// Where those colours live in the bedroom's palettes (BG palettes 6 and 9 share
// the floor and wall shades; the rug is only in 6).
#define ROOM_PAL_MAIN  6
#define ROOM_PAL_TRIM  9
static const u8 sFloorSlots[4] = {7, 8, 5, 6};
static const u8 sWallSlots[2] = {3, 9};
static const u8 sRugSlots[3] = {10, 11, 12};

static bool32 IsRoomThemeOwned(u32 id)
{
    if (sRoomThemes[id].price == 0)
        return TRUE;
    if (id < 16)
        return (VarGet(VAR_UNDERDOG_ROOMS_OWNED) >> id) & 1;
    id -= 16;
    return (gSaveBlock2Ptr->frontier.wildcardRoomsOwned[id / 8] >> (id % 8)) & 1;
}

static void SetRoomThemeOwned(u32 id)
{
    if (id < 16)
    {
        VarSet(VAR_UNDERDOG_ROOMS_OWNED, VarGet(VAR_UNDERDOG_ROOMS_OWNED) | (1 << id));
        return;
    }
    id -= 16;
    gSaveBlock2Ptr->frontier.wildcardRoomsOwned[id / 8] |= 1 << (id % 8);
}

static u32 CurrentRoomTheme(void)
{
    struct Date today = Today();
    u32 id = VarGet(VAR_UNDERDOG_ROOM_THEME);

    switch (Sundial_EventForDate(today.year, today.month, today.day))
    {
    case SUNDIAL_EVENT_HALLOWEEN:
        return ROOM_HALLOWEEN;
    case SUNDIAL_EVENT_CHRISTMAS:
        return ROOM_CHRISTMAS;
    default:
        return (id < ROOM_THEME_COUNT && IsRoomThemeOwned(id)) ? id : ROOM_HONEY;
    }
}

// Called by fieldmap.c straight after the bedroom's palettes load.
void DailyUnderdog_ApplyRoomTheme(bool32 skipFaded)
{
    const struct RoomTheme *theme = &sRoomThemes[CurrentRoomTheme()];
    u32 i;

    WildcardBedroom_LoadWindowPalette(skipFaded);
    if (theme->floor[0] == 0)
        return;
    for (i = 0; i < ARRAY_COUNT(sFloorSlots); i++)
    {
        gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_MAIN) + sFloorSlots[i]] = theme->floor[i];
        gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_TRIM) + sFloorSlots[i]] = theme->floor[i];
    }
    for (i = 0; i < ARRAY_COUNT(sWallSlots) && theme->wall[0] != 0; i++)
    {
        gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_MAIN) + sWallSlots[i]] = theme->wall[i];
        gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_TRIM) + sWallSlots[i]] = theme->wall[i];
    }
    for (i = 0; i < ARRAY_COUNT(sRugSlots); i++)
        gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_MAIN) + sRugSlots[i]] = theme->rug[i];
    if (!skipFaded)
    {
        CpuCopy16(&gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_MAIN)], &gPlttBufferFaded[BG_PLTT_ID(ROOM_PAL_MAIN)], PLTT_SIZE_4BPP);
        CpuCopy16(&gPlttBufferUnfaded[BG_PLTT_ID(ROOM_PAL_TRIM)], &gPlttBufferFaded[BG_PLTT_ID(ROOM_PAL_TRIM)], PLTT_SIZE_4BPP);
    }
}

// For the window's animation (src/tileset_anims.c).
u32 DailyUnderdog_RoomWindowView(void)
{
    return sRoomWindows[CurrentRoomTheme()][0];
}

static void SetPlant(u32 x, u32 y, bool32 on, u16 plantTop, u16 plantBottom, u16 floorTop, u16 floorBottom)
{
    MapGridSetMetatileIdAt(x + MAP_OFFSET, y + MAP_OFFSET, on ? (plantTop | MAPGRID_IMPASSABLE) : floorTop);
    MapGridSetMetatileIdAt(x + MAP_OFFSET, y + 1 + MAP_OFFSET, on ? (plantBottom | MAPGRID_IMPASSABLE) : floorBottom);
}

// The theme's dolls and cushions: objects 7-9 draw from VAR_OBJ_GFX_ID_6-8 and
// hide behind FLAG_TEMP_16-18 when the slot is empty. Called from SetUpRoom.
static void SetUpRoomDecor(void)
{
    const struct RoomTheme *theme = &sRoomThemes[CurrentRoomTheme()];
    u32 plants = sRoomWindows[CurrentRoomTheme()][1];
    u32 i;

    // Plants are map tiles: only the ON_LOAD call (after the map grid exists) sticks.
    SetPlant(BEDROOM_PLANT_A_X, BEDROOM_PLANT_A_Y, plants & PLANT_BY_BED_CORNER,
             METATILE_BEDROOM_PLANT_A0, METATILE_BEDROOM_PLANT_A1, METATILE_BEDROOM_FLOOR_A0, METATILE_BEDROOM_FLOOR_A1);
    SetPlant(BEDROOM_PLANT_B_X, BEDROOM_PLANT_B_Y, plants & PLANT_BY_STAIRS,
             METATILE_BEDROOM_PLANT_B0, METATILE_BEDROOM_PLANT_B1, METATILE_BEDROOM_FLOOR_B0, METATILE_BEDROOM_FLOOR_B1);

    for (i = 0; i < DECOR_SLOTS; i++)
    {
        if (theme->decor[i] != 0)
        {
            VarSet(VAR_OBJ_GFX_ID_6 + i, theme->decor[i]);
            FlagClear(FLAG_TEMP_16 + i);
        }
        else
        {
            FlagSet(FLAG_TEMP_16 + i);
        }
    }
}

// PC -> DECORATE. Unowned colours show their price; event rooms aren't listed.
void DailyUnderdog_PushRoomThemes(void)
{
    u32 i;

    for (i = 0; i < ROOM_THEME_COUNT; i++)
    {
        struct ListMenuItem item;
        u8 *name;
        u8 *end;

        if (sRoomThemes[i].price == ROOM_EVENT_ONLY)
            continue;
        name = Alloc(20); // the menu frees item names when it closes
        end = StringCopy(name, sRoomThemes[i].name);
        if (!IsRoomThemeOwned(i))
        {
            *end++ = CHAR_SPACE;
            *end++ = CHAR_CURRENCY;
            ConvertIntToDecimalStringN(end, sRoomThemes[i].price, STR_CONV_MODE_LEFT_ALIGN, 5);
        }
        item.name = name;
        item.id = i;
        MultichoiceDynamic_PushElement(item);
    }
}

// VAR_0x8004 holds a room colour. VAR_RESULT: TRUE if owned. Buffers its name
// (STR_VAR_1) and price (STR_VAR_2) for the buy prompt.
void DailyUnderdog_CheckRoomTheme(void)
{
    u32 id = gSpecialVar_0x8004;

    gSpecialVar_Result = IsRoomThemeOwned(id);
    StringCopy(gStringVar1, sRoomThemes[id].name);
    ConvertIntToDecimalStringN(gStringVar2, sRoomThemes[id].price, STR_CONV_MODE_LEFT_ALIGN, 5);
}

// VAR_0x8004 holds a room colour. VAR_RESULT: TRUE if bought.
void DailyUnderdog_BuyRoomTheme(void)
{
    u32 id = gSpecialVar_0x8004;

    gSpecialVar_Result = FALSE;
    if (!IsEnoughMoney(&gSaveBlock1Ptr->money, sRoomThemes[id].price))
        return;
    RemoveMoney(&gSaveBlock1Ptr->money, sRoomThemes[id].price);
    SetRoomThemeOwned(id);
    gSpecialVar_Result = TRUE;
}

// VAR_0x8004 holds a room colour. The script fades to black around this.
void DailyUnderdog_SetRoomTheme(void)
{
    if (gSpecialVar_0x8004 >= ROOM_THEME_COUNT || !IsRoomThemeOwned(gSpecialVar_0x8004))
        return;
    VarSet(VAR_UNDERDOG_ROOM_THEME, gSpecialVar_0x8004);
    LoadSecondaryTilesetPalette(gMapHeader.mapLayout, TRUE);
    RefreshRoom(); // the theme's dolls, cushions and plants
    DrawWholeMapView();
}

// Wardrobe. Same as the debug menu's rename; the script waits and carries on afterwards.
void DailyUnderdog_RenamePlayer(void)
{
    DoNamingScreen(NAMING_SCREEN_PLAYER, gSaveBlock2Ptr->playerName, gSaveBlock2Ptr->playerGender, 0, 0, CB2_ReturnToFieldContinueScript);
}
