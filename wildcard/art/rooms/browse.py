# Renders every layout that uses the given secondary tilesets, one sheet each,
# to find furniture worth borrowing.  python3 browse.py BrendansMaysHouse ...
import sys, os, json
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../arenas'))
import mapkit as mk

class FrlgKit(mk.Kit):
    # FRLG: 640 tiles and metatiles in the primary, 7 primary palettes.
    def __init__(self, primary, secondary):
        pt, pm, pa, pp = mk.load_tileset(primary); st, sm, sa, sp = mk.load_tileset(secondary)
        self.tiles = (pt + [[[0]*8]*8]*640)[:640] + st
        self.mets = (pm + [(0,)*8]*640)[:640] + sm
        self.attrs = (pa + [0]*640)[:640] + sa
        self.pals = pp[:7] + sp[7:13] + [[(0,0,0)]*16]*3

def kit_for(l):
    return (FrlgKit if 'Frlg' in l['primary_tileset'] else mk.Kit)(l['primary_tileset'], l['secondary_tileset'])

def grid_for(l):
    import struct
    b = open(mk.R + l['blockdata_filepath'], 'rb').read(); w, h = l['width'], l['height']
    return [[struct.unpack_from('<H', b, 2*(y*w+x))[0] for x in range(w)] for y in range(h)]

def browse(sec, maxw=1400):
    ims = []
    for lid, l in mk.LAYOUTS.items():
        if l.get('secondary_tileset') != 'gTileset_' + sec or l['width'] * l['height'] > 900: continue
        try:
            k, g = kit_for(l), grid_for(l)
            ims.append((lid, k.render(g)))
        except Exception as e:
            print('skip', lid, e)
    if not ims: return
    x = y = rowh = 0; places = []
    for lid, im in ims:
        if x + im.width > maxw: x = 0; y += rowh + 14; rowh = 0
        places.append((lid, im, x, y)); x += im.width + 6; rowh = max(rowh, im.height)
    out = Image.new('RGB', (maxw, y + rowh + 14), (20, 20, 26)); d = ImageDraw.Draw(out)
    for lid, im, px, py in places:
        out.paste(im, (px, py + 12)); d.text((px, py), lid[7:][:28], fill=(255, 220, 90))
    out.save(f'out/browse_{sec}.png'); print(sec, len(ims))

for s in sys.argv[1:]: browse(s)
