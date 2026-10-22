import trace2 as T2, trace_summit as T, summit as S, mapkit as mk
from PIL import Image
W, PL, PR = T2.W, T2.PL, T2.PR

def build(crest):
    red = crest                           # Red stands level with the top of the walls
    g = T2.lines(3, 2, top=crest, step_rows=(red + 1, red + 2, red + 3))
    for x in range(W):
        if PL <= x <= PR: continue
        v = g[crest][x]
        g[crest][x] = (S.ES if x < PL else S.WS) if v in (S.V_R, S.V_L) else S.H
    g[crest][PL - 1] = S.H; g[crest][PR + 1] = S.H
    for x in range(PL, PR + 1): g[crest][x] = S.G      # Red's spot at the very top of the path
    return g, red

def render(g, crest, red, sky=(128, 148, 178)):
    im = S.kit.render(g, [(S.RED, 21, red), (S.PIKA, 22, red), (S.player(), 21, red + 5)], T.crisp_pals())
    px = im.load()
    for x in range(im.width):
        lip = 6 if not (PL*16 <= x < (PR + 1)*16) else 0
        for y in range(0, crest*16 + lip): px[x, y] = sky
    S.snowfall(im, 300, 5)
    return im

if __name__ == '__main__':
    rows = []
    for crest, n in [(2, 'Red at the very top, sky behind him (2 rows of sky)'), (3, 'Same, 3 rows of sky')]:
        g, red = build(crest); im = render(g, crest, red)
        rows.append((n, im, im.crop((21*16 + 8 - 120, 0, 21*16 + 8 + 120, 160))))
    sh = Image.new('RGB', (12 + 640 + 12 + 720 + 12, 12 + 2*(34 + 480 + 12)), (12, 12, 16)); y = 12
    for n, im, o in rows:
        sh.paste(mk.label(im, n, 1), (12, y)); sh.paste(mk.label(o.resize((720, 480), 0), 'on screen', 1), (664, y)); y += 34 + 480 + 12
    sh.save('sheet_red_peak.png')
