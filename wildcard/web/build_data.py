# Writes what the web player shows next to the game: data/schedule.json (each
# date's opponent, rule, event and six, read out of the built ROM by the balance
# sim's schedule mode, plus where art.js finds each picture in the player's ROM)
# and art/ (our own drawings only: the title screen's stadium and the wordmark).
#
#   python3 wildcard/web/build_data.py [--start 2026-10-14] [--days 120]
#   python3 wildcard/web/build_data.py --art-table   (then rebuild)
#
# Run it after a build. The ROM plays the dates on a copy of pokeemerald.sav, so
# the rival matches that save's player (a boy meets May). Both outputs are
# generated and gitignored. Trainer pictures and party icons are never hosted:
# the page reads them out of the player's own patched ROM (src/wildcard_web_art.c).
# --art-table rewrites src/data/wildcard_web_art.h, the trainer pictures the ROM
# keeps uncompressed for the page; the normal run stops if it's out of date.
import argparse, datetime, json, os, re, subprocess, sys, time
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(GAME, 'wildcard', 'playtest'))
sys.path.insert(0, os.path.join(GAME, 'wildcard', 'art', 'title'))
import balance  # noqa: E402

SIM_SCHEDULE = 3
ART = os.path.join(HERE, 'art')
EVENTS = {0: '', 1: 'Halloween', 2: 'Christmas', 3: 'Easter'}


def run_rom(start, days):
    """One headless run of the ROM, one schedule line per date."""
    wdir = os.path.join(GAME, 'wildcard', 'playtest', 'runs', 'schedule')
    out = os.path.join(wdir, 'results.csv')
    if os.path.exists(out):
        os.remove(out)
    dates = balance.dates(start, days, 1)
    p = balance.launch(wdir, [(SIM_SCHEDULE, 0, 0, d.year, d.month, d.day) for d in dates])
    t0 = time.time()
    while not os.path.exists(os.path.join(wdir, 'DONE')):
        if p.poll() is not None or time.time() - t0 > 300:
            p.kill()
            sys.exit('the ROM stopped before finishing the schedule: see ' + wdir + '/now.png')
        time.sleep(1)
    p.kill()
    p.wait()
    return open(out).read().splitlines()


def type_list(t1, t2):
    return [t1] if t1 == t2 else [t1, t2]


def parse(lines):
    """The ROM's schedule lines: one per date (opponent, rule, event, your six), then a G| line
    with that date's gauntlet week (draft and the ladder to Red; ReportGauntletWeek)."""
    days, gauntlet = {}, {}
    for line in lines:
        f = line.split('|')
        if f[0] == 'G':
            y, m, d = (int(x) for x in f[1].split('-'))
            star = f.index('*')
            draft = [dict(zip(('species', 'name'), (int(s), n)), types=type_list(t1, t2))
                     for s, n, t1, t2 in (x.split(',') for x in f[4:star])]
            ladder = [{'round': r, 'slot': int(s), 'trainer': n, 'type': t}
                      for r, (s, n, t) in enumerate((x.split(',') for x in f[star + 1:]), 1)]
            gauntlet[f[2]] = {'week': int(f[3]), 'draft': draft, 'ladder': ladder}
            days[f'{y:04d}-{m:02d}-{d:02d}']['week'] = f[2]
            continue
        y, m, d = (int(x) for x in f[0].split('-'))
        team = []
        for mon in f[5:]:
            species, name, t1, t2, moves = mon.split(',')
            team.append({'species': int(species), 'name': name,
                         'types': type_list(t1, t2), 'moves': moves.split('/') if moves else []})
        days[f'{y:04d}-{m:02d}-{d:02d}'] = {'slot': int(f[1]), 'trainer': f[2], 'rule': f[3],
                                            'event': EVENTS.get(int(f[4]), ''), 'team': team}
    return days, gauntlet


def slot_colours():
    """The results card's colour per arena slot (sundial_card.c), as its lighter panel shade."""
    src = open(os.path.join(GAME, 'src', 'sundial_card.c')).read()
    block = src[src.index('sSlotColours[][3]'):]
    block = block[:block.index('};')]
    out = {}
    for slot, r, g, b in re.findall(r'\[\s*(\d+)\] = \{(\d+), (\d+), (\d+)\}', block):
        panel = [min(31, int(c) * 27 // 20 + 2) for c in (r, g, b)]
        out[int(slot)] = '#%02x%02x%02x' % tuple(c * 8 + c // 4 for c in panel)
    return out


def slot_trainers():
    """Arena slot to TRAINER_ constant, from the sim's slot table."""
    sim = open(os.path.join(GAME, 'src', 'wildcard_sim.c')).read()
    return dict((int(s), t) for s, t in re.findall(r'\[\s*(\d+)\] = (TRAINER_\w+),', sim))


def slot_pics():
    """Arena slot to TRAINER_PIC_ constant, via the sim's slot table and trainers.party."""
    party = open(os.path.join(GAME, 'src', 'data', 'trainers.party')).read()
    pics = {}
    for slot, t in slot_trainers().items():
        m = re.search(r'=== ' + t + r' ===\n(?:.*\n)*?Pic: (.+)', party)
        if m:
            pics[slot] = 'TRAINER_PIC_' + m.group(1).strip().upper().replace(' ', '_')
    return pics


def costume_pics():
    """Wardrobe costume id to its TRAINER_PIC_ constant (sCostumes in daily_underdog.c)."""
    src = open(os.path.join(GAME, 'src', 'daily_underdog.c')).read()
    block = src[src.index('sCostumes[] ='):]
    block = block[:block.index('};')]
    return {int(i): pic for i, pic in re.findall(r'\[\s*(\d+)\]\s*=\s*\{[^,]+,[^,]+,\s*(TRAINER_PIC_\w+)', block)}




def art_pics():
    """The trainer pictures the page shows, in the order of the ROM's table: both players, then
    every arena slot's, then every costume's."""
    out = ['TRAINER_PIC_BRENDAN', 'TRAINER_PIC_MAY'] + [p for _, p in sorted(slot_pics().items())] \
        + [p for _, p in sorted(costume_pics().items())]
    return list(dict.fromkeys(out))


ART_TABLE = os.path.join(GAME, 'src', 'data', 'wildcard_web_art.h')


def art_table():
    """src/data/wildcard_web_art.h: an uncompressed copy of each picture in art_pics() (the game's
    own are smol-compressed) and its palette, as src/data/graphics/trainers.h includes them."""
    h = open(os.path.join(GAME, 'src', 'data', 'graphics', 'trainers.h')).read()
    out = ['// Generated by wildcard/web/build_data.py --art-table: the trainer pictures the web',
           '// player shows, uncompressed (src/wildcard_web_art.c). Don\'t edit.', '']
    rows = []
    for i, const in enumerate(art_pics()):
        pic, pal = re.search(r'\[' + const + r'\] =\s*\{\s*\.frontPic = TRAINER_FRONT_PIC\((\w+), (\w+)', h).groups()
        png = re.search(pic + r'\[\] = INCGFX_U32\("([^"]+\.png)"', h).group(1)
        if Image.open(os.path.join(GAME, png)).size != (64, 64):
            sys.exit(f'{png} isn\'t 64x64: art.js reads every trainer picture as 64x64')
        out.append(f'static const u32 sWebPic{i}[] = INCGFX_U32("{png}", ".4bpp");')
        out.append(f'static const u16 sWebPal{i}[] = ' + re.search(pal + r'\[\] = (INC\w+\([^)]*\));', h).group(1) + ';')
        rows.append(f'    {{sWebPic{i}, sWebPal{i}}}, /* {i} {const} */ \\')
    return '\n'.join(out + ['', '#define WEB_TRAINER_PICS { \\'] + rows + ['}', ''])


def gcc(name, code, *args):
    """Compiles a probe against the game's headers (build/NAME.c) and returns the output's path."""
    probe = os.path.join(GAME, 'build', name)
    with open(probe + '.c', 'w') as f:
        f.write(code)
    out = probe + ('.s' if '-S' in args else '.o')
    subprocess.run([os.path.join(os.environ.get('DEVKITARM', '/opt/devkitpro/devkitARM'), 'bin', 'arm-none-eabi-gcc'),
                    *args, '-o', out, '-iquote', 'include', '-DMODERN=1', '-DTESTING=0', '-DEMERALD',
                    '-std=gnu17', '-mthumb', '-mabi=apcs-gnu', '-march=armv4t', probe + '.c'], cwd=GAME, check=True)
    return out


def asm_words(asm):
    # a zero comes out as `.space 4` rather than `.word 0`
    return lambda name: int(re.search(name + r':\s*\.(?:word\s+(\d+)|space\s+4)', asm).group(1) or 0)


def save_layout():
    """Where the web page finds the player's name, gender and costume in a .sav, from the game's own headers."""
    word = asm_words(open(gcc('web_save_layout', '#include "global.h"\n'
                              'const u32 kVars = offsetof(struct SaveBlock1, vars);\n'
                              'const u32 kGender = offsetof(struct SaveBlock2, playerGender);\n'
                              'const u32 kName = offsetof(struct SaveBlock2, playerName);\n', '-S')).read())
    vars_h = open(os.path.join(GAME, 'include', 'constants', 'vars.h')).read()
    var = lambda name: word('kVars') + (int(re.search(r'#define ' + name + r'\s+(0x[0-9A-Fa-f]+)', vars_h).group(1), 16)
                                        - 0x4000) * 2
    return {'gender': word('kGender'), 'name': word('kName'), 'costume': var('VAR_UNDERDOG_COSTUME'),
            'gauntletWeek': var('VAR_GAUNTLET_WEEK'), 'gauntletBest': var('VAR_GAUNTLET_BEST'),
            # the daily record, for the share line
            'lastDaily': var('VAR_UNDERDOG_LAST_DAILY'), 'lastResult': var('VAR_UNDERDOG_LAST_RESULT'),
            'lastCard': var('VAR_UNDERDOG_LAST_CARD'), 'winStreak': var('VAR_UNDERDOG_WIN_STREAK'),
            'playStreak': var('VAR_UNDERDOG_PLAY_STREAK')}


def launch_date():
    """Day #1 for the card's number (LAUNCH_* in include/constants/sundial.h)."""
    h = open(os.path.join(GAME, 'include', 'constants', 'sundial.h')).read()
    return [int(re.search(r'#define LAUNCH_' + k + r'\s+(\d+)', h).group(1)) for k in ('YEAR', 'MONTH', 'DAY')]




def species_layout():
    """Where art.js finds a species' party icon and its palette number in gSpeciesInfo, from the
    game's headers. iconPalIndex is a bitfield, so a probe sets it alone and the object file
    shows which bits it took."""
    word = asm_words(open(gcc('web_species_layout', '#include "global.h"\n#include "pokemon.h"\n'
                              'const u32 kSize = sizeof(struct SpeciesInfo);\n'
                              'const u32 kIcon = offsetof(struct SpeciesInfo, iconSprite);\n', '-S')).read())
    obj = gcc('web_species_pal', '#include "global.h"\n#include "pokemon.h"\n'
              '__attribute__((section(".probe"))) const struct SpeciesInfo kPal = {.iconPalIndex = 7};\n', '-c')
    subprocess.run([os.path.join(os.environ.get('DEVKITARM', '/opt/devkitpro/devkitARM'), 'bin', 'arm-none-eabi-objcopy'),
                    '-O', 'binary', '-j', '.probe', obj, obj + '.bin'], check=True)
    raw = open(obj + '.bin', 'rb').read()
    at = [i for i, b in enumerate(raw) if b]
    if len(at) != 1 or len(raw) != word('kSize'):
        sys.exit('iconPalIndex isn\'t one byte\'s bits: art.js needs a look')
    shift = (raw[at[0]] & -raw[at[0]]).bit_length() - 1
    return {'size': word('kSize'), 'icon': word('kIcon'), 'palByte': at[0], 'palShift': shift}


# The little Pokémon beside the wordmark: one per type, and opponents without one type
# get the baby of their ace.
TYPE_MASCOT = {
    'grass': 'turtwig', 'fire': 'torchic', 'water': 'oshawott', 'electric': 'pincurchin', 'ice': 'snom',
    'rock': 'geodude', 'fighting': 'riolu', 'normal': 'wooloo', 'flying': 'swablu', 'psychic': 'ralts',
    'dark': 'poochyena', 'ghost': 'gastly', 'dragon': 'gible', 'steel': 'beldum', 'poison': 'koffing',
    'ground': 'diglett',
}
OPPONENT_TYPE = {  # by the TRAINER_ constant, without TRAINER_ and UNDERDOG_, longest match wins
    'ROXANNE': 'rock', 'BRAWLY': 'fighting', 'WATTSON': 'electric', 'FLANNERY': 'fire', 'NORMAN': 'normal',
    'WINONA': 'flying', 'TATE_AND_LIZA': 'psychic', 'JUAN': 'water', 'SIDNEY': 'dark', 'PHOEBE': 'ghost',
    'GLACIA': 'ice', 'DRAKE': 'dragon', 'STEVEN': 'steel', 'BROCK': 'rock', 'MISTY': 'water',
    'LT_SURGE': 'electric', 'ERIKA': 'grass', 'KOGA': 'poison', 'SABRINA': 'psychic', 'BLAINE': 'fire',
    'GIOVANNI': 'ground', 'LORELEI': 'ice', 'BRUNO': 'fighting', 'AGATHA': 'ghost', 'LANCE': 'dragon',
}
OWN_MASCOT = {  # the rivals' slots are named for the player's starter, so theirs is the next one round
    'MAXIE': 'numel', 'ARCHIE': 'carvanha', 'WALLACE': 'feebas', 'RED': 'pikachu', 'RED_ORIGINS': 'charmander',
    'BLUE_SQUIRTLE': 'squirtle', 'BLUE_BULBASAUR': 'bulbasaur', 'BLUE_CHARMANDER': 'charmander',
    'BRENDAN_LILYCOVE_TREECKO': 'torchic', 'BRENDAN_LILYCOVE_TORCHIC': 'mudkip', 'BRENDAN_LILYCOVE_MUDKIP': 'treecko',
    'MAY_LILYCOVE_TREECKO': 'torchic', 'MAY_LILYCOVE_TORCHIC': 'mudkip', 'MAY_LILYCOVE_MUDKIP': 'treecko',
}


def mascot(trainer):
    """The mascot's graphics/pokemon folder name for a TRAINER_ constant."""
    name = trainer.removeprefix('TRAINER_').removeprefix('UNDERDOG_')
    best = lambda table: max((k for k in table if name.startswith(k)), key=len, default=None)
    if (k := best(OWN_MASCOT)):
        return OWN_MASCOT[k]
    return TYPE_MASCOT[OPPONENT_TYPE[best(OPPONENT_TYPE)]]




def species_number(name):
    """SPECIES_<NAME>'s number, from include/constants/species.h."""
    consts = open(os.path.join(GAME, 'include', 'constants', 'species.h')).read()
    return int(re.search(r'SPECIES_' + name.upper() + r' = (\d+),', consts).group(1))


HEAD_NUDGE = {'TRAINER_PIC_CHAMPION_WALLACE': (8, 3)}  # his raised arm pulls the face's centre left


def art_index():
    """What art.js needs to draw each picture from the ROM: the table's row for each arena slot,
    costume and player, each slot's mascot species, and the gSpeciesInfo layout."""
    rows = {p: i for i, p in enumerate(art_pics())}
    return {'trainers': {s: rows[p] for s, p in slot_pics().items()},
            'costumes': {c: rows[p] for c, p in costume_pics().items()},
            'players': [rows['TRAINER_PIC_BRENDAN'], rows['TRAINER_PIC_MAY']],
            'nudge': {rows[p]: d for p, d in HEAD_NUDGE.items() if p in rows},
            'mascots': {s: species_number(mascot(t)) for s, t in slot_trainers().items()},
            'species': species_layout()}


def write_art():
    """art/: our own drawings only (build_title.py): the stadium behind the top bar, the wordmark."""
    os.makedirs(ART, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(GAME)  # the title builder reads graphics/ by relative path
    import build_title as bt
    for theme in ('day', 'dusk', 'night'):
        bt.stadium_back(theme).convert('RGBA').save(os.path.join(ART, f'stadium_{theme}.png'))
    colours = bt.SUBTITLE_COLOURS[bt.SUBTITLE_COLOUR]
    wild, card = bt.subtitle_word('WILD', 20, 0, bands=colours[1]), bt.subtitle_word('CARD', 20, 0, bands=colours[2])
    mark = Image.new('RGBA', (wild.width + card.width - 3, max(wild.height, card.height)), (0, 0, 0, 0))
    mark.alpha_composite(wild, (0, 0))
    mark.alpha_composite(card, (wild.width - 3, 0))
    mark.save(os.path.join(ART, 'wordmark.png'))
    os.chdir(cwd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default=(datetime.date.today() - datetime.timedelta(days=7)).isoformat())
    ap.add_argument('--days', type=int, default=120)
    ap.add_argument('--art-table', action='store_true', help='rewrite src/data/wildcard_web_art.h, then rebuild')
    args = ap.parse_args()
    if args.art_table:
        open(ART_TABLE, 'w').write(art_table())
        print(f'wrote {ART_TABLE} ({len(art_pics())} pictures); rebuild the ROM')
        return
    if not os.path.exists(ART_TABLE) or open(ART_TABLE).read() != art_table():
        sys.exit('src/data/wildcard_web_art.h is out of date: run build_data.py --art-table, rebuild, then this')
    days, gauntlet = parse(run_rom(args.start, args.days))
    pics = slot_pics()
    colours = slot_colours()
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    # the rival is the other player character, so a Brendan day means the save plays as May
    rivals = {pics.get(d['slot'], '') for d in days.values()}
    player = 'may' if 'TRAINER_PIC_BRENDAN' in rivals else 'brendan'
    with open(os.path.join(HERE, 'data', 'schedule.json'), 'w') as f:
        json.dump({'built': datetime.datetime.now().isoformat(timespec='seconds'), 'player': player,
                   'save': save_layout(), 'art': art_index(), 'launch': launch_date(),
                   'colours': colours, 'days': days, 'gauntlet': gauntlet}, f, separators=(',', ':'))
    write_art()
    print(f'{len(days)} days from {min(days)} to {max(days)}; art in {ART}')


if __name__ == '__main__':
    main()
