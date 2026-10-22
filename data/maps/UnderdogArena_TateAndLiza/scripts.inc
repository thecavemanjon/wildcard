@ Daily Underdog arena: MossdeepCity_Gym's room with only today's opponent in it (its
@ owner, or a Kanto stand-in). The battle is the shared UnderdogArena_EventScript_Opponent.
UnderdogArena_TateAndLiza_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, UnderdogArena_TateAndLiza_OnTransition
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, UnderdogArena_TateAndLiza_OnWarp
	.byte 0

@ Liza only appears beside Tate (Sabrina borrows this room too).
UnderdogArena_TateAndLiza_OnTransition:
	setflag FLAG_TEMP_1
	goto_if_ne VAR_UNDERDOG_ARENA_SLOT, 6, UnderdogArena_TateAndLiza_OnTransitionEnd
	clearflag FLAG_TEMP_1
UnderdogArena_TateAndLiza_OnTransitionEnd:
	end

UnderdogArena_TateAndLiza_OnWarp:
	map_script_2 VAR_TEMP_1, 0, UnderdogArena_TateAndLiza_EventScript_PlayerTurn
	.2byte 0

UnderdogArena_TateAndLiza_EventScript_PlayerTurn::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_TEMP_1, 1
	end
