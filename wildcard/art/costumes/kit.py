"""Shared helpers for turning RichardPT-style Essentials kits into pokeemerald assets.

Kits are drawn at 2x; `half` takes the majority colour of each 2x2 block (the few
hand-touched pixels lose to their neighbours), so nothing is resampled or blurred.
"""
from collections import Counter, deque
import numpy as np
from PIL import Image


def load(path):
    a = np.array(Image.open(path).convert('RGBA'))
    a[a[:, :, 3] < 128] = 0          # fully transparent = (0,0,0,0)
    a[a[:, :, 3] >= 128, 3] = 255
    return a


def half(a):
    h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
    a = a[:h, :w]
    out = np.zeros((h // 2, w // 2, 4), np.uint8)
    for y in range(h // 2):
        for x in range(w // 2):
            block = [tuple(p) for p in a[2*y:2*y+2, 2*x:2*x+2].reshape(4, 4)]
            out[y, x] = Counter(block).most_common(1)[0][0]
    return out


def components(a, min_area=20):
    """Bounding boxes (y0, x0, y1, x1), inclusive, of 8-connected opaque blobs."""
    op = a[:, :, 3] > 0
    H, W = op.shape
    seen = np.zeros_like(op)
    boxes = []
    for y in range(H):
        for x in range(W):
            if op[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = 1
                y0 = y1 = y; x0 = x1 = x
                while q:
                    cy, cx = q.popleft()
                    y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and op[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = 1; q.append((ny, nx))
                if (y1 - y0 + 1) * (x1 - x0 + 1) >= min_area:
                    boxes.append((y0, x0, y1, x1))
    return sorted(boxes)


def colours(arrs):
    s = set()
    for a in arrs:
        s |= {tuple(p[:3]) for p in a.reshape(-1, 4) if p[3]}
    return s


def _lab(c):
    """sRGB 0-255 -> CIELAB (D65), so colour distance matches what the eye sees."""
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(v)) for v in c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def reduce_palette(arrs, limit=15, keep=()):
    """Merge the least-used colour into its nearest (by RGB distance) until <= limit.
    Colours in `keep` (e.g. eyes) never move. Returns (mapping, merges as (old, new, pixels))."""
    cnt = Counter()
    for a in arrs:
        for p in a.reshape(-1, 4):
            if p[3]:
                cnt[tuple(int(v) for v in p[:3])] += 1
    mapping = {c: c for c in cnt}
    merges = []
    live = dict(cnt)
    dist = lambda c1, c2: sum((x - y) ** 2 for x, y in zip(_lab(c1), _lab(c2))) ** 0.5
    while len(live) > limit:
        # cheapest merge: pixels affected x how far the colour moves. Keeps small but
        # distinct colours (eyes) and merges near-duplicate shades first.
        best = None
        for c in live:
            if c in keep:
                continue
            near = min((o for o in live if o != c), key=lambda o: dist(c, o))
            d = dist(c, near)
            cost = live[c] * d * (100 if d > 25 else 1)   # a clearly different colour (eyes) is expensive to lose
            if best is None or cost < best[0]:
                best = (cost, c, near)
        _, rare, near = best
        merges.append((rare, near, live[rare]))
        live[near] += live.pop(rare)
        for k, v in mapping.items():
            if v == rare:
                mapping[k] = near
    return mapping, merges


def apply(a, mapping):
    out = a.copy()
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            if a[y, x, 3]:
                out[y, x, :3] = mapping[tuple(int(v) for v in a[y, x, :3])]
    return out


def save_indexed(arrs_with_paths, transparent=(0, 255, 0)):
    """Write RGBA arrays that share one palette as 4bpp indexed PNGs (index 0 = transparent)."""
    cols = sorted(colours([a for a, _ in arrs_with_paths]))
    assert len(cols) <= 15, f'{len(cols)} colours, max 15'
    pal = [transparent] + cols
    index = {c: i for i, c in enumerate(pal)}
    flat = [v for c in pal for v in c] + [0] * (3 * (16 - len(pal)))
    for a, path in arrs_with_paths:
        idx = np.zeros(a.shape[:2], np.uint8)
        for y in range(a.shape[0]):
            for x in range(a.shape[1]):
                if a[y, x, 3]:
                    idx[y, x] = index[tuple(int(v) for v in a[y, x, :3])]
        im = Image.fromarray(idx, 'P')
        im.putpalette(flat)
        im.save(path, bits=4)
    return pal
