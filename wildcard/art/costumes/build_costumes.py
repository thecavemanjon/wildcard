"""RichardPT Essentials kits -> pokeemerald costume assets (front pic, back pic, walk+run sheet).

Per-character layouts below were measured from each sheet (see DECISIONS 2026-10-12).
Everything at 2x in the sheet is halved by majority colour per 2x2 block.
Run with a name to build one, or no args for all; writes previews to out/<name>/.
"""
import os, sys
import numpy as np
from PIL import Image
import kit

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

RAW = 'raw/pokemon_{}_by_richardpt_{}.png'
G = os.path.join(HERE, '..', '..', '..', 'graphics')   # repo root/graphics

# front: (x, y) of the 128x128 cell, or ('free', x0, y0, x1, y1) for a sprite outside the grid
# back: ('grid', x0, y0, n) 128x128 cells, or ('free', y0, y1, [x ranges]) aligned by lower body
# ow: list of (kind, params, rows, walk_cols, run_cols)
KITS = {
    'lyra':    dict(src=RAW.format('heartgold_girlprotagonist_in_gen_3_style_', 'ddqrrtb'),
                    front=(100, 0), back=('grid', 228, 0, 5),
                    ow=[('spaced', (0, 170, 660, 520), [0, 1, 2, 3], [4, 5, 6, 7])]),
    'kris':    dict(src=RAW.format('crystal_girl_protagonist_in_gen_3_style_', 'ddqrrvw'),
                    front=(100, 0), back=('grid', 228, 0, 5),
                    ow=[('grid', (0, 32, 4, 129, 48), [0, 1, 2, 3], None),
                        ('spaced', (140, 170, 440, 520), None, [0, 1, 2, 3])]),
    'calem':   dict(src=RAW.format('x_and_y_boy_protagonist_in_gen_3_style_', 'ddbnfxl'),
                    front=(100, 0), back=('grid', 228, 0, 4),
                    ow=[('grid', (0, 32, 4, 129, 48), [0, 1, 2, 3], None),
                        ('spaced', (140, 170, 440, 520), None, [0, 1, 2, 3])]),
    'ethan':   dict(src=RAW.format('heartgold_boy_protagonist_in_gen_3_style_', 'ddqrrlf'),
                    front=(100, 0), back=('grid', 228, 0, 5),
                    ow=[('grid', (0, 32, 8, 129, 48), [0, 1, 2, 3], [4, 5, 6, 7])]),
    'lucas':   dict(src=RAW.format('diamond_boy_protagonist_in_gen_3_style_', 'deqpttv'),
                    front=(100, 0), back=('free', 0, 128, [(236, 334), (354, 476), (496, 630), (650, 792), (812, 950)]),
                    ow=[('grid', (0, 32, 8, 129, 48), [0, 1, 2, 3], [4, 5, 6, 7])]),
    'hilbert': dict(src=RAW.format('black_boy_protagonist_in_gen_3_style_', 'df959aj'),
                    front=('free', 20, 170, 108, 288), back=('free', 32, 160, [(148, 216), (278, 408), (428, 536), (608, 736), (768, 878)]),
                    ow=[('grid', (128, 32, 8, 161, 48), [0, 1, 2, 3], [4, 5, 6, 7])]),
}


def even(v):
    return v - (v % 2)


def front_pic(a, spec):
    out = np.zeros((64, 64, 4), np.uint8)
    if spec[0] == 'free':
        _, x0, y0, x1, y1 = spec
        spr = kit.half(a[even(y0):y1, even(x0):x1])
        spr = crop(spr)
        top, left = 64 - spr.shape[0], (64 - spr.shape[1]) // 2
        out[top:, left:left + spr.shape[1]] = spr
        return out
    x, y = spec
    return kit.half(a[y:y + 128, x:x + 128])


def crop(s):
    op = s[:, :, 3] > 0
    ys, xs = np.where(op.any(1))[0], np.where(op.any(0))[0]
    return s[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def back_pics(a, spec):
    if spec[0] == 'grid':
        _, x0, y0, n = spec
        return [kit.half(a[y0:y0 + 128, x0 + 128 * k:x0 + 128 * (k + 1)]) for k in range(n)], []
    _, y0, y1, ranges = spec
    sprs = [kit.half(a[even(y0):y1, even(x0):x1 + 1]) for x0, x1 in ranges]
    # anchor every frame to frame 0 by matching the bottom rows (the body barely moves)
    band = 10
    shifts = [0]
    ref = sprs[0][-band:]
    for s in sprs[1:]:
        b = s[-band:]
        best = None
        for dx in range(-s.shape[1], ref.shape[1]):
            score = 0
            for x in range(b.shape[1]):
                rx = x + dx
                if 0 <= rx < ref.shape[1]:
                    both = (b[:, x, 3] > 0) & (ref[:, rx, 3] > 0)
                    score += int((both & np.all(b[:, x, :3] == ref[:, rx, :3], axis=1)).sum())
            if best is None or score > best[0]:
                best = (score, dx)
        shifts.append(best[1])
    lefts = shifts
    rights = [shifts[i] + sprs[i].shape[1] for i in range(len(sprs))]
    span = max(rights) - min(lefts)
    # The idle frame (shown while sliding into battle) must fit whole; among those positions,
    # pick the one that clips the fewest pixels from the throw frames.
    def clipped_at(b):
        n = 0
        for s, sh in zip(sprs, shifts):
            for x in range(s.shape[1]):
                if not 0 <= b + sh + x < 64:
                    n += int((s[:, x, 3] > 0).sum())
        return n
    options = [b for b in range(-128, 128) if b + shifts[0] >= 0 and b + shifts[0] + sprs[0].shape[1] <= 64]
    base = min(options, key=lambda b: (clipped_at(b), abs(b + (min(lefts) + max(rights)) / 2 - 32)))
    frames, clipped = [], []
    for s, sh in zip(sprs, shifts):
        out = np.zeros((64, 64, 4), np.uint8)
        top = 64 - s.shape[0]
        for x in range(s.shape[1]):
            tx = base + sh + x
            if 0 <= tx < 64:
                out[max(top, 0):, tx] = s[max(0, -top):, x]
            elif (s[:, x, 3] > 0).any():
                clipped.append(int((s[:, x, 3] > 0).sum()))
        frames.append(out)
    return frames, clipped


def cells_grid(a, x0, px, n, y0, py):
    """Cut a packed grid; each 4-connected blob goes to the cell holding its centre."""
    from scipy import ndimage
    region = a[y0:y0 + 4 * py, max(x0, 0):x0 + n * px]
    lab, k = ndimage.label(region[:, :, 3] > 0)
    cells = [[np.zeros((py, px, 4), np.uint8) for _ in range(n)] for _ in range(4)]
    for i in range(1, k + 1):
        ys, xs = np.where(lab == i)
        cy, cx = ys.mean(), xs.mean()
        r, c = min(int(cy // py), 3), min(int(cx // px), n - 1)
        merged = xs.max() - xs.min() + 1 > px * 1.2       # neighbours touching: split on the grid lines
        for y, x in zip(ys, xs):
            rr, cc = (min(int(y // py), 3), min(int(x // px), n - 1)) if merged else (r, c)
            ly, lx = y - rr * py, x - cc * px
            if 0 <= ly < py and 0 <= lx < px:
                cells[rr][cc][ly, lx] = region[y, x]
    return [[kit.half(c) for c in row] for row in cells]


def cells_spaced(a, box):
    x0, y0, x1, y1 = box
    area = kit.half(a[y0:y1, x0:x1])
    boxes = kit.components(area, 10)
    rows = {}
    for b in sorted(boxes):
        key = next((k for k in rows if abs(k - b[0]) < 12), b[0])
        rows.setdefault(key, []).append(b)
    rows = [sorted(r, key=lambda b: b[1]) for _, r in sorted(rows.items())]
    assert len(rows) == 4, [len(r) for r in rows]
    return [[area[b[0]:b[2] + 1, b[1]:b[3] + 1] for b in r] for r in rows]


def frame32(spr, baseline_shift):
    spr = crop(spr)
    head = spr[:8]
    hx = np.where((head[:, :, 3] > 0).any(0))[0]
    cx = (hx.min() + hx.max()) / 2                 # centre on the head so swinging arms don't jitter
    out = np.zeros((32, 32, 4), np.uint8)
    top = 31 - (spr.shape[0] - 1) - baseline_shift
    left = int(round(16 - cx - 0.5))
    for y in range(spr.shape[0]):
        for x in range(spr.shape[1]):
            if spr[y, x, 3] and 0 <= top + y < 32 and 0 <= left + x < 32:
                out[top + y, left + x] = spr[y, x]
    return out


def emerald_order(rows, cols):
    """rows: [down, left, right, up] lists of sprites; cols: the 4 columns (stand, step, stand, step)."""
    down, left, _right, up = rows
    def bottoms(row):
        return [crop(row[c]).shape[0] + (np.where((row[c][:, :, 3] > 0).any(1))[0].min()) for c in cols]
    frames = []
    for row, picks in ((down, [0]), (up, [0]), (left, [0]), (down, [1, 3]), (up, [1, 3]), (left, [1, 3])):
        bs = bottoms(row)
        base = max(bs)
        for p in picks:
            frames.append(frame32(row[cols[p]], base - bs[p]))
    return frames


def overworld(a, specs):
    walk = run = None
    for kind, params, wcols, rcols in specs:
        rows = cells_grid(a, *params) if kind == 'grid' else cells_spaced(a, params)
        if wcols:
            walk = emerald_order(rows, wcols)
        if rcols:
            run = emerald_order(rows, rcols)
    return walk, run


def build(name):
    cfg = KITS[name]
    a = kit.load(cfg['src'])
    out = f'out/{name}'
    os.makedirs(out, exist_ok=True)
    front = front_pic(a, cfg['front'])
    backs, clipped = back_pics(a, cfg['back'])
    walk, run = overworld(a, cfg['ow'])

    mf, merges_f = kit.reduce_palette([front])
    mb, merges_b = kit.reduce_palette(backs)
    ow = np.concatenate(walk + run, axis=1)
    mo, merges_o = kit.reduce_palette([ow])
    front15, backs15, ow15 = kit.apply(front, mf), [kit.apply(b, mb) for b in backs], kit.apply(ow, mo)

    os.makedirs(f'{G}/object_events/pics/people/{name}', exist_ok=True)
    kit.save_indexed([(front15, f'{G}/trainers/front_pics/{name}.png')])
    kit.save_indexed([(np.concatenate(backs15, axis=0), f'{G}/trainers/back_pics/{name}.png')])
    kit.save_indexed([(ow15, f'{G}/object_events/pics/people/{name}/walking_running.png')])

    preview(out, front, front15, backs15, ow15)
    report = [f'{name}: back frames {len(backs)}; clipped back px {sum(clipped)}',
              f'  front merges ({sum(n for *_, n in merges_f)} px): {merges_f}',
              f'  back merges ({sum(n for *_, n in merges_b)} px): {merges_b}',
              f'  overworld merges ({sum(n for *_, n in merges_o)} px): {merges_o}']
    print('\n'.join(report))


def preview(out, front, front15, backs, ow):
    def onbg(arr, scale):
        im = Image.fromarray(np.ascontiguousarray(arr))
        bg = Image.new('RGBA', im.size, (120, 184, 136, 255)); bg.alpha_composite(im)
        return bg.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
    tiles = [onbg(front, 3), onbg(front15, 3)] + [onbg(b, 3) for b in backs]
    row1 = Image.new('RGBA', (sum(t.size[0] + 6 for t in tiles), 192), (40, 40, 40, 255))
    x = 0
    for t in tiles:
        row1.paste(t, (x, 0)); x += t.size[0] + 6
    o = onbg(ow, 2)
    prev = Image.new('RGBA', (max(row1.size[0], o.size[0]), 192 + 6 + o.size[1]), (40, 40, 40, 255))
    prev.paste(row1, (0, 0)); prev.paste(o, (0, 198))
    prev.save(f'{out}/preview.png')


if __name__ == '__main__':
    for n in (sys.argv[1:] or KITS):
        build(n)
