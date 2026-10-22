# Red's summit, take 2: parallel ridge lines beside the path that all step outwards
# together every few rows, like the HeartGold/SoulSilver map.
import trace_summit as T, summit as S, mapkit as mk
from PIL import Image
G = S.G
W, Hh = 40, 30
PL, PR = 20, 22          # path columns

def lines(jog=3, gap=2, top=0, bottom_open=22, open_l=12, open_r=27, flip=False, step_rows=(3, 4, 5)):
    g = [[G]*W for _ in range(Hh)]
    def put(x, y, t):
        if 0 <= x < W and 0 <= y < Hh: g[y][x] = t
    for side in (-1, 1):
        V = S.V_R if side < 0 else S.V_L
        turn_out = S.NW if side < 0 else S.NE        # from above, turning outwards
        turn_down = S.ES if side < 0 else S.WS       # from the inside, turning down
        start = PL - 1 if side < 0 else PR + 1
        for y in range(top, Hh):                       # the path's own wall
            if y < bottom_open: put(start, y, V)
        # nested lines: a new one peels off the path wall every 2*jog rows and steps outwards
        for o in range(-Hh, 14*gap*jog, gap*jog):
            y0 = max(top, top - o) + (1 if o < 0 else 0)
            steps = (y0 - top + o)//jog
            x = start + side*(steps + (gap - 1)*steps//1 if False else steps)
            x = start + side*steps
            if o < 0: x += side                      # starts one column out from the path wall
            for y in range(y0, Hh):
                if y >= bottom_open and open_l <= x <= open_r: break
                if not (0 <= x < W): break
                if (y - top + o) % jog == 0 and y > y0:
                    put(x, y, turn_out); x += side; put(x, y, turn_down)
                else:
                    put(x, y, V)
    if flip:  # the ribs step inwards as they come down, ending against the path wall
        for y in range(top, bottom_open):
            for x in range(W):
                if not (PL - 1 <= x <= PR + 1): g[y][x] = G
        for side in (-1, 1):
            start = PL - 1 if side < 0 else PR + 1
            V = S.V_L if side < 0 else S.V_R
            turn_in = S.NE if side < 0 else S.NW          # from above, turning toward the path
            turn_dn = S.WS if side < 0 else S.ES          # from the outside, turning down
            for k in range(1, 40):
                x = start + side*gap*k
                for y in range(top, bottom_open):
                    if (y - top) % jog == jog - 1 and y > top:
                        nx = x - side
                        if nx == start: break             # met the path wall
                        put(x, y, turn_in); put(nx, y, turn_dn); x = nx
                    else:
                        put(x, y, V)
    # the foot of the upper walls: a ledge right across (the path runs through it), then
    # straight ribbed cliffs either side of a wide snowy area, as on the HGSS map
    for y in range(bottom_open, Hh):
        for x in range(W): g[y][x] = G
    for x in range(W):
        if not (PL - 1 <= x <= PR + 1): g[bottom_open][x] = S.H
    g[bottom_open][PL - 2] = S.NW; g[bottom_open][PR + 2] = S.NE
    for y in range(bottom_open + 1, Hh):
        for x in range(0, open_l, gap): g[y][x] = S.V_R
        for x in range(open_r + 1, W, gap): g[y][x] = S.V_L
    for x in range(0, open_l): g[bottom_open + 1][x] = S.H if x % gap else S.ES
    for x in range(open_r + 1, W): g[bottom_open + 1][x] = S.H if (x - open_r - 1) % gap else S.WS
    # the summit: steps up to Red, rock either side of them
    for x in range(PL, PR + 1):
        for y in step_rows: g[y][x] = S.STEP
        for y in range(0, step_rows[0]): g[y][x] = G
    return g

def scene(jog, gap, name, flip=False):
    g = lines(jog, gap, flip=flip)
    im = S.kit.render(g, [(S.RED, 21, 1), (S.PIKA, 22, 1), (S.player(), 21, 7)], T.crisp_pals())
    S.snowfall(im, 300, 5)
    return name, im

if __name__ == '__main__':
    ref = Image.open('../ref/summit_hgss.png').convert('RGB')
    outs = [('Reference', ref)]
    for jog, gap, n in [(3, 1, 'Take 5: a rib every tile, step every 3 rows'), (3, 2, 'Take 5: a rib every 2 tiles, step every 3 rows')]:
        outs.append(scene(jog, gap, n))
    tiles = [mk.label(im, n, 1) for n, im in outs]
    sh = Image.new('RGB', (sum(t.width for t in tiles) + 48, max(t.height for t in tiles) + 24), (12, 12, 16)); x = 12
    for t in tiles: sh.paste(t, (x, 12)); x += t.width + 12
    sh.save('trace2_compare.png')
    n, im = outs[1]
    o = im.crop((21*16 + 8 - 120, 0, 21*16 + 8 + 120, 160)); r = ref.crop((200, 16, 456, 208))
    cmp = Image.new('RGB', (768 + 720 + 30, 596), (12, 12, 16)); cmp.paste(r.resize((768, 576), 0), (10, 10)); cmp.paste(o.resize((720, 480), 0), (788, 10))
    cmp.save('trace2_screens.png')
