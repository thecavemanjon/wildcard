# The same stadiums drawn with each crowd style, for picking one.
#   python3 compare_crowds.py   -> out/crowd_<style>_<variant>.gif and out/crowd_styles.png
from PIL import Image, ImageDraw
import kit as K, schemes as S

STYLES = ['mixed', 'figures', 'contest', 'blobs', 'dots']
CASES = [('grand', 'day'), ('grand', 'sunset'), ('neon', 'synth'), ('colosseum', 'moonlit')]

def main():
    stills = {}
    for st in STYLES:
        for scheme, var in CASES:
            fn, variants = S.SCHEMES[scheme]
            make, (px, py) = fn(dict(variants[var], crowd_style=st))
            frames = [make(i / S.FRAMES) for i in range(S.FRAMES)]
            screens = [K.screen_crop(f, px, py) for f in frames]
            K.save_gif(screens, f'{S.OUT}/crowd_{st}_{scheme}_{var}.gif', 100, 3)
            K.save_gif(frames, f'{S.OUT}/crowd_{st}_{scheme}_{var}_map.gif', 100, 2)
            stills[st, scheme, var] = frames[4]
    # one sheet: styles down, cases across, the top of the map (back stand) at 2x
    cw, ch = 400, 128
    sheet = Image.new('RGB', (cw * 2 * len(CASES) // 2, (ch * 2 + 24) * len(STYLES)), (20, 20, 28))
    d = ImageDraw.Draw(sheet)
    for r, st in enumerate(STYLES):
        for c, (scheme, var) in enumerate(CASES[:2]):
            im = stills[st, scheme, var].crop((0, 16, cw, 16 + ch)).resize((cw * 2, ch * 2), Image.NEAREST)
            sheet.paste(im, (c * cw * 2, r * (ch * 2 + 24) + 24))
        d.text((8, r * (ch * 2 + 24) + 6), st, fill=(255, 220, 80))
    sheet.save(f'{S.OUT}/crowd_styles.png')

if __name__ == '__main__':
    main()
