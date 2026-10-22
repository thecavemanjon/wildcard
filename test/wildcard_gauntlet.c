#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "event_data.h"
#include "pokemon.h"
#include "sundial_gauntlet.h"
#include "wildcard_gauntlet.h"
#include "constants/items.h"
#include "constants/sundial.h"

void Gauntlet_ShowTheirs(void);
void Gauntlet_ShowYours(void);
void Gauntlet_CancelSwap(void);
void Gauntlet_DoSwap(void);
void Gauntlet_UnlockShinyLine(void);
void Wildcard_SetFollowerShiny(void);

static void GiveTo(struct Pokemon *party, u32 slot, u16 species)
{
    CreateMon(&party[slot], species, 50, 0, OTID_STRUCT_PLAYER_ID);
}

TEST("Gauntlet game: a round's opponent fields that round's three")
{
    struct SundialMon team[GAUNTLET_TEAM_SIZE];
    u32 i, week = 1400;

    VarSet(VAR_GAUNTLET_WEEK, week);
    VarSet(VAR_GAUNTLET_ROUND, 2);
    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_GAUNTLET);
    EXPECT(Gauntlet_IsBattle());
    Gauntlet_FillEnemyParty(gParties[B_TRAINER_OPPONENT_A]);
    Gauntlet_OpponentTeam(Gauntlet_WeekSeed(week), 2, team);
    for (i = 0; i < GAUNTLET_TEAM_SIZE; i++)
    {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][i], MON_DATA_SPECIES), team[i].species);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][i], MON_DATA_LEVEL), SUNDIAL_LEVEL);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][i], MON_DATA_HELD_ITEM), ITEM_NONE);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][i], MON_DATA_DYNAMAX_LEVEL), BLOCK_AI_DYNAMAX);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][i], MON_DATA_TERA_TYPE), TYPE_MYSTERY);
    }
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][GAUNTLET_TEAM_SIZE], MON_DATA_SPECIES), SPECIES_NONE);

    VarSet(VAR_GAUNTLET_ROUND, 4);
    Gauntlet_FillEnemyParty(gParties[B_TRAINER_OPPONENT_A]);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_HELD_ITEM), ITEM_SITRUS_BERRY);
    VarSet(VAR_GAUNTLET_ROUND, 7);
    Gauntlet_FillEnemyParty(gParties[B_TRAINER_OPPONENT_A]);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_HELD_ITEM), ITEM_LEFTOVERS);

    VarSet(VAR_GAUNTLET_ROUND, GAUNTLET_RED_ROUND);
    Gauntlet_FillEnemyParty(gParties[B_TRAINER_OPPONENT_A]);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_SPECIES), SPECIES_PIKACHU);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_HELD_ITEM), ITEM_LIGHT_BALL);

    VarSet(VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_DAILY);
    EXPECT(!Gauntlet_IsBattle());
}

TEST("Gauntlet game: a swap shows their three, then yours, and trades one for one")
{
    struct SundialMon beaten[GAUNTLET_TEAM_SIZE];

    VarSet(VAR_GAUNTLET_WEEK, 1400);
    VarSet(VAR_GAUNTLET_ROUND, 2); // round 1 just won
    Gauntlet_OpponentTeam(Gauntlet_WeekSeed(1400), 1, beaten);
    ZeroPlayerPartyMons();
    GiveTo(gParties[B_TRAINER_PLAYER], 0, SPECIES_BULBASAUR);
    GiveTo(gParties[B_TRAINER_PLAYER], 1, SPECIES_CHARMANDER);
    GiveTo(gParties[B_TRAINER_PLAYER], 2, SPECIES_SQUIRTLE);
    ZeroEnemyPartyMons(); // the battle wipes it

    Gauntlet_ShowTheirs();
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), beaten[1].species);
    gSpecialVar_0x8005 = 1; // the second of theirs
    Gauntlet_ShowYours();
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), SPECIES_CHARMANDER);
    gSpecialVar_0x8004 = 1; // for Charmander
    Gauntlet_DoSwap();
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_BULBASAUR);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), beaten[1].species);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_SPECIES), SPECIES_SQUIRTLE);
}

TEST("Gauntlet game: backing out of a swap leaves your three as they were")
{
    ZeroPlayerPartyMons();
    GiveTo(gParties[B_TRAINER_PLAYER], 0, SPECIES_BULBASAUR);
    GiveTo(gParties[B_TRAINER_PLAYER], 1, SPECIES_CHARMANDER);
    GiveTo(gParties[B_TRAINER_PLAYER], 2, SPECIES_SQUIRTLE);
    VarSet(VAR_GAUNTLET_WEEK, 1400);
    VarSet(VAR_GAUNTLET_ROUND, 2);
    Gauntlet_ShowTheirs();
    Gauntlet_CancelSwap();
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_BULBASAUR);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_SPECIES), SPECIES_SQUIRTLE);
}

TEST("Gauntlet game: a reward unlocks the whole evolution line as shiny followers")
{
    memset(gSaveBlock2Ptr->frontier.wildcardShinyLines, 0, sizeof(gSaveBlock2Ptr->frontier.wildcardShinyLines));
    ZeroPlayerPartyMons();
    GiveTo(gParties[B_TRAINER_PLAYER], 0, SPECIES_CHARMELEON);
    GiveTo(gParties[B_TRAINER_PLAYER], 1, SPECIES_EEVEE);
    gSpecialVar_0x8004 = 0;
    Gauntlet_UnlockShinyLine();
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_CHARMANDER));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_CHARMELEON));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_CHARIZARD));
    EXPECT(!Wildcard_IsShinyUnlocked(SPECIES_SQUIRTLE));
    EXPECT(!Wildcard_IsShinyUnlocked(SPECIES_EEVEE));

    gSpecialVar_0x8004 = 1;
    Gauntlet_UnlockShinyLine();
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_EEVEE));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_VAPOREON));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_UMBREON));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_SYLVEON));
}

TEST("Gauntlet game: an unlocked follower can be switched back to normal colours")
{
    memset(gSaveBlock2Ptr->frontier.wildcardShinyLines, 0, sizeof(gSaveBlock2Ptr->frontier.wildcardShinyLines));
    memset(gSaveBlock2Ptr->frontier.wildcardShinyOff, 0, sizeof(gSaveBlock2Ptr->frontier.wildcardShinyOff));
    ZeroPlayerPartyMons();
    GiveTo(gParties[B_TRAINER_PLAYER], 0, SPECIES_CHARMANDER);
    gSpecialVar_0x8004 = 0;
    Gauntlet_UnlockShinyLine();
    VarSet(VAR_UNDERDOG_FOLLOWER, SPECIES_CHARIZARD);
    EXPECT(Wildcard_ShowsShiny(SPECIES_CHARIZARD));

    gSpecialVar_0x8004 = 1; // NORMAL
    Wildcard_SetFollowerShiny();
    EXPECT(!Wildcard_ShowsShiny(SPECIES_CHARIZARD));
    EXPECT(Wildcard_IsShinyUnlocked(SPECIES_CHARIZARD)); // still owned, just not worn
    EXPECT(Wildcard_ShowsShiny(SPECIES_CHARMELEON));     // the rest of the line keeps its own choice
    EXPECT(!IsMonShiny(&gParties[B_TRAINER_PLAYER][0]));

    gSpecialVar_0x8004 = 0; // SHINY
    Wildcard_SetFollowerShiny();
    EXPECT(Wildcard_ShowsShiny(SPECIES_CHARIZARD));
    EXPECT(IsMonShiny(&gParties[B_TRAINER_PLAYER][0]));
}
