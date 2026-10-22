"""Grookey's battle sprites from lennybitao's "Grookey sprite GBA and NDS" sheet.

The pick: the sheet's sitting frame (drawn as its back sprite) becomes
the front, mirrored to face the player's side, and the battle back stays the
original expansion sprite, remapped onto the new palette (read from git HEAD
so reruns don't remap twice). Colours come from the GBA row; the shiny palette
is read off the sheet's shiny row. Writes straight into graphics/pokemon/grookey/. Run from the repo root: python3 wildcard/art/sprites/build_grookey.py
"""
import io
import subprocess
from collections import Counter
from PIL import Image

SHEET = 'wildcard/art/sprites/raw/grookey_lennybitao.gif'
OUT = 'graphics/pokemon/grookey/'
PREVIEW = 'wildcard/art/sprites/out/grookey.png'

# (left, top) of each 64x64 window on the sheet. The colour windows are the
# whole GBA row; SITTING is placed so its feet land where the old front's did (y 52).
COLOUR_WINDOWS = [(69, 187), (141, 187), (203, 182)]
SITTING = (203, 186)
# Where each colour window's shiny twin sits, relative to it (outlines match exactly).
SHINY_OFFSETS = [(2, 68), (2, 69), (2, 69)]


def load():
    sheet = Image.open(SHEET)
    sheet.seek(0)
    return sheet.convert('RGBA')


def read_pal(text):
    v = text.split()
    return [tuple(int(n) for n in v[3 + 3 * k:6 + 3 * k]) for k in range(16)]


def git_head(path):
    return subprocess.run(['git', 'show', 'HEAD:' + path], capture_output=True, check=True).stdout


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3]))


def main():
    sheet = load()
    bg = sheet.getpixel((sheet.width - 1, sheet.height - 1))
    windows = COLOUR_WINDOWS
    cells = [sheet.crop((x, y, x + 64, y + 64)) for x, y in windows]

    colours = Counter(p for c in cells for p in c.getdata() if p != bg)
    assert len(colours) <= 15, f'{len(colours)} colours, need 15'
    palette = [bg] + [c for c, _ in colours.most_common()]

    # Shiny: the same pixel in the shiny twin, per colour, majority vote.
    votes = {c: Counter() for c in palette[1:]}
    for (x, y), (dx, dy) in zip(windows, SHINY_OFFSETS):
        for j in range(64):
            for i in range(64):
                n = sheet.getpixel((x + i, y + j))
                s = sheet.getpixel((x + i + dx, y + j + dy))
                if n != bg and s != bg:
                    votes[n][s] += 1
    shiny = [bg] + [votes[c].most_common(1)[0][0] for c in palette[1:]]

    index = {c: k for k, c in enumerate(palette)}
    flat = sum(([r, g, b] for r, g, b, _ in palette), []) + [0] * 3 * (16 - len(palette))

    sitting = sheet.crop((SITTING[0], SITTING[1], SITTING[0] + 64, SITTING[1] + 64)).transpose(Image.FLIP_LEFT_RIGHT)
    frame = Image.new('P', (64, 64))
    frame.putpalette(flat)
    frame.putdata([index[p] if p != bg else 0 for p in sitting.getdata()])
    front = Image.new('P', (64, 128))
    front.putpalette(flat)
    front.paste(frame, (0, 0))
    front.paste(frame, (0, 64))  # one drawing, so both animation frames match
    front.save(OUT + 'anim_front.png')

    old_normal = read_pal(git_head(OUT + 'normal.pal').decode())
    old_back = Image.open(io.BytesIO(git_head(OUT + 'back.png')))
    remap = [0] + [min(range(1, len(palette)), key=lambda k: dist(old_normal[i], palette[k])) for i in range(1, 16)]
    back = Image.new('P', old_back.size)
    back.putpalette(flat)
    back.putdata([remap[v] for v in old_back.getdata()])
    back.save(OUT + 'back.png')

    for name, pal in (('normal.pal', palette), ('shiny.pal', shiny)):
        pal = pal + [(0, 0, 0, 255)] * (16 - len(pal))
        with open(OUT + name, 'w', newline='\r\n') as f:
            f.write('JASC-PAL\n0100\n16\n')
            f.writelines(f'{r} {g} {b}\n' for r, g, b, _ in pal)

    # Preview: front, back, then the same in shiny, at 4x.
    preview = Image.new('RGBA', (64 * 2, 128), (200, 230, 200, 255))
    for row, pal in enumerate((palette, shiny)):
        for col, img in enumerate((frame, back)):
            rgba = Image.new('RGBA', (64, 64))
            rgba.putdata([(0, 0, 0, 0) if v == 0 else pal[v] for v in img.getdata()])
            preview.alpha_composite(rgba, (64 * col, 64 * row))
    preview.resize((preview.width * 4, preview.height * 4), Image.NEAREST).save(PREVIEW)


if __name__ == '__main__':
    main()
