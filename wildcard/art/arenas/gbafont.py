import os, re
from PIL import Image
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '/'
src = open(R + 'src/fonts.c').read()
body = src.split('gFontNormalLatinGlyphWidths[] = {')[1].split('};')[0]
WIDTHS = [int(v) for v in re.findall(r'\d+', body)]
CHARMAP = {}
for line in open(R + 'charmap.txt', encoding='utf-8'):
    m = re.match(r"^'(.)'\s*=\s*([0-9A-F]{2})\s*$", line)
    if m and m.group(1) not in CHARMAP: CHARMAP[m.group(1)] = int(m.group(2), 16)
SHEET = Image.open(R + 'graphics/fonts/latin_normal.png'); SP = SHEET.load()

def draw(img, text, x, y, fg, shadow):
    p = img.load()
    for ch in text:
        c = CHARMAP[ch]; gx, gy = (c % 16)*16, (c//16)*16
        for yy in range(16):
            for xx in range(16):
                v = SP[gx+xx, gy+yy]
                if v == 1 and 0 <= x+xx < img.width: p[x+xx, y+yy] = fg
                elif v == 2 and 0 <= x+xx < img.width: p[x+xx, y+yy] = shadow
        x += WIDTHS[c]
    return x
