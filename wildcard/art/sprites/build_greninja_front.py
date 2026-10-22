"""Greninja's front battle sprite from scorpios_1's DinoPixel "Greninja for @bwohard8".

The download is the 80x80 drawing scaled 8x. The art is 64x65, so the top row
(an ear tip) is trimmed. The back sprite shares the front's palette, so it is
remapped to the nearest new colours; the shiny palette takes, for each new
colour, the shiny partner of the nearest old normal colour. The back is read
from git HEAD so reruns don't remap twice. Run from the repo root.
"""
import io
import subprocess
from PIL import Image

SHEET = 'wildcard/art/sprites/raw/greninja_scorpios1.png'
OUT = 'graphics/pokemon/greninja/'
PREVIEW = 'wildcard/art/sprites/out/greninja_front.png'
ART = (8, 7, 72, 71)  # 64x64 on the 80x80 canvas, top row dropped


def read_pal(text):
    v = text.split()
    return [tuple(int(n) for n in v[3 + 3 * k:6 + 3 * k]) for k in range(16)]


def git_head(path):
    return subprocess.run(['git', 'show', 'HEAD:' + path], capture_output=True, check=True).stdout


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3]))


def write_pal(path, pal):
    pal = list(pal) + [(0, 0, 0)] * (16 - len(pal))
    with open(path, 'w', newline='\r\n') as f:
        f.write('JASC-PAL\n0100\n16\n')
        f.writelines(f'{c[0]} {c[1]} {c[2]}\n' for c in pal)


def main():
    art = Image.open(SHEET).convert('RGBA').resize((80, 80), Image.NEAREST)
    bg = art.getpixel((0, 0))
    art = art.crop(ART)
    pixels = [None if p == bg or p[3] == 0 else p[:3] for p in art.getdata()]
    colours = sorted({p for p in pixels if p}, key=lambda c: -pixels.count(c))
    assert len(colours) <= 15, len(colours)

    old_normal = read_pal(git_head(OUT + 'normal.pal').decode())
    old_shiny = read_pal(git_head(OUT + 'shiny.pal').decode())
    palette = [old_normal[0]] + colours
    shiny = [old_shiny[0]] + [old_shiny[min(range(1, 16), key=lambda k: dist(c, old_normal[k]))] for c in colours]
    flat = sum((list(c) for c in palette), []) + [0] * 3 * (16 - len(palette))

    frame = Image.new('P', (64, 64))
    frame.putpalette(flat)
    frame.putdata([0 if p is None else 1 + colours.index(p) for p in pixels])
    front = Image.new('P', (64, 128))
    front.putpalette(flat)
    front.paste(frame, (0, 0))
    front.paste(frame, (0, 64))  # one drawing, so both animation frames match
    front.save(OUT + 'anim_front.png')

    back = Image.open(io.BytesIO(git_head(OUT + 'back.png')))
    remap = [0] + [min(range(1, len(palette)), key=lambda k: dist(old_normal[i], palette[k])) for i in range(1, 16)]
    new_back = Image.new('P', back.size)
    new_back.putpalette(flat)
    new_back.putdata([remap[v] for v in back.getdata()])
    new_back.save(OUT + 'back.png')

    write_pal(OUT + 'normal.pal', palette)
    write_pal(OUT + 'shiny.pal', shiny)

    preview = Image.new('RGBA', (64 * 4, 64), (200, 230, 200, 255))
    for col, (img, pal) in enumerate(((frame, palette), (new_back, palette), (frame, shiny), (new_back, shiny))):
        rgba = Image.new('RGBA', (64, 64))
        rgba.putdata([(0, 0, 0, 0) if v == 0 else tuple(pal[v]) + (255,) for v in img.getdata()])
        preview.alpha_composite(rgba, (64 * col, 0))
    preview.resize((64 * 4 * 4, 64 * 4), Image.NEAREST).save(PREVIEW)


if __name__ == '__main__':
    main()
