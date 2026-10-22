#ifndef GUARD_CONSTANTS_SUNDIAL_H
#define GUARD_CONSTANTS_SUNDIAL_H

// How the last daily went (VAR_UNDERDOG_LAST_RESULT). Scripts switch on these too.
#define SUNDIAL_RESULT_NONE        0 // no daily yet
#define SUNDIAL_RESULT_IN_PROGRESS 1 // started, not finished (a reset mid-battle leaves this)
#define SUNDIAL_RESULT_WON         2
#define SUNDIAL_RESULT_LOST        3

// What the arena battle is (VAR_UNDERDOG_BATTLE_KIND).
#define SUNDIAL_BATTLE_PRACTICE  0 // PRACTICE (pick an opponent): a card, never recorded
#define SUNDIAL_BATTLE_DAILY     1 // on the record, card, Hall of Fame on a win
#define SUNDIAL_BATTLE_FREE_PLAY 2 // a word seed: card, never recorded
#define SUNDIAL_BATTLE_GAUNTLET  3 // a round of the gauntlet (src/wildcard_gauntlet.c)

// Gauntlet_AfterBattle's VAR_RESULT.
#define GAUNTLET_LOST     0
#define GAUNTLET_WON      1
#define GAUNTLET_BEAT_RED 2

// Launch day: the card's day number and the gauntlet's week number count from here.
#define LAUNCH_YEAR  2026
#define LAUNCH_MONTH 10
#define LAUNCH_DAY   12

#endif // GUARD_CONSTANTS_SUNDIAL_H
