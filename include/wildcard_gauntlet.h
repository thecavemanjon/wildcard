#ifndef GUARD_WILDCARD_GAUNTLET_H
#define GUARD_WILDCARD_GAUNTLET_H

// The gauntlet's game side (src/wildcard_gauntlet.c). The script specials
// (Gauntlet_StartRun and friends) are listed in data/specials.inc.
bool32 Gauntlet_IsBattle(void);
void Gauntlet_FillEnemyParty(struct Pokemon *party);
bool32 Wildcard_IsShinyUnlocked(u16 species);
bool32 Wildcard_ShowsShiny(u16 species);

// Also called by the balance sim (src/wildcard_sim.c).
void Gauntlet_StartRun(void);
void Gauntlet_SetUpRound(void);
void Gauntlet_AfterBattle(void);
void Gauntlet_ShowTheirs(void);
void Gauntlet_ShowYours(void);
void Gauntlet_DoSwap(void);
void Gauntlet_CancelSwap(void);

#endif // GUARD_WILDCARD_GAUNTLET_H
