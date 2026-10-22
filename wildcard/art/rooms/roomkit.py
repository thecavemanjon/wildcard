# Room mockup kit: draws whole bedrooms at GBA pixel scale (16px metatiles), with
# the moving parts (windows that follow the clock, TVs, fish, fire, neon) as
# frames, so a design can later go through the stadium builder unchanged.
# The PC, GameCube, wardrobe and bed are lifted from the current bedroom so
# the rooms still read as Pokémon; everything else is drawn here.
import sys, os, math, random
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../arenas'))
sys.path.insert(0, os.path.join(HERE, '../stadiums'))
import mapkit as mk
from kit import shade, mix, draw_text, text_width

T = 16
W, H = 9, 8                   # metatiles: the same footprint as the bedroom
PW, PH = W * T, H * T
WALL = 2                      # back wall height in metatiles
TIMES = ('day', 'sunset', 'night')

def rect(img, x0, y0, x1, y1, c):
    """Filled box, inclusive-exclusive, clipped to the image."""
    px = img.load()
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            px[x, y] = c[:3] if img.mode == 'RGB' else (tuple(c[:3]) + (255,))

def box(img, x0, y0, x1, y1, fill, outline=None, hi=None, lo=None):
    """A GBA-style object: dark outline, light top-left edge, dark bottom-right."""
    o = outline or shade(fill, -0.6)
    rect(img, x0, y0, x1, y1, o)
    rect(img, x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
    if hi: rect(img, x0 + 1, y0 + 1, x1 - 1, y0 + 2, hi); rect(img, x0 + 1, y0 + 1, x0 + 2, y1 - 1, hi)
    if lo: rect(img, x0 + 1, y1 - 2, x1 - 1, y1 - 1, lo)

def ramp(c):
    """Outline, dark, base, light, highlight."""
    return shade(c, -0.62), shade(c, -0.25), c, shade(c, 0.3), shade(c, 0.6)

# Night: frame() dims the room after drawing, then runs LATE (lights, so they stay bright).
STATE = {'time': 'day', 'late': [], 'dim': []}
def light(fn):
    if STATE['time'] == 'night': STATE['late'].append(fn)
    else: fn()

def night_dim(img, k, tint=(20, 24, 60), spare=()):
    STATE['dim'].append((k, tint, list(spare)))

def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.load()[x, y] = c[:3]

def glow(img, cx, cy, r, col, k=0.4):
    px = img.load()
    for y in range(max(0, cy - r), min(img.height, cy + r + 1)):
        for x in range(max(0, cx - r), min(img.width, cx + r + 1)):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1:
                # banded, not smooth: GBA palettes can't do gradients
                band = 0.0 if d > 0.8 else (k * 0.5 if d > 0.5 else k)
                if band: px[x, y] = mix(px[x, y], col, band)

def dim(img, k, tint=(20, 24, 60), spare=()):
    """Night: everything darker and bluer, except the rects in spare (lamps, screens)."""
    px = img.load()
    keep = set()
    for x0, y0, x1, y1 in spare:
        for y in range(y0, y1):
            for x in range(x0, x1): keep.add((x, y))
    for y in range(img.height):
        for x in range(img.width):
            if (x, y) not in keep:
                px[x, y] = mix(px[x, y], tint, k)

# ---- skies, for windows ----------------------------------------------------------------
SKY = {
    'day':    [(120, 184, 248), (160, 208, 248), (200, 232, 248)],
    'sunset': [(88, 64, 136), (232, 112, 96), (248, 184, 104)],
    'night':  [(16, 20, 56), (24, 32, 80), (40, 48, 104)],
}

def sky(img, x0, y0, x1, y1, time, t=0, extra=None, seed=1):
    bands = SKY[time]; h = y1 - y0
    for y in range(y0, y1):
        c = bands[min(len(bands) - 1, (y - y0) * len(bands) // max(1, h))]
        rect(img, x0, y, x1, y + 1, c)
    r = random.Random(seed)
    if time == 'night':
        for i in range(max(2, (x1 - x0) * (y1 - y0) // 40)):
            sx, sy = r.randrange(x0, x1), r.randrange(y0, y1)
            if (i + t // 3) % 5: put(img, sx, sy, (248, 248, 216) if i % 3 else (168, 176, 232))
        mx = x1 - 7
        if mx - 3 > x0: rect(img, mx - 3, y0 + 2, mx, y0 + 5, (248, 240, 192)); put(img, mx - 3, y0 + 2, bands[0])
    else:
        # drifting clouds
        for k in range(2):
            cx = x0 + ((r.randrange(0, 60) + t // 2 + k * 23) % (x1 - x0 + 16)) - 8
            cy = y0 + 2 + k * max(1, h // 3)
            col = (248, 248, 248) if time == 'day' else (248, 200, 168)
            for dx in range(9):
                for dy in range(2 + (2 < dx < 6)):
                    if x0 <= cx + dx < x1 and y0 <= cy + dy < y1: put(img, cx + dx, cy - (dy if 2 < dx < 6 else 0) + 1, col)
        if time == 'sunset':
            sx = x0 + (x1 - x0) // 3
            for dy in range(4):
                for dx in range(-3 + (dy == 0), 4 - (dy == 0)):
                    if x0 <= sx + dx < x1 and y0 <= y1 - 4 + dy < y1: put(img, sx + dx, y1 - 4 + dy, (248, 224, 120))
    if extra: extra(img, x0, y0, x1, y1, time, t)

def window(img, x0, y0, w, h, time, t=0, frame=(232, 232, 224), extra=None, panes=2, sill=True, curtains=None, seed=1, round_=False):
    """A window in pixels (x0, y0) of size w x h, sky by time, optional curtains."""
    fo, fd, fb, fl, fh = ramp(frame)
    rect(img, x0, y0, x0 + w, y0 + h, fo)
    sky(img, x0 + 2, y0 + 2, x0 + w - 2, y0 + h - 2, time, t, extra, seed)
    rect(img, x0 + 1, y0 + 1, x0 + w - 1, y0 + 2, fb); rect(img, x0 + 1, y0 + 1, x0 + 2, y0 + h - 1, fb)
    rect(img, x0 + w - 2, y0 + 1, x0 + w - 1, y0 + h - 1, fd); rect(img, x0 + 1, y0 + h - 2, x0 + w - 1, y0 + h - 1, fd)
    for i in range(1, panes):
        px_ = x0 + i * w // panes
        rect(img, px_ - 1, y0 + 1, px_ + 1, y0 + h - 1, fb); put(img, px_ - 1, y0 + 1, fl)
    if h > 20: rect(img, x0 + 1, y0 + h // 2, x0 + w - 1, y0 + h // 2 + 1, fb)
    # glass glint
    for i in range(3): put(img, x0 + 4 + i, y0 + 3 + i, mix(SKY[time][2], (255, 255, 255), 0.6))
    if sill: rect(img, x0 - 2, y0 + h, x0 + w + 2, y0 + h + 2, fb); rect(img, x0 - 2, y0 + h + 2, x0 + w + 2, y0 + h + 3, fo)
    if curtains:
        co, cd, cb, cl, ch = ramp(curtains)
        for side in (0, 1):
            cx = x0 - 3 if side == 0 else x0 + w - 4
            for y in range(y0 - 2, y0 + h + 1):
                sway = 0
                rect(img, cx + sway, y, cx + 7 + sway, y + 1, cb)
                put(img, cx + 2 + sway, y, cd); put(img, cx + 5 + sway, y, cl)
                put(img, cx + sway, y, co); put(img, cx + 6 + sway, y, co)
        rect(img, x0 - 5, y0 - 4, x0 + w + 5, y0 - 2, shade(curtains, -0.4))
    if round_:
        # knock the corners off for a porthole look
        for (cx, cy) in ((x0, y0), (x0 + w - 1, y0), (x0, y0 + h - 1), (x0 + w - 1, y0 + h - 1)):
            pass

# ---- walls and floors --------------------------------------------------------------------
def wall_plain(img, base, trim, y1=WALL * T, stripe=None, pattern=None, skirting=None):
    o, d, b, l, h = ramp(base)
    rect(img, 0, 0, PW, y1, b)
    rect(img, 0, 0, PW, 3, trim); rect(img, 0, 3, PW, 4, shade(trim, -0.4))
    if stripe:
        for x in range(0, PW, stripe[0]):
            rect(img, x, 4, x + stripe[1], y1, stripe[2])
    if pattern: pattern(img, 4, y1)
    sk = skirting or shade(base, -0.35)
    rect(img, 0, y1 - 4, PW, y1 - 1, sk); rect(img, 0, y1 - 1, PW, y1, shade(sk, -0.5))

def _tile_patch(img, patch, y0):
    """Repeat a small patch over the floor, so the floor costs a handful of tiles."""
    for y in range(y0, PH, patch.height):
        for x in range(0, PW, patch.width):
            img.paste(patch, (x, y))

def floor_planks(img, base, y0=WALL * T, plank=8, seed=2, gap=None):
    o, d, b, l, h = ramp(base)
    r = random.Random(seed)
    pw_, ph_ = 48, plank * 4
    patch = Image.new('RGB', (pw_, ph_))
    for row in range(4):
        y = row * plank
        rect(patch, 0, y, pw_, y + plank, b if row % 2 else mix(b, l, 0.25))
        rect(patch, 0, y + plank - 1, pw_, y + plank, gap or d)
        seam = (row * 19 + 7) % pw_
        rect(patch, seam, y, seam + 1, y + plank - 1, gap or d)
        gx = (seam + 20) % (pw_ - 5); gy = y + 2 + r.randrange(0, plank - 4)
        rect(patch, gx, gy, gx + 4, gy + 1, d if row % 2 else l)
    _tile_patch(img, patch, y0)

def floor_tiles(img, a, b2, y0=WALL * T, size=16, grout=None):
    for y in range(y0, PH, size):
        for x in range(0, PW, size):
            c = a if ((x // size) + (y // size)) % 2 == 0 else b2
            rect(img, x, y, x + size, y + size, c)
            if grout: rect(img, x, y + size - 1, x + size, y + size, grout); rect(img, x + size - 1, y, x + size, y + size, grout)

def floor_tatami(img, y0=WALL * T):
    base = (200, 196, 120); edge = (64, 88, 56)
    for y in range(y0, PH, 32):
        for x in range(0, PW, 32):
            horiz = ((x // 32) + (y // 32)) % 2
            w_, h_ = (32, 16) if horiz else (16, 32)
            for sx in range(x, x + 32, w_):
                for sy in range(y, y + 32, h_):
                    rect(img, sx, sy, sx + w_, sy + h_, edge)
                    rect(img, sx + 1, sy + 1, sx + w_ - 1, sy + h_ - 1, base)
                    for k in range(sx + 2 if horiz else sy + 2, (sx + w_ - 2) if horiz else (sy + h_ - 2), 2):
                        if horiz: rect(img, k, sy + 2, k + 1, sy + h_ - 2, shade(base, -0.08))
                        else: rect(img, sx + 2, k, sx + w_ - 2, k + 1, shade(base, -0.08))

def floor_carpet(img, base, y0=WALL * T, seed=5):
    patch = Image.new('RGB', (32, 32), base)
    r = random.Random(seed); px = patch.load()
    for _ in range(32 * 32 // 9):
        x, y = r.randrange(0, 32), r.randrange(0, 32)
        px[x, y] = shade(base, 0.12 if r.random() < 0.5 else -0.12)
    _tile_patch(img, patch, y0)

def floor_metal(img, base, y0=WALL * T):
    o, d, b, l, h = ramp(base)
    for y in range(y0, PH, 16):
        for x in range(0, PW, 16):
            rect(img, x, y, x + 16, y + 16, b)
            rect(img, x, y, x + 16, y + 1, l); rect(img, x, y, x + 1, y + 16, l)
            rect(img, x, y + 15, x + 16, y + 16, d); rect(img, x + 15, y, x + 16, y + 16, d)
            for cx, cy in ((3, 3), (12, 3), (3, 12), (12, 12)): put(img, x + cx, y + cy, o)

def side_walls(img, col, y0=WALL * T, thick=4):
    o, d, b, l, h = ramp(col)
    rect(img, 0, 0, thick, PH, b); rect(img, thick, 0, thick + 1, PH, o)
    rect(img, PW - thick, 0, PW, PH, b); rect(img, PW - thick - 1, 0, PW - thick, PH, o)
    rect(img, 0, PH - 3, PW, PH, b); rect(img, 0, PH - 4, PW, PH - 3, o)

def shadow_under(img, x0, x1, y, k=0.25):
    px = img.load()
    for x in range(max(0, x0), min(PW, x1)):
        for dy in range(2):
            if 0 <= y + dy < PH: px[x, y + dy] = shade(px[x, y + dy], -k)

# ---- furniture: lifted from the current bedroom ------------------------------------------
_BED = None
def _bedroom_top():
    global _BED
    if _BED is None:
        k, g = mk.layout('LAYOUT_UNDERDOG_BEDROOM')
        Hh, Ww = len(g), len(g[0])
        img = Image.new('RGBA', (Ww * T, Hh * T), (0, 0, 0, 0))
        tmp = Image.new('RGB', (Ww * T, Hh * T), (255, 0, 255))
        for y in range(Hh):
            for x in range(Ww):
                m = k.mets[g[y][x] & 0x3FF]
                for i in range(4): k.tile(tmp, m[4 + i], x * T + (i % 2) * 8, y * T + (i // 2) * 8, k.pals)
        px, o = tmp.load(), img.load()
        for y in range(tmp.height):
            for x in range(tmp.width):
                if px[x, y] != (255, 0, 255): o[x, y] = px[x, y] + (255,)
        _BED = img
    return _BED

def cut(x0, y0, x1, y1):
    return _bedroom_top().crop((x0, y0, x1, y1))

def gamecube(): return cut(16, 16, 32, 32)
def wardrobe(): return cut(32, 0, 48, 32)
def pc_desk():  return cut(64, 0, 96, 48)
def bed_stamp(): return cut(112, 96, 128, 128)

def recolour(spr, pairs):
    """Swap colours by nearest match: pairs = [(from, to), ...]."""
    out = spr.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3] == 0: continue
            for f, t_ in pairs:
                if sum(abs(c[i] - f[i]) for i in range(3)) < 30:
                    px[x, y] = tuple(t_) + (255,); break
    return out

def paste(img, spr, x, y):
    img.paste(spr, (x, y), spr)

# ---- furniture: drawn ---------------------------------------------------------------------
def tv(img, x, y, t, w=24, h=18, body=(64, 64, 72), content='static', time='day'):
    """CRT on a stand, its picture animated."""
    o, d, b, l, hh = ramp(body)
    rect(img, x, y, x + w, y + h, o); rect(img, x + 1, y + 1, x + w - 1, y + h - 1, b)
    rect(img, x + 1, y + 1, x + w - 1, y + 2, l)
    sx0, sy0, sx1, sy1 = x + 3, y + 3, x + w - 6, y + h - 3
    if content == 'static':
        r = random.Random(t)
        for yy in range(sy0, sy1):
            for xx in range(sx0, sx1):
                put(img, xx, yy, (r.randrange(120, 230),) * 3)
    elif content == 'battle':
        # a battle on screen: two mons trading hits, HP bars
        rect(img, sx0, sy0, sx1, sy1, (136, 200, 120))
        rect(img, sx0, sy0 + (sy1 - sy0) // 2, sx1, sy1, (216, 200, 136))
        flash = (t // 4) % 6 == 0
        rect(img, sx0 + 2, sy1 - 5, sx0 + 6, sy1 - 1, (232, 80, 64) if not flash else (255, 255, 255))
        rect(img, sx1 - 6, sy0 + 2, sx1 - 2, sy0 + 6, (72, 120, 232))
        hp = 8 - (t // 6) % 8
        rect(img, sx0 + 1, sy0 + 1, sx0 + 1 + hp, sy0 + 2, (72, 216, 72))
        rect(img, sx1 - 9, sy1 - 2, sx1 - 1, sy1 - 1, (72, 216, 72))
    elif content == 'game':
        rect(img, sx0, sy0, sx1, sy1, (24, 24, 64))
        for i in range(4):
            bx = sx0 + ((t * 2 + i * 7) % (sx1 - sx0))
            put(img, bx, sy0 + 2 + i * 3 % (sy1 - sy0 - 2), (248, 248, 120))
        rect(img, sx0 + ((t // 2) % (sx1 - sx0 - 3)), sy1 - 3, sx0 + ((t // 2) % (sx1 - sx0 - 3)) + 3, sy1 - 1, (248, 96, 96))
    rect(img, x + w - 5, y + 4, x + w - 2, y + 5, hh); rect(img, x + w - 5, y + 7, x + w - 2, y + 8, d)
    glow_rect = (sx0, sy0, sx1, sy1)
    return glow_rect

def tv_stand(img, x, y, w=28, col=(120, 80, 48)):
    o, d, b, l, h = ramp(col)
    rect(img, x, y, x + w, y + 10, o); rect(img, x + 1, y + 1, x + w - 1, y + 9, b)
    rect(img, x + 1, y + 1, x + w - 1, y + 2, l); rect(img, x + 3, y + 4, x + w - 3, y + 8, d)

def clock(img, x, y, face=(248, 248, 240), rim=(72, 120, 200), t=0):
    for yy in range(-6, 7):
        for xx in range(-6, 7):
            d = math.hypot(xx, yy)
            if d <= 6.4: put(img, x + xx, y + yy, rim if d > 4.6 else face)
            if 5.6 < d <= 6.4: put(img, x + xx, y + yy, shade(rim, -0.5))
    a = t * 0.2
    for k in range(4): put(img, x + int(round(math.sin(a) * k)), y - int(round(math.cos(a) * k)), (40, 40, 48))
    for k in range(3): put(img, x + k, y, (200, 48, 48))

def bookshelf(img, x, y, w=16, h=30, col=(136, 88, 48), seed=4):
    o, d, b, l, hh = ramp(col)
    rect(img, x, y, x + w, y + h, o); rect(img, x + 1, y + 1, x + w - 1, y + h - 1, b)
    r = random.Random(seed)
    cols = [(200, 64, 56), (64, 112, 200), (232, 192, 72), (88, 168, 96), (168, 96, 192), (232, 232, 224)]
    for sy in range(y + 2, y + h - 3, 9):
        rect(img, x + 2, sy, x + w - 2, sy + 7, shade(col, -0.45))
        bx = x + 2
        while bx < x + w - 3:
            bw = r.choice((1, 2, 2, 3)); bh = r.randrange(4, 7)
            c = r.choice(cols)
            rect(img, bx, sy + 7 - bh, min(bx + bw, x + w - 2), sy + 7, c)
            put(img, bx, sy + 7 - bh, shade(c, 0.4))
            bx += bw
        rect(img, x + 1, sy + 7, x + w - 1, sy + 8, l)

def plant(img, x, y, kind='fern', pot=(200, 104, 64), t=0):
    """x, y: bottom-centre."""
    o, d, b, l, h = ramp(pot)
    rect(img, x - 4, y - 7, x + 4, y, o); rect(img, x - 3, y - 6, x + 3, y - 1, b); rect(img, x - 3, y - 6, x + 3, y - 5, l)
    g = [(32, 96, 48), (56, 144, 64), (104, 192, 88)]
    if kind == 'fern':
        for i, (dx, dy) in enumerate([(-5, -12), (5, -12), (-3, -17), (3, -17), (0, -20), (-7, -9), (7, -9)]):
            for k in range(7):
                put(img, x + int(dx * k / 6), y - 7 + int(dy * k / 6 * 0.7) - 1, g[(i + k) % 3 if k < 6 else 2])
                put(img, x + int(dx * k / 6) + 1, y - 7 + int(dy * k / 6 * 0.7) - 1, g[0])
    elif kind == 'cactus':
        rect(img, x - 2, y - 18, x + 2, y - 6, g[1]); rect(img, x - 2, y - 18, x - 1, y - 6, g[2]); rect(img, x + 1, y - 18, x + 2, y - 6, g[0])
        rect(img, x - 6, y - 13, x - 2, y - 11, g[1]); rect(img, x - 6, y - 16, x - 4, y - 11, g[1])
        put(img, x, y - 19, (248, 120, 160))
    elif kind == 'palm':
        rect(img, x - 1, y - 22, x + 1, y - 6, (136, 96, 56))
        for dx, dy in [(-9, 3), (9, 3), (-7, -2), (7, -2), (-2, -5), (3, -5)]:
            for k in range(9):
                put(img, x + dx * k // 8, y - 22 + dy * k // 8 + (k * k) // 18, g[1 if k < 6 else 2])
                put(img, x + dx * k // 8, y - 21 + dy * k // 8 + (k * k) // 18, g[0])
    elif kind == 'bonsai':
        rect(img, x - 1, y - 12, x + 1, y - 6, (96, 64, 40)); rect(img, x, y - 14, x + 4, y - 12, (96, 64, 40))
        for cx, cy, r_ in [(-3, -15, 4), (4, -17, 3), (0, -19, 3)]:
            for yy in range(-r_, r_ + 1):
                for xx in range(-r_ - 1, r_ + 2):
                    if xx * xx / 1.4 + yy * yy <= r_ * r_: put(img, x + cx + xx, y + cy + yy, g[1] if yy > -r_ + 1 else g[2])
    elif kind == 'blossom':
        rect(img, x - 1, y - 14, x + 1, y - 6, (96, 64, 40))
        for cx, cy, r_ in [(-4, -16, 4), (4, -17, 4), (0, -21, 4)]:
            for yy in range(-r_, r_ + 1):
                for xx in range(-r_, r_ + 1):
                    if xx * xx + yy * yy <= r_ * r_: put(img, x + cx + xx, y + cy + yy, (248, 168, 200) if (xx + yy) % 3 else (248, 216, 232))

def rug(img, x0, y0, x1, y1, base, border, pattern='plain', t=0):
    o, d, b, l, h = ramp(base)
    rect(img, x0, y0, x1, y1, border); rect(img, x0 + 2, y0 + 2, x1 - 2, y1 - 2, base)
    rect(img, x0 + 3, y0 + 3, x1 - 3, y0 + 4, l); rect(img, x0 + 3, y1 - 4, x1 - 3, y1 - 3, l)
    rect(img, x0 + 3, y0 + 3, x0 + 4, y1 - 3, l); rect(img, x1 - 4, y0 + 3, x1 - 3, y1 - 3, l)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    if pattern == 'pokeball':
        r_ = min(x1 - x0, y1 - y0) // 2 - 6
        for yy in range(-r_, r_ + 1):
            for xx in range(-r_, r_ + 1):
                dd = math.hypot(xx, yy)
                if dd <= r_:
                    c = (224, 64, 56) if yy < -1 else ((40, 40, 48) if yy <= 1 else (240, 240, 232))
                    if dd > r_ - 1.2: c = (40, 40, 48)
                    if dd < 4: c = (40, 40, 48) if dd > 2.5 else (240, 240, 232)
                    put(img, cx + xx, cy + yy, c)
    elif pattern == 'round':
        r_ = min(x1 - x0, y1 - y0) // 2
    elif pattern == 'stripes':
        for y in range(y0 + 5, y1 - 5, 6): rect(img, x0 + 5, y, x1 - 5, y + 2, d)
    elif pattern == 'diamond':
        for y in range(y0 + 5, y1 - 5):
            for x in range(x0 + 5, x1 - 5):
                if (abs(x - cx) + abs(y - cy)) % 10 < 2: put(img, x, y, d)
    elif pattern == 'star':
        for k in range(5):
            a = -math.pi / 2 + k * 2 * math.pi / 5
            for s in range(10): put(img, cx + int(math.cos(a) * s), cy + int(math.sin(a) * s * 0.8), h)

def round_rug(img, cx, cy, rx, ry, rings):
    for yy in range(-ry, ry + 1):
        for xx in range(-rx, rx + 1):
            d = (xx / rx) ** 2 + (yy / ry) ** 2
            if d <= 1:
                put(img, cx + xx, cy + yy, rings[min(len(rings) - 1, int(d * len(rings)))])

def beanbag(img, x, y, col):
    """x, y: bottom-centre."""
    o, d, b, l, h = ramp(col)
    for yy in range(-10, 1):
        for xx in range(-9, 10):
            dd = (xx / 9) ** 2 + ((yy + 4) / 6.5) ** 2
            if dd <= 1:
                c = b
                if dd > 0.8: c = o
                elif yy < -6 + abs(xx) // 4: c = l
                elif yy > -2: c = d
                put(img, x + xx, y + yy, c)
    put(img, x - 3, y - 8, h); put(img, x - 2, y - 8, h)

def sofa(img, x, y, w, col):
    o, d, b, l, h = ramp(col)
    rect(img, x, y, x + w, y + 20, o)
    rect(img, x + 1, y + 1, x + w - 1, y + 9, b); rect(img, x + 1, y + 1, x + w - 1, y + 2, l)
    rect(img, x + 1, y + 9, x + w - 1, y + 16, l); rect(img, x + 1, y + 15, x + w - 1, y + 19, d)
    rect(img, x + 1, y + 6, x + 5, y + 19, b); rect(img, x + w - 5, y + 6, x + w - 1, y + 19, b)
    for k in range(x + 5, x + w - 5, (w - 10) // 2 or 1): rect(img, k, y + 9, k + 1, y + 15, d)

def table_low(img, x, y, w, h, col):
    o, d, b, l, hh = ramp(col)
    rect(img, x, y, x + w, y + h, o); rect(img, x + 1, y + 1, x + w - 1, y + h - 3, b)
    rect(img, x + 1, y + 1, x + w - 1, y + 2, hh); rect(img, x + 1, y + h - 3, x + w - 1, y + h - 1, d)

def lamp(img, x, y, shade_col=(248, 216, 120), on=True):
    """Floor lamp; x, y bottom-centre."""
    rect(img, x - 3, y - 2, x + 4, y, (56, 48, 48)); rect(img, x, y - 22, x + 1, y - 2, (80, 72, 64))
    o, d, b, l, h = ramp(shade_col)
    for k in range(6):
        rect(img, x - 3 - k // 2, y - 30 + k, x + 4 + k // 2, y - 29 + k, b if k < 5 else d)
    rect(img, x - 3, y - 30, x + 4, y - 29, h)
    if on: light(lambda: glow(img, x, y - 26, 20, (248, 232, 160), 0.22 if STATE['time'] != 'night' else 0.35))

def fairy_lights(img, x0, x1, y, t, cols=((248, 96, 96), (248, 216, 96), (96, 200, 248), (120, 232, 120)), sag=4, _late=False):
    if not _late and STATE['time'] == 'night':
        STATE['late'].append(lambda: fairy_lights(img, x0, x1, y, t, cols, sag, True))
    for x in range(x0, x1):
        u = (x - x0) % 32 / 32
        yy = y + int(sag * math.sin(u * math.pi))
        put(img, x, yy, (48, 56, 48))
        if (x - x0) % 8 == 4:
            i = (x - x0) // 8
            c = cols[i % len(cols)]
            on = (i + t // 4) % 3 != 0
            put(img, x, yy + 1, c if on else shade(c, -0.5)); put(img, x, yy + 2, shade(c, -0.2) if on else shade(c, -0.6))
            if on: put(img, x - 1, yy + 1, mix(c, (255, 255, 255), 0.5))

def poster(img, x, y, w, h, bg, art, frame=(240, 240, 232)):
    rect(img, x, y, x + w, y + h, frame); rect(img, x + 1, y + 1, x + w - 1, y + h - 1, bg)
    art(img, x + 1, y + 1, x + w - 1, y + h - 1)
    put(img, x + w // 2, y, (200, 48, 48))

def mon_art(name, size=14):
    def art(img, x0, y0, x1, y1):
        m = mk.mon(name).crop((0, 0, 32, 32))
        bb = m.getbbox()
        if bb: m = m.crop(bb)
        sc = min((x1 - x0) / m.width, (y1 - y0) / m.height)
        m = m.resize((max(1, int(m.width * sc)), max(1, int(m.height * sc))), Image.NEAREST)
        img.paste(m, (x0 + (x1 - x0 - m.width) // 2, y1 - m.height), m)
    return art

def neon_strip(img, x0, x1, y, t, cols=((248, 72, 200), (72, 232, 248), (176, 96, 248)), _late=False):
    if not _late and STATE['time'] == 'night':
        STATE['late'].append(lambda: neon_strip(img, x0, x1, y, t, cols, True))
    for x in range(x0, x1):
        c = cols[((x - x0) // 24 + t // 6) % len(cols)]
        put(img, x, y, mix(c, (255, 255, 255), 0.5)); put(img, x, y + 1, c)
        put(img, x, y - 1, mix(img.load()[x, y - 1], c, 0.35)); put(img, x, y + 2, mix(img.load()[x, y + 2], c, 0.35))

def neon_sign(img, x, y, text, t, col=(248, 72, 200), flicker=True):
    on = not (flicker and (t % 23) in (3, 5))
    c = col if on else shade(col, -0.6)
    w = text_width(text)
    rect(img, x - 2, y - 2, x + w + 1, y + 7, (20, 16, 28))
    px = img.load()
    draw_text(px, text, x, y, c)
    if on: glow(img, x + w // 2, y + 2, max(8, w // 2 + 4), col, 0.2); draw_text(px, text, x, y, mix(c, (255, 255, 255), 0.35))

def arcade(img, x, y, t, body=(56, 40, 104), screen=(24, 24, 48)):
    """Arcade cabinet, 16 x 32, x/y top-left."""
    o, d, b, l, h = ramp(body)
    rect(img, x, y, x + 16, y + 32, o); rect(img, x + 1, y + 1, x + 15, y + 31, b)
    rect(img, x + 1, y + 1, x + 15, y + 5, (248, 200, 64)); draw_text(img.load(), 'GO', x + 4, y + 1, (200, 40, 40))
    rect(img, x + 2, y + 7, x + 14, y + 17, screen)
    for i in range(3):
        put(img, x + 3 + (t + i * 4) % 10, y + 9 + i * 3, (248, 248, 120) if i else (120, 248, 248))
    rect(img, x + 1, y + 18, x + 15, y + 22, d); put(img, x + 4, y + 19, (232, 56, 56)); put(img, x + 10, y + 20, (56, 200, 248))
    rect(img, x + 3, y + 24, x + 13, y + 30, d)

def aquarium(img, x0, y0, x1, y1, t, water=(56, 136, 216), seed=3):
    rect(img, x0, y0, x1, y1, (40, 48, 64)); wx0, wy0, wx1, wy1 = x0 + 2, y0 + 2, x1 - 2, y1 - 3
    for y in range(wy0, wy1):
        c = mix(shade(water, 0.25), shade(water, -0.25), (y - wy0) / max(1, wy1 - wy0))
        rect(img, wx0, y, wx1, y + 1, c)
    # caustic ripples
    for x in range(wx0, wx1):
        if (x + t) % 7 < 2: put(img, x, wy0 + 1 + ((x + t // 2) % 3 == 0), shade(water, 0.5))
    rect(img, wx0, wy1 - 3, wx1, wy1, (216, 200, 152))
    r = random.Random(seed)
    for k in range(max(3, (x1 - x0) // 30)):
        sx = r.randrange(wx0 + 2, wx1 - 4)
        for i in range((wy1 - wy0) // 2):
            put(img, sx + int(math.sin((t + i * 3 + k) / 4) * 1), wy1 - 4 - i, (64, 168, 72) if i % 3 else (104, 200, 96))
    fish = [((248, 152, 48), 1), ((248, 232, 96), -1), ((232, 80, 120), 1), ((120, 232, 216), -1), ((248, 248, 248), 1)][:max(3, (x1 - x0) // 50)]
    for i, (c, dirn) in enumerate(fish):
        span = wx1 - wx0 - 6
        fx = wx0 + 3 + ((t * (i + 1) // 2 + i * 13) % span if dirn > 0 else span - (t * (i + 1) // 2 + i * 13) % span)
        fy = wy0 + 3 + (i * 5) % max(1, (wy1 - wy0 - 8)) + int(math.sin(t / 5 + i))
        rect(img, fx - 2, fy, fx + 2, fy + 2, c)
        put(img, fx - 3 * dirn, fy, shade(c, -0.3)); put(img, fx - 3 * dirn, fy + 1, shade(c, -0.3))
        put(img, fx + dirn, fy, (24, 24, 32))
    for i in range(3):
        by = wy1 - 4 - ((t + i * 7) % max(1, (wy1 - wy0 - 5)))
        put(img, wx0 + 6 + i * 9, by, (216, 240, 248))
    rect(img, x0, y0, x1, y0 + 2, (120, 128, 144))
    return (wx0, wy0, wx1, wy1)

def fireplace(img, x, y, t, stone=(144, 136, 128)):
    """32 wide x 32 tall, top-left x, y."""
    o, d, b, l, h = ramp(stone)
    rect(img, x, y, x + 32, y + 32, o)
    for yy in range(y + 1, y + 31, 5):
        for xx in range(x + 1 + ((yy - y) // 5 % 2) * 3, x + 31, 7):
            rect(img, xx, yy, min(xx + 6, x + 31), yy + 4, b if (xx + yy) % 3 else l)
    rect(img, x - 2, y + 6, x + 34, y + 9, shade(stone, -0.1)); rect(img, x - 2, y + 6, x + 34, y + 7, h)
    rect(img, x + 7, y + 13, x + 25, y + 31, (24, 16, 16))
    # flames, three frames' worth of shapes
    flames = [(248, 216, 96), (248, 144, 48), (216, 64, 32)]
    for k in range(5):
        fx = x + 9 + k * 3; hgt = 6 + int(4 * abs(math.sin((t + k * 2) * 0.9)))
        for i in range(hgt):
            c = flames[min(2, i * 3 // hgt)]
            c = flames[2 - min(2, i * 3 // hgt)]
            put(img, fx, y + 29 - i, c); put(img, fx + 1, y + 29 - i, c if i < hgt - 1 else (24, 16, 16))
    rect(img, x + 9, y + 29, x + 23, y + 31, (88, 56, 40))
    light(lambda: glow(img, x + 16, y + 30, 26, (248, 160, 72), 0.25 if STATE['time'] != 'night' else 0.32))

def trophy_case(img, x, y, w, t, wood=(104, 48, 40), cups=3):
    o, d, b, l, h = ramp(wood)
    rect(img, x, y, x + w, y + 30, o); rect(img, x + 1, y + 1, x + w - 1, y + 29, b)
    for sy in (y + 3, y + 16):
        rect(img, x + 2, sy, x + w - 2, sy + 11, (64, 88, 120))
        for k in range(cups):
            cx = x + 5 + k * (w - 8) // cups
            gold = (248, 208, 64) if (k + sy) % 4 else (200, 208, 224)
            rect(img, cx, sy + 2, cx + 5, sy + 6, gold); rect(img, cx + 2, sy + 6, cx + 3, sy + 8, gold); rect(img, cx + 1, sy + 8, cx + 4, sy + 10, shade(gold, -0.3))
            put(img, cx + 1, sy + 3, (255, 255, 224)) if (t // 6 + k) % 4 == 0 else None
        rect(img, x + 1, sy + 11, x + w - 1, sy + 12, l)

def hammock(img, x0, x1, y, col=(232, 200, 120)):
    o, d, b, l, h = ramp(col)
    for x in range(x0, x1):
        u = (x - x0) / (x1 - x0)
        yy = y + int(8 * math.sin(u * math.pi))
        for k in range(4): put(img, x, yy + k, [l, b, b, d][k])
        put(img, x, yy + 4, o)
    rect(img, x0 - 1, y - 6, x0 + 1, y + 2, (120, 88, 56)); rect(img, x1 - 1, y - 6, x1 + 1, y + 2, (120, 88, 56))

def surfboard(img, x, y, col=(248, 120, 72)):
    o, d, b, l, h = ramp(col)
    for yy in range(28):
        wdt = int(3.5 * math.sin((yy + 1) / 29 * math.pi)) + 1
        rect(img, x - wdt, y + yy, x + wdt + 1, y + yy + 1, b)
        put(img, x - wdt, y + yy, o); put(img, x + wdt, y + yy, o)
    rect(img, x, y + 2, x + 1, y + 26, (248, 248, 232))

def lantern(img, x, y, t, col=(232, 72, 56)):
    o, d, b, l, h = ramp(col)
    rect(img, x, y - 6, x + 1, y, (60, 50, 40))
    for yy in range(9):
        wdt = int(4 * math.sin((yy + 1) / 10 * math.pi)) + 1
        rect(img, x - wdt + 1, y + yy, x + wdt, y + yy + 1, b if yy % 3 else d)
    rect(img, x - 1, y - 1, x + 2, y, o); rect(img, x - 1, y + 9, x + 2, y + 10, o)
    k = 0.25 + 0.08 * ((t // 3) % 2)
    def lit():
        glow(img, x, y + 4, 14, (248, 200, 120), k)
        for yy in range(9):
            wdt = int(4 * math.sin((yy + 1) / 10 * math.pi)) + 1
            rect(img, x - wdt + 1, y + yy, x + wdt, y + yy + 1, l if yy % 3 else b)
    light(lit)

def bed(img, x, y, quilt, frame=(136, 88, 56), pillow=(248, 248, 240), pattern=None, w=24, h=34, canopy=None):
    """A bed seen from above, headboard at the top; x, y top-left."""
    fo, fd, fb, fl, fh = ramp(frame)
    qo, qd, qb, ql, qh = ramp(quilt)
    rect(img, x, y, x + w, y + h, fo)
    rect(img, x + 1, y + 1, x + w - 1, y + 6, fb); rect(img, x + 1, y + 1, x + w - 1, y + 2, fl)
    rect(img, x + 2, y + 6, x + w - 2, y + h - 2, (240, 240, 232))
    box(img, x + 3, y + 7, x + w - 3, y + 14, pillow, hi=shade(pillow, 0.5), lo=shade(pillow, -0.15))
    rect(img, x + 2, y + 15, x + w - 2, y + h - 2, qb)
    rect(img, x + 2, y + 15, x + w - 2, y + 17, ql); rect(img, x + 2, y + 17, x + w - 2, y + 18, qd)
    if pattern == 'stripes':
        for yy in range(y + 21, y + h - 3, 4): rect(img, x + 2, yy, x + w - 2, yy + 1, qd)
    elif pattern == 'check':
        for yy in range(y + 18, y + h - 2):
            for xx in range(x + 2, x + w - 2):
                if ((xx - x) // 4 + (yy - y) // 4) % 2: put(img, xx, yy, ql)
    elif pattern == 'stars':
        for (dx, dy) in ((5, 22), (14, 26), (9, 30), (18, 21)): put(img, x + dx, y + dy, (248, 232, 120))
    elif pattern == 'ball':
        cx, cy = x + w // 2, y + 25
        for yy in range(-4, 5):
            for xx in range(-4, 5):
                if xx * xx + yy * yy <= 16: put(img, cx + xx, cy + yy, (224, 64, 56) if yy < 0 else ((40, 40, 48) if yy == 0 else (240, 240, 232)))
    rect(img, x + 1, y + h - 2, x + w - 1, y + h - 1, qd)
    rect(img, x + 1, y + 15, x + 2, y + h - 1, qd); rect(img, x + w - 2, y + 15, x + w - 1, y + h - 1, qd)
    if canopy:
        co, cd, cb, cl, ch = ramp(canopy)
        rect(img, x - 2, y - 3, x + w + 2, y + 1, cb); rect(img, x - 2, y - 3, x + w + 2, y - 2, cl)
        for k in (x - 2, x + w): rect(img, k, y - 3, k + 2, y + h, cd)
    shadow_under(img, x + 1, x + w + 1, y + h)

# ---- sprites for scale ---------------------------------------------------------------------
def player_sprite():
    for p in ('graphics/object_events/pics/people/brendan/walking.png', 'graphics/object_events/pics/people/brendan/running.png'):
        if os.path.exists(mk.R + p): return mk.person(p)
    return None

def stamp_mon(img, name, mx, my, dy=0, frame=0):
    m = mk.mon(name, frame)
    img.paste(m, (mx * T + 8 - m.width // 2, my * T + 16 - m.height + dy), m)

def stamp_player(img, mx, my):
    p = player_sprite()
    if p: img.paste(p, (mx * T, my * T + 16 - p.height), p)

def tile_budget(img):
    px = img.load(); tiles = set()
    for ty in range(0, img.height, 8):
        for tx in range(0, img.width, 8):
            tiles.add(tuple(px[tx + x, ty + y] for y in range(8) for x in range(8)))
    colours = set(img.getdata())
    return len(tiles), len(colours)

def save_gif(frames, path, ms=120, scale=3):
    big = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    big[0].save(path, save_all=True, append_images=big[1:], duration=ms, loop=0)
