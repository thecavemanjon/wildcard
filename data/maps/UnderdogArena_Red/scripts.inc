@ Daily Underdog arena: Red's Mt. Silver stand-in. Mt. Pyre's summit (Emerald's only
@ open-air peak) with the snow weather Emerald never uses; Red waits at the shrine.
UnderdogArena_Red_MapScripts::
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, UnderdogArena_Red_OnWarp
	.byte 0

UnderdogArena_Red_OnWarp:
	map_script_2 VAR_TEMP_1, 0, UnderdogArena_Red_EventScript_PlayerTurn
	.2byte 0

UnderdogArena_Red_EventScript_PlayerTurn::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_TEMP_1, 1
	end
