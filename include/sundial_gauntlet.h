#ifndef GUARD_SUNDIAL_GAUNTLET_H
#define GUARD_SUNDIAL_GAUNTLET_H

#include "sundial_seed.h"

// The gauntlet (DECISIONS 2026-10-15/19): an endless 3v3 run against the Kanto
// crew, seeded by the week so everyone gets the same draft and opponents, with
// unlimited retries. Plain C, no game state, so the unit tests cover it.

#define GAUNTLET_DRAFT_SIZE  6
#define GAUNTLET_TEAM_SIZE   3
#define GAUNTLET_RED_ROUND   10 // Red waits on the summit; the run carries on after him
#define GAUNTLET_REWARD_ROUND 5 // a run that gets this far earns a shiny line

u32 Gauntlet_WeekNumber(u32 dayNumber); // weeks run Monday to Sunday
u32 Gauntlet_WeekSeed(u32 week);
void Gauntlet_Draft(u32 seed, struct SundialMon *draft);
enum SundialOpponent Gauntlet_Opponent(u32 seed, u32 round);
enum Type Gauntlet_OpponentType(enum SundialOpponent opponent);
void Gauntlet_OpponentTeam(u32 seed, u32 round, struct SundialMon *team);
u32 Gauntlet_EffortForRound(u32 round);
bool32 Gauntlet_EarnsReward(u32 roundReached);
u32 Gauntlet_BaseStatTotal(u16 species);

#endif // GUARD_SUNDIAL_GAUNTLET_H
