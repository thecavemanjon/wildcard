# A hand-shaped peak painted over the Pyramid-top mockup: real diagonal slopes,
# a lit face and a shadow face, rock showing through, a trodden path and steps.
import random, peak as P, summit as S, mapkit as mk
from PIL import Image, ImageDraw

SNOW_LIT, SNOW, SNOW_SH, SNOW_DEEP = (244, 247, 252), (226, 233, 244), (194, 205, 224), (164, 178, 204)
ROCK, ROCK_DK, PATH, STEP_LT, STEP_DK = (112, 120, 142), (72, 78, 100), (210, 218, 234), (200, 204, 214), (120, 124, 140)

def paint(base, apex=(280, 120), slope=0.42, seed=5):
    W, H = base.size; rnd = random.Random(seed)
    im = base.copy(); px = im.load()
    ax, ay = apex
    # silhouette: a slightly wobbly line down each side, with a shoulder or two
    def edge(dir_):
        ys, y, wob = {}, ay, 0.0
        for i in range(0, W):
            x = ax + dir_*i
            if not (0 <= x < W): break
            wob += rnd.uniform(-0.6, 0.6); wob = max(-5, min(5, wob))
            shoulder = 10 if 70 < i < 110 else 0          # a little flat shoulder on each side
            ys[x] = int(ay + i*slope - (shoulder*(1 - abs(i - 90)/20) if 70 < i < 110 else 0) + wob)
        return ys
    left, right = edge(-1), edge(+1)
    top = {**left, **right}
    for x in range(max(0, ax - 90), min(W, ax + 90)):   # clear leftover pyramid tiers above the new skyline
        if abs(x - ax) < 38: continue
        for y in range(max(0, ay - 20), top.get(x, H)):
            px[x, y] = base.getpixel((2, y))
    ridge = {}  # the dividing ridge between the lit and shadow faces wanders down from the apex
    rx = float(ax)
    for y in range(ay, H):
        rx += rnd.uniform(-0.5, 0.7); ridge[y] = int(rx)
    for x in range(W):
        t = top.get(x, H)
        for y in range(max(0, t), H):
            lit = x < ridge.get(y, ax)
            depth = y - t
            c = SNOW_LIT if lit else SNOW_SH
            if depth < 2: c = (255, 255, 255) if lit else SNOW
            # wind streaks and dither so it isn't flat
            if (x*7 + y*13) % 23 == 0: c = SNOW if lit else SNOW_DEEP
            px[x, y] = c
    d = ImageDraw.Draw(im)
    # rock outcrops poking through the snow: jagged triangles with a lit and a dark side
    for _ in range(18):
        x = rnd.randrange(14, W - 14); t = top.get(x, H)
        if t >= H - 16 or abs(x - ax) < 34: continue
        y = rnd.randrange(t + 10, H - 6); w = rnd.randrange(10, 26); h = rnd.randrange(6, 13)
        for k in range(h):
            half = int(w/2 * (k + 1)/h) + rnd.randrange(0, 2)
            for xx in range(x - half, x + half + 1):
                if 0 <= xx < W and 0 <= y + k < H:
                    px[xx, y + k] = ROCK if xx < x + rnd.randrange(-1, 2) else ROCK_DK
        d.line([(x - 1, y), (x + 1, y)], fill=(255, 255, 255)); d.point((x, y - 1), fill=(255, 255, 255))
    # the trodden path up the middle, with stone steps near the top
    for y in range(ay + 4, H):
        half = 11 + (y - ay)//24
        for x in range(ax - half, ax + half):
            if px[x, y] in (SNOW_LIT, SNOW_SH, SNOW, SNOW_DEEP, (255, 255, 255)):
                px[x, y] = PATH if (x + y) % 9 else SNOW
    for i in range(6):
        y = ay + 10 + i*6
        d.rectangle((ax - 14, y, ax + 13, y + 3), fill=STEP_LT); d.line([(ax - 14, y + 4), (ax + 13, y + 4)], fill=STEP_DK)
    # the summit cap Red stands on
    d.ellipse((ax - 22, ay - 6, ax + 22, ay + 10), fill=(255, 255, 255))
    return im

def scene(pals, flakes, seed, name, grid=None):
    base = P.kit.render(grid or P.g, (), pals)
    im = paint(base)
    for spr, x, y in [(S.RED, 17, 7), (S.PIKA, 18, 7), (S.player(), 17, 11)]:
        im.paste(spr, (x*16 + 8 - spr.width//2, y*16 + 16 - spr.height), spr)
    if flakes: S.snowfall(im, flakes, seed)
    return S.pair(name, im, S.screen(im, 17, 10))

if __name__ == '__main__':
    scene(P.DAY, 220, 1, 'P1 smooth: overcast, pale sun').save('smooth_1.png')
    scene(P.NOSUN, 420, 2, 'P2 smooth: snowstorm', P.sunless()).save('smooth_2.png')
