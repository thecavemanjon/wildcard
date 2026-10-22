# Writes what the web player shows next to the game: data/schedule.json (each
# date's opponent, rule, event and six, read out of the built ROM by the balance
# sim's schedule mode) and art/ (the title screen's stadium and wordmark, trainer
# pictures, party icons, type badges).
#
#   python3 wildcard/web/build_data.py [--start 2026-10-14] [--days 120]
#
# Run it after a build. The ROM plays the dates on a copy of pokeemerald.sav, so
# the rival matches that save's player (a boy meets May). Both outputs are
# generated and gitignored: art/ is Nintendo's, for local testing only. The
# public site will read sprites from the player's own ROM instead.
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


def parse(lines):
    days = {}
    for line in lines:
        f = line.split('|')
        y, m, d = (int(x) for x in f[0].split('-'))
        team = []
        for mon in f[5:]:
            species, name, t1, t2, moves = mon.split(',')
            team.append({'species': int(species), 'name': name,
                         'types': [t1] if t1 == t2 else [t1, t2], 'moves': moves.split('/') if moves else []})
        days[f'{y:04d}-{m:02d}-{d:02d}'] = {'slot': int(f[1]), 'trainer': f[2], 'rule': f[3],
                                            'event': EVENTS.get(int(f[4]), ''), 'team': team}
    return days


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


def slot_pics():
    """Arena slot to trainer picture file, via the sim's slot table and trainers.party."""
    sim = open(os.path.join(GAME, 'src', 'wildcard_sim.c')).read()
    trainers = dict((int(s), t) for s, t in re.findall(r'\[\s*(\d+)\] = (TRAINER_\w+),', sim))
    party = open(os.path.join(GAME, 'src', 'data', 'trainers.party')).read()
    pics = {}
    for slot, t in trainers.items():
        m = re.search(r'=== ' + t + r' ===\n(?:.*\n)*?Pic: (.+)', party)
        if m:
            pics[slot] = m.group(1).strip().lower().replace(' ', '_') + '.png'
    return pics


def costume_pics():
    """Wardrobe costume id to its TRAINER_PIC_ constant (sCostumes in daily_underdog.c)."""
    src = open(os.path.join(GAME, 'src', 'daily_underdog.c')).read()
    block = src[src.index('sCostumes[] ='):]
    block = block[:block.index('};')]
    return {int(i): pic for i, pic in re.findall(r'\[\s*(\d+)\]\s*=\s*\{[^,]+,[^,]+,\s*(TRAINER_PIC_\w+)', block)}


def trainer_pic(const):
    """A TRAINER_PIC_ constant's front picture with its palette, from src/data/graphics/trainers.h."""
    h = open(os.path.join(GAME, 'src', 'data', 'graphics', 'trainers.h')).read()
    pic, pal = re.search(r'\[' + const + r'\] =\s*\{\s*\.frontPic = TRAINER_FRONT_PIC\((\w+), (\w+)\)', h).groups()
    path = lambda sym: os.path.join(GAME, re.search(sym + r'\[\] = INCGFX_U\d+\("([^"]+)"', h).group(1))
    im = Image.open(path(pic))
    if path(pal).endswith('.pal'):  # JASC-PAL: three header lines, then "r g b" per colour
        im.putpalette([int(v) for line in open(path(pal)).read().split('\n')[3:] for v in line.split()])
    return im


def save_layout():
    """Where the web page finds the player's gender and costume in a .sav, from the game's own headers."""
    probe = os.path.join(GAME, 'build', 'web_save_layout')
    with open(probe + '.c', 'w') as f:
        f.write('#include "global.h"\n'
                'const u32 kVars = offsetof(struct SaveBlock1, vars);\n'
                'const u32 kGender = offsetof(struct SaveBlock2, playerGender);\n')
    subprocess.run([os.path.join(os.environ.get('DEVKITARM', '/opt/devkitpro/devkitARM'), 'bin', 'arm-none-eabi-gcc'),
                    '-S', '-o', probe + '.s', '-iquote', 'include', '-DMODERN=1', '-DTESTING=0', '-DEMERALD',
                    '-std=gnu17', '-mthumb', '-mabi=apcs-gnu', '-march=armv4t', probe + '.c'], cwd=GAME, check=True)
    asm = open(probe + '.s').read()
    word = lambda name: int(re.search(name + r':\s*\.word\s+(\d+)', asm).group(1))
    vars_h = open(os.path.join(GAME, 'include', 'constants', 'vars.h')).read()
    costume_var = int(re.search(r'#define VAR_UNDERDOG_COSTUME\s+(0x[0-9A-Fa-f]+)', vars_h).group(1), 16)
    return {'gender': word('kGender'), 'costume': word('kVars') + (costume_var - 0x4000) * 2}


def transparent(path, box=None):
    """A sprite with palette index 0 made transparent, trimmed (as the game draws it). Takes a path or an image."""
    im = path if isinstance(path, Image.Image) else Image.open(path)
    if box:
        im = im.crop(box)
    rgba = im.convert('RGBA')
    if im.mode == 'P':
        px, out = im.load(), rgba.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y] == 0:
                    out[x, y] = (0, 0, 0, 0)
    return rgba


HEAD = 30
HEAD_NUDGE = {'champion_wallace.png': (8, 3)}  # his raised arm pulls the centre left


def head(pic, name):
    """A square crop around the trainer's face, for the fixtures line."""
    a = pic.getchannel('A').load()
    top = next(y for y in range(pic.height) if any(a[x, y] for x in range(pic.width)))
    xs = [x for y in range(top + 6, min(pic.height, top + 20)) for x in range(pic.width) if a[x, y]]
    dx, dy = HEAD_NUDGE.get(name, (0, 0))
    cx, top = round(sum(xs) / len(xs)) + dx, top + dy
    out = Image.new('RGBA', (HEAD, HEAD), (0, 0, 0, 0))
    out.alpha_composite(pic.crop((cx - HEAD // 2, top, cx + HEAD // 2, top + HEAD)))
    return out


def species_folder(species):
    """graphics/pokemon/<name>/ for a species number, forms as a subfolder (DUGTRIO_ALOLA -> dugtrio/alola)."""
    consts = open(os.path.join(GAME, 'include', 'constants', 'species.h')).read()
    name = next((n for n, v in re.findall(r'SPECIES_(\w+) = (\d+),', consts) if int(v) == species), None)
    if name is None:
        return None
    base = os.path.join(GAME, 'graphics', 'pokemon')
    parts = name.lower().split('_')
    for cut in range(len(parts), 0, -1):
        folder = os.path.join(base, '_'.join(parts[:cut]), *parts[cut:])
        if os.path.exists(os.path.join(folder, 'icon.png')):
            return folder
    return None


def write_art(days, pics):
    os.makedirs(ART, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(GAME)  # the title builder reads graphics/ by relative path
    import build_title as bt
    for theme in ('day', 'dusk', 'night'):
        bt.stadium_back(theme).convert('RGBA').save(os.path.join(ART, f'stadium_{theme}.png'))
        bt.stadium_clouds(theme).save(os.path.join(ART, f'clouds_{theme}.png'))
    colours = bt.SUBTITLE_COLOURS[bt.SUBTITLE_COLOUR]
    wild, card = bt.subtitle_word('WILD', 20, 0, bands=colours[1]), bt.subtitle_word('CARD', 20, 0, bands=colours[2])
    mark = Image.new('RGBA', (wild.width + card.width - 3, max(wild.height, card.height)), (0, 0, 0, 0))
    mark.alpha_composite(wild, (0, 0))
    mark.alpha_composite(card, (wild.width - 3, 0))
    mark.save(os.path.join(ART, 'wordmark.png'))
    os.chdir(cwd)

    front = os.path.join(GAME, 'graphics', 'trainers', 'front_pics')
    for slot, file in sorted(pics.items()):
        if os.path.exists(os.path.join(front, file)):
            pic = transparent(os.path.join(front, file))
            pic.save(os.path.join(ART, f'trainer_{slot}.png'))
            head(pic, file).save(os.path.join(ART, f'head_{slot}.png'))
    for who in ('brendan', 'may'):
        transparent(os.path.join(front, f'{who}.png')).save(os.path.join(ART, f'player_{who}.png'))
    for costume, const in costume_pics().items():
        transparent(trainer_pic(const)).save(os.path.join(ART, f'costume_{costume}.png'))

    types = set()
    for species in sorted({m['species'] for day in days.values() for m in day['team']}):
        folder = species_folder(species)
        if folder:
            transparent(os.path.join(folder, 'icon.png'), (0, 0, 32, 32)).save(os.path.join(ART, f'icon_{species}.png'))
    for day in days.values():
        for m in day['team']:
            types.update(m['types'])
    for t in types:
        file = {'fighting': 'fight'}.get(t.lower(), t.lower())
        path = os.path.join(GAME, 'graphics', 'types', file + '.png')
        if os.path.exists(path):
            transparent(path).save(os.path.join(ART, f'type_{t.lower()}.png'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default=(datetime.date.today() - datetime.timedelta(days=7)).isoformat())
    ap.add_argument('--days', type=int, default=120)
    args = ap.parse_args()
    days = parse(run_rom(args.start, args.days))
    pics = slot_pics()
    colours = slot_colours()
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    # the rival is the other player character, so a Brendan day means the save plays as May
    rivals = {pics.get(d['slot'], '') for d in days.values()}
    player = 'may' if 'brendan.png' in rivals else 'brendan'
    with open(os.path.join(HERE, 'data', 'schedule.json'), 'w') as f:
        json.dump({'built': datetime.datetime.now().isoformat(timespec='seconds'), 'player': player,
                   'costumes': sorted(costume_pics()), 'save': save_layout(),
                   'colours': colours, 'days': days}, f, separators=(',', ':'))
    write_art(days, pics)
    print(f'{len(days)} days from {min(days)} to {max(days)}; art in {ART}')


if __name__ == '__main__':
    main()
