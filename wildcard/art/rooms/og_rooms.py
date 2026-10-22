# Themed bedrooms that stay in Emerald's style (DECISIONS 2026-10-20 "Rooms
# closer to the original"): the real bedroom render with its own palette slots
# recoloured (wall, floor, rug: the slots the room colours already change, so
# they cost no tiles), plus Emerald's own decoration art (secret base dolls and
# cushions, furniture lifted from Hoenn houses) and a small window on the free
# wall tile that follows the clock.
#   python3 og_rooms.py [name ...]   -> out/og_<name>_<time>.gif, out/og_<name>.png
import sys, os, math
from PIL import Image
from roomkit import mk, put, rect, sky, ramp, shade, mix, save_gif, tile_budget, stamp_mon, stamp_player, T, TIMES, HERE

# Palette slots in the bedroom (src/daily_underdog.c, ROOM_PAL_MAIN / ROOM_PAL_TRIM)
PAL_MAIN, PAL_TRIM = 6, 9
FLOOR_SLOTS, WALL_SLOTS, RUG_SLOTS = (7, 8, 5, 6), (3, 9), (10, 11, 12)
SPOTS = [(2, 4), (4, 4), (5, 6), (8, 2), (1, 6)]
START = (3, 3)

def base(floor=None, wall=None, rug=None):
    """The bedroom exactly as the game draws it, with its theme colours swapped."""
    k, g = mk.layout('LAYOUT_UNDERDOG_BEDROOM')
    pals = [list(p) for p in k.pals]
    for slots, cols, pal_ids in ((FLOOR_SLOTS, floor, (PAL_MAIN, PAL_TRIM)), (WALL_SLOTS, wall, (PAL_MAIN, PAL_TRIM)), (RUG_SLOTS, rug, (PAL_MAIN,))):
        if not cols: continue
        for p in pal_ids:
            for s, c in zip(slots, cols): pals[p][s] = c
    img = k.render(g, pals=pals)
    # The stairwell moves right (x 108-134 -> 116-142) so the window gets a whole tile.
    door = img.crop((DOOR_X0, 0, DOOR_X1, 32))
    wall = img.crop((100, 0, 101, 32))
    for x in range(DOOR_X0, PWIDTH): img.paste(wall, (x, 0))
    img.paste(door, (DOOR_TO, 0))
    return img

DOOR_X0, DOOR_X1, PWIDTH, DOOR_TO = 108, 134, 144, 116
BOX_TILE = (8, 1)   # the moving boxes follow the stairs (map.json had them at 7, 1)

# ---- Emerald art ------------------------------------------------------------------------------
def doll(name, big=False):
    return mk.person(f'graphics/object_events/pics/dolls/{name}_doll.png' if not big else f'graphics/object_events/pics/dolls/big_{name}_doll.png',
                     32 if big else 16, 32 if big else 16)

def cushion(name):
    return mk.person(f'graphics/object_events/pics/cushions/{name}_cushion.png', 16, 16)

_HOUSE = None
def house_top():
    """Top layer of Rustboro's house: a bookshelf, cabinets, a table and chairs, potted plants."""
    global _HOUSE
    if _HOUSE is None:
        k, g = mk.layout('LAYOUT_RUSTBORO_CITY_HOUSE')
        Hh, Ww = len(g), len(g[0])
        tmp = Image.new('RGB', (Ww * T, Hh * T), (255, 0, 255))
        for y in range(Hh):
            for x in range(Ww):
                m = k.mets[g[y][x] & 0x3FF]
                for i in range(4): k.tile(tmp, m[4 + i], x * T + (i % 2) * 8, y * T + (i // 2) * 8, k.pals)
        out = Image.new('RGBA', tmp.size, (0, 0, 0, 0)); px, o = tmp.load(), out.load()
        for y in range(tmp.height):
            for x in range(tmp.width):
                if px[x, y] != (255, 0, 255): o[x, y] = px[x, y] + (255,)
        _HOUSE = out
    return _HOUSE

def plant():     return house_top().crop((0, 104, 16, 144))
def bookshelf(): return house_top().crop((0, 0, 32, 32))
def cabinet():   return house_top().crop((160, 0, 192, 32))
def stool():     return house_top().crop((64, 64, 80, 80))

def put_spr(img, spr, x, y):
    img.paste(spr, (x, y), spr)

def recolour(spr, pairs):
    out = spr.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3] == 0: continue
            for f, t_ in pairs:
                if sum(abs(c[i] - f[i]) for i in range(3)) < 40: px[x, y] = tuple(t_) + (255,); break
    return out

# ---- the window, Emerald style (white frame, two panes), on the free wall tile -------------------
def window(img, time, t, x=98, y=4, w=14, h=18, frame=(248, 248, 248), view=None):
    # between the notebook desk (ends x 96) and the stairwell, now from x 116
    o = (72, 72, 88)
    rect(img, x, y, x + w, y + h, o)
    sky(img, x + 1, y + 1, x + w - 1, y + h - 1, time, t, view)
    rect(img, x + 1, y + 1, x + w - 1, y + 2, frame); rect(img, x + 1, y + h - 2, x + w - 1, y + h - 1, frame)
    rect(img, x + 1, y + 1, x + 2, y + h - 1, frame); rect(img, x + w - 2, y + 1, x + w - 1, y + h - 1, frame)
    rect(img, x + 1, y + h // 2, x + w - 1, y + h // 2 + 1, frame)
    rect(img, x - 1, y + h, x + w + 1, y + h + 2, frame); rect(img, x - 1, y + h + 2, x + w + 1, y + h + 3, o)

def poster(img, x, y, mon, bg=(248, 240, 200)):
    """Emerald's posters: 16 x 24, a white border round a Pokémon."""
    rect(img, x, y, x + 14, y + 20, (72, 72, 88)); rect(img, x + 1, y + 1, x + 13, y + 19, (248, 248, 248))
    rect(img, x + 2, y + 2, x + 12, y + 18, bg)
    m = mk.mon(mon).crop((0, 0, 32, 32)); bb = m.getbbox()
    if bb: m = m.crop(bb)
    sc = min(10 / m.width, 15 / m.height); m = m.resize((max(1, int(m.width * sc)), max(1, int(m.height * sc))), Image.NEAREST)
    img.paste(m, (x + 2 + (10 - m.width) // 2, y + 17 - m.height), m)

# ---- views for the window ----------------------------------------------------------------------
def view_sea(im, x0, y0, x1, y1, tm, tt):
    hy = y0 + (y1 - y0) // 2 + 1
    water = {'day': (64, 152, 216), 'sunset': (152, 88, 128), 'night': (24, 32, 72)}[tm]
    rect(im, x0, hy, x1, y1, water)
    for x in range(x0, x1):
        if (x + tt // 2) % 5 < 2: put(im, x, hy + 2 + (x % 2), shade(water, 0.35))

def view_snow(im, x0, y0, x1, y1, tm, tt):
    for k in range(5):
        put(im, x0 + (k * 5 + tt // 3) % (x1 - x0), y0 + (k * 7 + tt) % (y1 - y0), (248, 248, 248))
    rect(im, x0, y1 - 2, x1, y1, (232, 240, 248))

def view_leaves(im, x0, y0, x1, y1, tm, tt):
    g = {'day': (56, 144, 64), 'sunset': (152, 112, 56), 'night': (24, 56, 48)}[tm]
    for x in range(x0, x1):
        put(im, x, y0 + (x * 3 % 3), g); put(im, x, y1 - 1 - (x % 2), g)

def view_city(im, x0, y0, x1, y1, tm, tt):
    for i, x in enumerate(range(x0, x1, 3)):
        h = 3 + (i * 5) % 6
        rect(im, x, y1 - h, x + 2, y1, {'day': (120, 136, 168), 'sunset': (88, 64, 96), 'night': (24, 24, 48)}[tm])
        if tm == 'night' and (i + tt // 6) % 3: put(im, x, y1 - h + 1, (248, 224, 120))

def view_stars(im, x0, y0, x1, y1, tm, tt):
    rect(im, x0, y0, x1, y1, (8, 8, 32))
    for k in range(6):
        if (k + tt // 4) % 4: put(im, x0 + (k * 7) % (x1 - x0), y0 + (k * 5) % (y1 - y0), (248, 248, 248))
    rect(im, x0 + 3, y1 - 5, x0 + 7, y1 - 1, (216, 128, 72))

def view_blossom(im, x0, y0, x1, y1, tm, tt):
    for k in range(4):
        put(im, x0 + (k * 5 + tt // 2) % (x1 - x0), y0 + (k * 7 + tt // 3) % (y1 - y0), (248, 176, 200))

def view_fish(im, x0, y0, x1, y1, tm, tt):
    rect(im, x0, y0, x1, y1, {'day': (56, 136, 216), 'sunset': (72, 104, 184), 'night': (24, 48, 112)}[tm])
    fx = x0 + (tt // 2) % (x1 - x0)
    rect(im, fx, y0 + 6, fx + 3, y0 + 8, (248, 152, 48))
    put(im, x0 + 3, y1 - 2 - (tt % 6), (216, 240, 248))

def view_lava(im, x0, y0, x1, y1, tm, tt):
    rect(im, x0, y0, x1, y1, (56, 24, 24))
    for x in range(x0, x1): put(im, x, y1 - 2 - ((x + tt // 2) % 3 == 0), (248, 120, 40))

# ---- the rooms -------------------------------------------------------------------------------
# floor: 4 shades darkest first; wall: 2 shades; rug: 3 shades (dark, mid, light)
ROOMS = {
    'loft': dict(title='Cosy Attic', blurb='Warm wood and a sunny window, a Pikachu poster, a round cushion, a Pikachu doll by the bed.',
        floor=[(26, 18, 10), (21, 14, 8), (28, 21, 13), (24, 17, 10)], wall=None, rug=[(24, 11, 9), (29, 15, 12), (31, 24, 16)],
        view=None, decor=[('poster', 'pikachu', 99, 4), ('doll', 'pikachu', 0, 64), ('cushion', 'round', 16, 48), ('plant', 0, 96)],
        mons=('pikachu', 'eevee', 'togepi', 'skitty', 'mudkip')),
    'den': dict(title='Gamer Den', blurb='Dusk-purple walls, a dark carpet with a Poké Ball rug colour, a Porygon2 doll and a spin cushion.',
        floor=[(5, 4, 9), (8, 6, 12), (10, 8, 15), (12, 10, 17)], wall=[(9, 8, 16), (12, 11, 20)], rug=[(20, 4, 4), (26, 8, 8), (30, 28, 28)],
        view='stars', decor=[('doll', 'unused_porygon2', 0, 64), ('cushion', 'spin', 16, 48), ('cushion', 'ball', 112, 64)],
        mons=('porygon', 'rotom', 'magnemite', 'gengar', 'pikachu')),
    'cabin': dict(title='Snow Lodge', blurb='Dark log browns, a red rug, snow falling past the window, a big Snorlax doll to lean on.',
        floor=[(11, 7, 4), (14, 9, 5), (17, 12, 7), (20, 14, 8)], wall=[(19, 15, 11), (23, 19, 14)], rug=[(18, 4, 4), (24, 7, 7), (29, 14, 12)],
        view='snow', decor=[('bigdoll', 'snorlax', 96, 48), ('cushion', 'fire', 16, 48), ('plant', 0, 96)],
        mons=('snorunt', 'swinub', 'spheal', 'vulpix', 'smoochum')),
    'beach': dict(title='Seaside', blurb='Pale sand floor, sky-blue walls, a sea view, a big Wailmer doll and a Mudkip doll, a water cushion.',
        floor=[(24, 21, 15), (27, 24, 18), (29, 27, 21), (30, 28, 23)], wall=[(20, 26, 30), (25, 29, 31)], rug=[(4, 14, 22), (8, 19, 27), (17, 26, 30)],
        view='sea', decor=[('bigdoll', 'wailmer', 96, 48), ('doll', 'mudkip', 0, 64), ('cushion', 'water', 16, 48), ('plant', 0, 96)],
        mons=('wingull', 'corphish', 'lapras', 'psyduck', 'krabby')),
    'treehouse': dict(title='Forest Nook', blurb='Leafy greens on the walls and rug, a window full of leaves, a Treecko doll and two potted plants.',
        floor=[(16, 11, 6), (20, 14, 8), (23, 17, 10), (26, 20, 12)], wall=[(17, 23, 14), (22, 27, 18)], rug=[(8, 16, 6), (12, 21, 9), (20, 27, 14)],
        view='leaves', decor=[('doll', 'treecko', 0, 64), ('cushion', 'grass', 16, 48), ('plant', 0, 96), ('plant', 128, 56)],
        mons=('treecko', 'pikachu', 'oddish', 'bulbasaur', 'shroomish')),
    'champion': dict(title='Champion Suite', blurb='Cream and gold, a deep red rug, a city view that lights up at night, a big Rhydon doll, a cabinet.',
        floor=[(22, 20, 17), (25, 23, 20), (28, 27, 24), (30, 29, 27)], wall=[(29, 26, 18), (31, 29, 22)], rug=[(16, 3, 4), (22, 5, 6), (29, 23, 8)],
        view='city', decor=[('bigdoll', 'rhydon', 96, 48), ('cushion', 'diamond', 16, 48), ('plant', 0, 96)],
        mons=('dragonite', 'garchomp', 'metagross', 'milotic', 'salamence')),
    'space': dict(title='Stargazer', blurb='Midnight-blue walls, a starry window with a planet, silver floor, a Clefairy doll and a Swablu doll.',
        floor=[(12, 13, 15), (15, 16, 18), (18, 19, 21), (21, 22, 24)], wall=[(5, 6, 13), (8, 9, 17)], rug=[(4, 6, 12), (7, 9, 17), (24, 26, 8)],
        view='stars', decor=[('doll', 'clefairy', 0, 64), ('doll', 'swablu', 16, 48), ('cushion', 'zigzag', 112, 64)],
        mons=('clefairy', 'porygon', 'beldum', 'lunatone', 'solrock')),
    'tatami': dict(title='Johto Room', blurb='Straw floor, paper-white walls, a deep blue rug, cherry blossom at the window, Cyndaquil and Chikorita dolls.',
        floor=[(20, 19, 10), (23, 22, 12), (25, 24, 15), (27, 26, 17)], wall=[(29, 28, 25), (31, 30, 27)], rug=[(4, 7, 16), (7, 11, 21), (14, 18, 26)],
        view='blossom', decor=[('doll', 'cyndaquil', 0, 64), ('doll', 'chikorita', 16, 48), ('doll', 'totodile', 112, 64), ('plant', 0, 96)],
        mons=('eevee', 'espeon', 'umbreon', 'sentret', 'hoothoot')),
    'aquarium': dict(title='Aquarium', blurb='Blue tiles of light, a window onto a tank with a fish swimming past, Marill and Lotad dolls, a big Lapras doll.',
        floor=[(9, 13, 20), (11, 15, 22), (13, 18, 25), (15, 20, 27)], wall=[(14, 21, 28), (19, 25, 30)], rug=[(4, 15, 20), (8, 20, 25), (18, 27, 30)],
        view='fish', decor=[('bigdoll', 'lapras', 96, 48), ('doll', 'marill', 0, 64), ('doll', 'lotad', 16, 48)],
        mons=('mudkip', 'wooper', 'luvdisc', 'horsea', 'chinchou')),
    'greenhouse': dict(title='Garden Room', blurb='Mint walls, terracotta floor, a sunny window, plants in every corner, Seedot and Lotad dolls, a grass cushion.',
        floor=[(20, 12, 8), (24, 15, 10), (27, 18, 12), (29, 21, 15)], wall=[(22, 28, 22), (26, 30, 26)], rug=[(8, 18, 8), (12, 23, 11), (22, 28, 16)],
        view=None, decor=[('plant', 0, 96), ('plant', 128, 56), ('doll', 'seedot', 0, 64), ('cushion', 'grass', 16, 48)],
        mons=('bellossom', 'oddish', 'roselia', 'chikorita', 'bulbasaur')),
    'lair': dict(title='Magma Den', blurb='Charcoal floor, ember-red walls and rug, a glowing window of lava, a big Regirock doll, a fire cushion.',
        floor=[(6, 4, 4), (8, 6, 6), (10, 8, 8), (12, 9, 9)], wall=[(14, 5, 4), (18, 8, 6)], rug=[(18, 6, 2), (25, 10, 3), (30, 20, 6)],
        view='lava', decor=[('bigdoll', 'regirock', 96, 48), ('cushion', 'fire', 16, 48), ('doll', 'torchic', 0, 64)],
        mons=('houndoom', 'torkoal', 'magcargo', 'slugma', 'numel')),
    'clouds': dict(title='Sky Loft', blurb='White and sky blue, a gold-trimmed rug, clouds drifting past the window, Swablu and Togepi dolls.',
        floor=[(25, 25, 27), (27, 27, 29), (29, 29, 30), (31, 31, 31)], wall=[(22, 27, 31), (26, 29, 31)], rug=[(22, 18, 6), (27, 23, 10), (30, 28, 18)],
        view=None, decor=[('doll', 'swablu', 0, 64), ('doll', 'togepi', 16, 48), ('cushion', 'kiss', 112, 64)],
        mons=('altaria', 'swablu', 'pidgeot', 'togekiss', 'jigglypuff')),
}
VIEWS = dict(sea=view_sea, snow=view_snow, leaves=view_leaves, city=view_city, stars=view_stars, blossom=view_blossom, fish=view_fish, lava=view_lava)

def rgb15(c): return tuple(v * 8 for v in c)

def frame(name, t, time):
    r = ROOMS[name]
    img = base([rgb15(c) for c in r['floor']] if r['floor'] else None,
               [rgb15(c) for c in r['wall']] if r['wall'] else None,
               [rgb15(c) for c in r['rug']] if r['rug'] else None)
    has_poster = any(d[0] == 'poster' for d in r['decor'])
    if not has_poster:
        view = VIEWS.get(r['view'])
        window(img, time, t, view=view)
    for d in r['decor']:
        kind = d[0]
        if kind == 'poster': poster(img, d[2], d[3], d[1])
        elif kind == 'doll': put_spr(img, doll(d[1]), d[2], d[3])
        elif kind == 'bigdoll': put_spr(img, doll(d[1], big=True), d[2], d[3])
        elif kind == 'cushion': put_spr(img, cushion(d[1]), d[2], d[3])
        elif kind == 'plant': put_spr(img, plant(), d[1], d[2] - 8)
    return img

def still(name):
    img = frame(name, 0, 'day')
    b = mk.person('graphics/object_events/pics/misc/moving_box.png', 16, 16)
    img.paste(b, (BOX_TILE[0] * T, BOX_TILE[1] * T), b)
    for (mx, my), m in zip(SPOTS, ROOMS[name]['mons']):
        try: stamp_mon(img, m, mx, my)
        except Exception: pass
    stamp_player(img, *START)
    try: stamp_mon(img, ROOMS[name]['mons'][0], START[0], START[1] + 1)
    except Exception: pass
    return img

if __name__ == '__main__':
    names = sys.argv[1:] or list(ROOMS)
    for n in names:
        for tm in TIMES:
            save_gif([frame(n, t, tm) for t in range(0, 48, 2)], f'{HERE}/out/og_{n}_{tm}.gif', scale=4)
        still(n).resize((144 * 4, 128 * 4), Image.NEAREST).save(f'{HERE}/out/og_{n}.png')
        print(n, 'tiles', tile_budget(frame(n, 0, 'day'))[0])
