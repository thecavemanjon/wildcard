import trace2 as T2, trace_summit as T, summit as S, mapkit as mk
from PIL import Image
W, PL, PR = T2.W, T2.PL, T2.PR

def base():
    return T2.lines(3, 2, top=1, step_rows=(4, 5, 6))

def caps(g):  # round off the top of every rib
    for x in range(W):
        if g[1][x] == S.V_R: g[1][x] = S.ES
        elif g[1][x] == S.V_L: g[1][x] = S.WS
    return g

def crest(g):  # one continuous snowy crest along the top, joining the ribs
    for x in range(W):
        if PL - 1 <= x <= PR + 1: continue
        v = g[1][x]
        if v in (S.V_R, S.V_L): g[1][x] = S.ES if x < PL else S.WS
        else: g[1][x] = S.H
    g[1][0] = S.H; g[1][W - 1] = S.H
    g[1][PL - 1] = S.WS; g[1][PR + 1] = S.ES   # the crest turns down into the path walls
    return g

def crest_full(g):  # the crest runs right across, behind Red too
    g = crest(g)
    for x in range(PL - 1, PR + 2): g[1][x] = S.H
    return g

def render(g, sky=None, sky_all=False):
    im = S.kit.render(g, [(S.RED, 21, 2), (S.PIKA, 22, 2), (S.player(), 21, 8)], T.crisp_pals())
    if sky:
        px = im.load()
        for x in range(im.width):
            if PL*16 <= x < (PR + 1)*16 and not sky_all: continue
            for y in range(0, 16 + 6): px[x, y] = sky
    S.snowfall(im, 300, 5)
    return im

opts = [('Now: ribs stop at a flat strip', render(base())),
        ('A. Each rib rounded off at the top', render(caps(base()))),
        ('B. A snowy crest joining the ribs', render(crest(base()))),
        ('C. Crest, with sky behind it', render(crest(base()), (128, 148, 178))),
        ('D. Crest right across behind Red, sky above', render(crest_full(base()), (128, 148, 178), True))]
crops = [(n, im.crop((21*16 + 8 - 200, 0, 21*16 + 8 + 200, 120)).resize((800, 240), Image.NEAREST)) for n, im in opts]
sh = Image.new('RGB', (2*800 + 36, 3*(240 + 34) + 48), (12, 12, 16))
for i, (n, c) in enumerate(crops):
    sh.paste(mk.label(c, n, 1), (12 + (i % 2)*812, 12 + (i//2)*286))
sh.save('sheet_red_top.png')
