# Take 7: the traced summit, but the walls rise to a point where Red stands,
# with sky above the slopes either side.
import trace2 as T2, trace_summit as T, summit as S, mapkit as mk
from PIL import Image
G, W, Hh, PL, PR = S.G, T2.W, T2.Hh, T2.PL, T2.PR
SKY = None

def build(jog=3, gap=2, run=2):
    g = T2.lines(jog, gap)
    sky = set()
    cx = (PL + PR)//2
    for side in (-1, 1):
        # the skyline: a stepped ledge running down and away from the summit
        x, y = (PL - 2 if side < 0 else PR + 2), 1
        while 0 <= x < W and y < 21:
            for _ in range(run):
                if not (0 <= x < W): break
                g[y][x] = S.H
                for yy in range(0, y): sky.add((x, yy))
                x += side
            if not (0 <= x < W): break
            g[y][x] = S.WS if side > 0 else S.ES
            for yy in range(0, y): sky.add((x, yy))
            y += 1
            g[y][x] = S.NE if side > 0 else S.NW
            for yy in range(0, y): sky.add((x, yy))
            x += side
        for xx in range(0, W):
            if (xx < PL - 1 and side < 0) or (xx > PR + 1 and side > 0):
                pass
    # the summit itself: Red's little plateau, a ledge each side of the steps
    for x in range(PL - 1, PR + 2): sky.add((x, 0))     # nothing above Red but sky
    g[1][PL - 1] = S.ES; g[1][PR + 1] = S.WS              # the summit's rounded shoulders
    return g, sky

def render(g, sky, top=(96, 118, 150), bottom=(196, 214, 232)):
    im = S.kit.render(g, [(S.RED, 21, 1), (S.PIKA, 22, 1), (S.player(), 21, 7)], T.crisp_pals())
    px = im.load()
    for (x, y) in sky:
        for yy in range(16):
            t = (y*16 + yy) / (16*12)
            c = tuple(int(top[k] + (bottom[k] - top[k])*min(1, t)) for k in range(3))
            for xx in range(16): px[x*16 + xx, y*16 + yy] = c
    S.snowfall(im, 300, 5)
    return im

if __name__ == '__main__':
    ref = Image.open('../ref/summit_hgss.png').convert('RGB')
    rows = []
    for run, label in [(2, 'Take 7: Red on the peak, gentle slopes'), (1, 'Take 7: Red on the peak, steep slopes')]:
        g, sky = build(run=run); im = render(g, sky)
        rows.append((label, im, im.crop((21*16 + 8 - 120, 0, 21*16 + 8 + 120, 160))))
    sh = Image.new('RGB', (12 + 640 + 12 + 720 + 12, 12 + 3*(34 + 480 + 12)), (12, 12, 16))
    def put(img, x, y, text): sh.paste(mk.label(img, text, 1), (x, y))
    put(ref, 12, 12, 'Reference'); put(ref.crop((200, 16, 456, 208)).resize((640, 480), 0), 664, 12, 'Reference, close up')
    y = 12 + 34 + 480 + 12
    for label, im, o in rows:
        put(im, 12, y, label); put(o.resize((720, 480), 0), 664, y, 'on screen'); y += 34 + 480 + 12
    sh.save('sheet_red_take7.png')
