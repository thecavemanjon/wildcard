import trace2 as T2, trace_summit as T, summit as S, mapkit as mk
from PIL import Image
W, PL, PR = T2.W, T2.PL, T2.PR
CREST = 2          # one tile lower than before

def build(full):
    g = T2.lines(3, 2, top=CREST, step_rows=(CREST + 3, CREST + 4, CREST + 5))
    for x in range(W):
        if PL - 1 <= x <= PR + 1 and not full: continue
        v = g[CREST][x]
        g[CREST][x] = (S.ES if x < PL else S.WS) if v in (S.V_R, S.V_L) else S.H
    if not full: g[CREST][PL - 1] = S.WS; g[CREST][PR + 1] = S.ES
    for y in range(CREST):
        for x in range(W): g[y][x] = S.G
    return g

def render(g, full, sky=(128, 148, 178)):
    ry = CREST + 1
    im = S.kit.render(g, [(S.RED, 21, ry), (S.PIKA, 22, ry), (S.player(), 21, ry + 6)], T.crisp_pals())
    px = im.load()
    for x in range(im.width):
        if PL*16 <= x < (PR + 1)*16 and not full: continue
        for y in range(0, CREST*16 + 6): px[x, y] = sky
    S.snowfall(im, 300, 5)
    return im

if __name__ == '__main__':
    rows = []
    for full, n in [(False, 'C, a tile lower: sky either side, path runs up behind Red'), (True, 'D, a tile lower: crest right across behind Red')]:
        im = render(build(full), full)
        rows.append((n, im, im.crop((21*16 + 8 - 120, 0, 21*16 + 8 + 120, 160))))
    sh = Image.new('RGB', (12 + 640 + 12 + 720 + 12, 12 + 2*(34 + 480 + 12)), (12, 12, 16)); y = 12
    for n, im, o in rows:
        sh.paste(mk.label(im, n, 1), (12, y)); sh.paste(mk.label(o.resize((720, 480), 0), 'on screen', 1), (664, y)); y += 34 + 480 + 12
    sh.save('sheet_red_crest.png')
