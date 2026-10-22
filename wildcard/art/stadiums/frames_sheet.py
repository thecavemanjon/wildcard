# Contact sheet of a GIF's frames, for checking motion: python3 frames_sheet.py out/x.gif [step]
import sys
from PIL import Image, ImageSequence
g = Image.open(sys.argv[1]); step = int(sys.argv[2]) if len(sys.argv) > 2 else 3
fr = [f.convert('RGB').resize((f.width // 3, f.height // 3)) for i, f in enumerate(ImageSequence.Iterator(g)) if i % step == 0]
cols = 4; rows = (len(fr) + cols - 1) // cols
sheet = Image.new('RGB', (cols * fr[0].width * 2, rows * fr[0].height * 2))
for i, f in enumerate(fr): sheet.paste(f.resize((f.width * 2, f.height * 2), Image.NEAREST), ((i % cols) * f.width * 2, (i // cols) * f.height * 2))
sheet.save(sys.argv[1].replace('.gif', '_frames.png'))
