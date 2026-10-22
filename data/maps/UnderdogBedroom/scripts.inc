@ Wardrobe menu id for CHANGE NAME; costume ids come from sCostumes in src/daily_underdog.c.
	.set WARDROBE_CHANGE_NAME, 100

@ Daily Underdog hub. Own layout (LAYOUT_UNDERDOG_BEDROOM); no story objects, no stairs warp.
UnderdogBedroom_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, UnderdogBedroom_OnLoad
	map_script MAP_SCRIPT_ON_TRANSITION, UnderdogBedroom_OnTransition
	map_script MAP_SCRIPT_ON_FRAME_TABLE, UnderdogBedroom_OnFrame
	.byte 0

@ Runs on warps and on Continue (ON_TRANSITION only runs on warps).
UnderdogBedroom_OnLoad:
	setflag FLAG_SYS_B_DASH @ Running Shoes; vanilla gets them from Mom, who we skip
	setflag FLAG_SYS_POKEMON_GET @ POKéMON in the start menu; vanilla sets it with the starter
	setflag FLAG_SYS_POKEDEX_GET @ the POKéDEX is your collection: caught = bought
	special EnableNationalPokedex
	special DailyUnderdog_SetUpRoom @ Continue skips ON_TRANSITION
	setvar VAR_GAUNTLET_ROUND, 0 @ home means no gauntlet run (its team is gone)
	end

@ Coming home (from a battle or the Hall of Fame): swap the battle team for your buddy.
UnderdogBedroom_OnTransition:
	special DailyUnderdog_GiveFollowerParty
	special DailyUnderdog_SetUpRoom
	end

@ Easy in: today's daily, offered on arrival (once per power-on; see DailyUnderdog_ShouldOfferDaily).
UnderdogBedroom_OnFrame:
	map_script_2 VAR_UNDERDOG_COSTUME, 0, UnderdogBedroom_EventScript_FirstBoot
	map_script_2 VAR_TEMP_0, 0, UnderdogBedroom_EventScript_OfferDaily
	.2byte 0

@ A new save has no look yet: pick one of the free outfits (no backing out), then a name.
@ The daily offer follows on the next frame.
UnderdogBedroom_EventScript_FirstBoot::
	lockall
	msgbox UnderdogBedroom_Text_Welcome, MSGBOX_DEFAULT
	message UnderdogBedroom_Text_PickALook
	waitmessage
	special DailyUnderdog_PushFreeCostumes
	dynmultistack 0, 0, TRUE, 6, FALSE, 0, DYN_MULTICHOICE_CB_SHOW_COSTUME
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_SetCostume @ stays black: fading back in and out here flashed the new sprite
	special DailyUnderdog_RenamePlayer
	waitstate
	msgbox UnderdogBedroom_Text_NiceToMeetYou, MSGBOX_DEFAULT
	releaseall
	end

UnderdogBedroom_EventScript_OfferDaily::
	lockall
	setvar VAR_TEMP_0, 1
	special DailyUnderdog_ShouldOfferDaily
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_OfferDailyEnd
	msgbox UnderdogBedroom_Text_OfferDaily, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, UnderdogBedroom_EventScript_OfferDailyEnd
	special DailyUnderdog_TryStartDaily
	goto_if_ne VAR_RESULT, SUNDIAL_RESULT_NONE, UnderdogBedroom_EventScript_OfferDailyEnd
	msgbox UnderdogBedroom_Text_TodaysOpponent, MSGBOX_DEFAULT
	call UnderdogBedroom_EventScript_TodaysRule
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_Save @ the attempt counts from here
	releaseall
	special DailyUnderdog_WarpToArena
	waitstate
	end

UnderdogBedroom_EventScript_OfferDailyEnd::
	closemessage
	releaseall
	end

@ The wall clock without Emerald's Mum scene: set it the first time, then just look.
UnderdogBedroom_EventScript_WallClock::
	lockall
	goto_if_set FLAG_SET_WALL_CLOCK, UnderdogBedroom_EventScript_ViewWallClock
	msgbox UnderdogBedroom_Text_ClockStopped, MSGBOX_DEFAULT
	fadescreen FADE_TO_BLACK
	special StartWallClock
	setflag FLAG_SET_WALL_CLOCK
	releaseall
	end

UnderdogBedroom_EventScript_ViewWallClock::
	fadescreen FADE_TO_BLACK
	special Special_ViewWallClock
	releaseall
	end

UnderdogBedroom_EventScript_GameCube::
	lockall
	message UnderdogBedroom_Text_WhoComesAlong
	waitmessage
	special DailyUnderdog_OpenFollowerPicker
	waitstate
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_GameCubeCancel
	goto_if_eq VAR_UNDERDOG_FOLLOWER, SPECIES_NONE, UnderdogBedroom_EventScript_NoFollower
	special Wildcard_FollowerShinyChoice
	goto_if_eq VAR_RESULT, TRUE, UnderdogBedroom_EventScript_ShinyChoice
	bufferspeciesname STR_VAR_1, VAR_UNDERDOG_FOLLOWER
	msgbox UnderdogBedroom_Text_NowFollowing, MSGBOX_DEFAULT
	releaseall
	end

@ A gauntlet reward line: shiny or normal colours, per species (B keeps it as it is).
UnderdogBedroom_EventScript_ShinyChoice::
	message UnderdogBedroom_Text_ShinyOrNormal
	waitmessage
	dynmultichoice 0, 0, FALSE, 2, VAR_0x8005, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_Shiny, UnderdogBedroom_Text_Normal
	goto_if_eq VAR_RESULT, MULTI_B_PRESSED, UnderdogBedroom_EventScript_ShinyChoiceDone
	copyvar VAR_0x8004, VAR_RESULT
	special Wildcard_SetFollowerShiny
UnderdogBedroom_EventScript_ShinyChoiceDone::
	bufferspeciesname STR_VAR_1, VAR_UNDERDOG_FOLLOWER
	msgbox UnderdogBedroom_Text_NowFollowing, MSGBOX_DEFAULT
	releaseall
	end

UnderdogBedroom_EventScript_NoFollower::
	msgbox UnderdogBedroom_Text_NoFollower, MSGBOX_DEFAULT
	releaseall
	end

@ Your Pokémon lounging around the room (spots 0-4; src/daily_underdog.c, "The room").
UnderdogBedroom_EventScript_RoomMon1::
	setvar VAR_0x8004, 0
	goto UnderdogBedroom_EventScript_RoomMon
UnderdogBedroom_EventScript_RoomMon2::
	setvar VAR_0x8004, 1
	goto UnderdogBedroom_EventScript_RoomMon
UnderdogBedroom_EventScript_RoomMon3::
	setvar VAR_0x8004, 2
	goto UnderdogBedroom_EventScript_RoomMon
UnderdogBedroom_EventScript_RoomMon4::
	setvar VAR_0x8004, 3
	goto UnderdogBedroom_EventScript_RoomMon
UnderdogBedroom_EventScript_RoomMon5::
	setvar VAR_0x8004, 4
	goto UnderdogBedroom_EventScript_RoomMon

UnderdogBedroom_EventScript_RoomMon::
	lock
	faceplayer
	special DailyUnderdog_BufferRoomMon
	playmoncry VAR_0x8005, CRY_MODE_NORMAL
	message UnderdogBedroom_Text_RoomMonLounging
	waitmessage
	waitmoncry
	dynmultichoice 0, 0, FALSE, 2, 0, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_FollowMe, UnderdogBedroom_Text_LeaveIt
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_RoomMonFollow
	closemessage
	release
	end

UnderdogBedroom_EventScript_RoomMonFollow::
	closemessage
	special DailyUnderdog_RoomMonFollow
	bufferspeciesname STR_VAR_1, VAR_UNDERDOG_FOLLOWER
	msgbox UnderdogBedroom_Text_NowFollowing, MSGBOX_DEFAULT
	release
	end

UnderdogBedroom_EventScript_Wardrobe::
	lockall
	message UnderdogBedroom_Text_WardrobeWhatToWear
	waitmessage
	special DailyUnderdog_PushCostumeChoices
	dynmultipush UnderdogBedroom_Text_ChangeName, WARDROBE_CHANGE_NAME
	dynmultistack 0, 0, FALSE, 6, FALSE, 0, DYN_MULTICHOICE_CB_SHOW_COSTUME
	goto_if_eq VAR_RESULT, MULTI_B_PRESSED, UnderdogBedroom_EventScript_GameCubeCancel
	goto_if_eq VAR_RESULT, WARDROBE_CHANGE_NAME, UnderdogBedroom_EventScript_ChangeName
	copyvar VAR_0x8004, VAR_RESULT
	special DailyUnderdog_CheckCostume
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_BuyCostume
UnderdogBedroom_EventScript_WearCostume::
	closemessage
	copyvar VAR_RESULT, VAR_0x8004
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_SetCostume
	special DailyUnderdog_Save @ keeps a new purchase and the look; hidden by the fade
	fadescreen FADE_FROM_BLACK
	releaseall
	end

@ Costumes bought with daily winnings (prices in sCostumes, src/daily_underdog.c).
UnderdogBedroom_EventScript_BuyCostume::
	showmoneybox 0, 0
	msgbox UnderdogBedroom_Text_BuyCostume, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, UnderdogBedroom_EventScript_BuyCostumeEnd
	special DailyUnderdog_BuyCostume
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_CostumeTooPricey
	updatemoneybox
	special DailyUnderdog_CheckCostume @ the money box borrows STR_VAR_1 for the total; buffer the name again
	playse SE_SHOP
	msgbox UnderdogBedroom_Text_BoughtCostume, MSGBOX_DEFAULT
	hidemoneybox
	goto UnderdogBedroom_EventScript_WearCostume

UnderdogBedroom_EventScript_CostumeTooPricey::
	msgbox UnderdogBedroom_Text_CostumeTooPricey, MSGBOX_DEFAULT
UnderdogBedroom_EventScript_BuyCostumeEnd::
	hidemoneybox
	closemessage
	releaseall
	end

UnderdogBedroom_EventScript_ChangeName::
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_RenamePlayer
	waitstate
	releaseall
	end

@ The theme's dolls and cushions (objects 7-9, SetUpRoomDecor in src/daily_underdog.c).
UnderdogBedroom_EventScript_Decor::
	msgbox UnderdogBedroom_Text_Decor, MSGBOX_SIGN
	end

UnderdogBedroom_EventScript_GameCubeCancel::
	closemessage
	releaseall
	end

UnderdogBedroom_EventScript_PC::
	lockall
	setvar VAR_0x8004, PC_LOCATION_BRENDANS_HOUSE
	special DoPCTurnOnEffect
	playse SE_PC_ON
UnderdogBedroom_EventScript_PCMenu::
	message UnderdogBedroom_Text_PCWhatToDo
	waitmessage
	dynmultichoice 0, 0, FALSE, 6, 0, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_DailyBattle, UnderdogBedroom_Text_Gauntlet, UnderdogBedroom_Text_ChooseOpponent, UnderdogBedroom_Text_Shop, UnderdogBedroom_Text_More, UnderdogBedroom_Text_LogOff
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_DailyBattle
	case 1, UnderdogBedroom_EventScript_Gauntlet
	case 2, UnderdogBedroom_EventScript_ChooseOpponent
	case 3, UnderdogBedroom_EventScript_ShopMenu
	case 4, UnderdogBedroom_EventScript_PCMore
	goto UnderdogBedroom_EventScript_PCOff

@ GAUNTLET (src/wildcard_gauntlet.c): this week's six, pick three, then up the
@ Kanto ladder in each opponent's home stadium. The rounds themselves run from
@ the arena script (UnderdogArena_EventScript_GauntletAfterBattle).
UnderdogBedroom_EventScript_Gauntlet::
	special Gauntlet_Status
	goto_if_eq VAR_RESULT, TRUE, UnderdogBedroom_EventScript_GauntletWithBest
	msgbox UnderdogBedroom_Text_GauntletIntro, MSGBOX_YESNO
	goto UnderdogBedroom_EventScript_GauntletAnswer

UnderdogBedroom_EventScript_GauntletWithBest::
	msgbox UnderdogBedroom_Text_GauntletIntroBest, MSGBOX_YESNO
UnderdogBedroom_EventScript_GauntletAnswer::
	goto_if_ne VAR_RESULT, YES, UnderdogBedroom_EventScript_PCOff
	special Gauntlet_StartRun
	msgbox UnderdogBedroom_Text_GauntletPickThree, MSGBOX_DEFAULT
UnderdogBedroom_EventScript_GauntletDraft::
	closemessage
	fadescreen FADE_TO_BLACK
	callnative RemoveFollowingPokemon
	special Gauntlet_SetUpDraft
	special ChoosePartyForBattleFrontier
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_GauntletDraftCancelled
	special ReducePlayerPartyToSelectedMons
	special Gauntlet_SetUpRound
	msgbox UnderdogBedroom_Text_GauntletRound, MSGBOX_DEFAULT
	closemessage
	fadescreen FADE_TO_BLACK
	goto UnderdogBedroom_EventScript_GoToArena

UnderdogBedroom_EventScript_GauntletDraftCancelled::
	msgbox UnderdogBedroom_Text_GauntletCancel, MSGBOX_YESNO
	goto_if_ne VAR_RESULT, YES, UnderdogBedroom_EventScript_GauntletDraft
	setvar VAR_GAUNTLET_ROUND, 0
	special DailyUnderdog_GiveFollowerParty
	goto UnderdogBedroom_EventScript_PCOff

@ SHOP: Pokémon or room colours.
UnderdogBedroom_EventScript_ShopMenu::
	message UnderdogBedroom_Text_PCWhatToDo
	waitmessage
	dynmultichoice 0, 0, FALSE, 3, 0, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_Pkmn, UnderdogBedroom_Text_Rooms, UnderdogBedroom_Text_Back
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_Shop
	case 1, UnderdogBedroom_EventScript_Decorate
	goto UnderdogBedroom_EventScript_PCMenu @ BACK or B

@ Room colours (sRoomThemes, src/daily_underdog.c): wear one you own, or buy it.
UnderdogBedroom_EventScript_Decorate::
	message UnderdogBedroom_Text_WhichColours
	waitmessage
	special DailyUnderdog_PushRoomThemes
	dynmultistack 0, 0, FALSE, 6, FALSE, 0, DYN_MULTICHOICE_CB_NONE
	goto_if_eq VAR_RESULT, MULTI_B_PRESSED, UnderdogBedroom_EventScript_ShopMenu
	copyvar VAR_0x8004, VAR_RESULT
	special DailyUnderdog_CheckRoomTheme
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_BuyRoomTheme
UnderdogBedroom_EventScript_UseRoomTheme::
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_SetRoomTheme
	special DailyUnderdog_Save @ keeps a new purchase and the colours; hidden by the fade
	fadescreen FADE_FROM_BLACK
	goto UnderdogBedroom_EventScript_PCOff

UnderdogBedroom_EventScript_BuyRoomTheme::
	showmoneybox 0, 0
	msgbox UnderdogBedroom_Text_BuyCostume, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, UnderdogBedroom_EventScript_BuyRoomThemeEnd
	special DailyUnderdog_BuyRoomTheme
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_RoomThemeTooPricey
	updatemoneybox
	special DailyUnderdog_CheckRoomTheme @ the money box borrows STR_VAR_1 for the total; buffer the name again
	playse SE_SHOP
	msgbox UnderdogBedroom_Text_BoughtCostume, MSGBOX_DEFAULT
	hidemoneybox
	goto UnderdogBedroom_EventScript_UseRoomTheme

UnderdogBedroom_EventScript_RoomThemeTooPricey::
	msgbox UnderdogBedroom_Text_CostumeTooPricey, MSGBOX_DEFAULT
UnderdogBedroom_EventScript_BuyRoomThemeEnd::
	hidemoneybox
	goto UnderdogBedroom_EventScript_PCOff

@ The extras, a level down so the daily and PRACTICE are the first things you see.
UnderdogBedroom_EventScript_PCMore::
	message UnderdogBedroom_Text_PCWhatToDo
	waitmessage
#ifdef RELEASE
	@ make release: the testing extras (TEST MONEY, TEST DAY) stay out of what players get
	dynmultichoice 0, 0, FALSE, 2, 0, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_FreePlay, UnderdogBedroom_Text_Back
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_FreePlay
#else
	dynmultichoice 0, 0, FALSE, 4, 0, DYN_MULTICHOICE_CB_NONE, UnderdogBedroom_Text_FreePlay, UnderdogBedroom_Text_TestMoney, UnderdogBedroom_Text_TestDay, UnderdogBedroom_Text_Back
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_FreePlay
	case 1, UnderdogBedroom_EventScript_TestMoney
	case 2, UnderdogBedroom_EventScript_TestDay
#endif
	goto UnderdogBedroom_EventScript_PCMenu @ BACK or B

@ Today's random team, then off to Wallace's arena. The battle itself lives in the arena script.
UnderdogBedroom_EventScript_DailyBattle::
	special DailyUnderdog_TryStartDaily
	switch VAR_RESULT
	case SUNDIAL_RESULT_WON, UnderdogBedroom_EventScript_AlreadyWon
	case SUNDIAL_RESULT_LOST, UnderdogBedroom_EventScript_AlreadyLost
	case SUNDIAL_RESULT_IN_PROGRESS, UnderdogBedroom_EventScript_AlreadyStarted
	msgbox UnderdogBedroom_Text_TodaysOpponent, MSGBOX_DEFAULT
	call UnderdogBedroom_EventScript_TodaysRule
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_Save @ the attempt counts from here
	goto UnderdogBedroom_EventScript_GoToArena

@ Rule days (DailyUnderdog_BufferRule): told after the team is handed over.
UnderdogBedroom_EventScript_TodaysRule::
	special DailyUnderdog_BufferRule
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_NoRule
	msgbox UnderdogBedroom_Text_TodaysRule, MSGBOX_DEFAULT
UnderdogBedroom_EventScript_NoRule::
	return

UnderdogBedroom_EventScript_AlreadyWon::
	special DailyUnderdog_BufferTimeToNextDaily
	msgbox UnderdogBedroom_Text_AlreadyWon, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_PCOff

UnderdogBedroom_EventScript_AlreadyLost::
	special DailyUnderdog_BufferTimeToNextDaily
	msgbox UnderdogBedroom_Text_AlreadyLost, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_PCOff

UnderdogBedroom_EventScript_AlreadyStarted::
	msgbox UnderdogBedroom_Text_AlreadyStarted, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_PCOff

UnderdogBedroom_EventScript_GoToArena::
	setvar VAR_0x8004, PC_LOCATION_BRENDANS_HOUSE
	playse SE_PC_OFF
	special DoPCTurnOffEffect
	releaseall
	special DailyUnderdog_WarpToArena @ their own room, or the Champion's Room
	waitstate
	end

@ Free Play: type a word; the word picks the opponent and the team. Never recorded.
UnderdogBedroom_EventScript_FreePlay::
	msgbox UnderdogBedroom_Text_TypeAWord, MSGBOX_DEFAULT
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_EnterSeedWord
	waitstate
	special DailyUnderdog_StartFreePlay
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_PCOff
	msgbox UnderdogBedroom_Text_SeedReady, MSGBOX_DEFAULT
	closemessage
	fadescreen FADE_TO_BLACK
	goto UnderdogBedroom_EventScript_GoToArena

@ Testing: battle anyone on the roster with today's team. Becomes CHOOSE SEED later.
@ Spend daily winnings on followers (src/sundial_shop.c). Bought = caught in the Pokédex.
UnderdogBedroom_EventScript_Shop::
	message UnderdogBedroom_Text_ShopWelcome
	waitmessage
	showmoneybox 0, 0
	special DailyUnderdog_OpenShop
	waitstate
	hidemoneybox
	call_if_eq VAR_RESULT, TRUE, UnderdogBedroom_EventScript_SavePurchase
	goto UnderdogBedroom_EventScript_PCOff

@ Purchases save straight away, so a reset can't lose them.
UnderdogBedroom_EventScript_SavePurchase::
	special DailyUnderdog_Save
	return

@ Testing only: remove before launch (STATUS).
UnderdogBedroom_EventScript_TestMoney::
	addmoney 10000
	showmoneybox 0, 0
	playse SE_SHOP
	msgbox UnderdogBedroom_Text_TestMoneyAdded, MSGBOX_DEFAULT
	hidemoneybox
	goto UnderdogBedroom_EventScript_PCOff

@ Testing only: remove before launch (STATUS). PRACTICE uses the next day's team.
UnderdogBedroom_EventScript_TestDay::
	special DailyUnderdog_NextTestDay
	msgbox UnderdogBedroom_Text_TestDayMoved, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_PCOff

UnderdogBedroom_EventScript_ChooseOpponent::
	message UnderdogBedroom_Text_WhoToBattle
	waitmessage
	special DailyUnderdog_PushOpponentChoices
	dynmultistack 0, 0, FALSE, 6, FALSE, 0, DYN_MULTICHOICE_CB_SHOW_TRAINER
	goto_if_eq VAR_RESULT, MULTI_B_PRESSED, UnderdogBedroom_EventScript_PCOff
	special DailyUnderdog_GiveTeamVsChosenOpponent
	closemessage
	goto UnderdogBedroom_EventScript_GoToArena

@ The TV: today's POKéMON WILD CARD broadcast (DailyUnderdog_TVBroadcast). VAR_0x8005 is
@ today's event (1 Easter, 2 Halloween, 3 Christmas); VAR_RESULT what's on (TV_* in C).
UnderdogBedroom_EventScript_TV::
	lockall
	special DailyUnderdog_TVBroadcast
	call_if_eq VAR_0x8005, 1, UnderdogBedroom_EventScript_TVEaster
	call_if_eq VAR_0x8005, 2, UnderdogBedroom_EventScript_TVHalloween
	call_if_eq VAR_0x8005, 3, UnderdogBedroom_EventScript_TVChristmas
	switch VAR_RESULT
	case 0, UnderdogBedroom_EventScript_TVComingUp
	case 1, UnderdogBedroom_EventScript_TVChampionDay
	case 2, UnderdogBedroom_EventScript_TVYouWon
	msgbox UnderdogBedroom_Text_TVYouLost, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_TVGauntlet

UnderdogBedroom_EventScript_TVComingUp::
	msgbox UnderdogBedroom_Text_TVComingUp, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_TVRule

UnderdogBedroom_EventScript_TVChampionDay::
	msgbox UnderdogBedroom_Text_TVChampionDay, MSGBOX_DEFAULT
	goto UnderdogBedroom_EventScript_TVRule

UnderdogBedroom_EventScript_TVYouWon::
	playfanfare MUS_OBTAIN_BADGE
	msgbox UnderdogBedroom_Text_TVYouWon, MSGBOX_DEFAULT
	waitfanfare
	goto UnderdogBedroom_EventScript_TVGauntlet

@ Before today's daily: the rule, if there is one.
UnderdogBedroom_EventScript_TVRule::
	special DailyUnderdog_BufferRule
	goto_if_eq VAR_RESULT, FALSE, UnderdogBedroom_EventScript_TVGauntlet
	msgbox UnderdogBedroom_Text_TVRule, MSGBOX_DEFAULT
@ Every broadcast ends on the gauntlet.
UnderdogBedroom_EventScript_TVGauntlet::
	special Gauntlet_Status
	goto_if_eq VAR_RESULT, TRUE, UnderdogBedroom_EventScript_TVGauntletBest
	msgbox UnderdogBedroom_Text_TVGauntletOpen, MSGBOX_DEFAULT
	releaseall
	end

UnderdogBedroom_EventScript_TVGauntletBest::
	msgbox UnderdogBedroom_Text_TVGauntletBest, MSGBOX_DEFAULT
	releaseall
	end

UnderdogBedroom_EventScript_TVEaster::
	msgbox UnderdogBedroom_Text_TVEaster, MSGBOX_DEFAULT
	return

UnderdogBedroom_EventScript_TVHalloween::
	msgbox UnderdogBedroom_Text_TVHalloween, MSGBOX_DEFAULT
	return

UnderdogBedroom_EventScript_TVChristmas::
	msgbox UnderdogBedroom_Text_TVChristmas, MSGBOX_DEFAULT
	return

@ Your record. The game's own notebook script used to sit here.
UnderdogBedroom_EventScript_Notebook::
	lockall
	showmoneybox 0, 0
	buffernumberstring STR_VAR_1, VAR_UNDERDOG_WINS
	buffernumberstring STR_VAR_2, VAR_UNDERDOG_LOSSES
	msgbox UnderdogBedroom_Text_NotebookRecord, MSGBOX_DEFAULT
	buffernumberstring STR_VAR_1, VAR_UNDERDOG_WIN_STREAK
	buffernumberstring STR_VAR_2, VAR_UNDERDOG_PLAY_STREAK
	msgbox UnderdogBedroom_Text_NotebookStreaks, MSGBOX_DEFAULT
	special Gauntlet_Status
	call_if_eq VAR_RESULT, TRUE, UnderdogBedroom_EventScript_NotebookGauntlet
	hidemoneybox
	msgbox UnderdogBedroom_Text_NotebookTrophies, MSGBOX_YESNO
	goto_if_ne VAR_RESULT, YES, UnderdogBedroom_EventScript_NotebookEnd
	closemessage
	fadescreen FADE_TO_BLACK
	special DailyUnderdog_ShowTrophyWall
	waitstate
UnderdogBedroom_EventScript_NotebookEnd::
	releaseall
	end

UnderdogBedroom_EventScript_NotebookGauntlet::
	msgbox UnderdogBedroom_Text_NotebookGauntlet, MSGBOX_DEFAULT
	return

UnderdogBedroom_EventScript_PCOff::
	closemessage
	setvar VAR_0x8004, PC_LOCATION_BRENDANS_HOUSE
	playse SE_PC_OFF
	special DoPCTurnOffEffect
	releaseall
	end

UnderdogBedroom_EventScript_StairsBox::
	msgbox UnderdogBedroom_Text_StairsBox, MSGBOX_SIGN
	end

UnderdogBedroom_Text_StairsBox:
	.string "A tower of moving boxes blocks\n"
	.string "the stairs.\p"
	.string "Nobody's unpacking these until\n"
	.string "today's battle is done.$"

UnderdogBedroom_Text_PCWhatToDo:
	.string "{PLAYER} booted up the PC.\n"
	.string "What's the plan?$"

UnderdogBedroom_Text_DailyBattle:
	.string "DAILY BATTLE$"

UnderdogBedroom_Text_FreePlay:
	.string "FREE PLAY$"

UnderdogBedroom_Text_TypeAWord:
	.string "Type any word. The same word gives\n"
	.string "everyone the same battle.$"

UnderdogBedroom_Text_SeedReady:
	.string "Seed {STR_VAR_1}.\n"
	.string "Here's your team. Good luck!$"

UnderdogBedroom_Text_Shop:
	.string "SHOP$"

UnderdogBedroom_Text_Pkmn:
	.string "{PKMN}$"

UnderdogBedroom_Text_Rooms:
	.string "ROOMS$"

UnderdogBedroom_Text_WhichColours:
	.string "Which look for the room?$"

UnderdogBedroom_Text_ShopWelcome:
	.string "Who's coming home with you?$"

UnderdogBedroom_Text_NoFollower:
	.string "Nobody's following you now.$"

UnderdogBedroom_Text_BuyCostume:
	.string "Buy {STR_VAR_1} for ¥{STR_VAR_2}?$"

UnderdogBedroom_Text_BoughtCostume:
	.string "{STR_VAR_1} is yours!$"

UnderdogBedroom_Text_CostumeTooPricey:
	.string "Not enough money yet.\nWin some dailies first!$"

UnderdogBedroom_Text_RoomMonLounging:
	.string "{STR_VAR_1} is lounging around.$"

UnderdogBedroom_Text_FollowMe:
	.string "FOLLOW ME$"

UnderdogBedroom_Text_LeaveIt:
	.string "LEAVE IT$"

UnderdogBedroom_Text_More:
	.string "MORE...$"

UnderdogBedroom_Text_Back:
	.string "BACK$"

UnderdogBedroom_Text_TestMoney:
	.string "TEST MONEY$"

UnderdogBedroom_Text_TestDay:
	.string "TEST DAY$"

UnderdogBedroom_Text_TestDayMoved:
	.string "PRACTICE now uses the team for\n{STR_VAR_1}, until you turn off.$"

UnderdogBedroom_Text_TestMoneyAdded:
	.string "Added ¥10000 for testing.$"

UnderdogBedroom_Text_ClockStopped:
	.string "The clock's stopped.\nBetter set it.$"

UnderdogBedroom_Text_ChooseOpponent:
	.string "PRACTICE$"

UnderdogBedroom_Text_Gauntlet:
	.string "GAUNTLET$"

UnderdogBedroom_Text_NotebookTrophies:
	.string "Look at the trophy wall?$"

UnderdogBedroom_Text_NotebookGauntlet:
	.string "GAUNTLET, week {STR_VAR_1}: best ROUND\n"
	.string "{STR_VAR_2}. Furthest ever: ROUND {STR_VAR_3}.$"

UnderdogBedroom_Text_GauntletIntro:
	.string "GAUNTLET, WEEK {STR_VAR_1}.\n"
	.string "Draft three POKéMON and climb the\l"
	.string "KANTO LEAGUE. RED waits in ROUND 10.\p"
	.string "Lose and the run ends. Retry as\n"
	.string "often as you like. Start a run?$"

UnderdogBedroom_Text_GauntletIntroBest:
	.string "GAUNTLET, WEEK {STR_VAR_1}.\n"
	.string "Your best this week: ROUND {STR_VAR_2}.\p"
	.string "Start a run?$"

UnderdogBedroom_Text_GauntletPickThree:
	.string "This week's six. Everyone gets the\n"
	.string "same draft. Pick three!$"

UnderdogBedroom_Text_GauntletRound:
	.string "ROUND {STR_VAR_1}: {STR_VAR_2}!$"

UnderdogBedroom_Text_GauntletCancel:
	.string "Leave the GAUNTLET for now?$"

UnderdogBedroom_Text_LogOff:
	.string "LOG OFF$"

UnderdogBedroom_Text_OfferDaily:
	.string "Today's opponent: {STR_VAR_1}.\n"
	.string "Battle now?$"

UnderdogBedroom_Text_TodaysRule:
	.string "Today's rule: {STR_VAR_2}!\p"
	.string "{STR_VAR_3}$"

UnderdogBedroom_Text_TodaysOpponent:
	.string "Today's opponent is waiting\n"
	.string "in the arena.\p"
	.string "Here's your team. Good luck!$"

UnderdogBedroom_Text_AlreadyWon:
	.string "You beat today's opponent!\n"
	.string "Next daily in {STR_VAR_3}.$"

UnderdogBedroom_Text_AlreadyLost:
	.string "Today's battle is over.\n"
	.string "Next daily in {STR_VAR_3}.$"

UnderdogBedroom_Text_AlreadyStarted:
	.string "You walked out of today's battle,\n"
	.string "so it counts as a loss.\p"
	.string "Come back tomorrow!$"

UnderdogBedroom_Text_WhoToBattle:
	.string "Who do you want to battle?$"

UnderdogBedroom_Text_WhoComesAlong:
	.string "Who's tagging along today?$"

UnderdogBedroom_Text_Decor:
	.string "It's soft and squishy. It came\n"
	.string "with the room.$"

UnderdogBedroom_Text_NowFollowing:
	.string "{STR_VAR_1} is following you now!$"

UnderdogBedroom_Text_ShinyOrNormal:
	.string "{STR_VAR_1} can wear its shiny\ncolours. Which look today?$"

UnderdogBedroom_Text_Shiny:
	.string "SHINY$"

UnderdogBedroom_Text_Normal:
	.string "NORMAL$"

UnderdogBedroom_Text_Welcome:
	.string "Welcome to POKéMON WILD CARD!\p"
	.string "One battle a day, a random team,\n"
	.string "one shot. Win it and you get paid.\p"
	.string "First things first: who are you?\n"
	.string "Pick a look, then a name.$"

UnderdogBedroom_Text_PickALook:
	.string "Pick a look.$"

UnderdogBedroom_Text_NiceToMeetYou:
	.string "Nice to meet you, {PLAYER}!\p"
	.string "The wardrobe changes your look or\n"
	.string "name whenever you like.$"

UnderdogBedroom_Text_WardrobeWhatToWear:
	.string "Pick an outfit.$"

UnderdogBedroom_Text_ChangeName:
	.string "CHANGE NAME$"

UnderdogBedroom_Text_NotebookRecord:
	.string "DAILY BATTLES\n"
	.string "Won: {STR_VAR_1}   Lost: {STR_VAR_2}$"

UnderdogBedroom_Text_NotebookStreaks:
	.string "Win streak: {STR_VAR_1}\n"
	.string "Days in a row: {STR_VAR_2}$"

UnderdogBedroom_Text_TVRule:
	.string "And today's twist: {STR_VAR_2}!$"

UnderdogBedroom_Text_TVGauntletOpen:
	.string "Over in the GAUNTLET, the KANTO\n"
	.string "LEAGUE waits. Can anyone reach RED\l"
	.string "this week?$"

UnderdogBedroom_Text_TVGauntletBest:
	.string "And in the GAUNTLET this week, your\n"
	.string "best run reached ROUND {STR_VAR_2}!$"

UnderdogBedroom_Text_TVComingUp:
	.string "POKéMON WILD CARD is on!\p"
	.string "Today {STR_VAR_1} faces an\n"
	.string "underdog with a random team!\p"
	.string "Can the underdog pull it off?\n"
	.string "Tune in at your PC!$"

UnderdogBedroom_Text_TVChampionDay:
	.string "It's CHAMPION day on\n"
	.string "POKéMON WILD CARD!\p"
	.string "{STR_VAR_1} is waiting for a\n"
	.string "challenger brave enough!\p"
	.string "Will anyone take the title?\n"
	.string "Tune in at your PC!$"

UnderdogBedroom_Text_TVYouWon:
	.string "Breaking news on\n"
	.string "POKéMON WILD CARD!\p"
	.string "{PLAYER} beat {STR_VAR_1}\n"
	.string "with a random team!\p"
	.string "Win streak: {STR_VAR_2}.\n"
	.string "Next challenge in {STR_VAR_3}.$"

UnderdogBedroom_Text_TVYouLost:
	.string "POKéMON WILD CARD results:\p"
	.string "{STR_VAR_1} stays unbeaten today!\p"
	.string "Better luck next time, {PLAYER}!\n"
	.string "Next challenge in {STR_VAR_3}.$"

UnderdogBedroom_Text_TVEaster:
	.string "Happy EASTER from\n"
	.string "POKéMON WILD CARD!\p"
	.string "A special battle is on today!$"

UnderdogBedroom_Text_TVHalloween:
	.string "Happy HALLOWEEN from\n"
	.string "POKéMON WILD CARD!\p"
	.string "Something spooky is on today…$"

UnderdogBedroom_Text_TVChristmas:
	.string "Merry CHRISTMAS from\n"
	.string "POKéMON WILD CARD!\p"
	.string "A festive battle is on today!$"
