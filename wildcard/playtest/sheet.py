import sys, glob
from PIL import Image
d = sys.argv[1]; pat = sys.argv[2] if len(sys.argv) > 2 else '*.png'
fs = sorted(f for f in glob.glob(f'{d}/{pat}') if 'sheet' not in f)
ims = [Image.open(f) for f in fs]; cols = 2
s = Image.new('RGB', (240 * cols, 160 * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims): s.paste(im, ((i % cols) * 240, (i // cols) * 160))
s.resize((s.width * 2, s.height * 2), Image.NEAREST).save(f'{d}/sheet.png'); print([f.split('/')[-1] for f in fs])
