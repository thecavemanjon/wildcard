#include "global.h"
#include "battle.h"
#include "battle_main.h"
#include "battle_setup.h"
#include "daily_underdog.h"
#include "data.h"
#include "event_data.h"
#include "main.h"
#include "move.h"
#include "pokemon.h"
#include "script_pokemon_util.h"
#include "sundial_gauntlet.h"
#include "sundial_seed.h"
#include "wildcard_gauntlet.h"
#include "wildcard_sim.h"
#include "constants/battle.h"
#include "constants/characters.h"
#include "constants/sundial.h"
#include "constants/battle_partner.h"
#include "constants/trainers.h"

// The balance sim (wildcard/playtest/balance.py; DECISIONS 2026-10-20). Never
// reached in normal play: the runner's Lua script points gMain.callback2 at
// CB2_WildcardSimIdle and then posts jobs in gWildcardSim. A job is one daily,
// or one gauntlet run, on a pretend date; the real setup code builds both sides
// and each battle reports one CSV line in gWildcardSim.out.

#define SIM_IDLE      0
#define SIM_REQUESTED 1
#define SIM_RUNNING   2
#define SIM_DONE      3

#define SIM_LAZY      0
#define SIM_SMART     1
#define SIM_EXPERT    2
#define SIM_HUMAN     9 // the battle log's "policy" column: a person played it

#define SIM_DAILY     0
#define SIM_GAUNTLET  1
#define SIM_PRACTICE  2 // PRACTICE: no event team, no rule; needs a forced slot
#define SIM_SCHEDULE  3 // no battle: report the date's opponent, rule and six for the web player

struct WildcardSim
{
    u8 state;
    u8 mode;
    u8 smart;    // SIM_LAZY: the runner presses A; SIM_SMART, SIM_EXPERT: the AI plays your side
    u8 maxRound; // gauntlet: stop after this round even if still winning; daily, practice: 0 for the date's
                 // opponent, else fight arena slot maxRound - 1 (a fair sample per opponent)
    u16 year;
    u8 month;
    u8 day;
    u16 outLength;
    char out[1024];
    u16 logSeq; // normal play: bumped each time out holds a new battle-log line (battle_log.lua)
    u16 turnSeq; // every battle: bumped each time turn holds a new turn line
    u16 turnLength;
    char turn[256];
};

EWRAM_DATA struct WildcardSim gWildcardSim = {0};
static EWRAM_DATA struct Pokemon sTheirs[PARTY_SIZE] = {0}; // the battle wipes the enemy party, so a copy for the report

// Which trainer each arena slot fights as: the same cases as
// UnderdogArena_EventScript_Opponent (data/maps/UnderdogArena_Wallace/scripts.inc).
static const u16 sSlotTrainers[] =
{
    [ 0] = TRAINER_ROXANNE_5,
    [ 1] = TRAINER_BRAWLY_5,
    [ 2] = TRAINER_WATTSON_5,
    [ 3] = TRAINER_FLANNERY_5,
    [ 4] = TRAINER_NORMAN_5,
    [ 5] = TRAINER_WINONA_5,
    [ 6] = TRAINER_TATE_AND_LIZA_5,
    [ 7] = TRAINER_JUAN_5,
    [ 8] = TRAINER_SIDNEY,
    [ 9] = TRAINER_PHOEBE,
    [10] = TRAINER_GLACIA,
    [11] = TRAINER_DRAKE,
    [12] = TRAINER_MAXIE_MAGMA_HIDEOUT,
    [13] = TRAINER_ARCHIE,
    [14] = TRAINER_UNDERDOG_WALLACE,
    [15] = TRAINER_STEVEN,
    [16] = TRAINER_BRENDAN_LILYCOVE_TREECKO,
    [17] = TRAINER_BRENDAN_LILYCOVE_TORCHIC,
    [18] = TRAINER_BRENDAN_LILYCOVE_MUDKIP,
    [19] = TRAINER_MAY_LILYCOVE_TREECKO,
    [20] = TRAINER_MAY_LILYCOVE_TORCHIC,
    [21] = TRAINER_MAY_LILYCOVE_MUDKIP,
    [22] = TRAINER_UNDERDOG_BROCK,
    [23] = TRAINER_UNDERDOG_MISTY,
    [24] = TRAINER_UNDERDOG_LT_SURGE,
    [25] = TRAINER_UNDERDOG_ERIKA,
    [26] = TRAINER_UNDERDOG_KOGA,
    [27] = TRAINER_UNDERDOG_SABRINA,
    [28] = TRAINER_UNDERDOG_BLAINE,
    [29] = TRAINER_UNDERDOG_GIOVANNI,
    [30] = TRAINER_UNDERDOG_LORELEI,
    [31] = TRAINER_UNDERDOG_BRUNO,
    [32] = TRAINER_UNDERDOG_AGATHA,
    [33] = TRAINER_UNDERDOG_LANCE,
    [34] = TRAINER_RED,
    [35] = TRAINER_UNDERDOG_BLUE_SQUIRTLE,
    [36] = TRAINER_UNDERDOG_BLUE_BULBASAUR,
    [37] = TRAINER_UNDERDOG_BLUE_CHARMANDER,
    [38] = TRAINER_UNDERDOG_RED_ORIGINS,
};

static void CB2_AfterBattle(void);

// The date a running job pretends it is (from daily_underdog.c's Today(), which
// also keeps this file in the ROM: the linker drops anything nothing calls).
bool32 WildcardSim_GetDate(u32 *year, u32 *month, u32 *day)
{
    if (gWildcardSim.state != SIM_RUNNING)
        return FALSE;
    *year = gWildcardSim.year;
    *month = gWildcardSim.month;
    *day = gWildcardSim.day;
    return TRUE;
}

static bool8 sOutToTurn; // TRUE while LogTurn writes, so Out fills the turn buffer instead

static void Out(const char *s)
{
    char *buf = sOutToTurn ? gWildcardSim.turn : gWildcardSim.out;
    u16 *length = sOutToTurn ? &gWildcardSim.turnLength : &gWildcardSim.outLength;
    u32 size = sOutToTurn ? sizeof(gWildcardSim.turn) : sizeof(gWildcardSim.out);

    while (*s != '\0' && *length < size - 1)
        buf[(*length)++] = *s++;
    buf[*length] = '\0';
}

static void OutNum(u32 n)
{
    char buf[11];
    u32 i = sizeof(buf) - 1;

    buf[i] = '\0';
    do
    {
        buf[--i] = '0' + n % 10;
        n /= 10;
    } while (n != 0);
    Out(&buf[i]);
}

static u32 CountAlive(struct Pokemon *party)
{
    u32 i, alive = 0;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&party[i], MON_DATA_SPECIES) != SPECIES_NONE && GetMonData(&party[i], MON_DATA_HP) != 0)
            alive++;
    }
    return alive;
}

static void OutSpecies(struct Pokemon *party)
{
    u32 i;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        u16 species = GetMonData(&party[i], MON_DATA_SPECIES);

        if (species == SPECIES_NONE)
            break;
        if (i != 0)
            Out("/");
        OutNum(species);
    }
}

static void StartBattle(void)
{
    u16 trainer = sSlotTrainers[VarGet(VAR_UNDERDOG_ARENA_SLOT)];

    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.opponentA = trainer;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    if (GetTrainerBattleType(trainer) == TRAINER_BATTLE_TYPE_DOUBLES)
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE;
    // Your side plays as an in-game partner (a valid one keeps the partner's
    // messages working): smart is Steven, whose AI flags (Basic Trainer) are the
    // opponents'; expert is ours, with Smart Trainer (switching, prediction).
    gPartnerTrainerId = TRAINER_PARTNER(gWildcardSim.smart == SIM_EXPERT ? PARTNER_WILDCARD_EXPERT : PARTNER_STEVEN);
    if (gWildcardSim.smart)
        FlagSet(FLAG_SIM_AI_PLAYS);
    else
        FlagClear(FLAG_SIM_AI_PLAYS);
    FlagSet(B_FLAG_NO_WHITEOUT);

    // As DoTrainerBattle does.
    CreateNPCTrainerPartyFromTrainer(&gParties[B_TRAINER_OPPONENT_A][0], GetTrainerStructFromId(trainer));
    DailyUnderdog_ApplyBattleRule();
    if (Gauntlet_IsBattle())
        Gauntlet_FillEnemyParty(&gParties[B_TRAINER_OPPONENT_A][0]);

    memcpy(sTheirs, gEnemyParty, sizeof(sTheirs));
    gMain.savedCallback = CB2_AfterBattle;
    SetMainCallback2(CB2_InitBattle);
}

// The strongest (TRUE) or weakest of the three in the party, by base stat total.
static u32 PickByStats(bool32 strongest)
{
    u32 i, best = 0, bestBst = strongest ? 0 : 0xFFFF;

    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
    {
        u32 bst = Gauntlet_BaseStatTotal(GetMonData(&gPlayerParty[i], MON_DATA_SPECIES));

        if (strongest ? bst > bestBst : bst < bestBst)
        {
            best = i;
            bestBst = bst;
        }
    }
    return best;
}

// The draft: the AI players keep the three with the best stats, the lazy one the first three.
static void Draft(void)
{
    u32 i, j, keep[GAUNTLET_TEAM_SIZE] = {0, 1, 2};
    struct Pokemon *kept = gParties[B_TRAINER_OPPONENT_A];

    if (gWildcardSim.smart)
    {
        u8 order[GAUNTLET_DRAFT_SIZE] = {0, 1, 2, 3, 4, 5};

        for (i = 0; i < GAUNTLET_DRAFT_SIZE; i++)
        {
            for (j = i + 1; j < GAUNTLET_DRAFT_SIZE; j++)
            {
                if (Gauntlet_BaseStatTotal(GetMonData(&gPlayerParty[order[j]], MON_DATA_SPECIES))
                  > Gauntlet_BaseStatTotal(GetMonData(&gPlayerParty[order[i]], MON_DATA_SPECIES)))
                {
                    u8 tmp = order[i];
                    order[i] = order[j];
                    order[j] = tmp;
                }
            }
        }
        for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
            keep[i] = order[i];
    }
    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
        CopyMon(&kept[i], &gPlayerParty[keep[i]], sizeof(struct Pokemon));
    ZeroPlayerPartyMons();
    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
        CopyMon(&gPlayerParty[i], &kept[i], sizeof(struct Pokemon));
    ZeroEnemyPartyMons();
    CalculatePlayerPartyCount();
}

// After a win: the AI players take the beaten team's strongest if it beats their own weakest.
static void MaybeSwap(void)
{
    u32 theirs, take, drop;

    if (!gWildcardSim.smart)
        return;
    Gauntlet_ShowTheirs();
    take = PickByStats(TRUE);
    theirs = Gauntlet_BaseStatTotal(GetMonData(&gPlayerParty[take], MON_DATA_SPECIES));
    gSpecialVar_0x8005 = take;
    Gauntlet_ShowYours();
    drop = PickByStats(FALSE);
    if (theirs > Gauntlet_BaseStatTotal(GetMonData(&gPlayerParty[drop], MON_DATA_SPECIES)))
    {
        gSpecialVar_0x8004 = drop;
        Gauntlet_DoSwap();
    }
    else
    {
        Gauntlet_CancelSwap();
    }
}

// One CSV line per battle: mode,date,smart,round,slot,rule,event,won,turns,yoursLeft,theirsLeft,yours,theirs
// (smart is the policy: SIM_LAZY, SIM_SMART, SIM_EXPERT, or SIM_HUMAN in the battle log).
static void ReportLine(const char *mode, u32 who, u32 year, u32 month, u32 day, u32 round, u32 rule)
{
    Out(mode);
    OutNum(year);
    Out("-");
    OutNum(month);
    Out("-");
    OutNum(day);
    Out(",");
    OutNum(who);
    Out(",");
    OutNum(round);
    Out(",");
    OutNum(VarGet(VAR_UNDERDOG_ARENA_SLOT));
    Out(",");
    OutNum(rule);
    Out(",");
    OutNum(Sundial_EventForDate(year, month, day));
    Out(",");
    OutNum(gBattleOutcome == B_OUTCOME_WON);
    Out(",");
    OutNum(gBattleResults.battleTurnCounter);
    Out(",");
    OutNum(CountAlive(gPlayerParty));
    Out(",");
    OutNum(CountAlive(sTheirs) - gBattleResults.opponentFaintCounter);
    Out(",");
    OutSpecies(gPlayerParty);
    Out(",");
    OutSpecies(sTheirs);
    Out("\n");
}

static void ReportBattle(void)
{
    static const char *const modes[] = { [SIM_DAILY] = "daily,", [SIM_GAUNTLET] = "gauntlet,", [SIM_PRACTICE] = "practice," };
    u32 round = gWildcardSim.mode == SIM_GAUNTLET ? VarGet(VAR_GAUNTLET_ROUND) : 0;
    u32 rule = gWildcardSim.mode == SIM_DAILY ? Sundial_RuleForDate(gWildcardSim.year, gWildcardSim.month, gWildcardSim.day) : 0;

    ReportLine(modes[gWildcardSim.mode], gWildcardSim.smart, gWildcardSim.year, gWildcardSim.month, gWildcardSim.day, round, rule);
}

// The battle log, for real play (the sim reports its own): their six and the team's date as
// the battle starts, since the battle wipes the enemy party and may run past midnight...
static EWRAM_DATA u32 sLogYear = 0, sLogMonth = 0, sLogDay = 0;

void WildcardSim_LogBattleStart(void)
{
    if (gWildcardSim.state != SIM_RUNNING)
    {
        memcpy(sTheirs, gEnemyParty, sizeof(sTheirs));
        DailyUnderdog_GetTeamDate(&sLogYear, &sLogMonth, &sLogDay);
    }
}

// ...and one line as it ends, in the farm's format, for wildcard/playtest/battle_log.lua to collect.
void WildcardSim_LogBattleEnd(void)
{
    static const char *const kinds[] =
    {
        [SUNDIAL_BATTLE_PRACTICE]  = "practice,",
        [SUNDIAL_BATTLE_DAILY]     = "daily,",
        [SUNDIAL_BATTLE_FREE_PLAY] = "freeplay,",
        [SUNDIAL_BATTLE_GAUNTLET]  = "gauntlet,",
    };
    u32 kind = VarGet(VAR_UNDERDOG_BATTLE_KIND);

    if (gWildcardSim.state == SIM_RUNNING || kind >= ARRAY_COUNT(kinds))
        return;
    gWildcardSim.outLength = 0;
    ReportLine(kinds[kind], SIM_HUMAN, sLogYear, sLogMonth, sLogDay, kind == SUNDIAL_BATTLE_GAUNTLET ? VarGet(VAR_GAUNTLET_ROUND) : 0,
               kind == SUNDIAL_BATTLE_DAILY ? Sundial_RuleForDate(sLogYear, sLogMonth, sLogDay) : 0);
    gWildcardSim.logSeq++;
}

// Game text as plain ASCII (defined below, used by the turn log too)
static void OutText(const u8 *s);

// One line per turn, as it starts (everyone has chosen, nothing has happened yet):
// turn,species:hp:maxHP:action per battler (battlers 0 and 2 are yours, 1 and 3 theirs;
// action is the move chosen, switch, item or -). The next line's HP is this turn's result.
void WildcardSim_LogTurn(void)
{
    u32 i;

    sOutToTurn = TRUE;
    gWildcardSim.turnLength = 0;
    OutNum(gBattleResults.battleTurnCounter + 1);
    for (i = 0; i < gBattlersCount; i++)
    {
        Out(",");
        OutText(GetSpeciesName(gBattleMons[i].species));
        Out(":");
        OutNum(gBattleMons[i].hp);
        Out(":");
        OutNum(gBattleMons[i].maxHP);
        Out(":");
        if (gChosenActionByBattler[i] == B_ACTION_USE_MOVE && gChosenMoveByBattler[i] != MOVE_NONE)
            OutText(GetMoveName(gChosenMoveByBattler[i]));
        else if (gChosenActionByBattler[i] == B_ACTION_SWITCH)
            Out("switch");
        else if (gChosenActionByBattler[i] == B_ACTION_USE_ITEM)
            Out("item");
        else
            Out("-");
    }
    Out("\n");
    sOutToTurn = FALSE;
    gWildcardSim.turnSeq++;
}

// Game text as plain ASCII, for the schedule's names (é becomes e; anything odd, ?).
static void OutText(const u8 *s)
{
    char c[2] = {0};

    for (; *s != EOS; s++)
    {
        if (*s >= CHAR_A && *s <= CHAR_Z)
            c[0] = 'A' + *s - CHAR_A;
        else if (*s >= CHAR_a && *s <= CHAR_z)
            c[0] = 'a' + *s - CHAR_a;
        else if (*s >= CHAR_0 && *s <= CHAR_9)
            c[0] = '0' + *s - CHAR_0;
        else if (*s == CHAR_SPACE)
            c[0] = ' ';
        else if (*s == CHAR_e_ACUTE)
            c[0] = 'e';
        else if (*s == CHAR_HYPHEN)
            c[0] = '-';
        else if (*s == CHAR_PERIOD)
            c[0] = '.';
        else if (*s == CHAR_AMPERSAND) // TATE&LIZA
            c[0] = '&';
        else if (*s == CHAR_SGL_QUOTE_RIGHT)
            c[0] = '\'';
        else if (*s == CHAR_MALE)
            c[0] = 'M';
        else if (*s == CHAR_FEMALE)
            c[0] = 'F';
        else
            c[0] = '?';
        Out(c);
    }
}

// One line per date for the web player (wildcard/web/build_data.py):
// date|slot|trainer|rule|event|species,name,type,type,move/move/move/move|... for the six
static void ReportSchedule(void)
{
    u32 i, j;
    const u8 *rule = DailyUnderdog_RuleName(Sundial_RuleForDate(gWildcardSim.year, gWildcardSim.month, gWildcardSim.day));

    OutNum(gWildcardSim.year);
    Out("-");
    OutNum(gWildcardSim.month);
    Out("-");
    OutNum(gWildcardSim.day);
    Out("|");
    OutNum(VarGet(VAR_UNDERDOG_ARENA_SLOT));
    Out("|");
    OutText(GetTrainerNameFromId(sSlotTrainers[VarGet(VAR_UNDERDOG_ARENA_SLOT)]));
    Out("|");
    if (rule != NULL)
        OutText(rule);
    Out("|");
    OutNum(Sundial_EventForDate(gWildcardSim.year, gWildcardSim.month, gWildcardSim.day));
    for (i = 0; i < PARTY_SIZE; i++)
    {
        u16 species = GetMonData(&gPlayerParty[i], MON_DATA_SPECIES);

        if (species == SPECIES_NONE)
            break;
        Out("|");
        OutNum(species);
        Out(",");
        OutText(GetSpeciesName(species));
        Out(",");
        OutText(gTypesInfo[GetSpeciesType(species, 0)].name);
        Out(",");
        OutText(gTypesInfo[GetSpeciesType(species, 1)].name);
        Out(",");
        for (j = 0; j < MAX_MON_MOVES; j++)
        {
            u16 move = GetMonData(&gPlayerParty[i], MON_DATA_MOVE1 + j);

            if (move == MOVE_NONE)
                break;
            if (j != 0)
                Out("/");
            OutText(GetMoveName(move));
        }
    }
    Out("\n");
}

static void CB2_AfterBattle(void)
{
    u32 round;

    ReportBattle();
    FlagClear(FLAG_SIM_AI_PLAYS);
    if (gWildcardSim.mode == SIM_GAUNTLET)
    {
        round = VarGet(VAR_GAUNTLET_ROUND);
        Gauntlet_AfterBattle();
        if (gSpecialVar_Result != GAUNTLET_LOST && round < gWildcardSim.maxRound)
        {
            HealPlayerParty();
            MaybeSwap();
            Gauntlet_SetUpRound();
            StartBattle();
            return;
        }
        VarSet(VAR_GAUNTLET_ROUND, 0);
    }
    gWildcardSim.state = SIM_DONE;
    SetMainCallback2(CB2_WildcardSimIdle);
}

// Waits for the runner to post a job.
void CB2_WildcardSimIdle(void)
{
    if (gWildcardSim.state != SIM_REQUESTED)
        return;
    gWildcardSim.state = SIM_RUNNING;
    gWildcardSim.outLength = 0;
    gWildcardSim.out[0] = '\0';
    gSaveBlock2Ptr->optionsBattleSceneOff = TRUE; // no animations, instant text: a copy of the save, never written
    gSaveBlock2Ptr->optionsTextSpeed = OPTIONS_TEXT_SPEED_INSTANT;
    if (gWildcardSim.mode == SIM_GAUNTLET)
    {
        Gauntlet_StartRun();
        Draft();
        Gauntlet_SetUpRound();
    }
    else
    {
        if (gWildcardSim.mode == SIM_PRACTICE)
            DailyUnderdog_SetUpPractice();
        else
            DailyUnderdog_SetUpDaily();
        if (gWildcardSim.mode == SIM_SCHEDULE)
        {
            ReportSchedule();
            gWildcardSim.state = SIM_DONE;
            return;
        }
        if (gWildcardSim.maxRound != 0)
            VarSet(VAR_UNDERDOG_ARENA_SLOT, gWildcardSim.maxRound - 1);
    }
    StartBattle();
}
