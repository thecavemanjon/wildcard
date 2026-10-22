#ifndef GUARD_SUNDIAL_CARD_H
#define GUARD_SUNDIAL_CARD_H

void SundialCard_Capture(u16 trainerId, bool32 won, const u8 *seedWord, u32 year, u32 month, u32 day);
void SundialCard_SetPrize(u32 prize);
void SundialCard_SetPractice(void);
void SundialCard_SetGauntlet(u32 week, u32 round, u32 best);
void DailyUnderdog_ShowResultsCard(void);
void DailyUnderdog_ShowTrophyWall(void);

#endif // GUARD_SUNDIAL_CARD_H
