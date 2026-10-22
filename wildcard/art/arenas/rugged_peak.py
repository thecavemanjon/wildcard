# Middle ground between the blocky Pyramid steps and the smooth slope.
import random, peak as P, summit as S, smooth_peak as SP
from PIL import Image, ImageDraw
WHITE = (255, 255, 255)
LIT, SH, DEEP = SP.SNOW_LIT, SP.SNOW_SH, SP.SNOW_DEEP
ROCK, ROCK_DK = SP.ROCK, SP.ROCK_DK

def silhouette(W, ax, ay, slope, rnd, style):
    top = {}
    for dir_ in (-1, 1):
        x, y = ax, ay
        while 0 <= x < W:
            if style == 'steps':                      # small irregular steps
                run = rnd.randrange(5, 15); rise = max(2, int(run*slope + rnd.randrange(-2, 3)))
            elif style in ('chunky', 'terraces'):                   # tile-ish steps, uneven
                run = rnd.randrange(12, 24); rise = max(5, int(run*slope + rnd.randrange(-3, 5)))
            else:                                     # a slope with jagged little notches
                run = rnd.randrange(2, 6); rise = int(run*slope + rnd.choice((0, 0, 1, -1, 3)))
            for i in range(run):
                if 0 <= x < W: top[x] = y
                x += dir_
            y += rise
    return top

def paint(base, style, apex=(280, 120), slope=0.45, seed=11):
    W, H = base.size; rnd = random.Random(seed); ax, ay = apex
    im = base.copy(); px = im.load(); d = ImageDraw.Draw(im)
    top = silhouette(W, ax, ay, slope, rnd, style)
    for x in range(W):                                 # clear old pyramid above the skyline
        if abs(x - ax) < 38: continue
        for y in range(max(0, ay - 20), min(H, top.get(x, H))):
            px[x, y] = base.getpixel((2, y))
    rx, ridge = float(ax), {}
    for y in range(ay, H): rx += rnd.uniform(-0.6, 0.8); ridge[y] = int(rx)
    for x in range(W):
        t = top.get(x, H)
        for y in range(max(0, t), H):
            lit = x < ridge.get(y, ax)
            c = LIT if lit else SH
            if (x*5 + y*11) % 19 == 0: c = SH if lit else DEEP
            px[x, y] = c
        if t < H:
            px[x, t] = WHITE
            if t + 1 < H: px[x, t + 1] = WHITE if (x % 3) else LIT
    # rock faces under each step's lip (the drop between one step and the next)
    xs = sorted(top)
    for x in xs:
        nx = x + (1 if x >= ax else -1)
        if nx in top and top[nx] > top[x] + 1:        # a drop here: paint the exposed rock
            for y in range(top[x] + 2, top[nx] + 2):
                for k in range(0, (3 + (y - top[x])//3) if style != 'chunky' else 4 + (top[nx] - y)//2):
                    xx = nx + (k if x >= ax else -k)
                    if 0 <= xx < W and abs(xx - ax) > 20: px[xx, y] = ROCK_DK if k == 0 else ROCK
    if style == 'terraces':  # every step on the skyline carries on inwards as a terrace lip with rock under it
        for dir_ in (-1, 1):
            xs_side = sorted([x for x in top if (x - ax)*dir_ > 0], key=lambda x: abs(x - ax))
            for x in xs_side:
                nx = x + dir_
                if nx not in top or top[nx] <= top[x] + 5: continue
                y0, drop = top[nx], top[nx] - top[x]
                yy = float(y0); wob = rnd.Random() if False else None
                xx = nx
                while abs(xx - ax) > 18:
                    xx -= dir_
                    yy += rnd.uniform(-0.4, 0.4) - 0.04            # lips run level, rising a touch toward the middle
                    y = int(yy)
                    if y >= H or y <= top.get(xx, H): continue
                    face = max(2, int(drop*0.45))
                    for k in range(face):
                        if y + k < H: px[xx, y + k] = ROCK_DK if k >= face - 1 else ROCK
                    px[xx, y - 1] = WHITE
    if style == 'ledges':                              # rocky strata across the slopes, snow on top
        for band in range(6):
            y0 = ay + 22 + band*26 + rnd.randrange(-4, 5)
            for x in range(W):
                if abs(x - ax) < 20 or top.get(x, H) > y0 - 2: continue
                yy = y0 + int(3*((x*0.07) % 1)) + (x - ax)*0 // 1
                th = 2 + ((x*13 + band*7) % 5 == 0)
                for k in range(th): px[x, yy + k] = ROCK_DK if k == th - 1 else ROCK
                px[x, yy - 1] = WHITE
    # path and steps up the middle, summit cap
    for y in range(ay + 4, H):
        half = 11 + (y - ay)//24
        for x in range(ax - half, ax + half):
            if px[x, y] in (LIT, SH, DEEP, WHITE, ROCK, ROCK_DK): px[x, y] = SP.PATH if (x + y) % 9 else SP.SNOW
    for i in range(6):
        y = ay + 10 + i*6
        d.rectangle((ax - 14, y, ax + 13, y + 3), fill=SP.STEP_LT); d.line([(ax - 14, y + 4), (ax + 13, y + 4)], fill=SP.STEP_DK)
    d.ellipse((ax - 22, ay - 6, ax + 22, ay + 10), fill=WHITE)
    return im

def scene(style, name, pals=P.DAY, grid=None, flakes=220, seed=1):
    base = P.kit.render(grid or P.g, (), pals)
    im = paint(base, style)
    for spr, x, y in [(S.RED, 17, 7), (S.PIKA, 18, 7), (S.player(), 17, 11)]:
        im.paste(spr, (x*16 + 8 - spr.width//2, y*16 + 16 - spr.height), spr)
    S.snowfall(im, flakes, seed)
    return S.pair(name, im, S.screen(im, 17, 10))

if __name__ == '__main__':
    from PIL import Image
    ims = [Image.open('peak_1.png'), scene('terraces', 'T. Terraces: uneven steps that run across the face'), scene('chunky', 'a2. Chunky: uneven steps on the outline only')]
    W = max(i.width for i in ims); sh = Image.new('RGB', (W + 24, sum(i.height for i in ims) + 48), (12, 12, 16)); y = 12
    for im in ims: sh.paste(im, (12, y)); y += im.height + 12
    sh.save('sheet_rugged.png')
