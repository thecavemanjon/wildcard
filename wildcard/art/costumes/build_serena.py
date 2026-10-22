"""Serena (RichardPT kit) -> pokeemerald pieces. Writes RGBA working PNGs to out/serena/."""
import os
import numpy as np
from PIL import Image
import kit

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

SRC = 'raw/pokemon_x_and_y_girl_protagonist_in_gen_3_style__by_richardpt_ddbng7g.png'
OUT = 'out/serena'
EYE = (40, 96, 144)

a = kit.load(SRC)
os.makedirs(OUT, exist_ok=True)

# Battle pics: 128px cells at 2x. Front cell starts at x=100, back frames at x=228.
front = kit.half(a[0:128, 100:228])
backs = [kit.half(a[0:128, 228 + 128 * k: 356 + 128 * k]) for k in range(4)]

# Overworld: Essentials 4x4 grids (rows: down, left, right, up; cols: stand, step, stand, step).
walk_area = kit.half(a[130:330, 0:150])
run_area = kit.half(a[170:520, 160:450])

def grid(area):
    boxes = kit.components(area, 10)
    rows = {}
    for b in boxes:
        rows.setdefault(round(b[0] / 12), []).append(b)
    rows = [sorted(r, key=lambda b: b[1]) for _, r in sorted(rows.items())]
    assert len(rows) == 4 and all(len(r) == 4 for r in rows), [len(r) for r in rows]
    return rows

def frame32(area, box, baseline_shift):
    y0, x0, y1, x1 = box
    spr = area[y0:y1 + 1, x0:x1 + 1]
    head = spr[:8]
    hx = np.where((head[:, :, 3] > 0).any(0))[0]
    cx = (hx.min() + hx.max()) / 2            # centre on the head so swinging arms don't jitter
    out = np.zeros((32, 32, 4), np.uint8)
    top = 31 - (spr.shape[0] - 1) - baseline_shift
    left = int(round(16 - cx - 0.5))
    out[top:top + spr.shape[0], left:left + spr.shape[1]] = spr
    return out

def emerald_order(area):
    rows = grid(area)
    down, left, _right, up = rows
    frames = []
    for row, cols in ((down, [0]), (up, [0]), (left, [0]), (down, [1, 3]), (up, [1, 3]), (left, [1, 3])):
        base = max(b[2] for b in row)
        for c in cols:
            frames.append(frame32(area, row[c], base - row[c][2]))
    return frames

walk = emerald_order(walk_area)
run = emerald_order(run_area)

def save_strip(frames, name):
    Image.fromarray(np.concatenate(frames, axis=1)).save(f'{OUT}/{name}.png')

np.save(f'{OUT}/front.npy', front)
Image.fromarray(front).save(f'{OUT}/front_rgba.png')
save_strip(backs, 'back_rgba_h')
save_strip(walk, 'walking_rgba')
save_strip(run, 'running_rgba')
print('front', front.shape, 'backs', backs[0].shape, 'walk', len(walk), 'run', len(run))

# Preview: front (eye lost vs eye kept), back frames, walk + run, on a grass-ish background.
def onbg(arr, scale=4):
    im = Image.fromarray(arr)
    bg = Image.new('RGBA', im.size, (120, 184, 136, 255)); bg.alpha_composite(im)
    return bg.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
m1, _ = kit.reduce_palette([front])
m2, _ = kit.reduce_palette([front], keep={EYE})
mb, _ = kit.reduce_palette(backs, keep={EYE})
tiles = [onbg(front), onbg(kit.apply(front, m1)), onbg(kit.apply(front, m2))] + [onbg(kit.apply(b, mb)) for b in backs]
row1 = Image.new('RGBA', (sum(t.size[0] + 8 for t in tiles), 256), (40, 40, 40, 255))
x = 0
for t in tiles:
    row1.paste(t, (x, 0)); x += t.size[0] + 8
ow = onbg(np.concatenate(walk + [np.zeros((32, 8, 4), np.uint8)] + run, axis=1), 3)
prev = Image.new('RGBA', (max(row1.size[0], ow.size[0]), 256 + 8 + ow.size[1]), (40, 40, 40, 255))
prev.paste(row1, (0, 0)); prev.paste(ow, (0, 264))
prev.save(f'{OUT}/preview.png')


# --- Game-ready 4bpp PNGs (palettes reduced to 15 colours; eyes protected) ---
EYES = {EYE, (20, 166, 224)}
G = os.path.join(HERE, '..', '..', '..', 'graphics')   # repo root/graphics
mf, merges_f = kit.reduce_palette([front], keep=EYES)
mb, merges_b = kit.reduce_palette(backs, keep=EYES)
front15 = kit.apply(front, mf)
backs15 = np.concatenate([kit.apply(b, mb) for b in backs], axis=0)   # 64x256, frames stacked
ow = np.concatenate(walk + run, axis=1)                                # 576x32, 18 frames of 32x32
os.makedirs(f'{G}/object_events/pics/people/serena', exist_ok=True)
kit.save_indexed([(front15, f'{G}/trainers/front_pics/serena.png')])
kit.save_indexed([(backs15, f'{G}/trainers/back_pics/serena.png')])
kit.save_indexed([(ow, f'{G}/object_events/pics/people/serena/walking_running.png')])
print('front merges', merges_f); print('back merges', merges_b)
