import copy, random, summit as S, mapkit as mk
from PIL import Image
G, H = S.G, S.H
TREE_TOP, TREE_BOT, LAVA, LAVA_B = 0x2c5, 0x2cc, 0x2bd, 0x21c
BOULDER = mk.person('graphics/object_events/pics/misc/pushable_boulder.png', 16, 16)

def ring(g, x0, y0, x1, y1, gap):
    """A raised tier seen from the front: a rounded rim along the back, plain sides,
    and the cliff face only along the front, where the steps go up (Mt. Chimney's
    plateaus are drawn the same way)."""
    cx = (x0 + x1)//2
    for x in range(x0+1, x1): g[y0][x] = 0x269; g[y1][x] = H
    for y in range(y0+1, y1): g[y][x0] = S.V_L; g[y][x1] = S.V_R
    g[y0][x0], g[y0][x1], g[y1][x0], g[y1][x1] = 0x268, 0x26A, S.NE, S.NW
    if gap:
        for x in range(cx - 1, cx + 2): g[y1][x] = S.STEP

def amph(W=21, Hh=17):
    g = [[G]*W for _ in range(Hh)]
    ring(g, 2, 1, W - 3, Hh - 3, True)
    ring(g, 5, 4, W - 6, Hh - 6, True)
    return g, W//2

def band_cells(W, Hh, cx):  # the terrace between the two rings, minus the stair path
    return [(x, y) for y in range(2, Hh - 3) for x in range(3, W - 3)
            if not (5 <= x <= W - 6 and 4 <= y <= Hh - 6) and abs(x - cx) > 1]

def outside_cells(W, Hh):
    return [(x, y) for y in range(Hh) for x in range(W) if x in (0, W - 1) or y == Hh - 1 or (y >= Hh - 2 and (x < 2 or x > W - 3))]

def trees(g, cells, rnd, n):
    rnd.shuffle(cells); placed = 0
    for x, y in cells:
        if placed >= n: break
        if y + 1 < len(g) and g[y][x] == G and g[y+1][x] == G:
            g[y][x] = TREE_TOP; g[y+1][x] = TREE_BOT; placed += 1

RAMPS = {
    'rock':  [(48, 32, 20), (96, 68, 44), (150, 112, 74), (196, 160, 112), (228, 204, 160), (248, 236, 206)],
    'grass': [(16, 40, 22), (34, 78, 40), (62, 120, 58), (104, 162, 82), (156, 202, 122), (208, 232, 176)],
    'ghost': [(20, 12, 34), (48, 30, 76), (84, 56, 120), (124, 92, 164), (170, 140, 206), (214, 196, 238)],
    'ice':   S.SNOW,
    'steel': [(30, 34, 42), (64, 70, 84), (104, 112, 128), (148, 156, 170), (196, 202, 212), (236, 238, 244)],
}
def ow(n):
    for d in ('', 'gym_leaders/', 'elite_four/'):
        try: return mk.person(f'graphics/object_events/pics/people/{d}{n}.png')
        except FileNotFoundError: pass
    raise FileNotFoundError(n)

def build(kind, seed=4):
    rnd = random.Random(seed); g, cx = amph(); W, Hh = len(g[0]), len(g)
    sprites = []
    band = band_cells(W, Hh, cx)
    if kind == 'fire':
        for x, y in band: g[y][x] = LAVA_B if rnd.random() < 0.15 else LAVA
    elif kind in ('grass', 'ghost', 'ice'):
        trees(g, band, rnd, 14 if kind == 'grass' else 9)
        trees(g, [(x, y) for y in range(0, Hh - 1) for x in (0, 1, W - 2, W - 1)], rnd, 12)
    elif kind in ('rock', 'steel'):
        rnd.shuffle(band)
        for x, y in band[:10]:
            if g[y][x] == G: sprites.append((BOULDER, x, y))
    return g, cx, sprites

CASES = [('A1. Rock amphitheatre: Roxanne, Brock', 'rock', 'roxanne'),
         ('A2. Fire amphitheatre with a lava moat: Flannery, Blaine, Maxie', 'fire', 'flannery'),
         ('A3. Grass amphitheatre in the woods: Erika', 'grass', 'erika'),
         ('A4. Ghost amphitheatre, dead trees: Phoebe, Agatha', 'ghost', 'phoebe'),
         ('A5. Ice amphitheatre: Glacia, Lorelei', 'ice', 'glacia'),
         ('A6. Steel amphitheatre: Steven', 'steel', 'steven')]
if __name__ == '__main__':
    for i, (name, kind, opp) in enumerate(CASES):
        g, cx, spr = build(kind)
        p = S.pals(RAMPS[kind]) if kind in RAMPS else S.pals(S.STONE) if False else S.kit.pals
        if kind == 'fire':
            p = copy.deepcopy(S.kit.pals)
            for ci in range(11, 16): p[8][ci] = S.ramp_map(p[8][ci], S.STONE)
        im = S.kit.render(g, spr + [(ow(opp), cx, 6), (S.player(), cx, 10)], p)
        if kind == 'ice': S.snowfall(im, 200, 7)
        S.pair(name, im, S.screen(im, cx, 10)).save(f'amph_{i+1}.png')
