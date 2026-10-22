#include "global.h"
#include "battle.h"
#include "battle_setup.h"
#include "daily_underdog.h"
#include "event_data.h"
#include "load_save.h"
#include "overworld.h"
#include "save.h"
#include "pokedex.h"
#include "pokemon.h"
#include "script_pokemon_util.h"
#include "string_util.h"
#include "sundial_card.h"
#include "sundial_gauntlet.h"
#include "sundial_record.h"
#include "wildcard_gauntlet.h"
#include "constants/battle_frontier.h"
#include "constants/items.h"
#include "constants/sundial.h"

// The gauntlet's game side (the rules are in sundial_gauntlet.c; DECISIONS
// 2026-10-15/19). A run lives in the party (your three) and VAR_GAUNTLET_ROUND;
// the week it belongs to is VAR_GAUNTLET_WEEK, so a run that crosses midnight on
// Sunday keeps its opponents.

#define COSTUME_RED 11 // sCostumes in src/daily_underdog.c

// The round the last run ended in, for the reward check after the battle.
EWRAM_DATA static u16 sLastRunRound = 0;

static u32 ThisWeek(void)
{
    return Gauntlet_WeekNumber(DailyUnderdog_TodayNumber());
}

static u32 RunSeed(void)
{
    return Gauntlet_WeekSeed(VarGet(VAR_GAUNTLET_WEEK));
}

static u32 BestThisWeek(void)
{
    return VarGet(VAR_GAUNTLET_WEEK) == ThisWeek() ? VarGet(VAR_GAUNTLET_BEST) : 0;
}

// Weeks counted from launch week, like the daily's card number.
static u32 WeekSinceLaunch(u32 week)
{
    return week - Gauntlet_WeekNumber(Sundial_DayNumber(LAUNCH_YEAR, LAUNCH_MONTH, LAUNCH_DAY)) + 1;
}

static void NoteRoundReached(u32 round)
{
    if (round > VarGet(VAR_GAUNTLET_BEST))
        VarSet(VAR_GAUNTLET_BEST, round);
    if (round > VarGet(VAR_GAUNTLET_RECORD))
        VarSet(VAR_GAUNTLET_RECORD, round);
}

static const u8 *const sOpponentNames[SUNDIAL_OPP_COUNT] =
{
    [SUNDIAL_OPP_BROCK]    = COMPOUND_STRING("BROCK"),
    [SUNDIAL_OPP_MISTY]    = COMPOUND_STRING("MISTY"),
    [SUNDIAL_OPP_LT_SURGE] = COMPOUND_STRING("LT. SURGE"),
    [SUNDIAL_OPP_ERIKA]    = COMPOUND_STRING("ERIKA"),
    [SUNDIAL_OPP_KOGA]     = COMPOUND_STRING("KOGA"),
    [SUNDIAL_OPP_SABRINA]  = COMPOUND_STRING("SABRINA"),
    [SUNDIAL_OPP_BLAINE]   = COMPOUND_STRING("BLAINE"),
    [SUNDIAL_OPP_LORELEI]  = COMPOUND_STRING("LORELEI"),
    [SUNDIAL_OPP_BRUNO]    = COMPOUND_STRING("BRUNO"),
    [SUNDIAL_OPP_AGATHA]   = COMPOUND_STRING("AGATHA"),
    [SUNDIAL_OPP_LANCE]    = COMPOUND_STRING("LANCE"),
    [SUNDIAL_OPP_RED]      = COMPOUND_STRING("RED"),
};

static void BufferOpponent(u8 *dest, u32 round)
{
    const u8 *name = sOpponentNames[Gauntlet_Opponent(RunSeed(), round)];

    StringCopy(dest, name != NULL ? name : COMPOUND_STRING("???"));
}

// A Pokémon at the game's level with perfect IVs and the best-four moves.
// Effort goes into its better attacking stat and Speed.
static void GiveMon(const struct SundialMon *m, u8 side, u8 slot, u32 effort, u16 item)
{
    struct PokemonTemplate mon = {0};
    const struct SpeciesInfo *info = &gSpeciesInfo[m->species];
    u32 i;

    mon.species = m->species;
    mon.level = SUNDIAL_LEVEL;
    mon.nature = m->nature;
    mon.abilityNum = m->abilityNum;
    mon.doNotUseDefaultAbility = TRUE;
    mon.gender = MON_GENDER_RANDOM;
    mon.origin = GIFTMON_ORIGIN;
    mon.heldItem = item;
    for (i = 0; i < NUM_STATS; i++)
        mon.ivs[i] = MAX_PER_STAT_IVS;
    mon.evs[info->baseAttack >= info->baseSpAttack ? STAT_ATK : STAT_SPATK] = effort;
    mon.evs[STAT_SPEED] = effort;
    Sundial_PickMoves(mon.species, mon.moves);
    ScriptGiveMonParameterized(side, slot, &mon);
}

// PC -> GAUNTLET. STR_VAR_1 the week, STR_VAR_2 this week's best round, STR_VAR_3
// the best ever. VAR_RESULT TRUE if there's a best this week to show.
void Gauntlet_Status(void)
{
    VarSet(VAR_GAUNTLET_ROUND, 0); // at the PC, any earlier run was abandoned (a reset mid-run)
    ConvertIntToDecimalStringN(gStringVar1, WeekSinceLaunch(ThisWeek()), STR_CONV_MODE_LEFT_ALIGN, 4);
    ConvertIntToDecimalStringN(gStringVar2, BestThisWeek(), STR_CONV_MODE_LEFT_ALIGN, 3);
    ConvertIntToDecimalStringN(gStringVar3, VarGet(VAR_GAUNTLET_RECORD), STR_CONV_MODE_LEFT_ALIGN, 3);
    gSpecialVar_Result = BestThisWeek() > 0;
}

// Starts a run: this week's six to draft from, in the party.
void Gauntlet_StartRun(void)
{
    struct SundialMon draft[GAUNTLET_DRAFT_SIZE];
    u32 i;

    if (VarGet(VAR_GAUNTLET_WEEK) != ThisWeek())
    {
        VarSet(VAR_GAUNTLET_WEEK, ThisWeek());
        VarSet(VAR_GAUNTLET_BEST, 0);
    }
    VarSet(VAR_GAUNTLET_ROUND, 1);
    Gauntlet_Draft(RunSeed(), draft);
    ZeroPlayerPartyMons();
    for (i = 0; i < GAUNTLET_DRAFT_SIZE; i++)
        GiveMon(&draft[i], B_SIDE_PLAYER, PARTY_SIZE, 0, ITEM_NONE);
}

// Before ChoosePartyForBattleFrontier: pick exactly three, at level 50, with the
// Battle Tower's entry screen.
void Gauntlet_SetUpDraft(void)
{
    VarSet(VAR_FRONTIER_FACILITY, FRONTIER_FACILITY_TOWER);
    gSpecialVar_0x8004 = FRONTIER_LVL_50;
    gSpecialVar_0x8005 = GAUNTLET_TEAM_SIZE;
}

// The next round's opponent in their home stadium. STR_VAR_1 the round,
// STR_VAR_2 who.
void Gauntlet_SetUpRound(void)
{
    u32 round = VarGet(VAR_GAUNTLET_ROUND);

    DailyUnderdog_SetArenaOpponent(RunSeed(), Gauntlet_Opponent(RunSeed(), round));
    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_GAUNTLET);
    ConvertIntToDecimalStringN(gStringVar1, round, STR_CONV_MODE_LEFT_ALIGN, 3);
    BufferOpponent(gStringVar2, round);
}

bool32 Gauntlet_IsBattle(void)
{
    return VarGet(VAR_UNDERDOG_BATTLE_KIND) == SUNDIAL_BATTLE_GAUNTLET && VarGet(VAR_GAUNTLET_ROUND) != 0;
}

// A round's three (the same every time for the week): items from round 7 (Sitrus
// Berries); Red's Pikachu has its Light Ball.
static void FillTeamForRound(struct Pokemon *party, u8 side, u32 firstSlot, u32 round)
{
    struct SundialMon team[GAUNTLET_TEAM_SIZE];
    bool32 red = Gauntlet_Opponent(RunSeed(), round) == SUNDIAL_OPP_RED;
    u32 i;

    Gauntlet_OpponentTeam(RunSeed(), round, team);
    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
    {
        u16 item = ITEM_NONE;

        if (red)
            item = team[i].species == SPECIES_PIKACHU ? ITEM_LIGHT_BALL : ITEM_LEFTOVERS;
        else if (round >= 7)
            item = ITEM_LEFTOVERS;
        else if (round >= 4)
            item = ITEM_SITRUS_BERRY;
        GiveMon(&team[i], side, firstSlot + i, red ? MAX_PER_STAT_EVS : Gauntlet_EffortForRound(round), item);
        // No Dynamax or Tera from the crew (a made-up mon would otherwise allow both);
        // Red's last one may Dynamax: the boss moment of round 10.
        if (side == B_SIDE_OPPONENT && !(red && i == GAUNTLET_TEAM_SIZE - 1))
        {
            u32 blockDynamax = BLOCK_AI_DYNAMAX, noTera = TYPE_MYSTERY;

            SetMonData(&party[firstSlot + i], MON_DATA_DYNAMAX_LEVEL, &blockDynamax);
            SetMonData(&party[firstSlot + i], MON_DATA_TERA_TYPE, &noTera);
        }
    }
}

// From DoTrainerBattle: the round's three replace the trainer's own party.
void Gauntlet_FillEnemyParty(struct Pokemon *party)
{
    ZeroPartyMons(party);
    FillTeamForRound(party, B_SIDE_OPPONENT, 0, VarGet(VAR_GAUNTLET_ROUND));
}

// After a gauntlet battle (before healing). VAR_RESULT: GAUNTLET_LOST (the run is
// over: the card is ready), GAUNTLET_WON, or GAUNTLET_BEAT_RED (the first time
// also unlocks his outfit). STR_VAR_1 the round just played, STR_VAR_2 the next
// opponent.
void Gauntlet_AfterBattle(void)
{
    u32 round = VarGet(VAR_GAUNTLET_ROUND);
    bool32 won = (gBattleOutcome == B_OUTCOME_WON);
    u32 year, month, day;

    ConvertIntToDecimalStringN(gStringVar1, round, STR_CONV_MODE_LEFT_ALIGN, 3);
    if (!won)
    {
        NoteRoundReached(round);
        sLastRunRound = round;
        DailyUnderdog_GetToday(&year, &month, &day);
        SundialCard_Capture(TRAINER_BATTLE_PARAM.opponentA, FALSE, NULL, year, month, day);
        SundialCard_SetGauntlet(WeekSinceLaunch(VarGet(VAR_GAUNTLET_WEEK)), round, VarGet(VAR_GAUNTLET_BEST));
        VarSet(VAR_GAUNTLET_ROUND, 0);
        VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_PRACTICE);
        gSpecialVar_Result = GAUNTLET_LOST;
        return;
    }
    VarSet(VAR_GAUNTLET_ROUND, round + 1);
    NoteRoundReached(round + 1);
    BufferOpponent(gStringVar2, round + 1);
    gSpecialVar_Result = GAUNTLET_WON;
    if (Gauntlet_Opponent(RunSeed(), round) == SUNDIAL_OPP_RED)
    {
        gSpecialVar_Result = GAUNTLET_BEAT_RED;
        if (!FlagGet(FLAG_GAUNTLET_BEAT_RED))
        {
            FlagSet(FLAG_GAUNTLET_BEAT_RED);
            VarSet(VAR_UNDERDOG_COSTUMES_OWNED, VarGet(VAR_UNDERDOG_COSTUMES_OWNED) | (1 << COSTUME_RED));
        }
    }
}

// Saves with the next continue in the bedroom. A run can't be resumed after a
// reset (its team isn't kept), so the save never holds one in progress.
void Gauntlet_SaveProgress(void)
{
    u16 round = VarGet(VAR_GAUNTLET_ROUND);

    VarSet(VAR_GAUNTLET_ROUND, 0);
    SetContinueGameWarpToBedroomHub();
    SetContinueGameWarpStatus();
    TrySavingData(SAVE_NORMAL);
    VarSet(VAR_GAUNTLET_ROUND, round);
}

// For "ROUND n cleared! Next up: X." STR_VAR_1 the round just won, STR_VAR_2 the next opponent.
void Gauntlet_BufferCleared(void)
{
    u32 round = VarGet(VAR_GAUNTLET_ROUND);

    ConvertIntToDecimalStringN(gStringVar1, round - 1, STR_CONV_MODE_LEFT_ALIGN, 3);
    BufferOpponent(gStringVar2, round);
}

// VAR_RESULT TRUE if the run that just ended earns a shiny line.
void Gauntlet_EarnsShinyLine(void)
{
    gSpecialVar_Result = Gauntlet_EarnsReward(sLastRunRound);
}

// Swaps, the Battle Factory rule, in two party screens of three: theirs, then
// yours. While theirs are showing, yours wait in the enemy party (the battle
// wiped it), and the one picked waits in its slot 3.
#define sStash (gParties[B_TRAINER_OPPONENT_A])

static void RestoreYours(void)
{
    u32 i;

    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
        CopyMon(&gParties[B_TRAINER_PLAYER][i], &sStash[i], sizeof(struct Pokemon));
    for (i = GAUNTLET_TEAM_SIZE; i < PARTY_SIZE; i++)
        ZeroMonData(&gParties[B_TRAINER_PLAYER][i]);
    CalculatePlayerPartyCount();
}

// Step 1: the party is the three just beaten. Called with your own three in the
// party (after Gauntlet_AfterBattle has moved on to the next round).
void Gauntlet_ShowTheirs(void)
{
    u32 i;

    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
        CopyMon(&sStash[i], &gParties[B_TRAINER_PLAYER][i], sizeof(struct Pokemon));
    // They're the same for everyone, every time, so they're rebuilt for the party.
    FillTeamForRound(gParties[B_TRAINER_PLAYER], B_SIDE_PLAYER, 0, VarGet(VAR_GAUNTLET_ROUND) - 1);
    CalculatePlayerPartyCount();
}

// Step 2: VAR_0x8005 the one taken (0-2). The party is yours again. STR_VAR_1 its species.
void Gauntlet_ShowYours(void)
{
    u32 take = gSpecialVar_0x8005 < GAUNTLET_TEAM_SIZE ? gSpecialVar_0x8005 : 0;

    CopyMon(&sStash[GAUNTLET_TEAM_SIZE], &gParties[B_TRAINER_PLAYER][take], sizeof(struct Pokemon));
    StringCopy(gStringVar1, GetSpeciesName(GetMonData(&sStash[GAUNTLET_TEAM_SIZE], MON_DATA_SPECIES)));
    RestoreYours();
}

// VAR_0x8004 the one of yours it replaces (0-2). STR_VAR_1 the newcomer again
// (the party menu writes HP text over it).
void Gauntlet_DoSwap(void)
{
    if (gSpecialVar_0x8004 < GAUNTLET_TEAM_SIZE)
        CopyMon(&gParties[B_TRAINER_PLAYER][gSpecialVar_0x8004], &sStash[GAUNTLET_TEAM_SIZE], sizeof(struct Pokemon));
    StringCopy(gStringVar1, GetSpeciesName(GetMonData(&sStash[GAUNTLET_TEAM_SIZE], MON_DATA_SPECIES)));
    ZeroEnemyPartyMons();
}

// B on step 1: your three come back unchanged.
void Gauntlet_CancelSwap(void)
{
    RestoreYours();
    ZeroEnemyPartyMons();
}

#undef sStash

// Shiny followers: a whole evolution line per reward.
bool32 Wildcard_IsShinyUnlocked(u16 species)
{
    if (species == SPECIES_NONE || species >= NUM_SPECIES)
        return FALSE;
    return (gSaveBlock2Ptr->frontier.wildcardShinyLines[species / 8] >> (species % 8)) & 1;
}

// Unlocked and not switched back to normal at the GameCube: how it looks in the room and following you.
bool32 Wildcard_ShowsShiny(u16 species)
{
    if (!Wildcard_IsShinyUnlocked(species))
        return FALSE;
    return !((gSaveBlock2Ptr->frontier.wildcardShinyOff[species / 8] >> (species % 8)) & 1);
}

// GameCube: VAR_RESULT is TRUE if the follower has a shiny option, with
// VAR_0x8005 = 0 if it's shiny right now, 1 if normal. STR_VAR_1 its species.
void Wildcard_FollowerShinyChoice(void)
{
    u16 species = VarGet(VAR_UNDERDOG_FOLLOWER);

    gSpecialVar_Result = Wildcard_IsShinyUnlocked(species);
    gSpecialVar_0x8005 = !Wildcard_ShowsShiny(species);
    StringCopy(gStringVar1, GetSpeciesName(species));
}

// GameCube: VAR_0x8004 = 0 for shiny, 1 for normal colours.
void Wildcard_SetFollowerShiny(void)
{
    u16 species = VarGet(VAR_UNDERDOG_FOLLOWER);

    if (gSpecialVar_0x8004)
        gSaveBlock2Ptr->frontier.wildcardShinyOff[species / 8] |= 1 << (species % 8);
    else
        gSaveBlock2Ptr->frontier.wildcardShinyOff[species / 8] &= ~(1 << (species % 8));
    DailyUnderdog_MakeFollower(species); // rebuilds the party, so the follower changes colour
}

static void UnlockSpecies(u16 species)
{
    gSaveBlock2Ptr->frontier.wildcardShinyLines[species / 8] |= 1 << (species % 8);
    GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_SET_SEEN);
    GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_SET_CAUGHT); // the Pokédex is the collection
}

// Every species in the line: back to the first stage, then each evolution in turn.
static void UnlockLine(u16 species)
{
    u16 queue[32];
    u32 head = 0, tail = 0;
    u16 pre;

    while ((pre = GetSpeciesPreEvolution(species)) != SPECIES_NONE)
        species = pre;
    queue[tail++] = species;
    while (head < tail)
    {
        const struct Evolution *evolutions = GetSpeciesEvolutions(queue[head]);
        u32 i, j;

        UnlockSpecies(queue[head++]);
        for (i = 0; evolutions != NULL && evolutions[i].method != EVOLUTIONS_END; i++)
        {
            bool32 seen = FALSE;

            for (j = 0; j < tail; j++)
            {
                if (queue[j] == evolutions[i].targetSpecies)
                    seen = TRUE;
            }
            if (!seen && tail < ARRAY_COUNT(queue))
                queue[tail++] = evolutions[i].targetSpecies;
        }
    }
}

// VAR_0x8004: the party slot picked. STR_VAR_1 its species.
void Gauntlet_UnlockShinyLine(void)
{
    u16 species;

    if (gSpecialVar_0x8004 >= PARTY_SIZE)
        return;
    species = GetMonData(&gParties[B_TRAINER_PLAYER][gSpecialVar_0x8004], MON_DATA_SPECIES);
    if (species == SPECIES_NONE)
        return;
    UnlockLine(species);
    StringCopy(gStringVar1, GetSpeciesName(species));
}
