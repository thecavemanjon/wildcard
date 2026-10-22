# Renders the Emerald rooms that could seed a stadium, for a look.
import sys; sys.path.insert(0, '../arenas')
import mapkit as mk
for m in ['BattleFrontier_BattleDomeBattleRoom', 'ContestHall', 'LilycoveCity_ContestHall', 'BattleFrontier_BattleTowerBattleRoom',
          'BattleFrontier_BattleFactoryBattleRoom', 'BattleTentBattleRoom', 'BattleColosseum_2P', 'BattleColosseum_4P',
          'BattleFrontier_BattlePikeRoomFinal', 'TrainerHill_Roof', 'BattleFrontier_BattleDomePreBattleRoom', 'BattleFrontier_BattleDomeLobby',
          'SootopolisCity_LegendsBattle', 'EverGrandeCity_PokemonLeague_1F', 'BattleFrontier_RankingHall', 'BattleFrontier_BattlePyramidTop']:
    try:
        lid, _ = mk.map_layout(m)
    except FileNotFoundError:
        lid = 'LAYOUT_' + m.upper()
    try:
        kit, g = mk.layout(lid)
        mk.label(kit.render(g), f'{m} ({len(g[0])}x{len(g)})', 2).save(f'out/survey_{m}.png')
        print('ok', m)
    except Exception as e: print('FAIL', m, lid, e)
