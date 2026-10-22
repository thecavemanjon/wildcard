# Replays a built stadium from the game's data (tiles, metatiles and the
# generated animation table), the way the ROM plays it: python3 replay.py Volcano
import sys, re
sys.path.insert(0, '../arenas')
import mapkit as mk, kit as K
from PIL import Image
R = mk.R

def replay(name, seconds=2.4, step=6):
    low = name.lower(); up = re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()
    kit, g = mk.layout(f'LAYOUT_UNDERDOG_ARENA_{up}')
    hdr = open(R + 'src/data/tilesets/wildcard_stadium_anims.h').read()
    table = hdr.split(f'sWildcardAnims_{name}[] =')[1].split('};')[0]
    anims = [(a, int(b), int(c), int(d), int(e), int(f)) for a, b, c, d, e, f in
             re.findall(rf'sWildcard{name}_(\w+), (\d+), (\d+), (\d+), (\d+), (\d+)', table)]
    src = {}
    for a, *_ in anims:
        im = Image.open(R + f'data/tilesets/secondary/wildcard_{low}/anim/{a}.png'); px = im.load()
        src[a] = [[[px[tx * 8 + x, ty * 8 + y] for x in range(8)] for y in range(8)] for ty in range(im.height // 8) for tx in range(16)]
    frames = []
    for timer in range(0, int(seconds * 60), step):
        for a, tile, n, nf, interval, phase in anims:
            fi = (timer // interval) % nf
            for k in range(n): kit.tiles[512 + tile + k] = src[a][fi * n + k]
        frames.append(K.screen_crop(kit.render(g), 10, 8))
    K.save_gif(frames, f'out/replay_{name}.gif', step * 1000 // 60, 3)
    return frames

if __name__ == '__main__':
    for n in sys.argv[1:]:
        f = replay(n)
        f[0].resize((720, 480), Image.NEAREST).save(f'out/replay_{n}_0.png'); f[3].resize((720, 480), Image.NEAREST).save(f'out/replay_{n}_3.png')
