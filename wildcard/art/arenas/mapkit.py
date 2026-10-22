# Render any Emerald layout from the repo's tilesets, and compose new ones.
import re, struct, json, os, functools
from PIL import Image, ImageDraw, ImageFont
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '/'
HEAD = open(R + 'src/data/tilesets/headers.h').read()
GFX = open(R + 'src/data/tilesets/graphics.h').read() + open(R + 'src/graphics.c').read()
LAYOUTS = {l['id']: l for l in json.load(open(R + 'data/layouts/layouts.json'))['layouts'] if 'id' in l}

def tileset_dir(sym):
    block = HEAD.split(f'const struct Tileset {sym} =')[1].split('};')[0]
    tiles = re.search(r'\.tiles = (\w+)', block).group(1)
    path = re.search(tiles + r'\[\] = INCGFX_U32\("([^"]+)/tiles\.png"', GFX).group(1)
    return R + path + '/'

def jasc(p):
    return [tuple(int(v) for v in l.split()) for l in open(p).read().split('\n')[3:19]]

@functools.lru_cache(None)
def load_tileset(sym):
    d = tileset_dir(sym)
    im = Image.open(d + 'tiles.png'); px = im.load(); w, h = im.size
    tiles = [[[px[tx*8+x, ty*8+y] for x in range(8)] for y in range(8)] for ty in range(h//8) for tx in range(w//8)]
    b = open(d + 'metatiles.bin', 'rb').read()
    mets = [struct.unpack_from('<8H', b, i*16) for i in range(len(b)//16)]
    a = open(d + 'metatile_attributes.bin', 'rb').read()
    attrs = [struct.unpack_from('<H', a, i*2)[0] for i in range(len(a)//2)]
    pals = [jasc(d + f'palettes/{i:02}.pal') if os.path.exists(d + f'palettes/{i:02}.pal') else [(0,0,0)]*16 for i in range(16)]
    return tiles, mets, attrs, pals

class Kit:
    def __init__(self, primary, secondary):
        pt, pm, pa, pp = load_tileset(primary); st, sm, sa, sp = load_tileset(secondary)
        self.tiles = (pt + [[[0]*8]*8]*512)[:512] + st
        self.mets = (pm + [(0,)*8]*512)[:512] + sm
        self.attrs = (pa + [0]*512)[:512] + sa
        self.pals = pp[:6] + sp[6:13] + [[(0,0,0)]*16]*3
    def tile(self, img, e, ox, oy, pals):
        t = self.tiles[e & 0x3FF]; hf, vf, p = (e >> 10) & 1, (e >> 11) & 1, e >> 12
        px = img.load()
        for y in range(8):
            for x in range(8):
                c = t[7-y if vf else y][7-x if hf else x]
                if c: px[ox+x, oy+y] = pals[p][c]
    def render(self, grid, sprites=(), pals=None, above=False):
        pals = pals or self.pals
        H, W = len(grid), len(grid[0])
        img = Image.new('RGB', (W*16, H*16), pals[0][0]); top = []
        for y in range(H):
            for x in range(W):
                mid = grid[y][x] & 0x3FF
                if mid >= len(self.mets): continue
                m = self.mets[mid]; layer = (self.attrs[mid] >> 12) & 0xF
                for i in range(4): self.tile(img, m[i], x*16+(i%2)*8, y*16+(i//2)*8, pals)
                if layer == 0: top.append((m, x, y))
                else:
                    for i in range(4): self.tile(img, m[4+i], x*16+(i%2)*8, y*16+(i//2)*8, pals)
        def stamp():
            for spr, sx, sy in sorted(sprites, key=lambda s: s[2]):
                img.paste(spr, (sx*16 + 8 - spr.width//2, sy*16 + 16 - spr.height), spr)
        if not above: stamp()
        for m, x, y in top:
            for i in range(4): self.tile(img, m[4+i], x*16+(i%2)*8, y*16+(i//2)*8, pals)
        if above: stamp()  # objects at a high elevation draw over the top layer
        return img
    def sheet(self, start, count, cols=16, scale=3):
        rows = (count + cols - 1)//cols
        g = [[start + r*cols + c if r*cols + c < count else 0 for c in range(cols)] for r in range(rows)]
        im = self.render(g).resize((cols*16*scale, rows*16*scale), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for r in range(rows):
            for c in range(cols):
                d.text((c*16*scale+1, r*16*scale+1), f'{g[r][c]:x}', fill=(255, 0, 0))
        return im

def layout(lid):
    l = LAYOUTS[lid]
    b = open(R + l['blockdata_filepath'], 'rb').read()
    w, h = l['width'], l['height']
    return Kit(l['primary_tileset'], l['secondary_tileset']), [[struct.unpack_from('<H', b, 2*(y*w+x))[0] for x in range(w)] for y in range(h)]

def map_layout(mapname):
    m = json.load(open(R + f'data/maps/{mapname}/map.json'))
    return m['layout'], m

# Overworld sprites (people and Pokémon), first frame facing down.
def person(path, w=16, h=32, frame=0):
    im = Image.open(R + path); pal = im.getpalette(); src = im.load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); o = out.load()
    for y in range(h):
        for x in range(w):
            v = src[frame*w + x, y]
            if v: o[x, y] = tuple(pal[v*3:v*3+3]) + (255,)
    return out

def mon(name, frame=0):
    d = R + f'graphics/pokemon/{name}/'
    im = Image.open(d + 'overworld.png'); pal = jasc(d + 'overworld_normal.pal'); src = im.load()
    sz = im.height
    out = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); o = out.load()
    for y in range(sz):
        for x in range(sz):
            v = src[frame*sz + x, y]
            if v: o[x, y] = pal[v] + (255,)
    return out

try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20)
except Exception: FONT = ImageFont.load_default()
def label(img, text, scale=3):
    big = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
    out = Image.new('RGB', (big.width, big.height + 34), (24, 24, 30)); out.paste(big, (0, 34))
    ImageDraw.Draw(out).text((8, 8), text, fill=(240, 240, 240), font=FONT); return out

def gridded(kit, g, scale=2, x0=0, y0=0, w=None, h=None):
    w = w or len(g[0]) - x0; h = h or len(g) - y0
    sub = [row[x0:x0+w] for row in g[y0:y0+h]]
    im = kit.render(sub).resize((w*16*scale, h*16*scale), Image.NEAREST); d = ImageDraw.Draw(im)
    for x in range(w):
        if (x0+x) % 5 == 0: d.line([(x*16*scale, 0), (x*16*scale, im.height)], fill=(255, 255, 0)); d.text((x*16*scale+2, 2), str(x0+x), fill=(255, 255, 0))
    for y in range(h):
        if (y0+y) % 5 == 0: d.line([(0, y*16*scale), (im.width, y*16*scale)], fill=(0, 255, 255)); d.text((2, y*16*scale+2), str(y0+y), fill=(0, 255, 255))
    return im
