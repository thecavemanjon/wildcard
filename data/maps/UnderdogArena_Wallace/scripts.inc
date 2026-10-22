@ Daily Underdog arena: the Champion's Room, Wallace's (and Blue's stand-in).
@ Also holds the opponent script every arena shares. The PC specials set
@ VAR_UNDERDOG_ARENA_SLOT (the case numbers below match sArenaOpponents in
@ src/daily_underdog.c) and the sprite.
UnderdogArena_Wallace_MapScripts::
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, UnderdogArena_Wallace_OnWarp
	.byte 0

UnderdogArena_Wallace_OnWarp:
	map_script_2 VAR_TEMP_1, 0, UnderdogArena_Wallace_EventScript_PlayerTurnNorth
	.2byte 0

UnderdogArena_Wallace_EventScript_PlayerTurnNorth::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_TEMP_1, 1
	end

@ No intro (the script shows it), no "already beaten" check, script continues after.
	.macro underdog_battle trainer:req, lose_text:req, isDouble:req
	trainerbattle LOCALID_NONE, \trainer, NULL, \lose_text, NULL, LOCALID_NONE, TRAINER_NONE, NULL, NULL, NULL, NULL, NULL, \isDouble, TRUE, FALSE, FALSE, TRUE, FALSE, FALSE, TRUE
	.endm

UnderdogArena_EventScript_Opponent::
	lock
	faceplayer
	setflag B_FLAG_NO_WHITEOUT @ a loss goes home, not to a POKéMON CENTER
	switch VAR_UNDERDOG_ARENA_SLOT
	case 0, UnderdogArena_EventScript_Roxanne
	case 1, UnderdogArena_EventScript_Brawly
	case 2, UnderdogArena_EventScript_Wattson
	case 3, UnderdogArena_EventScript_Flannery
	case 4, UnderdogArena_EventScript_Norman
	case 5, UnderdogArena_EventScript_Winona
	case 6, UnderdogArena_EventScript_TateAndLiza
	case 7, UnderdogArena_EventScript_Juan
	case 8, UnderdogArena_EventScript_Sidney
	case 9, UnderdogArena_EventScript_Phoebe
	case 10, UnderdogArena_EventScript_Glacia
	case 11, UnderdogArena_EventScript_Drake
	case 12, UnderdogArena_EventScript_Maxie
	case 13, UnderdogArena_EventScript_Archie
	case 14, UnderdogArena_EventScript_Wallace
	case 15, UnderdogArena_EventScript_Steven
	case 16, UnderdogArena_EventScript_BrendanTreecko
	case 17, UnderdogArena_EventScript_BrendanTorchic
	case 18, UnderdogArena_EventScript_BrendanMudkip
	case 19, UnderdogArena_EventScript_MayTreecko
	case 20, UnderdogArena_EventScript_MayTorchic
	case 21, UnderdogArena_EventScript_MayMudkip
	case 22, UnderdogArena_EventScript_Brock
	case 23, UnderdogArena_EventScript_Misty
	case 24, UnderdogArena_EventScript_LtSurge
	case 25, UnderdogArena_EventScript_Erika
	case 26, UnderdogArena_EventScript_Koga
	case 27, UnderdogArena_EventScript_Sabrina
	case 28, UnderdogArena_EventScript_Blaine
	case 29, UnderdogArena_EventScript_Giovanni
	case 30, UnderdogArena_EventScript_Lorelei
	case 31, UnderdogArena_EventScript_Bruno
	case 32, UnderdogArena_EventScript_Agatha
	case 33, UnderdogArena_EventScript_Lance
	case 34, UnderdogArena_EventScript_Red
	case 35, UnderdogArena_EventScript_BlueSquirtle
	case 36, UnderdogArena_EventScript_BlueBulbasaur
	case 37, UnderdogArena_EventScript_BlueCharmander
	case 38, UnderdogArena_EventScript_RedOrigins
	goto UnderdogArena_EventScript_Wallace

UnderdogArena_EventScript_Roxanne:
	msgbox UnderdogArena_Text_RoxanneIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_ROXANNE_5
	underdog_battle TRAINER_ROXANNE_5, UnderdogArena_Text_RoxanneDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Brawly:
	msgbox UnderdogArena_Text_BrawlyIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_BRAWLY_5
	underdog_battle TRAINER_BRAWLY_5, UnderdogArena_Text_BrawlyDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Wattson:
	msgbox UnderdogArena_Text_WattsonIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_WATTSON_5
	underdog_battle TRAINER_WATTSON_5, UnderdogArena_Text_WattsonDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Flannery:
	msgbox UnderdogArena_Text_FlanneryIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_FLANNERY_5
	underdog_battle TRAINER_FLANNERY_5, UnderdogArena_Text_FlanneryDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Norman:
	msgbox UnderdogArena_Text_NormanIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_NORMAN_5
	underdog_battle TRAINER_NORMAN_5, UnderdogArena_Text_NormanDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Winona:
	msgbox UnderdogArena_Text_WinonaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_WINONA_5
	underdog_battle TRAINER_WINONA_5, UnderdogArena_Text_WinonaDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_TateAndLiza:
	msgbox UnderdogArena_Text_TateAndLizaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_TATE_AND_LIZA_5
	underdog_battle TRAINER_TATE_AND_LIZA_5, UnderdogArena_Text_TateAndLizaDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Juan:
	msgbox UnderdogArena_Text_JuanIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_JUAN_5
	underdog_battle TRAINER_JUAN_5, UnderdogArena_Text_JuanDefeat, TRUE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Sidney:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_SidneyIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_SIDNEY
	underdog_battle TRAINER_SIDNEY, UnderdogArena_Text_SidneyDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Phoebe:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_PhoebeIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_PHOEBE
	underdog_battle TRAINER_PHOEBE, UnderdogArena_Text_PhoebeDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Glacia:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_GlaciaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_GLACIA
	underdog_battle TRAINER_GLACIA, UnderdogArena_Text_GlaciaDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Drake:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_DrakeIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_DRAKE
	underdog_battle TRAINER_DRAKE, UnderdogArena_Text_DrakeDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Maxie:
	playbgm MUS_ENCOUNTER_MAGMA, FALSE
	msgbox UnderdogArena_Text_MaxieIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_MAXIE_MAGMA_HIDEOUT
	underdog_battle TRAINER_MAXIE_MAGMA_HIDEOUT, UnderdogArena_Text_MaxieDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Archie:
	playbgm MUS_ENCOUNTER_AQUA, FALSE
	msgbox UnderdogArena_Text_ArchieIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_ARCHIE
	underdog_battle TRAINER_ARCHIE, UnderdogArena_Text_ArchieDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Wallace:
	playbgm MUS_ENCOUNTER_CHAMPION, FALSE
	msgbox UnderdogArena_Wallace_Text_Intro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_WALLACE
	underdog_battle TRAINER_UNDERDOG_WALLACE, UnderdogArena_Wallace_Text_Defeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Steven:
	playbgm MUS_ENCOUNTER_CHAMPION, FALSE
	msgbox UnderdogArena_Text_StevenIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_STEVEN
	underdog_battle TRAINER_STEVEN, UnderdogArena_Text_StevenDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BrendanTreecko:
	playbgm MUS_ENCOUNTER_BRENDAN, FALSE
	msgbox UnderdogArena_Text_BrendanIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_BRENDAN_LILYCOVE_TREECKO
	underdog_battle TRAINER_BRENDAN_LILYCOVE_TREECKO, UnderdogArena_Text_BrendanDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BrendanTorchic:
	playbgm MUS_ENCOUNTER_BRENDAN, FALSE
	msgbox UnderdogArena_Text_BrendanIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_BRENDAN_LILYCOVE_TORCHIC
	underdog_battle TRAINER_BRENDAN_LILYCOVE_TORCHIC, UnderdogArena_Text_BrendanDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BrendanMudkip:
	playbgm MUS_ENCOUNTER_BRENDAN, FALSE
	msgbox UnderdogArena_Text_BrendanIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_BRENDAN_LILYCOVE_MUDKIP
	underdog_battle TRAINER_BRENDAN_LILYCOVE_MUDKIP, UnderdogArena_Text_BrendanDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_MayTreecko:
	playbgm MUS_ENCOUNTER_MAY, FALSE
	msgbox UnderdogArena_Text_MayIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_MAY_LILYCOVE_TREECKO
	underdog_battle TRAINER_MAY_LILYCOVE_TREECKO, UnderdogArena_Text_MayDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_MayTorchic:
	playbgm MUS_ENCOUNTER_MAY, FALSE
	msgbox UnderdogArena_Text_MayIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_MAY_LILYCOVE_TORCHIC
	underdog_battle TRAINER_MAY_LILYCOVE_TORCHIC, UnderdogArena_Text_MayDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_MayMudkip:
	playbgm MUS_ENCOUNTER_MAY, FALSE
	msgbox UnderdogArena_Text_MayIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_MAY_LILYCOVE_MUDKIP
	underdog_battle TRAINER_MAY_LILYCOVE_MUDKIP, UnderdogArena_Text_MayDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Brock:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_BrockIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BROCK
	underdog_battle TRAINER_UNDERDOG_BROCK, UnderdogArena_Text_BrockDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Misty:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_MistyIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_MISTY
	underdog_battle TRAINER_UNDERDOG_MISTY, UnderdogArena_Text_MistyDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_LtSurge:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_LtSurgeIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_LT_SURGE
	underdog_battle TRAINER_UNDERDOG_LT_SURGE, UnderdogArena_Text_LtSurgeDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Erika:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_ErikaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_ERIKA
	underdog_battle TRAINER_UNDERDOG_ERIKA, UnderdogArena_Text_ErikaDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Koga:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_KogaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_KOGA
	underdog_battle TRAINER_UNDERDOG_KOGA, UnderdogArena_Text_KogaDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Sabrina:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_SabrinaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_SABRINA
	underdog_battle TRAINER_UNDERDOG_SABRINA, UnderdogArena_Text_SabrinaDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Blaine:
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, FALSE
	msgbox UnderdogArena_Text_BlaineIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BLAINE
	underdog_battle TRAINER_UNDERDOG_BLAINE, UnderdogArena_Text_BlaineDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Giovanni:
	playbgm MUS_RG_ENCOUNTER_ROCKET, FALSE
	msgbox UnderdogArena_Text_GiovanniIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_GIOVANNI
	underdog_battle TRAINER_UNDERDOG_GIOVANNI, UnderdogArena_Text_GiovanniDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Lorelei:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_LoreleiIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_LORELEI
	underdog_battle TRAINER_UNDERDOG_LORELEI, UnderdogArena_Text_LoreleiDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Bruno:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_BrunoIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BRUNO
	underdog_battle TRAINER_UNDERDOG_BRUNO, UnderdogArena_Text_BrunoDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Agatha:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_AgathaIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_AGATHA
	underdog_battle TRAINER_UNDERDOG_AGATHA, UnderdogArena_Text_AgathaDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Lance:
	playbgm MUS_ENCOUNTER_ELITE_FOUR, FALSE
	msgbox UnderdogArena_Text_LanceIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_LANCE
	underdog_battle TRAINER_UNDERDOG_LANCE, UnderdogArena_Text_LanceDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_Red:
	msgbox UnderdogArena_Text_RedIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_RED
	underdog_battle TRAINER_RED, UnderdogArena_Text_RedDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

@ Secret word ORIGINS: Red with his Pokémon Origins team.
UnderdogArena_EventScript_RedOrigins:
	msgbox UnderdogArena_Text_RedIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_RED_ORIGINS
	underdog_battle TRAINER_UNDERDOG_RED_ORIGINS, UnderdogArena_Text_RedDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BlueSquirtle:
	playbgm MUS_RG_ENCOUNTER_RIVAL, FALSE
	msgbox UnderdogArena_Text_BlueIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BLUE_SQUIRTLE
	underdog_battle TRAINER_UNDERDOG_BLUE_SQUIRTLE, UnderdogArena_Text_BlueDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BlueBulbasaur:
	playbgm MUS_RG_ENCOUNTER_RIVAL, FALSE
	msgbox UnderdogArena_Text_BlueIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BLUE_BULBASAUR
	underdog_battle TRAINER_UNDERDOG_BLUE_BULBASAUR, UnderdogArena_Text_BlueDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_BlueCharmander:
	playbgm MUS_RG_ENCOUNTER_RIVAL, FALSE
	msgbox UnderdogArena_Text_BlueIntro, MSGBOX_DEFAULT
	cleartrainerflag TRAINER_UNDERDOG_BLUE_CHARMANDER
	underdog_battle TRAINER_UNDERDOG_BLUE_CHARMANDER, UnderdogArena_Text_BlueDefeat, FALSE
	goto UnderdogArena_EventScript_AfterBattle

UnderdogArena_EventScript_AfterBattle:
	goto_if_eq VAR_UNDERDOG_BATTLE_KIND, SUNDIAL_BATTLE_GAUNTLET, UnderdogArena_EventScript_GauntletAfterBattle
	clearflag B_FLAG_NO_WHITEOUT
	fadescreen FADE_TO_BLACK @ hides the save pause after a lost daily
	special DailyUnderdog_RecordResult
@ Every battle ends on the results card, which goes on to the Hall of Fame (a won
@ daily) or home (anything else).
	special HealPlayerParty
	release
	special DailyUnderdog_ShowResultsCard
	waitstate
	end

@ The gauntlet (src/wildcard_gauntlet.c): a win heals the team, offers a swap
@ (the Battle Factory rule: one of the three you just beat for one of yours), then
@ walks you into the next opponent's stadium. A loss ends the run: the reward if
@ it got far enough, the card, home.
UnderdogArena_EventScript_GauntletAfterBattle:
	clearflag B_FLAG_NO_WHITEOUT
	special Gauntlet_AfterBattle
	goto_if_eq VAR_RESULT, GAUNTLET_LOST, UnderdogArena_EventScript_GauntletRunOver
	special HealPlayerParty
	call_if_eq VAR_RESULT, GAUNTLET_BEAT_RED, UnderdogArena_EventScript_GauntletBeatRed
	special Gauntlet_BufferCleared
	msgbox UnderdogArena_Text_GauntletCleared, MSGBOX_DEFAULT
	msgbox UnderdogArena_Text_GauntletSwapOffer, MSGBOX_YESNO
	goto_if_ne VAR_RESULT, YES, UnderdogArena_EventScript_GauntletNextRound
UnderdogArena_EventScript_GauntletPickTheirs:
	special Gauntlet_ShowTheirs
	msgbox UnderdogArena_Text_GauntletPickTheirs, MSGBOX_DEFAULT
	special ChoosePartyMon
	waitstate
	goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, UnderdogArena_EventScript_GauntletSwapCancelled
	copyvar VAR_0x8005, VAR_0x8004
	special Gauntlet_ShowYours
	msgbox UnderdogArena_Text_GauntletPickYours, MSGBOX_DEFAULT
	special ChoosePartyMon
	waitstate
	goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, UnderdogArena_EventScript_GauntletPickTheirs
	special Gauntlet_DoSwap
	msgbox UnderdogArena_Text_GauntletJoins, MSGBOX_DEFAULT
	goto UnderdogArena_EventScript_GauntletNextRound

UnderdogArena_EventScript_GauntletSwapCancelled:
	special Gauntlet_CancelSwap
UnderdogArena_EventScript_GauntletNextRound:
	special Gauntlet_SetUpRound
	msgbox UnderdogArena_Text_GauntletRound, MSGBOX_DEFAULT
	closemessage
	fadescreen FADE_TO_BLACK
	release
	special DailyUnderdog_WarpToArena
	waitstate
	end

@ Beating Red: his outfit (Gauntlet_AfterBattle unlocked it) and a shiny line
@ from the team that did it. Saved straight away.
UnderdogArena_EventScript_GauntletBeatRed:
	msgbox UnderdogArena_Text_GauntletBeatRed, MSGBOX_DEFAULT
	call UnderdogArena_EventScript_GauntletPickShiny
	special Gauntlet_SaveProgress
	return

UnderdogArena_EventScript_GauntletPickShiny:
	msgbox UnderdogArena_Text_GauntletPickShiny, MSGBOX_DEFAULT
	special ChoosePartyMon
	goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, UnderdogArena_EventScript_GauntletPickShiny
	special Gauntlet_UnlockShinyLine
	playfanfare MUS_OBTAIN_ITEM
	msgbox UnderdogArena_Text_GauntletShinyUnlocked, MSGBOX_DEFAULT
	waitfanfare
	return

UnderdogArena_EventScript_GauntletRunOver:
	msgbox UnderdogArena_Text_GauntletRunOver, MSGBOX_DEFAULT
	special Gauntlet_EarnsShinyLine
	call_if_eq VAR_RESULT, TRUE, UnderdogArena_EventScript_GauntletRewardIntro
	fadescreen FADE_TO_BLACK
	special Gauntlet_SaveProgress
	special HealPlayerParty
	release
	special DailyUnderdog_ShowResultsCard
	waitstate
	end

UnderdogArena_EventScript_GauntletRewardIntro:
	msgbox UnderdogArena_Text_GauntletReward, MSGBOX_DEFAULT
	call UnderdogArena_EventScript_GauntletPickShiny
	return

UnderdogArena_Text_GauntletCleared:
	.string "ROUND {STR_VAR_1} cleared!\n"
	.string "Next up: {STR_VAR_2}.$"

UnderdogArena_Text_GauntletSwapOffer:
	.string "Trade one of yours for one of the\n"
	.string "three you just beat?$"

UnderdogArena_Text_GauntletPickTheirs:
	.string "These are the three you beat.\n"
	.string "Which one do you want?$"

UnderdogArena_Text_GauntletPickYours:
	.string "Now your team. Who makes room\n"
	.string "for {STR_VAR_1}?$"

UnderdogArena_Text_GauntletJoins:
	.string "{STR_VAR_1} joins your team!$"

UnderdogArena_Text_GauntletRound:
	.string "ROUND {STR_VAR_1}: {STR_VAR_2}!$"

UnderdogArena_Text_GauntletBeatRed:
	.string "You beat RED!\p"
	.string "RED's outfit is in your wardrobe.$"

UnderdogArena_Text_GauntletPickShiny:
	.string "Pick one of your team. Its whole\n"
	.string "family can follow you, shiny!$"

UnderdogArena_Text_GauntletShinyUnlocked:
	.string "{STR_VAR_1}'s family can now\n"
	.string "follow you, shiny!$"

UnderdogArena_Text_GauntletRunOver:
	.string "The run ends in ROUND {STR_VAR_1}.$"

UnderdogArena_Text_GauntletReward:
	.string "You made it to ROUND 5 or further!$"

@ Each opponent's own lines from their game: last page of each speech, or the
@ reaction page where the last one is a badge hand-over (DECISIONS). Wallace: intro
@ is the last two pages.
UnderdogArena_Wallace_Text_Intro:
	.string "WALLACE: Who can most elegantly dance\n"
	.string "with their POKéMON in HOENN?\p"
	.string "Show me right here and now!$"

UnderdogArena_Wallace_Text_Defeat:
	.string "You are a truly noble POKéMON\n"
	.string "TRAINER!$"

UnderdogArena_Text_RoxanneIntro:
	.string "I would like to see how much better\n"
	.string "we've become. Let us battle!$"

UnderdogArena_Text_RoxanneDefeat:
	.string "Grr…\n"
	.string "Again, I have lost…$"

UnderdogArena_Text_BrawlyIntro:
	.string "Show me how much higher\n"
	.string "you've gone!$"

UnderdogArena_Text_BrawlyDefeat:
	.string "Wow!\n"
	.string "Swamped again!$"

UnderdogArena_Text_WattsonIntro:
	.string "I'll make sparks fly from you!\n"
	.string "Don't say I didn't warn you!$"

UnderdogArena_Text_WattsonDefeat:
	.string "Oof…\n"
	.string "Our batteries ran dry…$"

UnderdogArena_Text_FlanneryIntro:
	.string "Let's exchange superhot moves\n"
	.string "in another battle!$"

UnderdogArena_Text_FlanneryDefeat:
	.string "Whew!\n"
	.string "On the verge of eruption!$"

UnderdogArena_Text_NormanIntro:
	.string "…No, because we are parent and child,\n"
	.string "we owe it to each other to do the best\l"
	.string "we can. Isn't that right, {PLAYER}?$"

UnderdogArena_Text_NormanDefeat:
	.string "Uh… Haha…\n"
	.string "Maybe that was going too hard…$"

UnderdogArena_Text_WinonaIntro:
	.string "Please, allow me to see your power\n"
	.string "at full flight!$"

UnderdogArena_Text_WinonaDefeat:
	.string "I failed to reach your height again…$"

UnderdogArena_Text_TateAndLizaIntro:
	.string "TATE: Our combination…\n"
	.string "LIZA: We'll show you again and again!$"

UnderdogArena_Text_TateAndLizaDefeat:
	.string "TATE: You and your POKéMON…\n"
	.string "LIZA: It's as if you were siblings!$"

UnderdogArena_Text_JuanIntro:
	.string "I shall be delighted to dance with you\n"
	.string "as often as you wish!$"

UnderdogArena_Text_JuanDefeat:
	.string "Ahahaha, you are the winner!\n"
	.string "You have defeated me again!$"

UnderdogArena_Text_SidneyIntro:
	.string "All right! You and me, let's enjoy\n"
	.string "a battle that can only be staged\l"
	.string "here in the POKéMON LEAGUE!$"

UnderdogArena_Text_SidneyDefeat:
	.string "Well, how do you like that? I lost!\n"
	.string "Eh, it was fun, so it doesn't matter.$"

UnderdogArena_Text_PhoebeIntro:
	.string "So, come on, just try and see if you can\n"
	.string "even inflict damage on my POKéMON!$"

UnderdogArena_Text_PhoebeDefeat:
	.string "Oh, darn.\n"
	.string "I've gone and lost.$"

UnderdogArena_Text_GlaciaIntro:
	.string "It would please me to no end if I could\n"
	.string "go all out against you!$"

UnderdogArena_Text_GlaciaDefeat:
	.string "It's no surprise that my icy skills\n"
	.string "failed to harm you.$"

UnderdogArena_Text_DrakeIntro:
	.string "If you don't, then you will never\n"
	.string "prevail over me!$"

UnderdogArena_Text_DrakeDefeat:
	.string "Superb, it should be said.$"

UnderdogArena_Text_MaxieIntro:
	.string "And show me…\n"
	.string "Show me the full extent of your power!$"

UnderdogArena_Text_MaxieDefeat:
	.string "What makes you so adept at handling\n"
	.string "POKéMON?$"

UnderdogArena_Text_ArchieIntro:
	.string "For the realization of my dream,\n"
	.string "you must disappear now!$"

UnderdogArena_Text_ArchieDefeat:
	.string "What?!\n"
	.string "I lost to a mere child like you?!$"

UnderdogArena_Text_StevenIntro:
	.string "Okay, {PLAYER}{KUN}, if you're going to mount\n"
	.string "a serious challenge, expect the worst!$"

UnderdogArena_Text_StevenDefeat:
	.string "You…\n"
	.string "I had no idea you'd become so strong…$"

UnderdogArena_Text_BrendanIntro:
	.string "BRENDAN: Want to battle to see who's\n"
	.string "been raising POKéMON better?$"

UnderdogArena_Text_BrendanDefeat:
	.string "That stings a bit--I had a head start\n"
	.string "on you as a TRAINER…$"

UnderdogArena_Text_MayIntro:
	.string "MAY: Come on, battle with me, so I can\n"
	.string "check out your POKéMON!$"

UnderdogArena_Text_MayDefeat:
	.string "That battle helped you become this\n"
	.string "strong, {PLAYER}{KUN}, didn't it?$"

UnderdogArena_Text_BrockIntro:
	.string "Fine, then!\n"
	.string "Show me your best!$"

UnderdogArena_Text_BrockDefeat:
	.string "I took you for granted, and so\n"
	.string "I lost.$"

UnderdogArena_Text_MistyIntro:
	.string "My policy is an all-out offensive\n"
	.string "with WATER-type POKéMON!$"

UnderdogArena_Text_MistyDefeat:
	.string "Wow!\n"
	.string "You're too much!$"

UnderdogArena_Text_LtSurgeIntro:
	.string "The same as I'll do to you!$"

UnderdogArena_Text_LtSurgeDefeat:
	.string "Now that's a shocker!$"

UnderdogArena_Text_ErikaIntro:
	.string "Very well, but I shall not lose.$"

UnderdogArena_Text_ErikaDefeat:
	.string "Oh!\n"
	.string "I concede defeat.\l"
	.string "You are remarkably strong.$"

UnderdogArena_Text_KogaIntro:
	.string "Despair to the creeping horror of\n"
	.string "POISON-type POKéMON!$"

UnderdogArena_Text_KogaDefeat:
	.string "Humph!\n"
	.string "You have proven your worth!$"

UnderdogArena_Text_SabrinaIntro:
	.string "I dislike battling, but if you wish,\n"
	.string "I will show you my powers!$"

UnderdogArena_Text_SabrinaDefeat:
	.string "This loss shocks me!\n"
	.string "But, a loss is a loss.$"

UnderdogArena_Text_BlaineIntro:
	.string "Hah!\n"
	.string "You better have BURN HEAL!$"

UnderdogArena_Text_BlaineDefeat:
	.string "I have burned down to nothing!\n"
	.string "Not even ashes remain!$"

UnderdogArena_Text_GiovanniIntro:
	.string "Once more, you shall face\n"
	.string "GIOVANNI, the greatest TRAINER!$"

UnderdogArena_Text_GiovanniDefeat:
	.string "Ha!\n"
	.string "That was a truly intense fight.\l"
	.string "You have won!$"

UnderdogArena_Text_LoreleiIntro:
	.string "Hahaha!\n"
	.string "Are you ready?$"

UnderdogArena_Text_LoreleiDefeat:
	.string "…Things shouldn't be this way!$"

UnderdogArena_Text_BrunoIntro:
	.string "Hoo hah!$"

UnderdogArena_Text_BrunoDefeat:
	.string "Why?\n"
	.string "How could I lose?$"

UnderdogArena_Text_AgathaIntro:
	.string "{PLAYER}! I'll show you how a real\n"
	.string "TRAINER battles!$"

UnderdogArena_Text_AgathaDefeat:
	.string "Oh, my!\n"
	.string "You're something special, child!$"

UnderdogArena_Text_LanceIntro:
	.string "Your LEAGUE challenge ends with\n"
	.string "me, {PLAYER}!$"

UnderdogArena_Text_LanceDefeat:
	.string "I hate to admit it, but you are a\n"
	.string "POKéMON master!$"

@ Red's only line in Gold/Silver and HGSS.
UnderdogArena_Text_RedIntro:
	.string "…$"

UnderdogArena_Text_RedDefeat:
	.string "…$"

UnderdogArena_Text_BlueIntro:
	.string "BLUE: I am the most powerful\n"
	.string "TRAINER in the world!$"

UnderdogArena_Text_BlueDefeat:
	.string "My reign is over already?\n"
	.string "It's not fair!$"
