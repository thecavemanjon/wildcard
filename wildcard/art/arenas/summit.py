import copy, random, mapkit as mk
from PIL import Image, ImageDraw
lid, _ = mk.map_layout('MtChimney'); kit, chim = mk.layout(lid)
G, V_L, V_R, H = 0x271, 0x270, 0x272, 0x274
NE, WS, NW, ES = 0x278, 0x27c, 0x27a, 0x27b
STEP = 0x2af

def ramp_map(c, ramp):
    L = (0.3*c[0] + 0.59*c[1] + 0.11*c[2]) / 255
    t = min(0.999, max(0, (L - 0.05) / 0.85)) * (len(ramp) - 1)
    i = int(t); f = t - i; a, b = ramp[i], ramp[i + 1]
    return tuple(int(a[k] + (b[k] - a[k])*f) for k in range(3))

SNOW = [(34, 42, 70), (70, 84, 120), (120, 138, 172), (176, 192, 216), (222, 232, 244), (250, 252, 255)]
NIGHT = [(14, 16, 34), (34, 40, 74), (62, 72, 116), (98, 112, 160), (140, 156, 200), (190, 204, 236)]
STONE = [(40, 40, 48), (80, 80, 92), (124, 124, 136), (168, 168, 178), (206, 206, 214), (236, 236, 240)]
def pals(ramp=SNOW):
    p = copy.deepcopy(kit.pals)
    for pi in (10, 11):
        for ci in range(1, 16):
            if p[pi][ci] not in ((255, 0, 255), (49, 49, 255)): p[pi][ci] = ramp_map(p[pi][ci], ramp)
    for ci in range(11, 16): p[8][ci] = ramp_map(p[8][ci], STONE)   # the wooden steps become stone
    return p

def staircase(g, x, y, dx, run, stop):
    W = len(g[0])
    while True:
        for _ in range(run):
            if not (0 <= x < W): return
            g[y][x] = H; x += dx
        if not (0 <= x < W) or y + 1 >= stop: return
        g[y][x] = WS if dx > 0 else ES
        y += 1
        g[y][x] = NE if dx > 0 else NW
        x += dx

def walls(g, cx, half, y0, y1, run=2, spacing=3):
    left, right = cx - half, cx + half
    for y in range(y0, y1):
        g[y][left - 1] = V_R; g[y][right + 1] = V_L
    for y in range(y0, y1 - 1, spacing):
        staircase(g, right + 2, y, +1, run, y1)
        staircase(g, left - 2, y, -1, run, y1)

def hgss(W=21, Hh=20):
    g = [[G]*W for _ in range(Hh)]; cx = W // 2
    # the peak: a ledge across the top with steps up to Red
    for x in range(W): g[3][x] = H
    g[3][cx - 3] = NE if False else g[3][cx - 3]
    for x in (cx - 1, cx, cx + 1): g[3][x] = STEP; g[4][x] = STEP
    g[4][cx - 2] = V_R; g[4][cx + 2] = V_L
    walls(g, cx, 1, 5, Hh - 4)
    for x in range(W):
        if g[Hh - 4][x] == G and abs(x - cx) > 1: g[Hh - 4][x] = H
    return g, cx, 2, 6

def gsc(W=21, Hh=20):
    g = [[G]*W for _ in range(Hh)]; cx = W // 2
    # a square plateau (the keyhole's head) with Red at the back
    x0, x1, y0, y1 = cx - 4, cx + 4, 1, 7
    for x in range(x0, x1 + 1): g[y1][x] = H
    for y in range(y0, y1): g[y][x0] = V_R; g[y][x1] = V_L
    g[y1][x0] = NE if False else ES; g[y1][x1] = WS
    g[y1][x0] = NW; g[y1][x1] = NE
    g[y1][cx] = STEP; g[y1 + 1][cx] = STEP
    walls(g, cx, 1, y1 + 1, Hh - 4, run=3, spacing=2)
    for x in range(W):
        if g[Hh - 4][x] == G and abs(x - cx) > 1: g[Hh - 4][x] = H
    return g, cx, 5, 10

def snowfall(im, n=260, seed=1, size=1):
    rnd = random.Random(seed); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rnd.randrange(im.width), rnd.randrange(im.height)
        d.rectangle((x, y, x + size, y + size), fill=(255, 255, 255))
    return im

RED = mk.person('graphics/object_events/pics/people/red/red_normal.png')
PIKA = mk.mon('pikachu')
def player():
    im = mk.person('graphics/object_events/pics/people/brendan/walking.png', frame=1)
    return im

def screen(full, px, py):  # the 240x160 GBA view centred on the player
    x = min(max(0, px*16 + 8 - 120), full.width - 240); y = min(max(0, py*16 + 8 - 80), full.height - 160)
    return full.crop((x, y, x + 240, y + 160))

def scene(gen, ramp, flakes, name, seed):
    g, cx, ry, py = gen()
    im = kit.render(g, [(RED, cx, ry), (PIKA, cx + 1, ry), (player(), cx, py)], pals(ramp))
    snowfall(im, flakes, seed)
    return name, im, screen(im, cx, py)

def pair(name, full, view):
    a = mk.label(full, name, 2); b = view.resize((480, 320), Image.NEAREST)
    out = Image.new('RGB', (a.width + 500, a.height), (24, 24, 30)); out.paste(a, (0, 0))
    out.paste(b, (a.width + 10, 34)); ImageDraw.Draw(out).text((a.width + 10, 8), 'on screen', fill=(200, 200, 200), font=mk.FONT)
    return out

if __name__ == '__main__':
    S = [scene(hgss, SNOW, 260, 'R1. Mt. Silver summit, HeartGold/SoulSilver style', 1),
         scene(gsc, SNOW, 260, 'R2. Mt. Silver summit, Gold/Silver/Crystal keyhole', 2),
         scene(hgss, NIGHT, 520, 'R3. Blizzard at night (snow weather + dark palette)', 3)]
    for i, (n, full, view) in enumerate(S): pair(n, full, view).save(f'summit_{i+1}.png')
