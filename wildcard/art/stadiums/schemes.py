# Stadium schemes for the gauntlet, each with variations. Writes, per variation,
# an animated screen view (what you see at the start of the battle) and a still
# of the whole map, into out/.
#
#   cd wildcard/art/stadiums && python3 schemes.py [scheme ...]
import sys, os, json, math, random
from PIL import Image, ImageDraw
import kit as K
from kit import T, rect, shade, mix

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
FRAMES = 24

# ---- shared pieces ---------------------------------------------------------------------
def pokeball_card(x, y, w, h):
    """Card stunt picture: a Poké Ball on stripes, in pixels across the stand."""
    cx, cy = w / 2, h / 2; r = h * 0.48
    d = math.hypot(x - cx, y - cy)
    if d > r: return [(232, 48, 48), (248, 248, 248)][(x // 24) % 2]
    if d > r - 4 or abs(y - cy) < 4 or d < 12: 
        return (248, 248, 248) if d < 8 else (40, 40, 48)
    return (232, 48, 48) if y < cy else (248, 248, 248)

def word_card(word, fg, bg):
    """Card stunt picture: a word in big LED letters."""
    def f(x, y, w, h):
        cell = h // 6 + 2; tw = (len(word) * 4 - 1) * cell
        k = (x - (w - tw) // 2) // cell; j = (y - (h - 5 * cell) // 2) // cell
        if 0 <= j < 5 and 0 <= k < len(word) * 4 - 1 and k % 4 != 3:
            if K.FONT[word[k // 4]][j * 3 + k % 4] == '1': return fg
        return bg
    return f

def screen_icon(name):
    def content(img, X, Y, w, h, t):
        px = img.load()
        for yy in range(Y + 1, Y + h - 1, 2):  # scanlines
            for xx in range(X, X + w): px[xx, yy] = shade(px[xx, yy], 0.06)
        f = int(t * 8) % 2
        try: m = K.mon(name, f)
        except Exception: m = None
        if m:
            m2 = m.resize((m.width, m.height), Image.NEAREST)
            img.paste(m2, (X + w // 2 - m2.width // 2, Y + h // 2 - m2.height // 2 - 2 + f), m2)
        if int(t * 4) % 2:
            K.draw_text(px, 'ROUND 3', X + w // 2 - 14, Y + h - 8, (255, 232, 96))
    return content

def screen_text(lines):
    def content(img, X, Y, w, h, t):
        px = img.load()
        s = lines[int(t * len(lines)) % len(lines)]
        K.draw_text(px, s, X + w // 2 - K.text_width(s) // 2, Y + h // 2 - 3, (255, 232, 96))
    return content

def place_battlers(img, s, t, px_x, opp_x, row, opp):
    K.stamp(img, K.person_frame('red/red_normal', 0 if True else 0), px_x, row)
    K.stamp(img, K.person(opp), opp_x, row)

def mascots(img, items, t):
    for name, x, y, kind in items:
        f = int(t * 8) % 2
        try: spr = K.mon(name, f if kind != 'still' else 0)
        except (FileNotFoundError, IndexError): print('no overworld sprite:', name); continue
        dy = -1 if (kind == 'hop' and int(t * 8) % 2) else 0
        img.paste(spr, (x * T + 8 - spr.width // 2, y * T + 16 - spr.height + dy), spr)

# ---- scheme 1: the Grand Stadium (Pokémon Stadium's bowl) ----------------------------
def grand(v):
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    back = K.Crowd(0, 2, W, 4, s, 'front', seed=1, density=s.get('density', 0.92), aisles=(6, 18),
                   card_art=s.get('cards'))
    front = K.Crowd(0, 11, W, 4, s, 'back', seed=2, density=s.get('density', 0.92), aisles=(6, 18))
    left = K.Crowd(0, 7, 3, 3, s, 'front', seed=3, density=0.8)
    right = K.Crowd(22, 7, 3, 3, s, 'front', seed=4, density=0.8)
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        K.sky(img, s['sky'][0], s['sky'][1], 2 * T)
        if s.get('stars'): K.stars(img, 2 * T, t)
        back.draw(img, t, s['mode']); front.draw(img, t, s['mode'] if 'card' not in s['mode'] else 'idle')
        for c in (left, right): c.draw(img, t, s['mode'] if 'card' not in s['mode'] else 'idle')
        # roof edge, floodlights and the big screen
        rect(img, 0, 2 * T - 3, W * T - 1, 2 * T - 1, s['roof'])
        for fx in (1, W - 2):
            K.floodlight(img, fx * T, 0, s, t, s.get('lights', True))
        K.jumbotron(img, 10, 0, 5, 2, s, t, s.get('screen_fn', screen_icon('pikachu')))
        K.led_board(img, 6, 0, W, s['ad'], t, s)
        rect(img, 0, 7 * T, 3 * T - 1, 7 * T, s['riser'])
        K.pitch(img, 3, 7, W - 3, 10, s, t)
        rect(img, 3 * T - 2, 7 * T, 3 * T - 1, 10 * T - 1, s['board_frame']); rect(img, (W - 3) * T, 7 * T, (W - 3) * T + 1, 10 * T - 1, s['board_frame'])
        K.led_board(img, 10, 0, W, s['ad2'], t * 0.5, s)
        rect(img, 0, 15 * T, W * T - 1, H * T - 1, shade(s['riser'], -0.3))
        mascots(img, s.get('mascots', []), t)
        if s.get('lights', True) and s.get('night'):
            for fx in (1, W - 2): K.glow(img, fx * T + 8, 8, 40, (255, 250, 220), 0.4)
        place_battlers(img, s, t, PX, OX, ROW, s['opp'])
        return img
    return frame, (PX, ROW)

GRAND = {
    'day': dict(name='Grand Stadium: day', sky=[(120, 184, 248), (184, 224, 248)], seat=(64, 112, 200), riser=(80, 88, 112),
                aisle=(150, 150, 160), roof=(220, 220, 228), shirts=[(232, 64, 64), (64, 112, 224), (248, 208, 40), (240, 240, 240), (72, 168, 88)],
                pitch='grass', pitch_a=(88, 176, 72), pitch_b=(104, 192, 88), line=(240, 248, 240),
                board=(24, 24, 32), board_frame=(56, 56, 72), board_text=(255, 200, 40), ad='WILD CARD GAUNTLET  *  ROUND 3  *  BROCK',
                ad2='SILPH CO  *  DEVON CORP  *  POKE MART', mode='cheer flags', flag=(232, 48, 48), opp='brock',
                mascots=[('pikachu', 4, 9, 'hop'), ('jigglypuff', 20, 9, 'hop')]),
    'night': dict(name='Grand Stadium: floodlit night', sky=[(16, 20, 48), (40, 44, 88)], seat=(48, 72, 136), riser=(40, 44, 64),
                  aisle=(90, 90, 104), roof=(120, 120, 140), shirts=[(220, 72, 72), (80, 104, 200), (240, 196, 60), (236, 220, 220), (128, 88, 176)],
                  pitch='grass', pitch_a=(56, 128, 64), pitch_b=(68, 144, 76), line=(232, 240, 232),
                  board=(16, 16, 24), board_frame=(40, 40, 52), board_text=(80, 220, 255), ad='NIGHT FINAL  *  ROUND 9  *  LANCE',
                  ad2='>>> >>> >>> WILD CARD >>> >>> >>>', mode='flash idle', flag=(80, 104, 200), opp='lance', night=True, stars=True,
                  screen_fn=screen_icon('dragonite')),
    'sunset': dict(name='Grand Stadium: sunset, the Mexican wave', sky=[(248, 120, 72), (252, 196, 112)], seat=(176, 64, 56), riser=(96, 64, 64),
                   aisle=(170, 140, 130), roof=(240, 220, 200), shirts=[(248, 248, 240), (232, 168, 48), (176, 48, 48), (64, 64, 80), (88, 136, 200)],
                   pitch='grass', pitch_a=(120, 160, 64), pitch_b=(136, 176, 72), line=(255, 244, 224),
                   board=(32, 20, 20), board_frame=(72, 48, 48), board_text=(255, 160, 64), ad='SUNSET SERIES  *  ROUND 5  *  ERIKA',
                   ad2='WAVE!  WAVE!  WAVE!', mode='wave idle', flag=(248, 200, 64), opp='erika',
                   screen_fn=screen_text(['WAVE!', 'ROUND 5', 'ERIKA'])),
    'cards': dict(name='Grand Stadium: card stunt (Poké Ball, then the round)', sky=[(120, 184, 248), (184, 224, 248)], seat=(64, 112, 200), riser=(80, 88, 112),
                  aisle=(150, 150, 160), roof=(220, 220, 228), shirts=[(232, 64, 64), (64, 112, 224), (248, 208, 40), (240, 240, 240)],
                  pitch='grass', pitch_a=(88, 176, 72), pitch_b=(104, 192, 88), line=(240, 248, 240),
                  board=(24, 24, 32), board_frame=(56, 56, 72), board_text=(255, 200, 40), ad='ROUND 10 NEXT  *  CAN YOU REACH RED',
                  ad2='WILD CARD', mode='card', flag=(232, 48, 48), opp='sabrina', density=1.0,
                  cards=[pokeball_card, word_card('GO!', (248, 208, 40), (40, 40, 120))]),
}

# ---- scheme 2: the Colosseum (stone tiers, sand, torches) ---------------------------------
def colosseum(v):
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    back = K.Crowd(0, 2, W, 4, s, 'front', seed=11, density=s.get('density', 0.8), aisles=(4, 12, 20))
    front = K.Crowd(0, 12, W, 3, s, 'back', seed=12, density=s.get('density', 0.8), aisles=(4, 12, 20))
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        K.sky(img, s['sky'][0], s['sky'][1], 2 * T)
        if s.get('stars'): K.stars(img, 2 * T, t, 5)
        if s.get('moon'):
            d = ImageDraw.Draw(img); d.ellipse([300, 4, 320, 24], fill=(248, 240, 208)); d.ellipse([306, 2, 326, 22], fill=s['sky'][0])
        # arches along the top
        for x in range(0, W * T, 32):
            rect(img, x, 6, x + 31, 2 * T - 1, s['stone'])
            d = ImageDraw.Draw(img); d.ellipse([x + 6, 8, x + 25, 34], fill=shade(s['stone'], -0.45)); rect(img, x + 6, 20, x + 25, 2 * T - 1, shade(s['stone'], -0.45))
            rect(img, x, 6, x + 31, 7, shade(s['stone'], 0.25))
        back.draw(img, t, s['mode']); front.draw(img, t, s['mode'])
        # the arena wall with torches and banners
        rect(img, 0, 6 * T, W * T - 1, 7 * T - 1, s['stone']); rect(img, 0, 6 * T, W * T - 1, 6 * T + 1, shade(s['stone'], 0.3))
        for x in range(0, W * T, 8): rect(img, x, 6 * T + 6, x, 7 * T - 1, shade(s['stone'], -0.2))
        for bx in (3, 8, 16, 21):
            d = ImageDraw.Draw(img); X = bx * T
            d.polygon([(X + 2, 6 * T + 2), (X + 13, 6 * T + 2), (X + 13, 7 * T + 6), (X + 8, 7 * T + 2), (X + 2, 7 * T + 6)], fill=s['banner'])
            rect(img, X + 6, 6 * T + 6, X + 9, 6 * T + 9, s.get('banner_mark', (248, 216, 96)))
        K.pitch(img, 0, 7, W, 11, s, t)
        rect(img, 0, 11 * T, W * T - 1, 12 * T - 1, s['stone']); rect(img, 0, 11 * T, W * T - 1, 11 * T + 1, shade(s['stone'], 0.3))
        for x in range(0, W * T, 8): rect(img, x, 11 * T + 6, x, 12 * T - 1, shade(s['stone'], -0.2))
        for tx in (1, 6, 12, 18, 23):
            K.torch(img, tx * T, 6 * T - 6, t, tx)
            K.glow(img, tx * T + 8, 6 * T, 22, (255, 160, 64), 0.3 if not s.get('night') else 0.5)
        if s.get('lava'):
            for y in (7 * T, 10 * T + 10):
                for x in range(0, W * T):
                    for k in range(6):
                        c = (248, 96, 32) if (x // 3 + k + int(t * 12)) % 5 else (255, 200, 64)
                        img.putpixel((x, y + k), c)
        mascots(img, s.get('mascots', []), t)
        place_battlers(img, s, t, PX, OX, ROW, s['opp'])
        return img
    return frame, (PX, ROW)

COLOSSEUM = {
    'sandstone': dict(name='Colosseum: sandstone, daylight', sky=[(136, 192, 248), (200, 228, 248)], stone=(208, 176, 128), seat=(176, 144, 104),
                      riser=(152, 120, 88), aisle=(196, 168, 128), shirts=[(240, 240, 232), (200, 64, 48), (72, 112, 176), (224, 184, 72)],
                      pitch='sand', pitch_a=(232, 208, 152), pitch_b=(208, 184, 128), line=(248, 240, 216), banner=(176, 40, 40),
                      mode='cheer flags', flag=(176, 40, 40), opp='bruno', mascots=[('machamp', 3, 9, 'still'), ('machamp', 21, 9, 'still')]),
    'moonlit': dict(name='Colosseum: moonlit marble', sky=[(16, 16, 40), (48, 48, 96)], stone=(184, 184, 200), seat=(120, 120, 144),
                    riser=(96, 96, 116), aisle=(150, 150, 170), shirts=[(200, 200, 224), (96, 72, 160), (64, 96, 176), (176, 64, 112)],
                    pitch='sand', pitch_a=(168, 168, 192), pitch_b=(148, 148, 176), line=(232, 232, 248), banner=(88, 56, 152),
                    mode='flash idle', flag=(88, 56, 152), opp='agatha', night=True, stars=True, moon=True,
                    mascots=[('gengar', 3, 9, 'hop'), ('haunter', 21, 8, 'hop')]),
    'volcanic': dict(name='Colosseum: obsidian, with a lava moat', sky=[(64, 16, 16), (160, 56, 24)], stone=(72, 60, 64), seat=(96, 48, 40),
                     riser=(56, 44, 48), aisle=(88, 76, 80), shirts=[(248, 120, 40), (232, 200, 64), (176, 40, 32), (240, 232, 216)],
                     pitch='sand', pitch_a=(112, 88, 80), pitch_b=(92, 72, 68), line=(248, 168, 72), banner=(232, 96, 32),
                     mode='cheer idle', flag=(232, 96, 32), opp='blaine', lava=True, banner_mark=(255, 232, 120),
                     mascots=[('magmar', 3, 9, 'hop'), ('rapidash', 21, 9, 'still')]),
}

# ---- scheme 3: the Neon Arena (indoor, dark, glowsticks) ------------------------------------
def neon(v):
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    back = K.Crowd(0, 2, W, 4, s, 'front', seed=21, density=0.95, aisles=(8, 16))
    front = K.Crowd(0, 11, W, 4, s, 'back', seed=22, density=0.95, aisles=(8, 16))
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        K.sky(img, s['sky'][0], s['sky'][1], 2 * T)
        # roof truss
        d = ImageDraw.Draw(img)
        for x in range(0, W * T, 16):
            d.line([x, 4, x + 16, 20], fill=(56, 56, 72)); d.line([x + 16, 4, x, 20], fill=(56, 56, 72))
        rect(img, 0, 2, W * T - 1, 4, (72, 72, 88)); rect(img, 0, 20, W * T - 1, 22, (72, 72, 88))
        back.draw(img, t, s['mode']); front.draw(img, t, s['mode'])
        # dim the crowd a little: they're in the dark
        for y0, y1 in ((2 * T, 6 * T), (11 * T, 15 * T)):
            for y in range(y0, y1):
                for x in range(W * T):
                    img.putpixel((x, y), shade(img.getpixel((x, y)), -0.35))
        # a rail of chasing lights above each board
        for y in (6 * T - 2, 11 * T - 2):
            for x in range(0, W * T, 4):
                k = (x // 4 + int(t * 24)) % 6
                c = s['chase'][k % len(s['chase'])] if k < 3 else shade(s['chase'][0], -0.6)
                rect(img, x, y, x + 2, y + 1, c)
        K.led_board(img, 6, 0, W, s['ad'], t, s)
        K.pitch(img, 0, 7, W, 10, s, t)
        K.led_board(img, 10, 0, W, s['ad2'], t * 0.5, s)
        rect(img, 0, 15 * T, W * T - 1, H * T - 1, (16, 16, 24))
        # spotlights sweeping the floor
        for k, base in enumerate((0.0, 0.5)):
            cx = int((math.sin((t + base) * 2 * math.pi) * 0.5 + 0.5) * (W - 4) * T) + 2 * T
            K.glow(img, cx, 8 * T + 8, 28, s['spot_col'], 0.35)
        K.jumbotron(img, 10, 0, 5, 2, s, t, s.get('screen_fn', screen_text(['ROUND 4', 'LT SURGE', 'GO!'])))
        mascots(img, s.get('mascots', []), t)
        place_battlers(img, s, t, PX, OX, ROW, s['opp'])
        return img
    return frame, (PX, ROW)

NEON = {
    'synth': dict(name='Neon Arena: synthwave', sky=[(20, 8, 36), (48, 16, 72)], seat=(72, 40, 96), riser=(36, 24, 48), aisle=(56, 40, 72),
                  shirts=[(248, 88, 176), (72, 216, 232), (240, 240, 248), (136, 88, 232)], glow=[(255, 96, 200), (96, 240, 255), (255, 240, 96)],
                  pitch='neon', pitch_a=(24, 12, 40), pitch_b=(255, 72, 200), line=(96, 240, 255), spot=(255, 72, 200),
                  board=(12, 8, 20), board_frame=(40, 24, 56), board_text=(255, 96, 200), chase=[(255, 72, 200), (96, 240, 255), (255, 240, 96)],
                  ad='WILD CARD LIVE  *  ROUND 6  *  SABRINA', ad2='>> >> >> >> >> >>', mode='glow cheer', spot_col=(255, 120, 220), opp='sabrina',
                  outline=(16, 8, 24), screen_fn=screen_icon('alakazam'), mascots=[('mr_mime', 3, 9, 'hop'), ('espeon', 21, 9, 'hop')]),
    'electric': dict(name='Neon Arena: electric (hazard stripes, sparks)', sky=[(16, 16, 16), (40, 40, 24)], seat=(64, 64, 40), riser=(32, 32, 24), aisle=(56, 56, 40),
                     shirts=[(248, 216, 40), (40, 40, 40), (240, 240, 240), (232, 120, 32)], glow=[(255, 240, 64), (255, 255, 255)],
                     pitch='neon', pitch_a=(28, 28, 20), pitch_b=(255, 224, 48), line=(255, 224, 48), spot=(255, 224, 48),
                     board=(10, 10, 6), board_frame=(56, 48, 16), board_text=(255, 224, 48), chase=[(255, 224, 48), (255, 255, 255), (255, 160, 32)],
                     ad='VOLTAGE  *  ROUND 4  *  LT SURGE', ad2='DANGER  HIGH VOLTAGE  DANGER', mode='glow flash', spot_col=(255, 240, 120), opp='lt_surge',
                     outline=(12, 12, 8), screen_fn=screen_icon('raichu'), mascots=[('pikachu', 3, 9, 'hop'), ('electabuzz', 21, 9, 'hop')]),
    'toxic': dict(name='Neon Arena: toxic (Koga)', sky=[(12, 20, 12), (32, 16, 40)], seat=(56, 32, 72), riser=(28, 20, 32), aisle=(48, 36, 56),
                  shirts=[(160, 72, 200), (96, 232, 96), (40, 40, 48), (232, 232, 232)], glow=[(120, 255, 96), (200, 96, 255)],
                  pitch='neon', pitch_a=(16, 24, 16), pitch_b=(120, 255, 96), line=(200, 96, 255), spot=(120, 255, 96),
                  board=(8, 12, 8), board_frame=(40, 24, 48), board_text=(120, 255, 96), chase=[(120, 255, 96), (200, 96, 255), (240, 240, 240)],
                  ad='NINJA NIGHT  *  ROUND 5  *  KOGA', ad2='POISON  POISON  POISON', mode='glow idle', spot_col=(140, 255, 120), opp='koga',
                  outline=(10, 14, 10), screen_fn=screen_icon('weezing'), mascots=[('weezing', 3, 8, 'hop'), ('venomoth', 21, 8, 'hop')]),
}

# ---- scheme 4: the Sky Arena (a platform in the clouds, fans on floating decks) -------------
def sky_arena(v):
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    left = K.Crowd(0, 5, 5, 3, s, 'front', seed=31, density=0.9)
    right = K.Crowd(20, 5, 5, 3, s, 'front', seed=32, density=0.9)
    front = K.Crowd(5, 12, 15, 2, s, 'back', seed=33, density=0.9)
    rnd = random.Random(4); clouds = [(rnd.randrange(W * T), rnd.randrange(H * T), rnd.randrange(24, 56), rnd.random() + 0.5) for _ in range(14)]
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        px = img.load()
        for y in range(H * T):
            c = mix(s['sky'][0], s['sky'][1], round(y / (H * T) * 6) / 6)
            for x in range(W * T): px[x, y] = c
        if s.get('stars'): K.stars(img, H * T, t, 9)
        for (x, y, w, sp) in clouds:  # far clouds drift slowly
            K.cloud(img, int(x - t * W * T * sp * 0.25) % (W * T + 60) - 60, y, w, s['cloud_far'])
        if s.get('storm') and int(t * FRAMES) in (5, 6, 17):
            for y in range(H * T):
                for x in range(W * T): px[x, y] = mix(px[x, y], (255, 255, 255), 0.45)
        # the platform and its underside
        def deck(x0, y0, x1, y1):
            rect(img, x0 * T, y0 * T, x1 * T - 1, y1 * T - 1, s['deck'])
            rect(img, x0 * T, y1 * T, x1 * T - 1, y1 * T + 9, shade(s['deck'], -0.35))
            rect(img, x0 * T, y1 * T + 10, x1 * T - 1, y1 * T + 11, shade(s['deck'], -0.55))
            for x in range(x0 * T + 6, x1 * T, 24):  # underside lights
                rect(img, x, y1 * T + 4, x + 3, y1 * T + 6, s['lamp'] if (x // 24 + int(t * 6)) % 3 else shade(s['lamp'], -0.5))
        deck(5, 6, 20, 11); K.pitch(img, 6, 7, 19, 10, s, t)
        deck(0, 5, 5, 8); deck(20, 5, 25, 8); deck(5, 12, 20, 14)
        left.draw(img, t, s['mode']); right.draw(img, t, s['mode']); front.draw(img, t, s['mode'])
        # rails
        for (x0, y0, x1) in ((5, 6, 20), (0, 5, 5), (20, 5, 25)):
            for x in range(x0 * T, x1 * T, 8): rect(img, x, y0 * T - 6, x + 1, y0 * T, (220, 220, 232))
            rect(img, x0 * T, y0 * T - 7, x1 * T - 1, y0 * T - 6, (240, 240, 248))
        # banners on poles at the deck corners
        for fx in (5, 19): K.flag(img, fx * T, 2 * T, s['flag'], t, fx)
        # near clouds pass in front, faster
        for (x, y, w, sp) in clouds[:4]:
            K.cloud(img, int(x * 1.3 - t * W * T * sp * 0.6) % (W * T + 80) - 80, (y % (3 * T)) + 13 * T, w + 20, s['cloud_near'])
        mascots(img, s.get('mascots', []), t)
        place_battlers(img, s, t, PX, OX, ROW, s['opp'])
        return img
    return frame, (PX, ROW)

SKY = {
    'day': dict(name='Sky Arena: high noon', sky=[(96, 168, 248), (200, 232, 252)], cloud_far=(232, 240, 252), cloud_near=(255, 255, 255),
                deck=(200, 204, 216), lamp=(255, 232, 128), seat=(88, 136, 216), riser=(176, 180, 196), aisle=(176, 180, 196),
                shirts=[(232, 64, 64), (64, 112, 224), (248, 208, 40), (240, 240, 240)], pitch='grass', pitch_a=(120, 200, 112), pitch_b=(136, 216, 128),
                line=(255, 255, 255), mode='cheer flags', flag=(64, 112, 224), opp='lance', mascots=[('dragonair', 2, 10, 'hop'), ('pidgeot', 22, 10, 'hop')]),
    'sunset': dict(name='Sky Arena: golden hour', sky=[(248, 136, 96), (252, 216, 152)], cloud_far=(252, 196, 168), cloud_near=(255, 228, 200),
                   deck=(224, 200, 176), lamp=(255, 240, 160), seat=(200, 88, 72), riser=(184, 160, 140), aisle=(184, 160, 140),
                   shirts=[(248, 248, 240), (232, 168, 48), (176, 48, 48), (88, 136, 200)], pitch='grass', pitch_a=(160, 184, 88), pitch_b=(176, 200, 104),
                   line=(255, 248, 232), mode='wave idle', flag=(248, 200, 64), opp='lance', mascots=[('charizard', 2, 10, 'hop')]),
    'storm': dict(name='Sky Arena: thunderstorm', sky=[(40, 44, 64), (96, 100, 124)], cloud_far=(72, 76, 96), cloud_near=(112, 116, 136),
                  deck=(120, 124, 140), lamp=(255, 232, 96), seat=(72, 80, 112), riser=(96, 100, 116), aisle=(96, 100, 116),
                  shirts=[(248, 216, 40), (40, 40, 48), (200, 200, 208), (232, 120, 32)], pitch='grass', pitch_a=(72, 120, 80), pitch_b=(84, 136, 92),
                  line=(220, 228, 232), mode='flash idle', flag=(248, 216, 40), opp='lt_surge', storm=True,
                  mascots=[('zapdos', 22, 10, 'hop')]),
}

# ---- scheme 5: the Aqua Stadium (a pool pitch, stands round it) --------------------------------
def aqua(v):
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    back = K.Crowd(0, 2, W, 4, s, 'front', seed=41, density=0.88, aisles=(6, 18))
    front = K.Crowd(0, 12, W, 3, s, 'back', seed=42, density=0.88, aisles=(6, 18))
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        K.sky(img, s['sky'][0], s['sky'][1], 2 * T)
        if s.get('palms'):
            for px_ in (16, 360):
                d = ImageDraw.Draw(img); d.rectangle([px_ + 6, 6, px_ + 9, 31], fill=(136, 96, 56))
                sway = int(t * 4) % 2
                for k in range(-2, 3): d.line([px_ + 8, 6, px_ + 8 + k * 7, 12 + abs(k) * 2 + sway], fill=(56, 152, 72), width=2)
        back.draw(img, t, s['mode']); front.draw(img, t, s['mode'])
        rect(img, 0, 6 * T, W * T - 1, 7 * T - 1, s['tile']);
        for x in range(0, W * T, 8):
            for y in range(6 * T, 7 * T, 8): rect(img, x, y, x + 7, y, shade(s['tile'], -0.12)); rect(img, x, y, x, y + 7, shade(s['tile'], -0.12))
        K.pitch(img, 0, 7, W, 11, dict(s, lines=False), t)
        # lane ropes and the battlers' floating platforms
        for x in range(0, W * T, 4):
            for y in (7 * T + 4, 11 * T - 6):
                rect(img, x, y + (1 if (x // 4 + int(t * 8)) % 4 < 2 else 0), x + 2, y + 1 + (1 if (x // 4 + int(t * 8)) % 4 < 2 else 0), (232, 64, 64) if (x // 8) % 2 else (248, 248, 248))
        for bx in (PX, OX):
            bob = 1 if int(t * 6 + bx) % 2 else 0
            rect(img, bx * T - 4, ROW * T - 2 + bob, bx * T + 19, ROW * T + 17 + bob, s['float'])
            rect(img, bx * T - 4, ROW * T + 15 + bob, bx * T + 19, ROW * T + 17 + bob, shade(s['float'], -0.3))
            ImageDraw.Draw(img).ellipse([bx * T + 2, ROW * T + 3 + bob, bx * T + 13, ROW * T + 12 + bob], outline=(255, 255, 255))
        if s.get('underlights'):
            for x in range(T, W * T, 3 * T): K.glow(img, x, 9 * T, 18, (120, 220, 255), 0.4)
        rect(img, 0, 11 * T, W * T - 1, 12 * T - 1, s['tile'])
        for x in range(0, W * T, 8):
            for y in range(11 * T, 12 * T, 8): rect(img, x, y, x + 7, y, shade(s['tile'], -0.12)); rect(img, x, y, x, y + 7, shade(s['tile'], -0.12))
        mascots(img, s.get('mascots', []), t)
        K.stamp(img, K.person('red/red_normal'), PX, ROW, -2 + (1 if int(t * 6 + PX) % 2 else 0))
        K.stamp(img, K.person(s['opp']), OX, ROW, -2 + (1 if int(t * 6 + OX) % 2 else 0))
        return img
    return frame, (PX, ROW)

AQUA = {
    'pool': dict(name='Aqua Stadium: the pool', sky=[(120, 184, 248), (184, 224, 248)], seat=(56, 144, 200), riser=(96, 120, 144), aisle=(160, 176, 192),
                 shirts=[(248, 248, 248), (64, 112, 224), (248, 208, 40), (232, 96, 96)], tile=(208, 232, 240), float=(240, 240, 232),
                 pitch='water', pitch_a=(64, 152, 232), pitch_b=(176, 224, 255), line=(255, 255, 255), mode='cheer flags', flag=(64, 112, 224),
                 opp='misty', mascots=[('starmie', 4, 9, 'hop'), ('psyduck', 6, 11, 'hop'), ('lapras', 20, 9, 'still')]),
    'lagoon': dict(name='Aqua Stadium: tropical lagoon', sky=[(80, 200, 248), (200, 240, 248)], seat=(232, 168, 64), riser=(176, 136, 96), aisle=(216, 196, 160),
                   shirts=[(248, 120, 120), (248, 232, 120), (120, 216, 168), (248, 248, 248)], tile=(240, 224, 176), float=(232, 200, 136),
                   pitch='water', pitch_a=(48, 200, 200), pitch_b=(200, 255, 240), line=(255, 255, 255), mode='wave idle', flag=(248, 120, 120),
                   opp='misty', palms=True, mascots=[('wailmer', 4, 10, 'hop'), ('corsola', 20, 9, 'hop')]),
    'night': dict(name='Aqua Stadium: night swim, lights under the water', sky=[(12, 20, 48), (24, 40, 88)], seat=(40, 80, 128), riser=(32, 44, 64), aisle=(64, 80, 100),
                  shirts=[(200, 220, 255), (64, 112, 224), (96, 232, 255), (240, 240, 248)], glow=[(96, 240, 255), (255, 255, 255)], tile=(120, 140, 168), float=(200, 208, 224),
                  pitch='water', pitch_a=(24, 72, 144), pitch_b=(120, 200, 255), line=(255, 255, 255), mode='glow flash', flag=(64, 112, 224),
                  opp='lorelei', underlights=True, mascots=[('lapras', 4, 9, 'still'), ('dewgong', 20, 9, 'hop')]),
}

# ---- scheme 6: the Frozen Rink and the Garden Court (two small themed bowls) --------------
def bowl(v):
    """A smaller bowl for type themes: one stand behind, low walls, scenery."""
    W, H = 25, 16
    s = dict(v); s['map_w'] = W
    PX, OX, ROW = 10, 14, 8
    back = K.Crowd(0, 2, W, 4, s, 'front', seed=51, density=s.get('density', 0.85), aisles=(5, 12, 19))
    front = K.Crowd(0, 12, W, 3, s, 'back', seed=52, density=s.get('density', 0.85), aisles=(5, 12, 19))
    rnd = random.Random(8); flakes = [(rnd.randrange(W * T), rnd.randrange(H * T)) for _ in range(160)]
    def frame(t):
        img = Image.new('RGB', (W * T, H * T), s['sky'][0])
        K.sky(img, s['sky'][0], s['sky'][1], 2 * T)
        if s.get('lanterns'):
            d = ImageDraw.Draw(img); d.line([0, 10, W * T, 10], fill=(80, 60, 40))
            for x in range(8, W * T, 24):
                sw = 1 if int(t * 4 + x / 24) % 2 else 0
                d.rectangle([x + sw, 12, x + 7 + sw, 22], fill=(232, 72, 56)); d.rectangle([x + 2 + sw, 14, x + 5 + sw, 20], fill=(255, 200, 96))
        back.draw(img, t, s['mode']); front.draw(img, t, s['mode'])
        rect(img, 0, 6 * T, W * T - 1, 7 * T - 1, s['wall']); rect(img, 0, 6 * T, W * T - 1, 6 * T + 2, shade(s['wall'], 0.3))
        if s.get('hedge'):
            for x in range(0, W * T, 4):
                for y in range(6 * T + 3, 7 * T):
                    if (x + y * 3) % 7 == 0: img.putpixel((x, y), shade(s['wall'], 0.25))
            for x in range(6, W * T, 20):
                c = s['flowers'][(x // 20) % len(s['flowers'])]
                bob = int(t * 6 + x) % 2
                rect(img, x, 6 * T + 5 - bob, x + 2, 6 * T + 7 - bob, c)
        K.pitch(img, 0, 7, W, 11, s, t)
        rect(img, 0, 11 * T, W * T - 1, 12 * T - 1, s['wall']); rect(img, 0, 11 * T, W * T - 1, 11 * T + 2, shade(s['wall'], 0.3))
        if s.get('snow'):
            px = img.load()
            for (x, y) in flakes:
                yy = int(y + t * H * T) % (H * T); xx = int(x + math.sin(t * 6.28 + y) * 4) % (W * T)
                px[xx, yy] = (255, 255, 255)
                if (x + y) % 3 == 0 and xx + 1 < W * T: px[xx + 1, yy] = (255, 255, 255)
        if s.get('petals'):
            px = img.load()
            for (x, y) in flakes[:60]:
                yy = int(y + t * H * T * 0.5) % (H * T); xx = int(x - t * W * T * 0.3) % (W * T)
                px[xx, yy] = (248, 168, 200);
                if xx + 1 < W * T: px[xx + 1, yy] = (248, 200, 220)
        mascots(img, s.get('mascots', []), t)
        place_battlers(img, s, t, PX, OX, ROW, s['opp'])
        return img
    return frame, (PX, ROW)

BOWL = {
    'ice': dict(name='Frozen Rink: ice pitch, snowfall', sky=[(176, 200, 232), (224, 236, 248)], seat=(96, 144, 200), riser=(152, 168, 192), aisle=(200, 212, 228),
                shirts=[(232, 64, 64), (248, 248, 248), (64, 112, 224), (120, 200, 232)], wall=(208, 224, 240), pitch='ice', pitch_a=(200, 228, 248), pitch_b=(248, 252, 255),
                line=(96, 160, 224), mode='idle flags', flag=(120, 200, 232), opp='lorelei', snow=True, mascots=[('jynx', 3, 9, 'hop'), ('cloyster', 21, 9, 'still')]),
    'garden': dict(name='Garden Court: hedges, flower crowd, petals', sky=[(152, 208, 248), (216, 240, 248)], seat=(96, 160, 80), riser=(112, 96, 72), aisle=(176, 160, 128),
                   shirts=[(248, 168, 200), (248, 240, 200), (200, 120, 200), (120, 200, 120)], wall=(64, 136, 64), hedge=True,
                   flowers=[(248, 96, 128), (248, 232, 96), (240, 240, 248), (184, 120, 232)], pitch='grass', pitch_a=(136, 200, 96), pitch_b=(152, 216, 112),
                   line=(255, 255, 240), mode='cheer idle', flag=(248, 168, 200), opp='erika', petals=True,
                   mascots=[('bellossom', 3, 9, 'hop'), ('vileplume', 21, 9, 'hop'), ('bulbasaur', 2, 10, 'hop')]),
    'dojo': dict(name='Dojo Hall: tatami, paper lanterns', sky=[(72, 48, 32), (112, 76, 48)], seat=(144, 104, 64), riser=(96, 64, 40), aisle=(128, 96, 64),
                 shirts=[(240, 236, 224), (40, 40, 48), (176, 40, 40), (104, 80, 56)], wall=(160, 112, 64), pitch='tatami', pitch_a=(200, 192, 120), pitch_b=(184, 176, 104),
                 line=(120, 80, 48), lines=True, mode='cheer idle', flag=(176, 40, 40), opp='bruno', lanterns=True,
                 mascots=[('hitmonlee', 3, 9, 'hop'), ('hitmonchan', 21, 9, 'hop')]),
    'rock': dict(name='Quarry Bowl: rock, dust and boulders', sky=[(184, 168, 136), (224, 208, 176)], seat=(144, 112, 80), riser=(112, 88, 64), aisle=(168, 144, 112),
                 shirts=[(200, 120, 64), (96, 80, 64), (232, 216, 184), (104, 128, 160)], wall=(136, 112, 88), pitch='sand', pitch_a=(184, 152, 112), pitch_b=(160, 128, 96),
                 line=(240, 224, 192), mode='cheer flags', flag=(200, 120, 64), opp='brock', mascots=[('onix', 2, 9, 'still'), ('geodude', 21, 9, 'hop')]),
}

SCHEMES = {'grand': (grand, GRAND), 'colosseum': (colosseum, COLOSSEUM), 'neon': (neon, NEON),
           'sky': (sky_arena, SKY), 'aqua': (aqua, AQUA), 'bowl': (bowl, BOWL)}

def run(which):
    os.makedirs(OUT, exist_ok=True)
    report = []
    for key in which:
        fn, variants = SCHEMES[key]
        for vk, v in variants.items():
            make, (px_, py_) = fn(v)
            frames = [make(i / FRAMES) for i in range(FRAMES)]
            screens = [K.screen_crop(f, px_, py_) for f in frames]
            base = f'{key}_{vk}'
            K.save_gif(screens, f'{OUT}/{base}.gif', 100, 3)
            K.save_gif(frames, f'{OUT}/{base}_map.gif', 100, 2)
            frames[0].resize((frames[0].width * 2, frames[0].height * 2), Image.NEAREST).save(f'{OUT}/{base}_map.png')
            screens[0].resize((720, 480), Image.NEAREST).save(f'{OUT}/{base}.png')
            tiles, pals = K.tile_budget(frames[0])
            report.append(dict(file=base, name=v['name'], tiles=tiles, palettes=pals))
            print(f'{base:22} {tiles:4} tiles, {pals:2} palettes  {v["name"]}')
    json.dump(report, open(f'{OUT}/report_{"_".join(which)}.json', 'w'), indent=1)

if __name__ == '__main__':
    run(sys.argv[1:] or list(SCHEMES))
