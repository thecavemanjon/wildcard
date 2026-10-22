# Wild Card

A daily Pokémon battle, built as a Pokémon Emerald ROM hack. Every day there's one
opponent, one random team of six at level 50, and one attempt. Everyone playing on
the same date gets the same opponent and the same team, so you can compare
results with friends.

It's a fan project and isn't released yet. There's no patch to download; for now
you build it from source (below).

## What's in it

- The daily battle. The date picks the opponent and your six, each with a
  sensible moveset. Mondays and Tuesdays are gym leaders, Wednesdays and Thursdays
  the Elite Four, Fridays Maxie, Archie or Giovanni, Saturdays a rival and Sundays
  Wallace or Steven. You get one go; the game saves your result, your streak and a
  results card you can share.
- Rule days. Some dates add a twist for the whole battle: a terrain, Trick Room or
  an inverse type chart.
- Event days. Halloween, Christmas and Easter bring their own opponents and teams.
- The gauntlet. A weekly run through a Kanto league: draft three of six, beat a
  round, take one of their Pokémon if you want it, keep going. Red waits at round
  ten. Wins earn shiny evolution lines.
- Practice and free play. Fight any opponent with a date's team, or type a word to
  seed a one-off battle.
- A stadium for every battle, with a crowd.
- A bedroom to come back to: a PC for the menus, followers bought in the shop,
  room themes, costumes and a clock on the wall.

## Playing it

The game reads the real-time clock, the same way Emerald does for berries and
tides, so play it in an emulator that supports Emerald's clock, such as mGBA. The
date your device reports is the date you play.

## Building

You need devkitARM and the usual pokeemerald-expansion toolchain; see
[INSTALL.md](INSTALL.md). Then:

```
make
```

That writes `pokeemerald.gba`. Don't change the ROM header: emulators use the game
code to switch on the clock.

Tests for the daily logic (seeds, teams, records, the gauntlet):

```
make check TESTS="Sundial"
```

Some code still uses older working names (`Underdog`, `Sundial`); they're internal
only.

## Where things are

Our own code sits alongside the expansion's: `src/daily_underdog.c` (game glue),
`src/sundial_*.c` (seeds, records, the results card, the shop),
`src/wildcard_*.c` (the gauntlet, the balance sim). Everything else of ours, from
design notes to art scripts and the playtest tools, is in [`wildcard/`](wildcard/).
Edits to vanilla files are marked `// Daily Underdog:`.

## Credits

Built on [pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion)
by RHH (Rom Hacking Hideout), which is built on pret's
[pokeemerald](https://github.com/pret/pokeemerald) decompilation:

```
Based off RHH's pokeemerald-expansion 1.17.2 https://github.com/rh-hideout/pokeemerald-expansion/
```

Sprite artists and their terms are listed in [wildcard/CREDITS.md](wildcard/CREDITS.md).
The expansion's own contributors are in [CREDITS.md](CREDITS.md).

## Legal

Wild Card is an unofficial fan project, not affiliated with or endorsed by
Nintendo, Game Freak, Creatures or The Pokémon Company. Pokémon is their
trademark. This repository contains no ROMs, and we will never distribute one: to
play, you need your own copy of Pokémon Emerald.
