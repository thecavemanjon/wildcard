#ifndef GUARD_WILDCARD_SIM_H
#define GUARD_WILDCARD_SIM_H

// The balance sim (src/wildcard_sim.c), driven by wildcard/playtest/balance.py.
bool32 WildcardSim_GetDate(u32 *year, u32 *month, u32 *day);
void CB2_WildcardSimIdle(void);
// The battle log (wildcard/playtest/battle_log.py): every real trainer battle as one CSV line.
void WildcardSim_LogBattleStart(void);
void WildcardSim_LogBattleEnd(void);
void WildcardSim_LogTurn(void); // from SetActionsAndBattlersTurnOrder, once per turn

#endif // GUARD_WILDCARD_SIM_H
