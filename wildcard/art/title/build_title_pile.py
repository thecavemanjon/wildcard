"""Title screen and cover art mockup for Pokémon Wild Card.

A stacked crowd of mismatched Pokémon (the game's own front sprites, each with
its own palette, as they'd be OBJ sprites on the GBA: 16 sprites, 16 palettes)
in a white stadium under Emerald's own POKéMON logo
(graphics/title_screen/pokemon_logo.png). The WILD CARD card is shelved for now
(logo() stays, unused). Writes a 240x160 title (with PRESS START) and a 4x cover
image (without) to out/. Run from the repo root:
    python3 wildcard/art/title/build_title_pile.py
"""
from PIL import Image, ImageDraw, ImageFont

OUT = 'wildcard/art/title/out/'
FONT = '/System/Library/Fonts/Supplemental/Arial Black.ttf'
W, H = 240, 160

# (species folder, centre x, feet y): a dogpile on two slopes climbing toward
# the Poké Ball in the middle. Everyone faces the middle (front sprites face
# left, so the left side is mirrored); JITTER roughs up the positions.
PILE = [
    # left slope, back to front
    ('garchomp',       30, 112),
    ('gengar',         72,  98),
    ('slowpoke',       26, 138),
    ('psyduck',        70, 126),
    ('bulbasaur',      90, 144),
    ('magikarp',       20, 160),
    ('torchic',        54, 158),
    ('piplup',         76, 154),
    # right slope, back to front
    ('dragonite',     206, 110),
    ('greninja/mega', 166,  96),
    ('scorbunny',     214, 138),
    ('oshawott',      170, 126),
    ('pikachu',       152, 144),
    ('snom',          222, 160),
    ('cyndaquil',     186, 158),
    ('smoliv',        168, 154),
]
JITTER = 5  # pixels, from a fixed seed so every build matches
PRIZE = (120, 134)  # centre of the Poké Ball they're all going for

WALL_TOP = (232, 238, 248)
WALL_MID = (240, 244, 252)
WALL_LOW = (248, 250, 255)
WALL_LIGHT = (255, 255, 255)
TRIM = (184, 196, 220)
FLOOR = (226, 232, 242)
FLOOR_SHINE = (250, 252, 255)
RING = (176, 200, 236)
CARD = (250, 246, 232)
CARD_EDGE = (24, 20, 40)
INK = (24, 20, 40)
GOLD = (255, 204, 40)
ORANGE = (240, 120, 24)
RED = (214, 40, 48)


def front_sprite(name):
    """First frame of a front sprite; index 0 is clear. name may be a form, e.g. greninja/mega."""
    import os
    folder = f'graphics/pokemon/{name}/'
    img = Image.open(folder + ('anim_front.png' if os.path.exists(folder + 'anim_front.png') else 'front.png'))
    frame = img.crop((0, 0, 64, 64))
    rgba = frame.convert('RGBA')
    px = frame.load()
    out = rgba.load()
    for y in range(64):
        for x in range(64):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    return rgba


def background():
    """A pristine white stadium: pale wall with light columns, a polished floor
    with a pale blue arena ring. Flat colours, as GBA palettes would allow."""
    bg = Image.new('RGBA', (W, H), WALL_TOP + (255,))
    d = ImageDraw.Draw(bg)
    for i, c in enumerate([WALL_TOP, WALL_MID, WALL_LOW]):
        d.rectangle((0, i * 24, W, (i + 1) * 24 + 24), fill=c + (255,))
    for x in range(12, W, 36):  # soft light columns on the back wall
        d.rectangle((x, 0, x + 8, 71), fill=WALL_LIGHT + (255,))
    d.rectangle((0, 72, W, H), fill=FLOOR + (255,))
    d.line((0, 72, W, 72), fill=TRIM + (255,), width=2)
    # the arena ring on the floor, in perspective
    d.ellipse((-30, 92, W + 30, H + 70), fill=RING + (255,))
    d.ellipse((-14, 98, W + 14, H + 58), fill=FLOOR_SHINE + (255,))
    d.line((W // 2, 98, W // 2, H), fill=RING + (255,), width=2)
    d.ellipse((W // 2 - 22, 118, W // 2 + 22, 140), outline=RING + (255,), width=2)
    return bg


def bg_rays():
    """Comic-book starburst: alternating rays from the prize."""
    import math
    bg = Image.new('RGBA', (W, H), (255, 214, 64, 255))
    d = ImageDraw.Draw(bg)
    cx, cy = 120, 110
    for k in range(0, 24, 2):
        a0, a1 = k * math.pi / 12, (k + 1) * math.pi / 12
        d.polygon([(cx, cy), (cx + 400 * math.cos(a0), cy + 400 * math.sin(a0)),
                   (cx + 400 * math.cos(a1), cy + 400 * math.sin(a1))], fill=(255, 160, 40, 255))
    return bg


def bg_felt():
    """A card table: green felt, gold-trimmed wooden rim, faint suit pattern."""
    bg = Image.new('RGBA', (W, H), (20, 110, 64, 255))
    d = ImageDraw.Draw(bg)
    for y in range(6, H, 22):
        for x in range(((y // 22) % 2) * 11 + 4, W, 22):
            d.polygon([(x + 3, y), (x + 6, y + 4), (x + 3, y + 8), (x, y + 4)], fill=(30, 128, 76, 255))
    d.ellipse((-40, 80, W + 40, H + 120), outline=(196, 160, 60, 255), width=2)
    d.rectangle((0, 0, W, 5), fill=(110, 60, 30, 255))
    d.rectangle((0, 5, W, 6), fill=(196, 160, 60, 255))
    return bg


def bg_pokeball():
    """Split like a Poké Ball: red top, white bottom, black band and button."""
    bg = Image.new('RGBA', (W, H), (232, 48, 48, 255))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 62, W, H), fill=(248, 248, 252, 255))
    d.rectangle((0, 58, W, 66), fill=(30, 30, 36, 255))
    d.ellipse((W // 2 - 26, 36, W // 2 + 26, 88), fill=(30, 30, 36, 255))
    d.ellipse((W // 2 - 18, 44, W // 2 + 18, 80), fill=(248, 248, 252, 255))
    d.rectangle((0, 0, W, 14), fill=(214, 36, 40, 255))
    return bg


def bg_field():
    """A battle field: blue sky, stadium stands, striped grass with white lines."""
    bg = Image.new('RGBA', (W, H), (150, 206, 248, 255))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 40, W, 70), fill=(120, 130, 160, 255))
    for x in range(0, W, 8):
        d.rectangle((x, 44, x + 3, 66), fill=(150, 160, 190, 255))
    for i, y in enumerate(range(70, H, 10)):
        d.rectangle((0, y, W, y + 10), fill=(88, 176, 72, 255) if i % 2 else (104, 192, 84, 255))
    d.line((0, 72, W, 72), fill=(255, 255, 255, 255), width=2)
    d.ellipse((60, 100, 180, 140), outline=(255, 255, 255, 255), width=2)
    d.line((W // 2, 72, W // 2, H), fill=(255, 255, 255, 255), width=2)
    return bg


def bg_sunset():
    """Golden hour: banded sunset with a big low sun behind the pile."""
    bg = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(bg)
    bands = [(64, 40, 120), (120, 56, 140), (196, 80, 120), (240, 128, 96), (252, 176, 96), (255, 216, 140)]
    for i, c in enumerate(bands):
        d.rectangle((0, i * 16, W, i * 16 + 16), fill=c + (255,))
    d.ellipse((60, 60, 180, 180), fill=(255, 236, 170, 255))
    d.rectangle((0, 96, W, H), fill=(72, 44, 92, 255))
    d.rectangle((0, 96, W, 98), fill=(255, 200, 120, 255))
    return bg


def bg_spotlight():
    """Night arena: dark stands, two crossing spotlights on the prize."""
    bg = Image.new('RGBA', (W, H), (16, 18, 36, 255))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 72, W, H), fill=(36, 40, 70, 255))
    for x in range(4, W, 10):
        d.point((x, 20 + (x * 7) % 30), fill=(90, 90, 140, 255))
    d.polygon([(10, 0), (40, 0), (150, 140), (90, 140)], fill=(60, 64, 110, 255))
    d.polygon([(200, 0), (230, 0), (150, 140), (90, 140)], fill=(60, 64, 110, 255))
    d.ellipse((60, 108, 180, 140), fill=(110, 116, 170, 255))
    return bg


BACKGROUNDS = {
    'stadium': background,
    'rays': bg_rays,
    'felt': bg_felt,
    'pokeball': bg_pokeball,
    'field': bg_field,
    'sunset': bg_sunset,
    'spotlight': bg_spotlight,
}


def text_mask(text, size):
    font = ImageFont.truetype(FONT, size)
    l, t, r, b = font.getbbox(text)
    mask = Image.new('1', (r - l + 2, b - t + 2), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = '1'  # no anti-aliasing: hard pixels
    d.text((1 - l, 1 - t), text, font=font, fill=1)
    return mask


def outlined_word(text, size, top, bottom):
    """A word with a two-tone fill (top/bottom) and a 2px ink outline."""
    mask = text_mask(text, size)
    w, h = mask.size
    img = Image.new('RGBA', (w + 4, h + 4), (0, 0, 0, 0))
    m = mask.load()
    out = img.load()
    for y in range(h):
        for x in range(w):
            if m[x, y]:
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if abs(dx) + abs(dy) <= 3:
                            out[x + 2 + dx, y + 2 + dy] = INK + (255,)
    for y in range(h):
        for x in range(w):
            if m[x, y]:
                out[x + 2, y + 2] = (top if y < h * 0.55 else bottom) + (255,)
    return img


def pokemon_logo():
    """Emerald's own POKéMON logo from its title screen graphics (index 0 is clear)."""
    sheet = Image.open('graphics/title_screen/pokemon_logo.png')
    px = sheet.load()
    rgba = sheet.convert('RGBA')
    out = rgba.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    return rgba.crop(rgba.getchannel('A').getbbox())


def logo():
    cw, ch = 104, 56
    card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=7, fill=CARD + (255,), outline=CARD_EDGE + (255,), width=2)
    d.rounded_rectangle((4, 4, cw - 5, ch - 5), radius=4, outline=RED + (255,), width=1)
    # suit pips in the corners
    for (x, y) in [(7, 7), (cw - 16, ch - 17)]:
        d.polygon([(x + 4, y), (x + 8, y + 5), (x + 4, y + 10), (x, y + 5)], fill=RED + (255,))
    wild = outlined_word('WILD', 20, GOLD, ORANGE)
    cardw = outlined_word('CARD', 20, GOLD, ORANGE)
    card.alpha_composite(wild, ((cw - wild.width) // 2, 6))
    card.alpha_composite(cardw, ((cw - cardw.width) // 2, 28))
    return card.rotate(-7, resample=Image.NEAREST, expand=True)


def item_icon(name):
    icon = Image.open(f'graphics/items/icons/{name}.png')
    px = icon.load()
    rgba = icon.convert('RGBA')
    out = rgba.load()
    for y in range(icon.height):
        for x in range(icon.width):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    return rgba


CLUB_PIXELS = [  # hand-drawn club, 13x11
    '.....###.....',
    '....#####....',
    '....#####....',
    '.##..###..##.',
    '####..#..####',
    '#############',
    '####.###.####',
    '.##..###..##.',
    '.....###.....',
    '....#####....',
    '...#######...',
]


def club(colour, outline):
    """The hand-drawn club with a 1px outline."""
    h, w = len(CLUB_PIXELS), len(CLUB_PIXELS[0])
    img = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    px = img.load()
    on = {(x, y) for y, row in enumerate(CLUB_PIXELS) for x, ch in enumerate(row) if ch == '#'}
    for (x, y) in on:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                px[x + 1 + dx, y + 1 + dy] = outline + (255,)
    for (x, y) in on:
        px[x + 1, y + 1] = colour + (255,)
    return img


def styled_word(text, size, fill_top, fill_bottom, outline, outline_px, club_colour):
    """A word in hard pixels with a two-tone fill and an outline. Every 'ı'
    (dotless i) gets a club where its dot would be."""
    font = ImageFont.truetype(FONT, size)
    l, t, r, b = font.getbbox(text)
    pad = outline_px + size
    mask = Image.new('1', (r - l + 2 * pad, b - t + 2 * pad), 0)
    dm = ImageDraw.Draw(mask)
    dm.fontmode = '1'
    dm.text((pad - l, pad - t), text, font=font, fill=1)
    # where the dotless i's go, to hang a club over each
    clubs = []
    for k, ch in enumerate(text):
        if ch == 'ı':
            x0 = font.getlength(text[:k])
            w = font.getlength(ch)
            clubs.append(pad - l + x0 + w / 2)
    w, h = mask.size
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    m = mask.load()
    out = img.load()
    rows = [y for y in range(h) for x in range(w) if m[x, y]]
    top, bottom = min(rows), max(rows)
    for y in range(h):
        for x in range(w):
            if m[x, y]:
                for dy in range(-outline_px, outline_px + 1):
                    for dx in range(-outline_px, outline_px + 1):
                        if abs(dx) + abs(dy) <= outline_px + 1 and 0 <= x + dx < w and 0 <= y + dy < h:
                            out[x + dx, y + dy] = outline + (255,)
    for y in range(h):
        for x in range(w):
            if m[x, y]:
                out[x, y] = (fill_top if y < top + (bottom - top) * 0.55 else fill_bottom) + (255,)
    for cx in clubs:
        # the dotless i's stem stops at the x-height; the club sits just above it
        stem_top = next(y for y in range(h) if m[int(cx), y])
        c = club(club_colour, outline)
        img.alpha_composite(c, (int(cx - c.width / 2 + 0.5), stem_top - c.height - outline_px + 1))
    return img.crop(img.getchannel('A').getbbox())


# Lettering options for the sheet: (label, lines, size, top, bottom, outline, outline px, club colour)
WORDMARKS = [
    ('caps, one line, gold', ['WıLD CARD'], 24, GOLD, ORANGE, INK, 2, (40, 160, 72)),
    ('caps, stacked, gold', ['WıLD', 'CARD'], 28, GOLD, ORANGE, INK, 2, (40, 160, 72)),
    ('title case, one line', ['Wıld Card'], 26, GOLD, ORANGE, INK, 2, (40, 160, 72)),
    ('title case, stacked', ['Wıld', 'Card'], 30, GOLD, ORANGE, INK, 2, (40, 160, 72)),
    ('caps, white on red', ['WıLD CARD'], 24, (255, 255, 255), (226, 230, 244), RED, 2, INK),
    ('caps, card red and black', ['WıLD', 'CARD'], 28, RED, (176, 24, 32), INK, 2, INK),
]
WORDMARK = 1  # index into WORDMARKS for the title and cover


def wordmark(spec):
    _, lines, size, top, bottom, outline, opx, club_colour = spec
    words = [styled_word(line, size, top, bottom, outline, opx, club_colour) for line in lines]
    w = max(x.width for x in words)
    h = sum(x.height for x in words) - 2 * (len(words) - 1)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    y = 0
    for x in words:
        img.alpha_composite(x, ((w - x.width) // 2, y))
        y += x.height - 2
    return img


def compose(press_start, bg_name='pokeball', mark=WORDMARK):  # the pick for now
    import random
    rng = random.Random(7)
    img = BACKGROUNDS[bg_name]()
    # a soft spotlight on the prize
    ImageDraw.Draw(img).ellipse((PRIZE[0] - 26, PRIZE[1] + 4, PRIZE[0] + 26, PRIZE[1] + 16), fill=(255, 255, 255, 255))
    ball = item_icon('poke_ball')
    img.alpha_composite(ball, (PRIZE[0] - 12, PRIZE[1] - 12))
    for name, cx, feet in PILE:
        sprite = front_sprite(name)
        if cx < W // 2:
            sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)  # face the middle
        cx += rng.randint(-JITTER, JITTER)
        feet += rng.randint(-JITTER, JITTER // 2)
        x0, y0, x1, y1 = sprite.getchannel('A').getbbox()
        img.paste(sprite, (cx - (x0 + x1) // 2, feet - y1), sprite)
    pk = pokemon_logo()
    img.alpha_composite(pk, ((W - pk.width) // 2, 1))
    if mark is not None:
        wm = wordmark(WORDMARKS[mark])
        img.alpha_composite(wm, ((W - wm.width) // 2, pk.height + 2 + (60 - wm.height) // 2))
    if press_start:
        word = outlined_word('PRESS START', 9, (255, 255, 255), (220, 220, 240))
        x, y = (W - word.width) // 2, H - word.height - 4
        ImageDraw.Draw(img).rounded_rectangle((x - 5, y - 1, x + word.width + 4, y + word.height), radius=5,
                                              fill=INK + (255,), outline=(120, 100, 200, 255))
        img.alpha_composite(word, (x, y))
    return img


def main():
    title = compose(True)
    title.save(OUT + 'title_240x160.png')
    title.resize((W * 4, H * 4), Image.NEAREST).save(OUT + 'title_preview_4x.png')
    compose(False).resize((W * 4, H * 4), Image.NEAREST).save(OUT + 'cover_960x640.png')
    # contact sheet of background options, 2x each, labelled
    names = list(BACKGROUNDS)
    cols, scale = 2, 2
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * W * scale + 12 * (cols + 1), rows * (H * scale + 22) + 10), (40, 40, 48, 255))
    d = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(FONT, 14)
    for k, name in enumerate(names):
        x = 12 + (k % cols) * (W * scale + 12)
        y = 6 + (k // cols) * (H * scale + 22)
        d.text((x, y), f'{k + 1}. {name}', font=label_font, fill=(240, 240, 240, 255))
        sheet.paste(compose(True, name, None).resize((W * scale, H * scale), Image.NEAREST), (x, y + 18))
    sheet.save(OUT + 'backgrounds_sheet.png')

    # lettering options, on the chosen background
    rows = (len(WORDMARKS) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * W * scale + 12 * (cols + 1), rows * (H * scale + 22) + 10), (40, 40, 48, 255))
    d = ImageDraw.Draw(sheet)
    for k, spec in enumerate(WORDMARKS):
        x = 12 + (k % cols) * (W * scale + 12)
        y = 6 + (k // cols) * (H * scale + 22)
        d.text((x, y), f'{k + 1}. {spec[0]}', font=label_font, fill=(240, 240, 240, 255))
        sheet.paste(compose(True, mark=k).resize((W * scale, H * scale), Image.NEAREST), (x, y + 18))
    sheet.save(OUT + 'wordmark_sheet.png')


if __name__ == '__main__':
    main()
