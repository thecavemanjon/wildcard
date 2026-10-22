"""Greninja's overworld (follower) sprite from Jhony-Rex's "Greninja: sprite" sheet.

The sheet is PMD style: rows face down, down-right, right, up-right, up, three
frames each. The game wants eight 32x32 frames: down x2, up x2, left x2,
right x2 (left is the right row mirrored). Colours are merged down to 15; the
shiny palette maps each colour to the nearest one in the old overworld palette
and takes that slot's shiny colour. Run from the repo root.
"""
from collections import Counter
from PIL import Image

SHEET = 'wildcard/art/sprites/raw/greninja_jhonyrex.png'
OUT = 'graphics/pokemon/greninja/'
PREVIEW = 'wildcard/art/sprites/out/greninja_ow.png'

# Bounding boxes on the sheet: (stand, step) for each direction.
DOWN = [(4, 85, 29, 115), (48, 86, 74, 115)]
RIGHT = [(5, 179, 26, 210), (43, 180, 69, 210)]
UP = [(5, 274, 30, 303), (48, 275, 73, 303)]
FEET_Y = 30  # bottom row of the old sprite's feet


def read_pal(path):
    lines = open(path).read().split()
    return [tuple(int(v) for v in lines[3 + 3 * k:6 + 3 * k]) for k in range(16)]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3]))


def main():
    sheet = Image.open(SHEET).convert('RGBA')
    bg = sheet.getpixel((sheet.width - 1, sheet.height - 1))

    def cell(box, flip=False):
        art = sheet.crop(box)
        if flip:
            art = art.transpose(Image.FLIP_LEFT_RIGHT)
        out = Image.new('RGBA', (32, 32), bg)
        out.paste(art, (16 - art.width // 2, FEET_Y - art.height))
        return out

    frames = [cell(b) for b in DOWN] + [cell(b) for b in UP] \
        + [cell(b, True) for b in RIGHT] + [cell(b) for b in RIGHT]

    counts = Counter(p for f in frames for p in f.getdata() if p != bg)
    # Merge the closest pair (keeping the commoner colour) until 15 are left.
    merged = {c: c for c in counts}
    live = dict(counts)
    while len(live) > 15:
        keys = list(live)
        a, b = min(((x, y) for i, x in enumerate(keys) for y in keys[i + 1:]), key=lambda p: dist(*p))
        keep, drop = (a, b) if live[a] >= live[b] else (b, a)
        live[keep] += live.pop(drop)
        for c, m in merged.items():
            if m == drop:
                merged[c] = keep
    palette = [bg] + sorted(live, key=lambda c: -live[c])
    index = {c: k for k, c in enumerate(palette)}

    old_normal = read_pal(OUT + 'overworld_normal.pal')
    old_shiny = read_pal(OUT + 'overworld_shiny.pal')
    shiny = [bg] + [old_shiny[min(range(1, 16), key=lambda k: dist(c, old_normal[k]))] + (255,) for c in palette[1:]]

    flat = sum(([r, g, b] for r, g, b, *_ in palette), []) + [0] * 3 * (16 - len(palette))
    strip = Image.new('P', (32 * 8, 32))
    strip.putpalette(flat)
    strip.putdata([index[merged.get(p, p)] if p != bg else 0
                   for y in range(32) for f in frames for p in [f.getpixel((x, y)) for x in range(32)]])
    strip.save(OUT + 'overworld.png')

    for name, pal in (('overworld_normal.pal', palette), ('overworld_shiny.pal', shiny)):
        pal = pal + [(0, 0, 0, 255)] * (16 - len(pal))
        with open(OUT + name, 'w', newline='\r\n') as f:
            f.write('JASC-PAL\n0100\n16\n')
            f.writelines(f'{c[0]} {c[1]} {c[2]}\n' for c in pal)

    preview = Image.new('RGBA', (256, 64), (200, 230, 200, 255))
    for row, pal in enumerate((palette, shiny)):
        rgba = Image.new('RGBA', (256, 32))
        rgba.putdata([(0, 0, 0, 0) if v == 0 else tuple(pal[v][:3]) + (255,) for v in strip.getdata()])
        preview.alpha_composite(rgba, (0, 32 * row))
    preview.resize((256 * 4, 64 * 4), Image.NEAREST).save(PREVIEW)
    print(f'{len(counts)} colours -> {len(palette) - 1}')


if __name__ == '__main__':
    main()
