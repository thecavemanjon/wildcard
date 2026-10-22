# Bedroom designs, on the bedroom's own 9 x 8 footprint with every fixture on
# its usual tile (map.json: TV 0, GameCube 1, wardrobe 2, clock 3, PC 4,
# notebook 5 along row 1; stairs and their box at 7-8; bed bottom-right;
# loungers at the five spots), so a room is a new layout on the same map.
# Each room's showpiece goes on the free wall tile (column 6), behind the
# furniture, on the stairs, or on the floor.
#   python3 rooms.py [name ...]   -> out/<name>_<time>.gif, out/<name>.png (still, with sprites)
import sys, os, math, random
from PIL import Image
from roomkit import *

ROOMS = {}
def room(name, title, blurb, mons=('pikachu', 'eevee', 'togepi', 'skitty', 'mudkip')):
    def reg(fn):
        ROOMS[name] = dict(draw=fn, title=title, blurb=blurb, mons=mons)
        return fn
    return reg

SPOTS = [(2, 4), (4, 4), (5, 6), (8, 2), (1, 6)]   # map.json object events 2-6
START = (3, 3)
BED = (110, 96)                                       # bed top-left in pixels (column 7, rows 6-7)

# ---- the fixtures, on their tiles ---------------------------------------------------------------
def fixtures(img, t, time, spare, stand=(120, 80, 48), tv_body=(64, 64, 72), tv_content='battle',
             wardrobe_cols=None, desk=None, clock_face=(248, 248, 240), clock_rim=(72, 120, 200)):
    tv_stand(img, 0, 22, 16, col=stand)
    spare.append(tv(img, 1, 6, t, w=14, h=15, body=tv_body, content=tv_content, time=time))
    paste(img, gamecube(), 16, 16)
    w = wardrobe()
    if wardrobe_cols: w = recolour(w, [((248, 160, 56), wardrobe_cols[0]), ((248, 200, 104), wardrobe_cols[1])])
    paste(img, w, 32, 0)
    clock(img, 56, 10, face=clock_face, rim=clock_rim, t=t)
    d = pc_desk()
    if desk: d = recolour(d, [((248, 176, 72), desk)])
    paste(img, d, 64, 0)

def stairs(img, style='plain', col=(120, 88, 56)):
    """The way downstairs, top-right (columns 7-8, rows 0-1); the box sits in front of it."""
    x0, x1 = 114, 142
    o, d, b, l, h = ramp(col)
    if style == 'ladder':
        rect(img, x0 + 6, 0, x0 + 22, 32, (24, 16, 16))
        for x in (x0 + 7, x0 + 19): rect(img, x, 0, x + 2, 32, b); rect(img, x, 0, x + 1, 32, l)
        for y in range(3, 32, 6): rect(img, x0 + 9, y, x0 + 19, y + 2, b); rect(img, x0 + 9, y, x0 + 19, y + 1, l)
        return
    if style == 'airlock':
        rect(img, x0, 2, x1, 32, (40, 44, 56)); rect(img, x0 + 2, 4, x1 - 2, 32, (88, 96, 112))
        rect(img, (x0 + x1) // 2, 4, (x0 + x1) // 2 + 1, 32, (40, 44, 56))
        for k in range(x0 + 3, x1 - 3, 4): put(img, k, 6, (248, 200, 64)); put(img, k + 1, 7, (40, 40, 40))
        return
    if style == 'shoji':
        rect(img, x0, 2, x1, 32, (104, 64, 40)); rect(img, x0 + 2, 4, x1 - 2, 30, (240, 232, 208))
        for x in range(x0 + 2, x1 - 2, 7): rect(img, x, 4, x + 1, 30, (152, 112, 72))
        for y in range(4, 30, 7): rect(img, x0 + 2, y, x1 - 2, y + 1, (152, 112, 72))
        rect(img, x0 + 13, 4, x0 + 15, 30, (24, 16, 16))   # slid open a crack
        return
    if style == 'arch':
        rect(img, x0, 0, x1, 32, o)
        for yy in range(0, 32):
            for xx in range(x0 + 2, x1 - 2):
                dx = (xx - (x0 + x1) / 2) / ((x1 - x0) / 2 - 2)
                if yy > 8 - 8 * max(0, 1 - dx * dx) ** 0.5 + 2: put(img, xx, yy, (24, 16, 16) if yy < 30 else d)
        rect(img, x0, 0, x1, 2, h)
        return
    if style == 'glass':
        rect(img, x0, 2, x1, 32, (200, 208, 216)); rect(img, x0 + 2, 4, x1 - 2, 32, (152, 200, 232))
        for k in range(4): put(img, x0 + 5 + k, 7 + k, (232, 248, 248))
        rect(img, (x0 + x1) // 2, 4, (x0 + x1) // 2 + 1, 32, (200, 208, 216))
        return
    # plain: a dark stairwell with steps going down
    rect(img, x0, 2, x1, 32, o); rect(img, x0 + 2, 4, x1 - 2, 32, (24, 20, 24))
    for k, y in enumerate(range(10, 32, 5)): rect(img, x0 + 3, y, x1 - 3, y + 2, shade(col, -0.5 + k * 0.1))
    rect(img, x0, 2, x1, 4, b)

def box_sprite():
    p = 'graphics/object_events/pics/misc/moving_box.png'
    return mk.person(p, 16, 16) if os.path.exists(mk.R + p) else None

def porthole(img, cx, cy, r_, time, t, rim=(88, 56, 40), extra=None):
    """A round window onto the sky (the same sky as the rectangular ones)."""
    for yy in range(-r_ - 2, r_ + 3):
        for xx in range(-r_ - 2, r_ + 3):
            if math.hypot(xx, yy) <= r_ + 1.5: put(img, cx + xx, cy + yy, rim)
    tmp = Image.new('RGB', (2 * r_, 2 * r_)); sky(tmp, 0, 0, 2 * r_, 2 * r_, time, t, extra)
    for yy in range(-r_, r_):
        for xx in range(-r_, r_):
            if math.hypot(xx + 0.5, yy + 0.5) <= r_ - 0.3: put(img, cx + xx, cy + yy, tmp.getpixel((xx + r_, yy + r_)))
    return (cx - r_, cy - r_, cx + r_, cy + r_)

# ---------------------------------------------------------------------------------------------
@room('loft', 'Attic Loft', 'Sloped beams, a round window that follows the clock, fairy lights over the bed, a ladder down.')
def loft(img, t, time):
    spare = []
    wall_plain(img, (216, 184, 144), (120, 80, 56))
    for k in range(10): rect(img, 0, 0, 10 - k, k * 3 + 3, (104, 72, 48)); rect(img, PW - 10 + k, 0, PW, k * 3 + 3, (104, 72, 48))
    floor_planks(img, (176, 120, 72), plank=8)
    spare.append(porthole(img, 104, 13, 7, time, t))
    rect(img, 97, 13, 111, 14, (88, 56, 40)); rect(img, 104, 6, 105, 20, (88, 56, 40))
    stairs(img, 'ladder', (152, 104, 64))
    fixtures(img, t, time, spare, wardrobe_cols=((176, 120, 216), (208, 168, 240)), clock_rim=(200, 104, 64))
    round_rug(img, 64, 80, 30, 16, [(232, 112, 96), (248, 200, 120), (232, 112, 96), (120, 168, 216)])
    bed(img, *BED, (232, 112, 96), pattern='check', w=22, h=30)
    fairy_lights(img, 100, 142, 90, t + 7, sag=3)
    beanbag(img, 104, 70, (96, 168, 216))
    plant(img, 8, 126, 'fern')
    if time == 'night': night_dim(img, 0.45, spare=spare)
    return spare

@room('den', 'Gamer Den', 'Lights off, neon on: an LED strip that cycles colour, an arcade cabinet, a Poké Ball rug.',
      mons=('porygon', 'rotom', 'magnemite', 'gengar', 'pikachu'))
def den(img, t, time):
    spare = []
    wall_plain(img, (40, 36, 64), (24, 20, 40), stripe=(16, 1, (52, 48, 84)))
    floor_carpet(img, (48, 44, 72))
    arcade(img, 96, 0, t); spare.append((96, 0, 112, 32))
    stairs(img, 'plain', (72, 64, 104))
    fixtures(img, t, time, spare, stand=(40, 36, 56), tv_body=(24, 24, 32), wardrobe_cols=((64, 56, 104), (96, 88, 144)),
             desk=(72, 72, 96), clock_face=(32, 32, 40), clock_rim=(248, 72, 200))
    neon_strip(img, 0, PW, 33, t)
    rug(img, 16, 52, 80, 92, (40, 120, 168), (24, 24, 40), 'pokeball')
    bed(img, *BED, (72, 72, 152), frame=(40, 36, 64), pattern='stars', w=22, h=30)
    beanbag(img, 104, 126, (248, 72, 200))
    spare.append((0, 31, PW, 36))
    if time == 'night': night_dim(img, 0.25, spare=spare)
    return spare

@room('cabin', 'Snow Cabin', 'Log walls, a pot-bellied stove that crackles, a fur rug and a red quilt. Cosiest at night.',
      mons=('snorunt', 'swinub', 'spheal', 'vulpix', 'cubchoo'))
def cabin(img, t, time):
    spare = []
    o, d, b, l, h = ramp((152, 96, 56))
    rect(img, 0, 0, PW, 32, b)
    for y in range(0, 30, 6):
        rect(img, 0, y, PW, y + 1, o); rect(img, 0, y + 1, PW, y + 2, l)
        for x in range(((y // 6) % 2) * 20, PW, 40): rect(img, x, y + 2, x + 1, y + 6, d)
    rect(img, 0, 28, PW, 31, d); rect(img, 0, 31, PW, 32, o)
    floor_planks(img, (136, 88, 56), plank=8, gap=(72, 44, 28))
    sx = 98   # the stove, on the free tile
    rect(img, sx + 5, 0, sx + 8, 14, (56, 56, 64))
    for yy in range(14, 30):
        wdt = 6 if yy < 26 else 5
        rect(img, sx + 6 - wdt, yy, sx + 7 + wdt, yy + 1, (64, 64, 72))
    rect(img, sx + 3, 19, sx + 10, 25, (24, 16, 16))
    for k in range(3):
        hgt = 2 + int(2 * abs(math.sin((t + k * 2) * 0.9)))
        rect(img, sx + 4 + k * 2, 25 - hgt, sx + 5 + k * 2, 25, (248, 160 + k * 30, 48))
    spare.append((sx + 3, 19, sx + 10, 25))
    light(lambda: glow(img, sx + 6, 24, 18, (248, 160, 72), 0.25 if time != 'night' else 0.32))
    stairs(img, 'plain', (104, 64, 40))
    fixtures(img, t, time, spare, stand=(104, 64, 40), tv_content='static' if time == 'night' else 'battle',
             wardrobe_cols=((152, 96, 56), (192, 136, 88)), clock_rim=(104, 64, 40))
    round_rug(img, 56, 82, 28, 14, [(240, 232, 216), (224, 212, 192), (240, 232, 216)])
    bed(img, *BED, (176, 48, 48), frame=(104, 64, 40), pattern='check', w=22, h=30)
    plant(img, 136, 70, 'fern', pot=(152, 96, 56))
    if time == 'night': night_dim(img, 0.5, tint=(24, 16, 40), spare=spare)
    return spare

@room('beach', 'Beach Hut', 'Whitewashed planks, a window onto the sea (waves roll, the sun sets in it), a surfboard, a striped rug.',
      mons=('wingull', 'corphish', 'lapras', 'psyduck', 'krabby'))
def beach(img, t, time):
    spare = []
    wall_plain(img, (232, 228, 212), (96, 168, 200), stripe=(12, 1, (212, 208, 192)))
    floor_planks(img, (216, 192, 144), plank=8, gap=(176, 144, 96))
    def sea(im, x0, y0, x1, y1, tm, tt):
        hy = y0 + (y1 - y0) // 2
        water = {'day': (64, 152, 216), 'sunset': (152, 88, 128), 'night': (24, 32, 72)}[tm]
        rect(im, x0, hy, x1, y1, water)
        for x in range(x0, x1):
            for k, yy in enumerate(range(hy + 1, y1, 2)):
                if (x + tt // 2 + k * 3) % 6 < 2: put(im, x, yy, shade(water, 0.35))
    window(img, 97, 4, 14, 18, time, t, frame=(96, 168, 200), extra=sea, panes=1)
    spare.append((99, 6, 109, 20))
    stairs(img, 'glass', (176, 144, 96))
    fixtures(img, t, time, spare, stand=(176, 144, 96), wardrobe_cols=((96, 168, 200), (160, 216, 232)), clock_rim=(96, 168, 200))
    rug(img, 20, 54, 84, 94, (248, 216, 128), (216, 152, 72), 'stripes')
    bed(img, *BED, (72, 200, 216), frame=(176, 144, 96), pattern='stripes', w=22, h=30)
    surfboard(img, 138, 36, (248, 120, 72))
    plant(img, 8, 126, 'palm', pot=(216, 152, 72))
    for (x, y) in ((92, 110), (40, 118)):
        put(img, x, y, (248, 176, 176)); put(img, x + 1, y, (248, 200, 200)); put(img, x, y + 1, (232, 144, 144))
    if time == 'night': night_dim(img, 0.45, spare=spare)
    return spare

@room('treehouse', 'Treehouse', 'Bark walls with a living branch through them, a leafy window, a swaying lantern, a ladder down.',
      mons=('treecko', 'pikachu', 'oddish', 'bulbasaur', 'shroomish'))
def treehouse(img, t, time):
    spare = []
    o, d, b, l, h = ramp((120, 84, 52))
    rect(img, 0, 0, PW, 32, b)
    for x in range(0, PW, 6):
        rect(img, x, 0, x + 1, 30, d)
        if x % 18 == 0: rect(img, x + 3, (x * 7) % 20, x + 4, (x * 7) % 20 + 6, l)
    rect(img, 0, 28, PW, 32, o)
    floor_planks(img, (184, 136, 80), plank=8, gap=(104, 72, 40))
    def leaves(im, x0, y0, x1, y1, tm, tt):
        g = {'day': [(56, 144, 64), (104, 192, 88)], 'sunset': [(120, 104, 56), (200, 144, 72)], 'night': [(16, 40, 40), (32, 64, 56)]}[tm]
        r = random.Random(4)
        for _ in range((x1 - x0) * (y1 - y0) // 4):
            lx, ly = r.randrange(x0, x1), r.randrange(y0, y1)
            if ly < y0 + 3 or ly > y1 - 4 or r.random() < 0.25: put(im, lx + int(math.sin(tt / 4 + lx) * 1), ly, g[r.randrange(2)])
    window(img, 97, 4, 14, 18, time, t, frame=(96, 64, 40), extra=leaves, panes=1)
    spare.append((99, 6, 109, 20))
    stairs(img, 'ladder', (136, 96, 60))
    fixtures(img, t, time, spare, stand=(120, 84, 52), wardrobe_cols=((120, 84, 52), (168, 120, 72)), clock_rim=(96, 64, 40))
    for x in range(0, 30):   # a branch growing in through the wall
        y = 40 + int(math.sin(x / 6) * 2)
        rect(img, x, y, x + 1, y + 3, (104, 72, 44)); put(img, x, y, (136, 96, 60))
    for lx, ly in ((10, 38), (20, 37), (28, 42)):
        for k in range(3): put(img, lx + k, ly - (k == 1), (56, 144, 64)); put(img, lx + k, ly + 1, (104, 192, 88))
    lantern(img, 88, 34 + int(math.sin(t / 6) * 1), t, col=(232, 96, 56))
    round_rug(img, 64, 82, 30, 15, [(104, 160, 80), (152, 200, 104), (104, 160, 80), (216, 184, 112)])
    bed(img, *BED, (104, 160, 80), frame=(104, 72, 44), pattern='check', w=22, h=30)
    plant(img, 8, 126, 'fern', pot=(120, 84, 52))
    if time == 'night': night_dim(img, 0.5, spare=spare)
    return spare

@room('champion', "Champion's Suite", 'Marble and red carpet, a skyline window that lights up at night, a gold trophy, a canopy bed.',
      mons=('dragonite', 'garchomp', 'metagross', 'milotic', 'salamence'))
def champion(img, t, time):
    spare = []
    wall_plain(img, (232, 224, 208), (200, 160, 64), stripe=(24, 2, (216, 208, 188)))
    floor_tiles(img, (232, 228, 220), (208, 204, 196), size=16, grout=(176, 172, 168))
    rect(img, 40, 32, 72, PH, (168, 32, 40)); rect(img, 42, 32, 70, PH, (200, 48, 56))
    for x in (42, 68): rect(img, x, 32, x + 2, PH, (232, 192, 72))
    def skyline(im, x0, y0, x1, y1, tm, tt):
        r = random.Random(11); x = x0
        while x < x1:
            bw = r.randrange(3, 6); bh = r.randrange(4, y1 - y0 - 1)
            rect(im, x, y1 - bh, min(x + bw, x1), y1, {'day': (120, 136, 168), 'sunset': (88, 64, 96), 'night': (24, 24, 48)}[tm])
            if tm != 'day':
                for wy in range(y1 - bh + 1, y1 - 1, 2):
                    for wx in range(x + 1, min(x + bw, x1) - 1, 2):
                        if r.random() < 0.5 and (wx + wy + tt // 6) % 7: put(im, wx, wy, (248, 224, 120))
            x += bw + 1
    window(img, 97, 3, 14, 20, time, t, frame=(200, 160, 64), extra=skyline, panes=1)
    spare.append((99, 5, 109, 21))
    stairs(img, 'arch', (200, 160, 64))
    fixtures(img, t, time, spare, stand=(80, 48, 40), wardrobe_cols=((104, 48, 40), (200, 160, 64)),
             desk=(168, 32, 40), clock_face=(248, 240, 216), clock_rim=(200, 160, 64))
    rect(img, 92, 100, 104, 112, (200, 192, 176)); rect(img, 92, 100, 104, 101, (240, 236, 224))   # trophy on a plinth
    rect(img, 94, 90, 102, 96, (248, 208, 64)); rect(img, 97, 96, 99, 99, (248, 208, 64)); rect(img, 95, 98, 101, 100, (200, 160, 48))
    if (t // 6) % 4 == 0: put(img, 95, 91, (255, 255, 224))
    bed(img, *BED, (168, 32, 40), frame=(200, 160, 64), pillow=(248, 240, 216), canopy=(232, 192, 72), pattern='ball', w=24, h=30)
    plant(img, 8, 126, 'bonsai', pot=(200, 160, 64))
    if time == 'night': night_dim(img, 0.4, spare=spare)
    return spare

@room('space', 'Space Station', 'Steel panels, a porthole with stars and a planet drifting by, blinking lights, an airlock instead of stairs.',
      mons=('clefairy', 'porygon', 'beldum', 'lunatone', 'solrock'))
def space(img, t, time):
    spare = []
    o, d, b, l, h = ramp((112, 120, 136))
    rect(img, 0, 0, PW, 32, b)
    for x in range(0, PW, 16): rect(img, x, 0, x + 1, 32, o); rect(img, x + 1, 0, x + 2, 32, l)
    rect(img, 0, 14, PW, 15, d); rect(img, 0, 28, PW, 32, o)
    floor_metal(img, (88, 96, 112))
    cx, cy, r_ = 104, 14, 7
    for yy in range(-r_ - 2, r_ + 3):
        for xx in range(-r_ - 2, r_ + 3):
            dd = math.hypot(xx, yy)
            if dd <= r_ + 2: put(img, cx + xx, cy + yy, (64, 72, 88) if dd > r_ + 1 else (160, 168, 184))
    for yy in range(-r_, r_ + 1):
        for xx in range(-r_, r_ + 1):
            if math.hypot(xx, yy) <= r_:
                put(img, cx + xx, cy + yy, (8, 8, 24))
                if ((xx * 7 + yy * 13 + t) % 23) == 0: put(img, cx + xx, cy + yy, (248, 248, 248))
    px_, py_ = cx - 8 + (t // 3) % 16, cy + 2
    for yy in range(-3, 4):
        for xx in range(-3, 4):
            if xx * xx + yy * yy <= 9 and math.hypot(px_ + xx - cx, py_ + yy - cy) <= r_:
                put(img, px_ + xx, py_ + yy, (216, 128, 72) if (yy + 1) % 3 else (248, 184, 120))
    spare.append((cx - r_, cy - r_, cx + r_, cy + r_))
    stairs(img, 'airlock')
    fixtures(img, t, time, spare, stand=(64, 72, 88), tv_body=(40, 44, 56), tv_content='game', wardrobe_cols=((112, 120, 136), (168, 176, 192)),
             desk=(72, 80, 96), clock_face=(16, 24, 32), clock_rim=(72, 232, 248))
    for k in range(9):   # status lights along the foot of the wall
        put(img, 4 + k * 16, 30, (72, 248, 120) if (k + t // 3) % 3 else (248, 96, 72))
    rug(img, 16, 52, 84, 92, (64, 72, 96), (72, 232, 248), 'star')
    bed(img, *BED, (72, 120, 200), frame=(200, 208, 224), pillow=(232, 240, 248), pattern='stars', w=22, h=30)
    rect(img, BED[0] - 1, BED[1] - 3, BED[0] + 23, BED[1], (72, 232, 248))
    light(lambda: glow(img, BED[0] + 11, BED[1] - 2, 14, (72, 232, 248), 0.2))
    for x in range(4, PW - 4):
        if (x + t) % 24 < 2: put(img, x, 124, (72, 232, 248))
    if time == 'night': night_dim(img, 0.3, spare=spare)
    return spare

@room('tatami', 'Tatami Room', 'Johto calm: shoji walls and door, tatami mats, a futon, a low table, cherry blossom past a round window.',
      mons=('eevee', 'espeon', 'umbreon', 'sentret', 'hoothoot'))
def tatami(img, t, time):
    spare = []
    rect(img, 0, 0, PW, 32, (240, 232, 208))
    for x in range(0, PW, 24): rect(img, x, 0, x + 2, 32, (104, 64, 40))
    for y in (10, 20): rect(img, 0, y, PW, y + 1, (152, 112, 72))
    rect(img, 0, 0, PW, 3, (104, 64, 40)); rect(img, 0, 28, PW, 32, (88, 56, 36))
    floor_tatami(img)
    def petals(im, x0, y0, x1, y1, tm, tt):
        r = random.Random(2)
        for k in range(5):
            put(im, x0 + (r.randrange(0, x1 - x0) + tt // 2) % (x1 - x0), y0 + (r.randrange(0, y1 - y0) + tt // 3) % (y1 - y0), (248, 176, 200))
    spare.append(porthole(img, 104, 14, 7, time, t, rim=(88, 56, 36), extra=petals))
    stairs(img, 'shoji')
    fixtures(img, t, time, spare, stand=(104, 64, 40), tv_body=(88, 56, 36), wardrobe_cols=((104, 64, 40), (152, 112, 72)), clock_rim=(104, 64, 40))
    table_low(img, 40, 66, 32, 18, (152, 96, 56))
    for x, y in ((30, 70), (76, 70)): rect(img, x, y, x + 8, y + 8, (168, 48, 48)); rect(img, x + 1, y + 1, x + 7, y + 7, (200, 72, 64))
    bed(img, *BED, (72, 96, 168), frame=(240, 232, 208), pillow=(248, 248, 240), pattern='check', w=22, h=30)
    plant(img, 8, 126, 'bonsai', pot=(72, 72, 80)); plant(img, 136, 70, 'blossom', pot=(72, 72, 80))
    lantern(img, 96, 40, t, col=(240, 232, 208))
    if time == 'night': night_dim(img, 0.45, spare=spare)
    return spare

@room('aquarium', 'Aquarium', 'The whole back wall is a tank: Luvdisc, Wailmer and Chinchou swim behind the furniture. Sleep in a clam.',
      mons=('mudkip', 'wooper', 'luvdisc', 'horsea', 'chinchou'))
def aquarium_room(img, t, time):
    spare = []
    floor_tiles(img, (88, 120, 168), (80, 112, 160), size=16, grout=(64, 88, 136))
    px = img.load()
    for y in range(34, PH):
        for x in range(0, PW):
            if ((x + t) % 32 - 16) ** 2 + ((y * 2 - t) % 32 - 16) ** 2 in range(60, 90): px[x, y] = mix(px[x, y], (168, 216, 248), 0.35)
    spare.append(aquarium(img, 0, 0, PW, 34, t, water={'day': (56, 136, 216), 'sunset': (72, 104, 184), 'night': (24, 48, 112)}[time]))
    for i, (m, sp, y, dirn) in enumerate((('luvdisc', 1, 2, 1), ('wailmer', 0.5, 0, -1), ('chinchou', 0.7, 8, 1))):
        spr = mk.mon(m)
        if dirn < 0: spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        x = int(((t * sp * dirn) + i * 50) % (PW + 32)) - 32
        bob = int(math.sin(t / 4 + i) * 1.5)
        c = spr.crop((0, 0, spr.width, max(1, min(spr.height, 30 - y - bob))))
        img.paste(c, (x, y + bob), c)
    stairs(img, 'glass')
    fixtures(img, t, time, spare, stand=(48, 56, 80), wardrobe_cols=((72, 152, 200), (160, 216, 232)), desk=(72, 152, 200), clock_rim=(72, 152, 200))
    cx, cy = BED[0] + 12, BED[1] + 18   # clam bed
    for yy in range(-14, 1):
        for xx in range(-13, 14):
            if (xx / 13) ** 2 + ((yy + 1) / 14) ** 2 <= 1: put(img, cx + xx, cy + yy - 6, (232, 160, 192) if (xx // 3) % 2 else (248, 192, 216))
    rect(img, cx - 12, cy - 6, cx + 12, cy + 8, (248, 216, 232)); rect(img, cx - 10, cy - 4, cx + 10, cy + 6, (120, 168, 232))
    rect(img, cx - 8, cy - 4, cx, cy, (248, 248, 240))
    round_rug(img, 60, 82, 28, 14, [(72, 168, 200), (120, 208, 232), (72, 168, 200)])
    for (x, y, c) in ((8, 124, (248, 120, 120)), (20, 126, (248, 176, 72))):
        for k in range(7): put(img, x + int(math.sin(k + t / 5) * 1), y - k, c)
    if time == 'night': night_dim(img, 0.35, tint=(8, 16, 56), spare=spare)
    return spare

@room('greenhouse', 'Greenhouse', 'Glass roof straight onto the sky, vines hanging over the furniture, a planter, a sprinkler ticking round.',
      mons=('bellossom', 'oddish', 'roselia', 'chikorita', 'bulbasaur'))
def greenhouse(img, t, time):
    spare = []
    sky(img, 0, 0, PW, 32, time, t, seed=6)
    for x in range(0, PW, 24): rect(img, x, 0, x + 2, 32, (232, 232, 224))
    rect(img, 0, 15, PW, 16, (232, 232, 224)); rect(img, 0, 28, PW, 32, (208, 208, 200))
    for x in range(4, PW, 24):
        for k in range(3): put(img, x + k, 2 + k, mix(SKY[time][2], (255, 255, 255), 0.6))
    floor_tiles(img, (200, 184, 152), (184, 168, 136), size=16, grout=(152, 136, 112))
    rect(img, 96, 18, 112, 30, (152, 96, 56)); rect(img, 97, 19, 111, 21, (88, 56, 32))
    plant(img, 100, 22, 'blossom', pot=(152, 96, 56)); plant(img, 108, 22, 'fern', pot=(152, 96, 56))
    stairs(img, 'glass')
    fixtures(img, t, time, spare, stand=(152, 96, 56), wardrobe_cols=((88, 160, 96), (152, 208, 136)), desk=(152, 96, 56), clock_rim=(56, 144, 64))
    r = random.Random(3)
    for x in range(4, PW - 4, 9):
        ln = r.randrange(4, 12)
        for k in range(ln): put(img, x + int(math.sin((k + t) / 4) * 1.2), 1 + k, (56, 144, 64) if k % 3 else (104, 192, 88))
    round_rug(img, 52, 80, 26, 13, [(120, 176, 96), (152, 200, 120), (120, 176, 96)])
    sx, sy = 52, 80
    rect(img, sx - 1, sy - 4, sx + 1, sy, (120, 120, 128))
    for k in range(4, 16, 2):
        ang = t * 0.5 + k * 0.08
        put(img, sx + int(math.cos(ang) * k), sy - 4 + int(math.sin(ang) * k * 0.5), (168, 216, 248))
    bed(img, *BED, (152, 200, 120), frame=(152, 96, 56), pattern='check', w=22, h=30)
    plant(img, 8, 126, 'palm', pot=(152, 96, 56)); plant(img, 136, 70, 'cactus', pot=(152, 96, 56))
    if time == 'night': night_dim(img, 0.45, spare=spare)
    return spare

@room('lair', 'Volcano Lair', 'Villain chic in raw rock: lava glowing through floor grates, a red monitor on the wall, a stone archway down.',
      mons=('houndoom', 'torkoal', 'magcargo', 'slugma', 'numel'))
def lair(img, t, time):
    spare = []
    o, d, b, l, h = ramp((96, 64, 64))
    rect(img, 0, 0, PW, 32, b)
    r = random.Random(8)
    for _ in range(50):
        x, y = r.randrange(0, PW), r.randrange(0, 28)
        rect(img, x, y, x + r.randrange(3, 9), y + 1, d if r.random() < 0.6 else l)
    rect(img, 0, 28, PW, 32, o)
    floor_tiles(img, (72, 56, 56), (64, 48, 52), size=16, grout=(40, 32, 36))
    rect(img, 96, 4, 112, 22, (24, 16, 20)); rect(img, 98, 6, 110, 20, (88, 16, 24) if (t // 8) % 3 else (136, 24, 32))
    draw_text(img.load(), 'HP', 100, 10, (248, 120, 120)); spare.append((96, 4, 112, 22))
    stairs(img, 'arch', (96, 64, 64))
    fixtures(img, t, time, spare, stand=(48, 32, 36), tv_body=(40, 24, 24), wardrobe_cols=((136, 24, 32), (200, 64, 56)),
             desk=(136, 24, 32), clock_face=(40, 24, 24), clock_rim=(232, 88, 32))
    for gx, gy in ((24, 74), (96, 72)):
        rect(img, gx, gy, gx + 20, gy + 10, (40, 24, 24))
        for k in range(gx + 2, gx + 18, 4):
            rect(img, k, gy + 2, k + 2, gy + 8, (248, 120, 40) if (k // 4 + t // 3) % 3 else (248, 216, 96))
        light(lambda gx=gx, gy=gy: glow(img, gx + 10, gy + 5, 16, (248, 112, 40), 0.22))
        spare.append((gx, gy, gx + 20, gy + 10))
    bed(img, *BED, (136, 24, 32), frame=(48, 32, 36), pattern='stripes', w=22, h=30)
    night_dim(img, 0.3 if time == 'night' else 0.15, tint=(24, 8, 8), spare=spare)
    return spare

@room('clouds', 'Cloud Castle', 'Up in the Sky Arena\'s sky: white and gold, the wall open to drifting clouds behind a balustrade.',
      mons=('altaria', 'swablu', 'pidgeot', 'togekiss', 'jigglypuff'))
def clouds(img, t, time):
    spare = []
    sky(img, 0, 0, PW, 32, time, t, seed=2)
    for k in range(0, PW + 40, 36):
        cx = (k + t) % (PW + 40) - 20
        for yy in range(-4, 5):
            for xx in range(-14, 15):
                if (xx / 14) ** 2 + (yy / 5) ** 2 <= 1: put(img, cx + xx, 12 + yy, (248, 248, 248) if time != 'sunset' else (248, 216, 200))
    for x in range(0, PW, 6): rect(img, x + 1, 20, x + 4, 30, (240, 232, 208)); rect(img, x + 1, 20, x + 2, 30, (255, 255, 240))
    rect(img, 0, 18, PW, 21, (232, 200, 104)); rect(img, 0, 29, PW, 32, (200, 168, 88))
    floor_tiles(img, (248, 244, 232), (232, 228, 216), size=16, grout=(216, 200, 160))
    stairs(img, 'arch', (232, 200, 104))
    fixtures(img, t, time, spare, stand=(232, 200, 104), wardrobe_cols=((232, 200, 104), (248, 232, 168)), desk=(96, 152, 216),
             clock_face=(255, 255, 248), clock_rim=(232, 200, 104))
    rug(img, 18, 54, 84, 94, (96, 152, 216), (232, 200, 104), 'star')
    bed(img, *BED, (96, 152, 216), frame=(232, 200, 104), pillow=(255, 255, 248), canopy=(248, 248, 240), pattern='stars', w=24, h=30)
    plant(img, 8, 126, 'blossom', pot=(232, 200, 104))
    if time == 'night': night_dim(img, 0.4, spare=spare)
    return spare

# ---------------------------------------------------------------------------------------------
def frame(name, t, time):
    img = Image.new('RGB', (PW, PH), (0, 0, 0))
    STATE.update(time=time, late=[], dim=[])
    ROOMS[name]['draw'](img, t, time)
    for k, tint, spare in STATE['dim']: dim(img, k, tint, spare)
    for fn in STATE['late']: fn()
    return img

def still(name, time='day'):
    img = frame(name, 0, time)
    b = box_sprite()
    if b: img.paste(b, (7 * T, T), b)
    for (mx, my), m in zip(SPOTS, ROOMS[name]['mons']):
        try: stamp_mon(img, m, mx, my)
        except Exception: pass
    stamp_player(img, *START)
    try: stamp_mon(img, ROOMS[name]['mons'][0], START[0], START[1] + 1)
    except Exception: pass
    return img

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    names = sys.argv[1:] or list(ROOMS)
    for n in names:
        for tm in TIMES:
            save_gif([frame(n, t, tm) for t in range(0, 48, 2)], f'{HERE}/out/{n}_{tm}.gif', scale=4)
        tb = tile_budget(frame(n, 0, 'day'))
        still(n).resize((PW * 4, PH * 4), Image.NEAREST).save(f'{HERE}/out/{n}.png')
        print(n, 'tiles', tb[0], 'colours', tb[1])
