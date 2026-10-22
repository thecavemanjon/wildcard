import copy, mapkit as mk, gbafont
from PIL import Image
lid, _ = mk.map_layout('BattleFrontier_BattleDomeBattleRoom'); kit, dome = mk.layout(lid)
FLOOR = dome[9][0]
P = mk.person
RED = P('graphics/object_events/pics/people/red/red_normal.png')
def ow(name): return P(f'graphics/object_events/pics/people/{name}.png')
EMBLEM = dome[3][0]
W = 24

def pad(r, n, fill=None):
    return ([fill]*n if fill else [r[i % 2] for i in range(n)]) + r + ([fill]*n if fill else [r[-2 + (i % 2)] for i in range(n)])

def grand(stand_rows=4, banner='frontier'):
    rows = [pad(dome[0], 2) for _ in range(stand_rows - 1)] + [pad(dome[2], 2)]
    b = [dome[3][(x + 5) % 7] for x in range(W)]  # the banner repeats every 7 tiles
    if banner != 'frontier':
        b = [EMBLEM if x in (2, W - 3) else dome[3][1] for x in range(W)]
    rows.append(b)
    rows += [[FLOOR]*3 + r + [FLOOR]*1 for r in dome[4:10]]
    rows += [[FLOOR]*W]
    return rows

def pal_with(changes):
    p = copy.deepcopy(kit.pals)
    for (i, c), v in changes.items(): p[i][c] = v
    return p

def podium_sprites(top, opp):
    return [(RED, 7, top + 3), (opp, 16, top + 3)]

def render(g, sprites, pals=None, text=None, banner_row=None):
    im = kit.render(g, sprites, pals)
    if text:  # blank the banner strip between the emblems, then letter it
        px = im.load(); bg = px[3*16 + 12, banner_row*16 + 8]
        for yy in range(banner_row*16 + 3, banner_row*16 + 13):
            for xx in range(0, W*16):
                if xx // 16 not in (2, W - 3): px[xx, yy] = bg
        y = banner_row*16 - 1
        wtxt = sum(gbafont.WIDTHS[gbafont.CHARMAP[c]] for c in text)
        gbafont.draw(im, text, (im.width - wtxt)//2, y, (255, 255, 255), (60, 90, 120))
    return im

CASES = []
g = grand(); CASES.append(('S1. Grand Dome: the Battle Dome with a bigger crowd', render(g, podium_sprites(4, ow('steven')))))
g = grand(banner='plain'); CASES.append(('S2. Wild Card Stadium: own banner (new banner tiles)', render(g, podium_sprites(4, ow('steven')), text='POKéMON WILD CARD', banner_row=4)))
grass = pal_with({(8, 11): (112, 176, 80), (8, 6): (72, 128, 64), (8, 12): (92, 104, 76)})
CASES.append(('S3. Stadium pitch: grass field, like Pokémon Stadium', render(g, podium_sprites(4, ow('steven')), grass, 'POKéMON WILD CARD', 4)))
night = pal_with({(8, 9): (84, 60, 132), (8, 10): (116, 88, 172), (8, 12): (52, 44, 64), (8, 6): (70, 58, 92), (8, 11): (196, 176, 236)})
CASES.append(('S4. Night final: purple stands, lavender field', render(g, podium_sprites(4, ow('steven')), night, 'POKéMON WILD CARD', 4)))
wc = pal_with({(8, 9): (164, 48, 48), (8, 10): (212, 84, 72), (8, 11): (244, 232, 200), (8, 12): (110, 88, 72), (8, 6): (150, 120, 96)})
CASES.append(('S5. Wild Card red: title-screen colours', render(g, podium_sprites(4, ow('steven')), wc, 'POKéMON WILD CARD', 4)))
for i, (n, im) in enumerate(CASES): mk.label(im, n, 2).save(f'stadium_{i+1}.png')
