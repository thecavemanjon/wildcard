# Contact sheets of every metatile in interior tilesets, to pick furniture from.
#   python3 sheets.py [secondary_symbol ...]   -> out/sheets/<name>.png
import sys, os, re
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../arenas'))
import mapkit as mk

def sheet(primary, secondary, cols=16):
    k = mk.Kit(primary, secondary)
    n = len(mk.load_tileset(secondary)[1])
    rows = (n + cols - 1) // cols
    img = Image.new('RGB', (cols * 18, rows * 18), (40, 40, 40))
    for i in range(n):
        tile = k.render([[512 + i]])
        img.paste(tile, ((i % cols) * 18 + 1, (i // cols) * 18 + 1))
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)

if __name__ == '__main__':
    for sec in sys.argv[1:]:
        prim = 'gTileset_BuildingFrlg' if 'Frlg' in sec else 'gTileset_Building'
        sheet(prim, sec).save(f'out/sheets/{sec[9:]}.png')
        print(sec)
