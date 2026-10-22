import copy, mapkit as mk, summit as S
from PIL import Image
lid, M = mk.map_layout('BattleFrontier_BattlePyramidTop'); kit, g = mk.layout(lid)

def theme(sky_top, sky, horizon, below, sun, sun_rim, flank, flank_tex, face, tier, tier_tex):
    p = copy.deepcopy(kit.pals)
    for i, c in {13: sky_top, 4: sky, 3: horizon, 2: below, 11: sun, 12: sun_rim, 5: flank, 6: flank_tex,
                 7: face, 9: tier, 10: tier_tex}.items():
        p[8][i] = c
    p[8][6] = p[8][5]; p[8][10] = p[8][9]   # no bricks: smooth snow slopes and ledges
    return p

DAY = theme((112, 128, 164), (170, 186, 212), (214, 224, 238), (236, 240, 248), (244, 244, 236), (206, 212, 224),
            (240, 244, 252), (186, 198, 218), (92, 100, 122), (218, 226, 240), (142, 152, 174))
NOSUN = theme((112, 128, 164), (170, 186, 212), (214, 224, 238), (236, 240, 248), (170, 186, 212), (170, 186, 212),
              (240, 244, 252), (186, 198, 218), (92, 100, 122), (218, 226, 240), (142, 152, 174))
NIGHT = theme((10, 14, 36), (28, 36, 74), (64, 76, 118), (96, 108, 150), (246, 246, 230), (176, 182, 200),
              (176, 190, 222), (120, 134, 172), (38, 42, 66), (150, 164, 200), (82, 92, 128))
DUSK = theme((92, 60, 120), (224, 120, 96), (250, 196, 140), (252, 224, 200), (255, 236, 200), (252, 170, 120),
             (252, 232, 232), (214, 180, 196), (96, 72, 100), (240, 212, 220), (150, 120, 150))

RED = S.RED; PIKA = S.PIKA
def sunless():  # swap the sun's tiles for plain sky from the same row
    h = [r[:] for r in g]
    for y in range(len(h)):
        for x in range(len(h[0])):
            m = kit.mets[h[y][x] & 0x3FF]
            if any(c in (11, 12) for e in m if e >> 12 == 8 for row in kit.tiles[e & 0x3FF] for c in row):
                h[y][x] = h[y][2]
    return h

def scene(p, flakes, seed, name, grid=None):
    im = kit.render(grid or g, [(RED, 17, 7), (PIKA, 18, 7), (S.player(), 17, 11)], p, above=True)
    if flakes: S.snowfall(im, flakes, seed)
    return S.pair(name, im, S.screen(im, 17, 10))

if __name__ == '__main__':
    scene(DAY, 220, 1, 'P1. The peak: overcast day, a sea of cloud below, pale sun').save('peak_1.png')
    scene(NOSUN, 420, 2, 'P2. The peak in a snowstorm (no sun, heavy snow)', sunless()).save('peak_2.png')
    scene(NIGHT, 260, 3, 'P3. The peak at night under a full moon').save('peak_3.png')
    scene(DUSK, 120, 4, 'P4. The peak at sunset (alpenglow)').save('peak_4.png')
