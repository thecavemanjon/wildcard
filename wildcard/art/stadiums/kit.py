# Stadium mockup kit: draws stadium maps at GBA pixel scale (16px metatiles),
# with a crowd that moves. Everything is drawn here rather than lifted from
# Emerald's tilesets (the Battle Dome's stands are empty seats), so each
# animation can be built later as tile frames (crowd poses, boards, flags) or
# palette cycles (camera flashes, glowsticks, lights).
import sys, random, math
sys.path.insert(0, '../arenas')
from PIL import Image, ImageDraw
import mapkit as mk

T = 16  # metatile size
SCREEN_W, SCREEN_H = 240, 160

def shade(c, k):
    """Lighter (k > 0) or darker (k < 0), by a fraction."""
    if k >= 0: return tuple(int(v + (255 - v) * k) for v in c)
    return tuple(int(v * (1 + k)) for v in c)

def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ---- a tiny LED font (3x5) -----------------------------------------------------------
FONT = {
    'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110',
    'E': '111100110100111', 'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101',
    'I': '111010010010111', 'J': '001001001101010', 'K': '101101110101101', 'L': '100100100100111',
    'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010', 'P': '110101110100100',
    'Q': '010101101110011', 'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010',
    'U': '101101101101111', 'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101',
    'Y': '101101010010010', 'Z': '111001010100111', ' ': '000000000000000', '!': '010010010000010',
    '0': '111101101101111', '1': '010110010010111', '2': '110001010100111', '3': '110001010001110',
    '4': '101101111001001', '5': '111100110001110', '6': '011100111101111', '7': '111001010010010',
    '8': '111101111101111', '9': '111101111001110', '.': '000000000000010', '-': '000000111000000',
    '*': '000101010101000', '>': '100010001010100',
}

def text_width(s): return len(s) * 4

def draw_text(px, s, x, y, col, clip=None):
    for ch in s:
        g = FONT.get(ch.upper(), FONT[' '])
        for i, b in enumerate(g):
            if b == '1':
                xx, yy = x + i % 3, y + i // 3
                if clip is None or (clip[0] <= xx < clip[2] and clip[1] <= yy < clip[3]):
                    px[xx, yy] = col
        x += 4

# ---- spectators ------------------------------------------------------------------------
SKINS = [((248, 208, 168), (216, 160, 120)), ((224, 168, 120), (184, 128, 88)),
         ((168, 112, 72), (128, 80, 48)), ((248, 224, 200), (224, 184, 152))]
HAIRS = [(56, 40, 32), (120, 72, 40), (232, 200, 96), (40, 40, 48), (176, 64, 40), (200, 200, 208)]

class Fan:
    def __init__(self, rnd, shirts, skins=SKINS, hairs=HAIRS):
        self.skin = rnd.choice(skins); self.hair = rnd.choice(hairs)
        self.shirt = rnd.choice(shirts); self.hat = rnd.random() < 0.18
        self.hatcol = rnd.choice(shirts); self.long = rnd.random() < 0.35
        self.flip = rnd.random() < 0.5

def _put(px, x, y, c, ox, oy, w, h, mask):
    if 0 <= x < w and 0 <= y < h:
        mask[(x, y)] = c

def draw_fan(img, ox, oy, fan, pose='sit', facing='front', outline=(32, 28, 40), card=None, light=None):
    """One spectator in a 16x16 cell at (ox, oy). Poses: sit, bob, cheer, stand,
    camera, flash, flag0/flag1, card, glow. Facing back = seen from behind."""
    m = {}
    lift = {'bob': 1, 'stand': 3, 'cheer': 1}.get(pose, 0)
    skin, skin_d = fan.skin; sh = fan.shirt; sh_d = shade(sh, -0.3)
    hy = 3 - lift
    put = lambda x, y, c: m.__setitem__((x, y), c)
    # body
    for y in range(8 - lift, 14):
        for x in range(4, 12):
            if y == 8 - lift and x in (4, 11): continue
            put(x, y, sh_d if x >= 10 else sh)
    # head
    for y in range(hy, hy + 5):
        for x in range(5, 11):
            if y == hy and x in (5, 10): continue
            put(x, y, skin_d if x == 10 else skin)
    if facing == 'front':
        for x in range(5, 11): put(x, hy, fan.hair)
        put(5, hy + 1, fan.hair); put(10, hy + 1, fan.hair)
        if fan.long: put(5, hy + 2, fan.hair); put(10, hy + 2, fan.hair); put(5, hy + 3, fan.hair); put(10, hy + 3, fan.hair)
        if pose not in ('camera', 'flash'):
            put(6, hy + 2, outline); put(9, hy + 2, outline)
            if pose in ('cheer', 'stand'): put(7, hy + 4, (160, 48, 56)); put(8, hy + 4, (160, 48, 56))
    else:  # back of the head
        for y in range(hy, hy + 5):
            for x in range(5, 11):
                if (x, y) in m: put(x, y, fan.hair if not (y == hy + 4 and x in (5, 10)) else skin_d)
    if fan.hat:
        for x in range(5, 11): put(x, hy - 1, fan.hatcol); put(x, hy, fan.hatcol)
        if facing == 'front':
            for x in range(4, 12): put(x, hy + 1 if False else hy, fan.hatcol)
    # arms
    if pose in ('cheer', 'stand'):
        for y in range(hy - 1, 9 - lift + 1):
            put(3, y, sh); put(12, y, sh_d)
        put(3, hy - 2, skin); put(12, hy - 2, skin); put(3, hy - 3, skin); put(12, hy - 3, skin)
    elif pose in ('flag0', 'flag1', 'glow'):
        for y in range(hy, 9):
            put(12, y, sh_d)
        put(12, hy - 1, skin)
        if pose == 'glow':
            put(12, hy - 2, light); put(12, hy - 3, light); put(12, hy - 4, shade(light, 0.5))
        else:
            for y in range(hy - 9, hy - 1): put(12, y, (120, 96, 72))
            wave = 0 if pose == 'flag0' else 1
            for y in range(4):
                for x in range(5):
                    yy = hy - 9 + y + (1 if (x + wave) % 4 >= 2 else 0)
                    put(13 + x if not fan.flip else 11 - x, yy, card if y < 2 else shade(card, -0.25))
    elif pose in ('camera', 'flash') and facing == 'front':
        for y in range(hy + 1, hy + 4):
            for x in range(6, 10): put(x, y, (72, 72, 84))
        put(7, hy + 2, (24, 24, 32))
        if pose == 'flash':
            for x, y in [(7, hy + 2), (6, hy + 2), (8, hy + 2), (7, hy + 1), (7, hy + 3), (7, hy)]: put(x, y, (255, 255, 255))
        put(5, hy + 4, skin); put(10, hy + 4, skin)
    elif pose == 'card':
        # the card goes up over the head, so the stand reads as one picture
        m.clear()
        for y in range(1, 15):
            for x in range(1, 15): put(x, y, card(ox + x, oy + y) if callable(card) else card)
        for y in (0, 15): put(4, y, skin); put(11, y, skin)
    else:
        put(4, 12, skin); put(11, 12, skin_d)
    # outline the silhouette, then paint
    if fan.flip and pose not in ('flag0', 'flag1', 'card'):
        m = {(15 - x, y): c for (x, y), c in m.items()}
    px = img.load(); W, H = img.size
    for (x, y), c in list(m.items()):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in m and 0 <= k[0] < 16 and -6 <= k[1] < 16:
                X, Y = ox + k[0], oy + k[1]
                if 0 <= X < W and 0 <= Y < H: px[X, Y] = outline
    for (x, y), c in m.items():
        X, Y = ox + x, oy + y
        if 0 <= X < W and 0 <= Y < H: px[X, Y] = c

def draw_seat(img, ox, oy, seat, riser, facing='front', empty=False):
    d = ImageDraw.Draw(img)
    d.rectangle([ox, oy, ox + 15, oy + 15], fill=riser)
    d.rectangle([ox, oy + 14, ox + 15, oy + 15], fill=shade(riser, -0.25))
    if facing == 'front':
        d.rectangle([ox + 2, oy + 3, ox + 13, oy + 13], fill=shade(seat, -0.2))
        d.rectangle([ox + 3, oy + 3, ox + 12, oy + 4], fill=shade(seat, 0.2))
        d.rectangle([ox + 3, oy + 5, ox + 12, oy + 12], fill=seat)
        if empty:
            d.rectangle([ox + 2, oy + 11, ox + 13, oy + 13], fill=shade(seat, 0.1))

def draw_seat_front_back(img, ox, oy, seat):
    """The seat back in front of a fan seen from behind."""
    d = ImageDraw.Draw(img)
    d.rectangle([ox + 2, oy + 10, ox + 13, oy + 15], fill=shade(seat, -0.15))
    d.rectangle([ox + 2, oy + 10, ox + 13, oy + 10], fill=shade(seat, 0.15))

# ---- crowd blocks ----------------------------------------------------------------------
class Crowd:
    """A rectangle of seats, in metatiles. Each seat has a fan (or is empty) and
    a column phase, which is what a Mexican wave keys off."""
    def __init__(self, x, y, w, h, scheme, facing='front', seed=0, density=0.9, aisles=(), card_art=None):
        self.x, self.y, self.w, self.h, self.s, self.facing = x, y, w, h, scheme, facing
        rnd = random.Random(seed)
        self.aisles = set(aisles); self.card_art = card_art
        self.fans = {}
        for j in range(h):
            for i in range(w):
                if i in self.aisles: continue
                if rnd.random() < density:
                    f = Fan(rnd, scheme['shirts'], scheme.get('skins', SKINS), scheme.get('hairs', HAIRS))
                    f.camera = rnd.random() < 0.12; f.flag = rnd.random() < 0.06
                    f.phase = rnd.random(); f.glowcol = rnd.choice(scheme.get('glow', [(255, 255, 255)]))
                    self.fans[i, j] = f

    def draw(self, img, t, mode):
        s = self.s
        if s.get('crowd_style', 'blobs') != 'figures':
            return draw_dense(self, img, t, mode, s.get('crowd_style', 'blobs'))
        for j in range(self.h):
            for i in range(self.w):
                ox, oy = (self.x + i) * T, (self.y + j) * T
                if i in self.aisles:
                    d = ImageDraw.Draw(img); d.rectangle([ox, oy, ox + 15, oy + 15], fill=s['aisle'])
                    for k in range(0, 16, 4): d.rectangle([ox, oy + k, ox + 15, oy + k + 1], fill=shade(s['aisle'], -0.15))
                    continue
                f = self.fans.get((i, j))
                draw_seat(img, ox, oy, s['seat'], s['riser'], self.facing, f is None)
        # fans draw after every seat so raised arms overlap the row above
        order = sorted(self.fans.items(), key=lambda kv: -kv[0][1]) if self.facing == 'front' else sorted(self.fans.items(), key=lambda kv: kv[0][1])
        for (i, j), f in order:
            ox, oy = (self.x + i) * T, (self.y + j) * T
            pose, card = self.pose(f, i, j, t, mode)
            draw_fan(img, ox, oy, f, pose, self.facing, s.get('outline', (32, 28, 40)), card, f.glowcol if pose == 'glow' else None)
            if self.facing == 'back': draw_seat_front_back(img, ox, oy, s['seat'])

    def pose(self, f, i, j, t, mode):
        """t runs 0..1 over the loop."""
        X = self.x + i
        if mode == 'card' and self.card_art:
            # each card is a patch of one big picture drawn across the whole block;
            # a picture holds, then a ripple runs along the stand flipping to the next
            n = len(self.card_art); seg = t * n; k = int(seg); u = seg - k
            flip = (u - 0.6) / 0.4 * (self.w + 2) - 1 if u > 0.6 else -99
            idx = (k + 1) % n if i < flip - 1 else k % n
            if flip - 1 <= i < flip: return 'cheer', None
            art = self.card_art[idx]; X0, Y0 = self.x * T, self.y * T; Wp, Hp = self.w * T, self.h * T
            return 'card', (lambda x, y: art(x - X0, y - Y0, Wp, Hp))
        if 'wave' in mode:
            # the wave runs left to right across the whole map width
            pos = t * (self.s['map_w'] + 8) - 4
            dist = X - pos
            if -1.0 <= dist <= 0.0: return 'stand', None
            if 0.0 < dist <= 1.0 or -2.0 <= dist < -1.0: return 'cheer', None
        if 'cheer' in mode:
            beat = int(t * 12 + f.phase * 2) % 2
            if f.phase < (0.65 if isinstance(f, Fan) else 0.3): return ('cheer' if beat else 'bob'), None
        if 'glow' in mode and f.phase < 0.5:
            return 'glow', None
        if 'flash' in mode and f.camera:
            k = int(t * 24 + f.phase * 97) % 24
            return ('flash' if k == 0 else 'camera'), None
        if 'flags' in mode and f.flag:
            return ('flag0' if int(t * 8 + f.phase * 4) % 2 else 'flag1'), self.s['flag']
        if 'idle' in mode or 'cheer' in mode or 'flash' in mode or 'flags' in mode or 'glow' in mode:
            return ('bob' if int(t * 6 + f.phase * 6) % 6 == 0 else 'sit'), None
        return 'sit', None

# ---- set pieces ------------------------------------------------------------------------
def rect(img, x0, y0, x1, y1, c):
    ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=c)

def led_board(img, y, x0, x1, text, t, s, speed=1.0, rows=1):
    """A strip of LED boards one metatile tall, the text scrolling right to left."""
    Y = y * T; X0, X1 = x0 * T, x1 * T
    rect(img, X0, Y, X1 - 1, Y + 15, s['board_frame'])
    rect(img, X0, Y + 2, X1 - 1, Y + 12, s['board'])
    rect(img, X0, Y + 13, X1 - 1, Y + 13, shade(s['board_frame'], 0.3))
    px = img.load()
    for X in range(X0, X1, 2):  # LED grain
        for YY in range(Y + 3, Y + 12, 2): px[X, YY] = shade(s['board'], 0.08)
    seg = text + '   '
    w = text_width(seg); off = int(t * w * speed) % w
    x = X0 - off
    while x < X1:
        draw_text(px, seg, x, Y + 5, s['board_text'], (X0, Y + 2, X1, Y + 13)); x += w
    for X in range(X0 + 48, X1, 64): rect(img, X, Y + 2, X, Y + 12, s['board_frame'])

_r = random.Random(7)
SAND = [[_r.random() < 0.85 for _ in range(32)] for _ in range(32)]

def pitch(img, x0, y0, x1, y1, s, t=0):
    """A pitch in metatiles [x0, x1) x [y0, y1)."""
    X0, Y0, X1, Y1 = x0 * T, y0 * T, x1 * T - 1, y1 * T - 1
    kind = s['pitch']; a, b = s['pitch_a'], s['pitch_b']; line = s['line']
    px = img.load(); rnd = random.Random(7)
    for Y in range(Y0, Y1 + 1):
        for X in range(X0, X1 + 1):
            if kind == 'grass': c = a if ((X - X0) // 16) % 2 == 0 else b
            elif kind == 'sand': c = a if SAND[(Y - Y0) % 32][(X - X0) % 32] else b  # repeats, so tiles can be shared
            elif kind == 'ice':
                c = a
                if (X + Y * 2) % 37 < 2: c = b
            elif kind == 'neon':
                c = a
                if (X - X0) % 16 == 0 or (Y - Y0) % 16 == 0:
                    c = mix(a, b, 0.5 + 0.5 * math.sin(t * 2 * math.pi + (X + Y) / 24))
            elif kind == 'water':
                c = a
                if (X // 2 + Y + int(t * 16)) % 11 == 0 and (Y // 3 + X // 7) % 3 == 0: c = b
            elif kind == 'wood': c = a if ((Y - Y0) // 4) % 2 == 0 else b; c = shade(c, -0.08) if (X - X0 + ((Y - Y0) // 4) * 23) % 48 == 0 else c
            elif kind == 'tatami': c = a if (((X - X0) // 32) + ((Y - Y0) // 16)) % 2 == 0 else b
            else: c = a
            px[X, Y] = c
    if s.get('lines', True):
        d = ImageDraw.Draw(img)
        d.rectangle([X0 + 4, Y0 + 4, X1 - 4, Y1 - 4], outline=line)
        cx, cy = (X0 + X1) // 2, (Y0 + Y1) // 2
        d.line([cx, Y0 + 4, cx, Y1 - 4], fill=line)
        r = min(14, (Y1 - Y0) // 2 - 6)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=line)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline=line, fill=s.get('spot', line))

def floodlight(img, X, Y, s, t, on=True):
    d = ImageDraw.Draw(img)
    d.rectangle([X + 6, Y + 8, X + 9, Y + 47], fill=s.get('pole', (90, 90, 104)))
    d.rectangle([X, Y, X + 15, Y + 9], fill=(70, 70, 84))
    lamp = (255, 252, 220) if on else (120, 120, 120)
    for k in range(4):
        d.rectangle([X + 1 + k * 4, Y + 1, X + 2 + k * 4, Y + 3], fill=lamp)
        d.rectangle([X + 1 + k * 4, Y + 5, X + 2 + k * 4, Y + 7], fill=lamp)

def glow(img, cx, cy, r, col, strength=0.35):
    px = img.load(); W, H = img.size
    for y in range(max(0, cy - r), min(H, cy + r)):
        for x in range(max(0, cx - r), min(W, cx + r)):
            dd = math.hypot(x - cx, y - cy) / r
            if dd < 1:
                k = strength * (1 - dd)
                # posterise to 3 steps so it reads as pixel art, not a blur
                k = round(k * 3) / 3 * strength * 2 if k > 0.04 else 0
                if k: px[x, y] = mix(px[x, y], col, min(k, 0.6))

def sky(img, top, bottom, h):
    px = img.load()
    for y in range(h):
        c = mix(top, bottom, round(y / max(1, h - 1) * 5) / 5)
        for x in range(img.width): px[x, y] = c

def stars(img, h, t, seed=3):
    rnd = random.Random(seed); px = img.load()
    for _ in range(img.width // 6):
        x, y = rnd.randrange(img.width), rnd.randrange(h)
        if (int(t * 8) + x) % 7: px[x, y] = (230, 230, 255)

def jumbotron(img, x, y, w, h, s, t, content):
    X, Y = x * T, y * T
    rect(img, X - 2, Y - 2, X + w * T + 1, Y + h * T + 1, (40, 40, 52))
    rect(img, X, Y, X + w * T - 1, Y + h * T - 1, s.get('screen', (24, 40, 72)))
    rect(img, X + w * T // 2 - 2, Y + h * T + 2, X + w * T // 2 + 1, Y + h * T + 15, (60, 60, 72))
    content(img, X, Y, w * T, h * T, t)

def torch(img, X, Y, t, phase=0):
    d = ImageDraw.Draw(img)
    d.rectangle([X + 6, Y + 8, X + 9, Y + 15], fill=(96, 72, 48))
    d.rectangle([X + 4, Y + 7, X + 11, Y + 8], fill=(64, 48, 32))
    f = int(t * 12 + phase) % 3
    flames = [[(7, 1), (8, 2), (6, 3), (9, 3)], [(8, 0), (7, 2), (9, 2), (6, 4)], [(7, 0), (6, 2), (9, 1), (8, 3)]][f]
    for y in range(2, 7):
        for x in range(5, 11):
            if abs(x - 7.5) + abs(y - 5) * 0.6 < 3.2: img.putpixel((X + x, Y + y), (248, 128, 32))
    for x, y in flames: img.putpixel((X + x, Y + y), (248, 200, 64))
    for x in (7, 8): img.putpixel((X + x, Y + 5), (255, 248, 200))

def flag(img, X, Y, col, t, phase=0):
    d = ImageDraw.Draw(img)
    d.rectangle([X + 2, Y, X + 3, Y + 31], fill=(200, 200, 208))
    w = int(t * 8 + phase) % 4
    for x in range(12):
        dy = [0, 1, 1, 0][(x // 3 + w) % 4]
        d.rectangle([X + 4 + x, Y + 2 + dy, X + 4 + x, Y + 9 + dy], fill=col if x % 6 < 5 else shade(col, -0.2))

def cloud(img, X, Y, w, col):
    d = ImageDraw.Draw(img)
    d.rectangle([X, Y + 6, X + w, Y + 12], fill=col)
    d.ellipse([X + 4, Y, X + 4 + w // 2, Y + 12], fill=col)
    d.ellipse([X + w // 3, Y - 4, X + w // 3 + w // 2, Y + 10], fill=col)
    d.rectangle([X, Y + 11, X + w, Y + 12], fill=shade(col, -0.12))

# ---- sprites -----------------------------------------------------------------------------
def person(name):
    for d in ('', 'red/'):
        try: return mk.person(f'graphics/object_events/pics/people/{d}{name}.png')
        except FileNotFoundError: pass
    raise FileNotFoundError(name)

def person_frame(name, frame):
    for d in ('', 'red/'):
        try: return mk.person(f'graphics/object_events/pics/people/{d}{name}.png', frame=frame)
        except (FileNotFoundError, IndexError): pass
    return person(name)

def mon(name, frame=0): return mk.mon(name, frame)

def stamp(img, spr, mx, my, dy=0):
    img.paste(spr, (mx * T + 8 - spr.width // 2, my * T + 16 - spr.height + dy), spr)

# ---- output --------------------------------------------------------------------------------
def screen_crop(img, px_x, px_y):
    """The 240x160 view with the player's metatile at screen column 7, row 4."""
    X = px_x * T - 7 * T; Y = px_y * T - 4 * T - 8
    X = max(0, min(img.width - SCREEN_W, X)); Y = max(0, min(img.height - SCREEN_H, Y))
    return img.crop((X, Y, X + SCREEN_W, Y + SCREEN_H))

def tile_budget(img):
    """Unique 8x8 tiles and the 15-colour palettes they'd need (greedy packing).
    A rough check against a secondary tileset's 512 tiles / 7 palettes, per frame."""
    px = img.load(); tiles = set(); sets = []
    for ty in range(0, img.height, 8):
        for tx in range(0, img.width, 8):
            t = tuple(px[tx + x, ty + y] for y in range(8) for x in range(8))
            tiles.add(t)
    for t in tiles:
        cs = frozenset(t)
        sets.append(cs)
    pals = []
    for cs in sorted(set(sets), key=len, reverse=True):
        for p in pals:
            if len(p | cs) <= 15: p |= cs; break
        else: pals.append(set(cs))
    return len(tiles), len(pals)

def save_gif(frames, path, ms=100, scale=3):
    big = [f.resize((f.width * scale, f.height * scale), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255) for f in frames]
    big[0].save(path, save_all=True, append_images=big[1:], duration=ms, loop=0, optimize=False, disposal=2)

# ---- other crowd styles ----------------------------------------------------------------
# 'figures' (above) is one seated person per seat, outlined. The others pack
# people tighter and drop the seat grid, which is how distant crowds read:
#   contest  heads and shoulders overlapping, outlines a darker shade of each
#            colour, after Emerald's contest audience (graphics/contest/audience.png)
#   blobs    two people per seat and two rows per step: a head and a shirt each
#   dots     the title screen's crowd: a head pixel over a shirt pixel
class Person:
    def __init__(self, rnd, s, x, y):
        self.x, self.y = x, y
        self.skin = rnd.choice(s.get('skins', SKINS)); self.hair = rnd.choice(s.get('hairs', HAIRS))
        self.shirt = rnd.choice(s['shirts']); self.phase = rnd.random()
        self.camera = rnd.random() < 0.12; self.flag = rnd.random() < 0.05
        self.glowcol = rnd.choice(s.get('glow', [(255, 255, 255)]))
        self.hairstyle = rnd.choice(['short', 'short', 'long', 'bun', 'cap', 'spiky'])
        self.capcol = rnd.choice(s['shirts']); self.dy = rnd.choice([0, 0, 0, 1, 2])  # kids sit lower

def dense_people(crowd, style):
    rnd = random.Random(hash((crowd.x, crowd.y, style)) & 0xFFFF)
    s = crowd.s; people = []
    sx, sy = {'contest': (9, 16), 'blobs': (8, 8), 'dots': (4, 4)}[style]
    for j in range(crowd.h * T // sy):
        for k in range(crowd.w * T // sx):
            x = crowd.x * T + k * sx + (sx // 2 if (j % 2 and style != 'contest') else 0) + (rnd.randint(-2, 2) if style == 'contest' else 0)
            i = (x - crowd.x * T) // T
            if i in crowd.aisles or rnd.random() > s.get('density', 0.92): continue
            people.append(Person(rnd, s, x, crowd.y * T + j * sy))
    return people

def _paint(px, pts, W, H):
    for (x, y), c in pts.items():
        if 0 <= x < W and 0 <= y < H: px[x, y] = c

def _rimmed(px, pts, W, H):
    """Paint {(x, y): colour}, then edge each colour's region in a darker shade of itself."""
    for (x, y), c in pts.items():
        if 0 <= x < W and 0 <= y < H: px[x, y] = c
    for (x, y), c in pts.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1)):
            k = (x + dx, y + dy)
            if k not in pts and 0 <= k[0] < W and 0 <= k[1] < H: px[k] = shade(c, -0.45)

def draw_contest_person(px, p, pose, facing, card, W, H):
    lift = {'bob': 1, 'stand': 3, 'cheer': 1}.get(pose, 0)
    x0, y0 = p.x - 4, p.y + 1 + p.dy - lift
    skin, skin_d = p.skin; sh, sh_d = p.shirt, shade(p.shirt, -0.25)
    pts = {}
    if pose == 'card':
        for y in range(y0 + 1, y0 + 15):
            for x in range(x0 - 1, x0 + 9): pts[x, y] = card(x, y) if callable(card) else card
        _rimmed(px, pts, W, H); return
    for y in range(y0 + 7, y0 + 18):  # shoulders and body, cut off by the row in front
        for x in range(x0, x0 + 9):
            if y == y0 + 7 and x in (x0, x0 + 8): continue
            pts[x, y] = sh_d if x >= x0 + 7 else sh
    for y in range(y0, y0 + 7):  # head
        for x in range(x0 + 1, x0 + 8):
            if (y in (y0, y0 + 6)) and x in (x0 + 1, x0 + 7): continue
            pts[x, y] = skin_d if x == x0 + 7 or y == y0 + 6 else skin
    hair = p.hair
    if facing == 'back':
        for (x, y) in list(pts):
            if y < y0 + 6: pts[x, y] = hair if x < x0 + 7 else shade(hair, -0.2)
    else:
        for x in range(x0 + 1, x0 + 8): pts[x, y0] = hair; pts[x, y0 + 1] = hair
        pts[x0 + 1, y0 + 2] = hair; pts[x0 + 7, y0 + 2] = hair
        if p.hairstyle == 'long':
            for y in range(y0 + 2, y0 + 8): pts[x0 + 1, y] = hair; pts[x0 + 7, y] = hair
        if p.hairstyle == 'spiky':
            for x in (x0 + 2, x0 + 4, x0 + 6): pts[x, y0 - 1] = hair
        if pose not in ('camera', 'flash'):
            pts[x0 + 3, y0 + 3] = shade(skin, -0.6); pts[x0 + 5, y0 + 3] = shade(skin, -0.6)
    if p.hairstyle == 'bun': pts[x0 + 4, y0 - 1] = hair; pts[x0 + 3, y0 - 1] = hair; pts[x0 + 4, y0 - 2] = hair
    if p.hairstyle == 'cap':
        for x in range(x0 + 1, x0 + 8): pts[x, y0] = p.capcol; pts[x, y0 - 1] = p.capcol if x0 + 1 < x < x0 + 7 else pts.get((x, y0 - 1), p.capcol)
        if facing != 'back': pts[x0 + 8, y0 + 1] = p.capcol
    _rimmed(px, pts, W, H); pts = {}
    if pose in ('cheer', 'stand'):
        for y in range(y0 - 1, y0 + 8): pts[x0, y] = sh; pts[x0 + 8, y] = sh_d
        for y in (y0 - 2, y0 - 3): pts[x0, y] = skin; pts[x0 + 8, y] = skin_d
    elif pose == 'glow':
        for y in range(y0 - 1, y0 + 8): pts[x0 + 9, y] = sh_d
        pts[x0 + 9, y0 - 2] = skin
        for y in (y0 - 3, y0 - 4, y0 - 5): pts[x0 + 9, y] = card
    elif pose in ('flag0', 'flag1'):
        for y in range(y0 - 1, y0 + 8): pts[x0 + 9, y] = sh_d
        for y in range(y0 - 9, y0 - 1): pts[x0 + 9, y] = (120, 96, 72)
        w = 0 if pose == 'flag0' else 1
        for yy in range(4):
            for xx in range(5): pts[x0 + 10 + xx, y0 - 9 + yy + (1 if (xx + w) % 4 >= 2 else 0)] = card if yy < 2 else shade(card, -0.25)
    elif pose in ('camera', 'flash') and facing == 'front':
        for y in range(y0 + 2, y0 + 5):
            for x in range(x0 + 2, x0 + 7): pts[x, y] = (72, 72, 84)
        if pose == 'flash':
            for d in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0, -2), (2, 0), (-2, 0)): pts[x0 + 4 + d[0], y0 + 3 + d[1]] = (255, 255, 255)
    _paint(px, pts, W, H)

def draw_blob(px, p, pose, facing, card, W, H, small=False):
    lift = {'bob': 1, 'stand': 2, 'cheer': 1}.get(pose, 0)
    skin = p.skin[0]; sh = p.shirt
    if small:  # dots: one head pixel over two shirt pixels
        x, y = p.x, p.y + 1 - lift
        cols = {(x, y): p.hair if facing == 'back' else skin, (x, y + 1): sh, (x + 1, y + 1): shade(sh, -0.2), (x + 1, y): p.hair}
        if pose == 'card': cols = {(x, y): card(x, y), (x + 1, y): card(x + 1, y), (x, y + 1): card(x, y + 1), (x + 1, y + 1): card(x + 1, y + 1)} if callable(card) else {}
        if pose in ('cheer', 'stand'): cols[(x - 1, y - 1)] = skin; cols[(x + 2, y - 1)] = skin
        if pose == 'flash': cols[(x, y)] = (255, 255, 255)
        if pose == 'glow': cols[(x + 2, y - 1)] = card
        for (a, b), c in cols.items():
            if 0 <= a < W and 0 <= b < H: px[a, b] = c
        return
    x0, y0 = p.x - 3, p.y + 1 - lift
    pts = {}
    if pose == 'card':
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + 7): pts[x, y] = card(x, y) if callable(card) else card
        _rimmed(px, pts, W, H); return
    for y in range(y0 + 4, y0 + 9):
        for x in range(x0, x0 + 7):
            if y == y0 + 4 and x in (x0, x0 + 6): continue
            pts[x, y] = sh if x < x0 + 5 else shade(sh, -0.25)
    for y in range(y0, y0 + 4):
        for x in range(x0 + 1, x0 + 6):
            if y == y0 and x in (x0 + 1, x0 + 5): continue
            pts[x, y] = (p.hair if (facing == 'back' or y == y0) else (skin if x < x0 + 5 else p.skin[1]))
    _rimmed(px, pts, W, H); pts = {}
    if pose in ('cheer', 'stand'):
        for y in range(y0 - 1, y0 + 5): pts[x0, y] = sh; pts[x0 + 6, y] = sh
        pts[x0, y0 - 2] = skin; pts[x0 + 6, y0 - 2] = skin
    elif pose == 'flash': pts[x0 + 3, y0 + 2] = (255, 255, 255); pts[x0 + 2, y0 + 2] = (255, 255, 255); pts[x0 + 4, y0 + 2] = (255, 255, 255); pts[x0 + 3, y0 + 1] = (255, 255, 255)
    elif pose == 'glow':
        for y in range(y0 - 3, y0 + 5): pts[x0 + 7, y] = sh if y > y0 - 1 else card
    elif pose in ('flag0', 'flag1'):
        for y in range(y0 - 6, y0 + 5): pts[x0 + 7, y] = (120, 96, 72)
        for yy in range(3):
            for xx in range(4): pts[x0 + 8 + xx, y0 - 6 + yy + (1 if (xx + (pose == 'flag1')) % 4 >= 2 else 0)] = card
    _rimmed(px, pts, W, H)

def draw_dense(crowd, img, t, mode, style):
    s = crowd.s
    if not hasattr(crowd, '_people'): crowd._people = {}
    if style not in crowd._people:
        if style == 'mixed':  # contest crowd in the two rows nearest the pitch, blobs behind them
            near = set(range(crowd.h - 2, crowd.h)) if crowd.facing == 'front' else {0, 1}
            if crowd.h <= 3: near = set(range(crowd.h))
            crowd._people[style] = ([p for p in dense_people(crowd, 'contest') if (p.y - crowd.y * T) // T in near] +
                                    [p for p in dense_people(crowd, 'blobs') if (p.y - crowd.y * T) // T not in near])
            for p in crowd._people[style]: p.kind = 'contest' if (p.y - crowd.y * T) // T in near else 'blobs'
        else:
            crowd._people[style] = dense_people(crowd, style)
            for p in crowd._people[style]: p.kind = style
    d = ImageDraw.Draw(img)
    back = shade(s['riser'], -0.35)
    for j in range(crowd.h):  # the stand behind: dark, with each step's lip
        Y = (crowd.y + j) * T
        d.rectangle([crowd.x * T, Y, (crowd.x + crowd.w) * T - 1, Y + 15], fill=back)
        d.rectangle([crowd.x * T, Y + 14, (crowd.x + crowd.w) * T - 1, Y + 15], fill=shade(s['seat'], -0.35))
    for i in crowd.aisles:
        X = (crowd.x + i) * T
        d.rectangle([X, crowd.y * T, X + 15, (crowd.y + crowd.h) * T - 1], fill=s['aisle'])
        for k in range(crowd.y * T, (crowd.y + crowd.h) * T, 4): d.rectangle([X, k, X + 15, k + 1], fill=shade(s['aisle'], -0.15))
    px = img.load(); W, H = img.size
    clip_y1 = (crowd.y + crowd.h) * T
    people = crowd._people[style]
    order = people if crowd.facing == 'front' else people  # rows top to bottom: nearer rows overlap
    for p in sorted(order, key=lambda p: p.y):
        i = (p.x - crowd.x * T) / T; j = (p.y - crowd.y * T) // T
        pose, card = crowd.pose(p, i, j, t, mode)
        if pose == 'glow': card = p.glowcol
        if pose in ('flag0', 'flag1'): card = s['flag']
        Hc = min(H, clip_y1)
        if p.kind == 'contest': draw_contest_person(px, p, pose, crowd.facing, card, W, Hc)
        else: draw_blob(px, p, pose, crowd.facing, card, W, Hc, small=(p.kind == 'dots'))
