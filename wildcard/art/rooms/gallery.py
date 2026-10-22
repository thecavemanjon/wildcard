# Writes the room gallery page (out/web/index.html) beside the GIFs and stills.
#   python3 rooms.py && python3 gallery.py
import os, json, shutil, html
import rooms as R
import og_rooms as O
from roomkit import tile_budget, TIMES

OUT = os.path.join(R.HERE, 'out')
WEB = os.path.join(OUT, 'web')

def main():
    os.makedirs(WEB, exist_ok=True)
    cards = []
    # Emerald-style rooms first (og_rooms.py); the bolder first round (rooms.py) rides along as a tab.
    for name, info in O.ROOMS.items():
        tiles, colours = tile_budget(O.frame(name, 0, 'day'))
        for tm in TIMES:
            shutil.copy(f'{OUT}/og_{name}_{tm}.gif', f'{WEB}/og_{name}_{tm}.gif')
            shutil.copy(f'{OUT}/{name}_{tm}.gif', f'{WEB}/{name}_{tm}.gif')
        shutil.copy(f'{OUT}/og_{name}.png', f'{WEB}/og_{name}.png')
        cards.append(dict(name=name, title=info['title'], blurb=info['blurb'], tiles=tiles, mons=', '.join(m.title() for m in info['mons'])))
    page = open(os.path.join(R.HERE, 'gallery_template.html')).read()
    page = page.replace('/*ROOMS*/[]', json.dumps(cards))
    open(f'{WEB}/index.html', 'w').write(page)
    print(len(cards), 'rooms ->', WEB)

if __name__ == '__main__': main()
