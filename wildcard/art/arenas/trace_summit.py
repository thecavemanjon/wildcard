# Red's summit traced from the HeartGold/SoulSilver map: same footprint, Emerald ridge tiles.
import copy, summit as S, mapkit as mk
from PIL import Image, ImageDraw
G, H = S.G, S.H
ROCKRAMP = [(64, 76, 64), (92, 104, 94), (120, 128, 120), (172, 206, 212), (214, 236, 248), (248, 248, 248)]  # sampled from the HGSS map

W, Hh = 40, 30
CORR = (20, 22)                 # the path, columns 20-22
def region(x, y):
    """'L'/'R' for the two rock walls, 'BL'/'BR' for the lower cliffs, None for snow."""
    if y <= 21:
        if 7 <= x < CORR[0] - 1 and y >= 1: return 'L'
        if CORR[1] + 1 < x <= 35 and y >= 1: return 'R'
        if x < 7 or x > 35: return 'BL' if x < 20 else 'BR'
        return None
    if x < 12: return 'BL'
    if x > 27: return 'BR'
    return None

def stair(g, x, y, dx, run, ok):
    while True:
        for _ in range(run):
            if not ok(x, y): return
            g[y][x] = H; x += dx
        if not ok(x, y) or not ok(x, y + 1): return
        g[y][x] = S.WS if dx > 0 else S.ES
        y += 1
        g[y][x] = S.NE if dx > 0 else S.NW
        x += dx

def build(spacing=1, run=2, ribs=False):
    g = [[G]*W for _ in range(Hh)]
    if ribs:  # vertical rock ribs everywhere in the walls; the ledges are drawn over them
        for y in range(Hh):
            for x in range(W):
                r = region(x, y)
                if r in ('L', 'BL'): g[y][x] = S.V_L
                elif r in ('R', 'BR'): g[y][x] = S.V_R
    L = lambda x, y: 0 <= x < W and 0 <= y < Hh and region(x, y) in ('L', 'BL')
    R = lambda x, y: 0 <= x < W and 0 <= y < Hh and region(x, y) in ('R', 'BR')
    # walls hugging the path, then ribs stepping down and away from it
    for y in range(7, 22):
        g[y][CORR[0] - 1] = S.V_R; g[y][CORR[1] + 1] = S.V_L
    for y in range(1, 22, spacing):
        stair(g, CORR[1] + 2, y, +1, run, R)
        stair(g, CORR[0] - 2, y, -1, run, L)
    for y in range(22, Hh, spacing):            # the lower cliffs either side of the open snow
        stair(g, 28, y, +1, run, R); stair(g, 11, y, -1, run, L)
    # the summit: steps up to Red, a ledge either side of them
    for x in range(CORR[0] - 1, CORR[1] + 2):
        g[6][x] = H
    for x in CORR[0], CORR[0] + 1, CORR[1]:
        g[4][x] = S.STEP; g[5][x] = S.STEP; g[6][x] = S.STEP
    for y in range(1, 7):
        g[y][CORR[0] - 1] = S.V_R; g[y][CORR[1] + 1] = S.V_L
    return g

def bright_pals(gamma=0.6):
    p = copy.deepcopy(S.kit.pals)
    def m(c):
        L = (0.3*c[0] + 0.59*c[1] + 0.11*c[2]) / 255
        L = min(0.999, max(0, (L - 0.05) / 0.85)) ** gamma
        t = L*(len(ROCKRAMP) - 1); i = int(t); f = t - i; a, b = ROCKRAMP[i], ROCKRAMP[i + 1]
        return tuple(int(a[k] + (b[k] - a[k])*f) for k in range(3))
    for pi in (10, 11):
        for ci in range(1, 16):
            if p[pi][ci] not in ((255, 0, 255), (49, 49, 255)): p[pi][ci] = m(p[pi][ci])
    for ci in range(11, 16): p[8][ci] = S.ramp_map(p[8][ci], [(96, 104, 112), (150, 158, 166), (196, 204, 210), (226, 232, 236), (244, 246, 248), (252, 252, 252)])
    return p

def crisp_pals():
    # colour by colour from the reference: white snow, mint shade, grey-green rock
    p = copy.deepcopy(S.kit.pals)
    m10 = {9: (248, 248, 248), 10: (248, 248, 248), 11: (236, 244, 248), 12: (196, 222, 230), 13: (104, 114, 104), 14: (64, 76, 64),
           1: (248, 248, 248), 2: (224, 240, 248), 3: (176, 208, 200), 4: (136, 144, 144), 5: (110, 118, 110), 8: (64, 76, 64)}
    m11 = {9: (248, 248, 248), 10: (232, 242, 248), 11: (172, 206, 212), 12: (120, 128, 120), 13: (92, 104, 94), 14: (64, 76, 64),
           1: (248, 248, 248), 2: (214, 236, 248), 3: (120, 128, 120), 4: (80, 92, 80), 6: (96, 104, 96), 8: (64, 76, 64), 15: (136, 144, 144)}
    for i, c in m10.items(): p[10][i] = c
    for i, c in m11.items(): p[11][i] = c
    for ci in range(11, 16): p[8][ci] = S.ramp_map(p[8][ci], [(96, 104, 112), (150, 158, 166), (196, 204, 210), (226, 232, 236), (244, 246, 248), (252, 252, 252)])
    return p

def scene(spacing, run, name, ribs=False, gamma=None):
    g = build(spacing, run, ribs)
    im = S.kit.render(g, [(S.RED, 21, 2), (S.PIKA, 22, 2), (S.player(), 21, 8)], (crisp_pals() if gamma == 'crisp' else bright_pals(gamma)) if gamma else S.pals(ROCKRAMP))
    S.snowfall(im, 300, 5)
    return name, im

if __name__ == '__main__':
    ref = Image.open('../ref/summit_hgss.png').convert('RGB')
    outs = [('Reference: HeartGold/SoulSilver summit', ref.resize((640, 480)))]
    for sp, run, rb, gm, n in [(3, 1, True, 'crisp', 'Traced, crisp: ledges every 3 rows'), (2, 1, True, 'crisp', 'Traced, crisp: ledges every 2 rows')]:
        name, im = scene(sp, run, n, rb, gm); outs.append((name, im))
    tiles = [mk.label(im, n, 1) for n, im in outs]
    sh = Image.new('RGB', (sum(t.width for t in tiles) + 48, max(t.height for t in tiles) + 24), (12, 12, 16)); x = 12
    for t in tiles: sh.paste(t, (x, 12)); x += t.width + 12
    sh.save('trace_compare.png'); print(sh.size)
