@ Daily Underdog arena: LittlerootTown_MaysHouse_2F's room with only today's opponent in it (its
@ owner, or a Kanto stand-in). The battle is the shared UnderdogArena_EventScript_Opponent.
UnderdogArena_May_MapScripts::
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, UnderdogArena_May_OnWarp
	.byte 0

UnderdogArena_May_OnWarp:
	map_script_2 VAR_TEMP_1, 0, UnderdogArena_May_EventScript_PlayerTurn
	.2byte 0

UnderdogArena_May_EventScript_PlayerTurn::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_TEMP_1, 1
	end
