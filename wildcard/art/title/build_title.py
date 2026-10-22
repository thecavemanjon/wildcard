"""Title screen mockups for Pokémon Wild Card, stripped back: Emerald's own
POKéMON logo, a WILD CARD subtitle in the official "version" style (white to
silver letters, heavy dark outline, drop shadow, a gentle arch, like Emerald's
EMERALD VERSION), on a banded gradient. Two layouts: centred like Emerald, and
logo top-left like FireRed/LeafGreen (room on the right for a hero Pokémon).

Writes contact sheets to out/. Run from the repo root:
    python3 wildcard/art/title/build_title.py
The earlier dogpile version is build_title_pile.py.
"""
from PIL import Image, ImageDraw, ImageFont

OUT = 'wildcard/art/title/out/'
FONT = '/System/Library/Fonts/Supplemental/Arial Black.ttf'
W, H = 240, 160

OUTLINE = (24, 16, 24)
SHADOW = (40, 32, 48)
FILL_BANDS = [(255, 255, 255), (238, 238, 238), (214, 214, 222), (176, 176, 190)]  # top to bottom

# (name, top colour, bottom colour)
GRADIENTS = [
    ('sky', (72, 144, 232), (228, 242, 255)),
    ('emerald', (10, 70, 50), (150, 226, 180)),
    ('sunset', (70, 36, 120), (252, 170, 90)),
    ('night', (6, 10, 36), (70, 46, 130)),
    ('gold', (250, 150, 40), (255, 238, 170)),
    ('silver', (150, 162, 190), (250, 250, 255)),
    ('fire', (16, 4, 8), (230, 90, 30)),
    ('leaf', (12, 60, 24), (200, 230, 90)),
]
STEPS = 16  # colour bands in a gradient (one 16-colour palette's worth)


# Soft white options: (name, kind, colour a, colour b). 'down' fades a to b top to
# bottom; 'glow' is a bright centre a fading out to b at the edges; 'horizon' is
# b at top and bottom with a white band a across the middle.
WHITES = [
    ('white to pale sky', 'down', (255, 255, 255), (198, 222, 248)),
    ('pale sky to white', 'down', (186, 214, 246), (255, 255, 255)),
    ('pearl', 'down', (250, 248, 255), (214, 214, 230)),
    ('cream', 'down', (255, 255, 250), (246, 232, 196)),
    ('mint', 'down', (255, 255, 255), (200, 236, 214)),
    ('lavender', 'down', (255, 255, 255), (222, 210, 246)),
    ('white glow', 'glow', (255, 255, 255), (196, 214, 240)),
    ('white horizon', 'horizon', (255, 255, 255), (200, 220, 246)),
]


# Sky options for the title (with clouds): same format as WHITES.
SKIES = [
    ('white horizon', 'horizon', (255, 255, 255), (200, 220, 246)),
    ('clear blue', 'down', (120, 176, 244), (236, 246, 255)),
    ('deep blue to white', 'down', (64, 120, 220), (250, 252, 255)),
    ('dawn', 'down', (252, 196, 210), (255, 246, 236)),
    ('golden hour', 'down', (252, 200, 120), (255, 244, 214)),
    ('twilight', 'down', (150, 140, 220), (252, 222, 236)),
    ('mint sky', 'down', (150, 226, 214), (244, 255, 250)),
    ('blue horizon', 'horizon', (240, 248, 255), (130, 180, 240)),
]


def soft_gradient(kind, a, b):
    if kind == 'down':
        return gradient(a, b)
    img = Image.new('RGBA', (W, H), b + (255,))
    d = ImageDraw.Draw(img)
    for i in range(STEPS):
        t = i / (STEPS - 1)
        c = tuple(round(y + (x - y) * t) for x, y in zip(a, b))
        if kind == 'glow':  # rings closing in on a bright centre
            k = 1 - t
            d.ellipse((W / 2 - W * 0.85 * k - 10, H / 2 - H * 0.95 * k - 6,
                       W / 2 + W * 0.85 * k + 10, H / 2 + H * 0.95 * k + 6), fill=c + (255,))
        else:  # horizon: bands narrowing toward a white middle
            half = (H / 2) * (1 - t)
            d.rectangle((0, H / 2 - half, W, H / 2 + half), fill=c + (255,))
    return img


def gradient(top, bottom):
    img = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(img)
    for i in range(STEPS):
        t = i / (STEPS - 1)
        c = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        d.rectangle((0, i * H // STEPS, W, (i + 1) * H // STEPS), fill=c + (255,))
    return img


def clear_index0(path):
    sheet = Image.open(path)
    px = sheet.load()
    rgba = sheet.convert('RGBA')
    out = rgba.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    return rgba.crop(rgba.getchannel('A').getbbox())


def pokemon_logo():
    """Emerald's own POKéMON logo from its title screen graphics."""
    return clear_index0('graphics/title_screen/pokemon_logo.png')


def word_mask(text, size, arch, gap_trim=0):
    """Hard-pixel letters, each column lifted by a gentle arch (centre highest).
    gap_trim narrows the space between words by that many pixels."""
    font = ImageFont.truetype(FONT, size)
    l, t, r, b = font.getbbox(text)
    pad = 2 + arch
    flat = Image.new('1', (r - l + 4, b - t + 4), 0)
    d = ImageDraw.Draw(flat)
    d.fontmode = '1'
    d.text((2 - l, 2 - t), text, font=font, fill=1)
    if gap_trim:  # cut columns out of the middle of the widest empty run (the space)
        fw, fh = flat.size
        fp = flat.load()
        cols = [x for x in range(fw) if any(fp[x, y] for y in range(fh))]
        run, start = max((cols[k + 1] - cols[k], cols[k]) for k in range(len(cols) - 1))
        cut = start + run // 2
        keep = [x for x in range(fw) if not cut <= x < cut + gap_trim]
        trimmed = Image.new('1', (len(keep), fh), 0)
        tp = trimmed.load()
        for nx, x in enumerate(keep):
            for y in range(fh):
                tp[nx, y] = fp[x, y]
        flat = trimmed
    w, h = flat.size
    arched = Image.new('1', (w, h + pad), 0)
    src, dst = flat.load(), arched.load()
    for x in range(w):
        u = (x - w / 2) / (w / 2)
        lift = round(arch * (1 - u * u))
        for y in range(h):
            if src[x, y]:
                dst[x, y + pad - lift] = 1
    return arched


SILVER = [(255, 255, 255), (238, 238, 238), (214, 214, 222), (176, 176, 190)]
GOLDS = [(255, 246, 170), (255, 222, 90), (246, 184, 40), (214, 136, 24)]
GREENS = [(200, 255, 214), (120, 226, 150), (48, 176, 104), (24, 128, 76)]
YELLOWS = [(255, 255, 160), (255, 240, 64), (248, 208, 24), (216, 160, 16)]
BLUES = [(196, 220, 255), (120, 168, 248), (64, 112, 224), (40, 72, 176)]
REDS = [(255, 170, 170), (248, 96, 96), (224, 48, 56), (168, 24, 36)]
BLACKS = [(120, 120, 136), (88, 88, 104), (60, 60, 74), (40, 40, 52)]
PINKS = [(255, 200, 240), (248, 128, 208), (224, 72, 168), (168, 40, 128)]
CYANS = [(200, 255, 255), (120, 232, 248), (48, 192, 224), (24, 140, 180)]

# (name, WILD bands, CARD bands, VERSION bands)
SUBTITLE_COLOURS = [
    ('silver', SILVER, SILVER, SILVER),
    ('gold', GOLDS, GOLDS, SILVER),
    ('gold WILD, silver CARD', GOLDS, SILVER, SILVER),
    ('emerald', GREENS, GREENS, SILVER),
    ('emerald WILD, silver CARD', GREENS, SILVER, SILVER),
    ('logo yellow and blue', YELLOWS, BLUES, SILVER),
    ('blue WILD, gold CARD', BLUES, GOLDS, SILVER),
    ('Poké Ball red and white', REDS, SILVER, SILVER),
    ('playing card red and black', REDS, BLACKS, SILVER),
    ('pink and cyan', PINKS, CYANS, SILVER),
]
SUBTITLE_COLOUR = 7  # Poké Ball red WILD, white CARD: the pick
WORD_GAP_TRIM = 2  # WILD and CARD each 1px closer
SUBTITLE_NUDGE = 2  # the drop shadow pushes the box centre right; this lines the letters up with POKéMON's


def subtitle_word(text, size, arch, outline_px=2, bands=None, right_bands=None, gap_trim=0):
    """The official subtitle treatment: banded white-to-silver fill, dark outline,
    a drop shadow down and right."""
    mask = word_mask(text, size, arch, gap_trim)
    w, h = mask.size
    img = Image.new('RGBA', (w + 2 * outline_px + 2, h + 2 * outline_px + 3), (0, 0, 0, 0))
    m = mask.load()
    out = img.load()
    on = [(x, y) for y in range(h) for x in range(w) if m[x, y]]
    top = min(y for _, y in on)
    bottom = max(y for _, y in on)
    o = outline_px
    for x, y in on:  # shadow
        for dy in range(-o, o + 1):
            for dx in range(-o, o + 1):
                if abs(dx) + abs(dy) <= o + 1:
                    out[x + o + dx + 1, y + o + dy + 2] = SHADOW + (255,)
    for x, y in on:  # outline
        for dy in range(-o, o + 1):
            for dx in range(-o, o + 1):
                if abs(dx) + abs(dy) <= o + 1:
                    out[x + o + dx, y + o + dy] = OUTLINE + (255,)
    # where the gap between words is, for two-tone schemes: the widest empty column run
    split = None
    if right_bands is not None:
        cols = sorted({x for x, _ in on})
        gaps = [(cols[k + 1] - cols[k], cols[k]) for k in range(len(cols) - 1)]
        split = max(gaps)[1] + 1 if gaps else None
    for x, y in on:  # fill, banded top to bottom
        t = (y - top) / max(1, bottom - top)
        use = right_bands if (split is not None and x >= split) else (bands or FILL_BANDS)
        out[x + o, y + o] = use[min(len(use) - 1, int(t * len(use)))] + (255,)
    return img.crop(img.getchannel('A').getbbox())


def subtitle(with_version, colours=None):
    _, wild, card, version = SUBTITLE_COLOURS[SUBTITLE_COLOUR if colours is None else colours]
    big = subtitle_word('WILD CARD', 20, 3, bands=wild, right_bands=card if card != wild else None,
                        gap_trim=WORD_GAP_TRIM)
    if not with_version:
        return big
    small = subtitle_word('VERSION', 11, 2, bands=version)
    img = Image.new('RGBA', (max(big.width, small.width), big.height + small.height - 3), (0, 0, 0, 0))
    img.alpha_composite(big, ((img.width - big.width) // 2, 0))
    img.alpha_composite(small, ((img.width - small.width) // 2, big.height - 3))
    return img


def press_start():
    return subtitle_word('PRESS START', 9, 0, outline_px=1)


# The stack: 16 Pokémon (the GBA's 16 sprite palettes), all as real sprites.
# Two totem towers flank the logo, bottom to top, each standing on the head of
# the one below; a heap runs along the bottom between them.
TOWERS = [
    (30,  ['snorlax', 'bulbasaur', 'pikachu', 'togepi']),
    (210, ['lapras', 'psyduck', 'piplup', 'snom']),
]
HEAP = [  # (folder, centre x, feet y), back to front
    ('magikarp',       76, 158),
    ('smoliv',         58, 162),
    ('grookey',        98, 162),
    ('torchic',       140, 160),
    ('cyndaquil',     160, 160),
    ('oshawott',      178, 162),
    ('scorbunny',     194, 164),
    ('greninja/mega', 120, 166),
]
SINK = 7  # how far each Pokémon sinks into the one it stands on


def front_sprite_frame(name, flip):
    """The first 64x64 front frame, index 0 clear, optionally mirrored."""
    import os
    folder = f'graphics/pokemon/{name}/'
    sheet = Image.open(folder + ('anim_front.png' if os.path.exists(folder + 'anim_front.png') else 'front.png'))
    frame = sheet.crop((0, 0, 64, 64))
    px = frame.load()
    rgba = frame.convert('RGBA')
    out = rgba.load()
    for y in range(64):
        for x in range(64):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    return rgba.transpose(Image.FLIP_LEFT_RIGHT) if flip else rgba


def front_sprite(name, flip):
    import os
    folder = f'graphics/pokemon/{name}/'
    sheet = Image.open(folder + ('anim_front.png' if os.path.exists(folder + 'anim_front.png') else 'front.png'))
    frame = sheet.crop((0, 0, 64, 64))
    px = frame.load()
    rgba = frame.convert('RGBA')
    out = rgba.load()
    for y in range(64):
        for x in range(64):
            if px[x, y] == 0:
                out[x, y] = (0, 0, 0, 0)
    if flip:
        rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    return rgba.crop(rgba.getchannel('A').getbbox())


FLOOR_TOP = 128  # where the floor meets the sky
FEET = 150       # where the stack's feet land, on the floor


def floor_stone(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(176, 180, 196, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 3), fill=(120, 124, 148, 255))
    for i, y in enumerate([FLOOR_TOP + 10, FLOOR_TOP + 19, FLOOR_TOP + 30]):
        d.line((0, y, W, y), fill=(150, 154, 172, 255))
    for x in range(-200, W + 200, 30):  # slab joints in perspective, meeting far away
        d.line((W // 2 + (x - W // 2) // 4, FLOOR_TOP + 3, x, H), fill=(150, 154, 172, 255))
    d.line((W // 2, FLOOR_TOP + 3, W // 2, H), fill=(240, 240, 248, 255), width=2)


def floor_grass(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(96, 184, 80, 255))
    for i, y in enumerate(range(FLOOR_TOP, H, 6)):
        if i % 2:
            d.rectangle((0, y, W, y + 6), fill=(110, 198, 92, 255))
    d.ellipse((24, FLOOR_TOP + 8, W - 24, H + 26), outline=(244, 248, 236, 255), width=2)
    d.line((W // 2, FLOOR_TOP + 8, W // 2, H), fill=(244, 248, 236, 255), width=2)
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 2), fill=(64, 140, 56, 255))


def floor_white(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(232, 238, 248, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 2), fill=(176, 192, 220, 255))
    d.ellipse((10, FLOOR_TOP + 10, W - 10, H + 40), fill=(198, 214, 240, 255))
    d.ellipse((24, FLOOR_TOP + 15, W - 24, H + 30), fill=(250, 252, 255, 255))
    d.line((W // 2, FLOOR_TOP + 15, W // 2, H), fill=(198, 214, 240, 255), width=2)


def floor_wood(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(178, 120, 70, 255))
    for y in range(FLOOR_TOP + 6, H, 7):
        d.line((0, y, W, y), fill=(150, 98, 56, 255))
    for k, y in enumerate(range(FLOOR_TOP + 6, H, 7)):
        for x in range((k * 37) % 60, W, 60):
            d.line((x, y - 6, x, y), fill=(150, 98, 56, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 3), fill=(232, 184, 64, 255))
    d.line((0, FLOOR_TOP + 4, W, FLOOR_TOP + 4), fill=(120, 76, 40, 255))


def floor_marble(img):
    """A checkerboard in perspective: every column edge runs to one vanishing point."""
    d = ImageDraw.Draw(img)
    vx, vy = W / 2, FLOOR_TOP - 70  # vanishing point, above the horizon
    d.rectangle((0, FLOOR_TOP, W, H), fill=(246, 248, 252, 255))

    def x_at(xb, y):  # column through xb at the bottom edge, at height y
        return vx + (xb - vx) * (y - vy) / (H - vy)

    rows = [FLOOR_TOP, FLOOR_TOP + 5, FLOOR_TOP + 11, FLOOR_TOP + 19, FLOOR_TOP + 29, H]
    step = 30
    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        for k in range(-12, 13):
            if (k + r) % 2:
                continue
            xb0, xb1 = W / 2 + (k - 0.5) * step, W / 2 + (k + 0.5) * step
            d.polygon([(x_at(xb0, y0), y0), (x_at(xb1, y0), y0), (x_at(xb1, y1), y1), (x_at(xb0, y1), y1)],
                      fill=(220, 226, 240, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 1), fill=(170, 186, 214, 255))


def floor_pokeball_court(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(236, 242, 250, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 2), fill=(170, 186, 214, 255))
    cx, cy, rx, ry = W // 2, FLOOR_TOP + 22, 46, 14
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(232, 64, 64, 255), outline=(40, 40, 52, 255), width=2)
    d.chord((cx - rx, cy - ry, cx + rx, cy + ry), 0, 180, fill=(250, 250, 252, 255), outline=(40, 40, 52, 255), width=2)
    d.line((cx - rx, cy, cx + rx, cy), fill=(40, 40, 52, 255), width=2)
    d.ellipse((cx - 9, cy - 4, cx + 9, cy + 4), fill=(250, 250, 252, 255), outline=(40, 40, 52, 255), width=2)


# Battle platform colours: (name, rim, top, inner ring), like the in-game battle bases.
PLATFORMS = [
    ('grass', (150, 172, 120), (196, 222, 140), (214, 236, 160)),
    ('tall grass', (64, 132, 64), (104, 176, 88), (128, 196, 104)),
    ('sand', (196, 160, 104), (232, 204, 148), (244, 222, 172)),
    ('stone', (130, 134, 150), (176, 180, 196), (196, 200, 214)),
    ('water', (64, 128, 196), (120, 180, 236), (156, 206, 248)),
    ('snow', (176, 196, 222), (232, 240, 252), (248, 252, 255)),
    ('ghost', (100, 76, 140), (150, 124, 196), (176, 152, 220)),
    ('lava', (176, 64, 40), (232, 120, 56), (248, 168, 80)),
    ('gold', (196, 150, 40), (240, 200, 72), (252, 226, 120)),
    ('emerald', (24, 120, 96), (64, 180, 140), (110, 210, 170)),
]
PLATFORM = 4  # water. Shortlist: dawn + grass, twilight + water (in the ROM), blue horizon + grass


def floor_platform(img, colours=None):
    _, rim, top, inner = colours or PLATFORMS[PLATFORM]
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP + 8, W, H), fill=(208, 220, 236, 255))
    # the raised oval stand from the battle screens
    d.ellipse((6, FLOOR_TOP + 6, W - 6, H + 18), fill=rim + (255,))
    d.ellipse((6, FLOOR_TOP, W - 6, H + 8), fill=top + (255,))
    d.ellipse((24, FLOOR_TOP + 6, W - 24, H + 2), fill=inner + (255,))


def floor_ice(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(214, 236, 250, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 1), fill=(150, 196, 232, 255))
    for x, w in [(20, 30), (90, 50), (170, 26)]:  # glints
        d.line((x, FLOOR_TOP + 8, x + w, FLOOR_TOP + 8), fill=(255, 255, 255, 255))
    for x, w in [(50, 40), (140, 60)]:
        d.line((x, FLOOR_TOP + 20, x + w, FLOOR_TOP + 20), fill=(240, 250, 255, 255))


def floor_court(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(92, 140, 210, 255))
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 2), fill=(60, 100, 170, 255))
    d.rectangle((14, FLOOR_TOP + 6, W - 14, H + 4), outline=(250, 250, 255, 255), width=2)
    d.line((W // 2, FLOOR_TOP + 6, W // 2, H), fill=(250, 250, 255, 255), width=2)
    d.ellipse((W // 2 - 22, FLOOR_TOP + 12, W // 2 + 22, FLOOR_TOP + 30), outline=(250, 250, 255, 255), width=2)


def floor_carpet(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_TOP, W, H), fill=(226, 230, 240, 255))
    d.polygon([(W // 2 - 26, FLOOR_TOP), (W // 2 + 26, FLOOR_TOP), (W // 2 + 70, H), (W // 2 - 70, H)], fill=(196, 40, 52, 255))
    d.line((W // 2 - 26, FLOOR_TOP, W // 2 - 70, H), fill=(240, 196, 72, 255), width=2)
    d.line((W // 2 + 26, FLOOR_TOP, W // 2 + 70, H), fill=(240, 196, 72, 255), width=2)
    d.rectangle((0, FLOOR_TOP, W, FLOOR_TOP + 1), fill=(176, 186, 210, 255))


FLOORS = [('stone stadium', floor_stone), ('grass battle base', floor_grass),
          ('polished white arena', floor_white), ('wooden stage', floor_wood),
          ('marble', floor_marble), ('Poké Ball court', floor_pokeball_court),
          ('battle platform', floor_platform), ('ice', floor_ice),
          ('blue court', floor_court), ('red carpet', floor_carpet)]
BACKGROUND = 7  # index into WHITES (older sheets)
TITLE_SKY = 5  # index into SKIES: twilight, in the ROM for now (shortlist: 3 dawn, 5 twilight, 7 blue horizon)
FLOOR = 0  # the picked floor goes here


# The line-up standing on the platform: (folder, centre x, feet y, face right).
# Snorlax far left, Pikachu centre, Mega Charizard X far right with Snom in front of it.
LINEUP = [  # back to front
    ('snorlax',           32, 149, True),
    ('charizard/mega_x', 202, 145, False),
    ('bulbasaur',        62, 149, True),
    ('piplup',           91, 147, True),
    ('pikachu',         125, 145, False),  # centred on its body, not its tail; in front of Piplup
    ('cyndaquil',       159, 145, False),
    ('snom',            184, 148, False),  # in front of Charizard's legs
]


# Flyers peeking in at the top corners, partly off screen: (folder, left x, top y, face right).
# None for now (2026-10-15); Pidgeot and Latias were here.
FLYERS = []


FLYER_OPTIONS = ['latias', 'latios', 'rayquaza', 'togekiss', 'staraptor', 'talonflame',
                 'noivern', 'yveltal', 'corviknight', 'kilowattrel', 'flamigo', 'ho_oh']


def frame_bbox(name, flip):
    """The 64x64 front frame's visible box, after flipping."""
    full = front_sprite_frame(name, flip)
    return full.getchannel('A').getbbox()


def lineup_placements(flyers=None):
    """(folder, frame top-left x, y, flipped) for every title sprite, back to front:
    the same positions the mockup draws and the ROM title uses."""
    out = []
    for name, x, y, face_right in flyers or FLYERS:
        x0, y0, _, _ = frame_bbox(name, face_right)
        out.append((name, x - x0, y - y0, face_right))
    for name, cx, feet, face_right in LINEUP:
        x0, y0, x1, y1 = frame_bbox(name, face_right)
        w, h = x1 - x0, y1 - y0
        out.append((name, cx - w // 2 - x0, feet - h - y0, face_right))
    return out


def place_lineup(img, flyers=None):
    for name, fx, fy, flip in lineup_placements(flyers):
        frame = front_sprite_frame(name, flip)
        img.paste(frame, (fx, fy), frame)


def place_stack(img):
    """Draws the heap, then the towers (towers in front, so they read as stacks)."""
    for name, cx, feet in HEAP:
        s = front_sprite(name, cx < W // 2)
        feet += FEET - H  # the heap's feet were laid out for the screen's bottom edge
        img.paste(s, (cx - s.width // 2, feet - s.height), s)
    for cx, names in TOWERS:
        feet = FEET + 2
        placed = []
        for name in names:
            s = front_sprite(name, cx < W // 2)
            placed.append((s, cx - s.width // 2, feet - s.height))
            feet = feet - s.height + SINK
        for s, x, y in reversed(placed):  # lower ones in front, like a real stack
            img.paste(s, (x, y), s)


def compose(layout, grad, with_version, stack=False, floor=None, platform=None, lineup=False, flyers=None,
            colours=None):
    if len(grad) == 4:  # a soft white option
        img = soft_gradient(grad[1], grad[2], grad[3])
    else:
        _, top, bottom = grad
        img = gradient(top, bottom)
    pk = pokemon_logo()
    sub = subtitle(with_version, colours)
    ps = press_start()
    if platform is not None:
        floor_platform(img, PLATFORMS[platform])
    elif floor is not None:
        FLOORS[floor][1](img)
    if layout == 'emerald' and lineup:
        # centred; clouds; the line-up stands on the platform; PRESS START along the bottom
        img.alpha_composite(cloud_layer().crop((0, 0, W, H)))
        place_lineup(img, flyers)
        img.alpha_composite(pk, ((W - pk.width) // 2, 5))
        img.alpha_composite(sub, ((W - sub.width) // 2 + SUBTITLE_NUDGE, 5 + pk.height - 2))
        img.alpha_composite(ps, ((W - ps.width) // 2, H - ps.height - 3))
    elif layout == 'emerald' and stack:
        # centred, logo nudged up; the stack frames it; PRESS START above the heap
        place_stack(img)
        img.alpha_composite(pk, ((W - pk.width) // 2, 4))
        img.alpha_composite(sub, ((W - sub.width) // 2, 4 + pk.height + 1))
        img.alpha_composite(ps, ((W - ps.width) // 2, 4 + pk.height + sub.height + 6))
    elif layout == 'emerald':
        # centred, like Emerald: logo up top, subtitle under it, PRESS START low
        img.alpha_composite(pk, ((W - pk.width) // 2, 18))
        img.alpha_composite(sub, ((W - sub.width) // 2, 18 + pk.height + 2))
        img.alpha_composite(ps, ((W - ps.width) // 2, H - ps.height - 14))
    else:
        # FireRed/LeafGreen: logo top-left, subtitle under its right end, the
        # right side open for a big Pokémon, PRESS START bottom-left
        img.alpha_composite(pk, (6, 8))
        img.alpha_composite(sub, (6 + pk.width - sub.width + 4, 8 + pk.height - 2))
        img.alpha_composite(ps, (14, H - ps.height - 12))
    return img


def sheet(cells, filename, cols=2, scale=2):
    rows = (len(cells) + cols - 1) // cols
    out = Image.new('RGBA', (cols * W * scale + 12 * (cols + 1), rows * (H * scale + 22) + 10), (40, 40, 48, 255))
    d = ImageDraw.Draw(out)
    font = ImageFont.truetype(FONT, 14)
    for k, (label, img) in enumerate(cells):
        x = 12 + (k % cols) * (W * scale + 12)
        y = 6 + (k // cols) * (H * scale + 22)
        d.text((x, y), f'{k + 1}. {label}', font=font, fill=(240, 240, 240, 255))
        out.paste(img.resize((W * scale, H * scale), Image.NEAREST), (x, y + 18))
    out.save(OUT + filename)


def main():
    sheet([(g[0], compose('emerald', g, False)) for g in GRADIENTS], 'gradients_sheet.png')
    sheet([(g[0], compose('emerald', g, True)) for g in WHITES], 'whites_sheet.png')
    sheet([
        ('centred (Emerald)', compose('emerald', GRADIENTS[0], False)),
        ('centred, with VERSION', compose('emerald', GRADIENTS[0], True)),
        ('FireRed/LeafGreen', compose('frlg', GRADIENTS[6], False)),
        ('FireRed/LeafGreen, with VERSION', compose('frlg', GRADIENTS[7], True)),
    ], 'layouts_sheet.png')
    big = subtitle(True)
    zoom = Image.new('RGBA', big.size, (90, 140, 220, 255))
    zoom.alpha_composite(big)
    zoom.resize((big.width * 6, big.height * 6), Image.NEAREST).save(OUT + 'subtitle_zoom.png')
    # The pick: centred, sky, with VERSION, and the stack
    bg = WHITES[BACKGROUND]
    picks = [0, 2, 4, 5, 6, 7, 8, 9]  # stone, white arena, and the new ones
    sheet([(FLOORS[k][0], compose('emerald', bg, True, floor=k)) for k in picks], 'floors_empty_sheet.png')
    sheet([(FLOORS[k][0], compose('emerald', bg, True, stack=True, floor=k)) for k in picks], 'floors_sheet.png')
    sheet([(p[0], compose('emerald', bg, True, platform=k)) for k, p in enumerate(PLATFORMS)], 'platforms_sheet.png')
    sheet([(p[0], compose('emerald', bg, True, stack=True, platform=k)) for k, p in enumerate(PLATFORMS)],
          'platforms_stack_sheet.png')
    sheet([(name, compose('emerald', bg, True, platform=PLATFORM, lineup=True,
                           flyers=[('pidgeot', -16, -3, True), (name, W - 50, -8, False)])) for name in FLYER_OPTIONS],
          'flyers_sheet.png', cols=3)
    sheet([(sky[0], compose('emerald', sky, True, platform=PLATFORM, lineup=True)) for sky in SKIES],
          'skies_sheet.png')
    # The three shortlisted skies against six platforms
    picks_sky = [3, 5, 7]  # dawn, twilight, blue horizon
    picks_plat = [9, 0, 4, 6, 8, 3]  # emerald, grass, water, ghost, gold, stone
    cells = [(f'{SKIES[a][0]} / {PLATFORMS[b][0]}', compose('emerald', SKIES[a], True, platform=b, lineup=True))
             for a in picks_sky for b in picks_plat]
    sheet(cells, 'sky_platform_grid.png', cols=len(picks_plat), scale=1)
    sheet([(c[0], compose('emerald', bg, True, platform=PLATFORM, lineup=True, colours=k))
           for k, c in enumerate(SUBTITLE_COLOURS)], 'subtitle_colours_sheet.png')
    export_gba()
    # what the ROM will show at each time of day, built from the exported layers
    for theme in TIMES_OF_DAY:
        layers = title_layers(theme)
        rom = layers[0][1].copy()
        rom.alpha_composite(layers[3][1].crop((0, 0, W, H)))
        for name, fx, fy, flip in lineup_placements():
            frame = front_sprite_frame(name, flip)
            rom.paste(frame, (fx, fy), frame)
        rom.alpha_composite(layers[1][1])
        rom.alpha_composite(layers[2][1])
        rom.save(OUT + f'title_{theme}_240x160.png')
        rom.resize((W * 4, H * 4), Image.NEAREST).save(OUT + f'title_{theme}_4x.png')


# ---- GBA export: the ROM title is built from exactly what the mockup draws ----

GBA_OUT = 'graphics/wildcard_title/'
LAYOUT_HEADER = 'src/data/wildcard_title_layout.h'


def title_layers(theme):
    """The background layers at 240x160 for one time of day: back (the stadium,
    opaque), logo (POKéMON and WILD CARD VERSION, transparent elsewhere), press
    (PRESS START, transparent elsewhere), clouds (a 256px wrapping strip)."""
    back = stadium_back(theme)
    logo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pk = pokemon_logo()
    sub = subtitle(True)
    logo.alpha_composite(pk, ((W - pk.width) // 2, 5))
    logo.alpha_composite(sub, ((W - sub.width) // 2 + SUBTITLE_NUDGE, 5 + pk.height - 2))
    logo = quantize_rows(logo)
    press = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ps = press_start()
    press.alpha_composite(ps, ((W - ps.width) // 2, H - ps.height - 3))
    return [('back', back, True), ('logo', logo, False), ('press', press, False), ('clouds', stadium_clouds(theme), False)]


def quantize_rows(img, colours=15):
    """Reduces each 8-pixel row of a layer to at most `colours` colours (median
    cut), so each tile row can share one 16-colour palette. Transparent stays
    transparent. Emerald's logo has 153 colours, shaded top to bottom."""
    out = img.copy()
    for ty in range(0, H, 8):
        strip = img.crop((0, ty, W, ty + 8))
        alpha = strip.getchannel('A')
        opaque = [c[:3] for c in strip.getdata() if c[3] >= 128]
        if len(set(gba_colour(c) for c in opaque)) <= colours:
            continue
        rgb = Image.new('RGB', strip.size)
        rgb.paste(strip.convert('RGB'))
        q = rgb.quantize(colors=colours, method=Image.Quantize.MEDIANCUT).convert('RGB')
        q.putalpha(alpha)
        # keep fully transparent pixels transparent
        out.paste(q, (0, ty), alpha)
        cleared = Image.new('RGBA', strip.size, (0, 0, 0, 0))
        out.paste(cleared, (0, ty), Image.eval(alpha, lambda a: 255 - a))
    return out


CLOUD_W = 256  # the GBA wraps a 32-tile layer at 256px, so the clouds loop seamlessly
CLOUD_LIGHT = (255, 255, 255)
CLOUD_MID = (226, 236, 250)
CLOUD_SHADE = (196, 214, 240)
# (centre x, base y, width): puffs drifting across the sky
CLOUDS = [(20, 30, 46), (92, 18, 34), (150, 44, 56), (214, 24, 40), (60, 70, 30), (190, 84, 36)]


def cloud_layer():
    """Soft pixel clouds on a transparent 256x160 strip: a flat-bottomed puff of
    circles, a pale blue underside so they show against the white band."""
    img = Image.new('RGBA', (CLOUD_W, H), (0, 0, 0, 0))
    for cx, base, w in CLOUDS:
        puff = Image.new('RGBA', (w + 8, w // 2 + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(puff)
        r = w // 4
        lobes = [(r + 2, puff.height - r - 2, r), (w // 2 + 4, puff.height - r - 5, r + 3),
                 (w - r + 4, puff.height - r - 2, r - 1), (w // 3 + 3, puff.height - r - 6, r - 1)]
        for x, y, rr in lobes:
            d.ellipse((x - rr, y - rr + 2, x + rr, y + rr + 2), fill=CLOUD_SHADE + (255,))
        for x, y, rr in lobes:
            d.ellipse((x - rr, y - rr, x + rr, y + rr - 1), fill=CLOUD_MID + (255,))
        for x, y, rr in lobes:
            d.ellipse((x - rr + 1, y - rr, x + rr - 2, y + rr - 4), fill=CLOUD_LIGHT + (255,))
        d.rectangle((0, puff.height - 2, puff.width, puff.height), fill=(0, 0, 0, 0))
        x0, y0 = cx - puff.width // 2, base - puff.height // 2
        for dx in (0, CLOUD_W, -CLOUD_W):  # wrap across the seam
            img.alpha_composite(puff, (x0 + dx, y0)) if 0 <= x0 + dx and x0 + dx + puff.width <= CLOUD_W else img.paste(puff, (x0 + dx, y0), puff)
    return img


# ---- The stadium: the title's backdrop, in three times of day ----
# The ROM picks one by the cartridge clock (sundial_title.c). Stands with a
# pixel crowd behind the line-up, a striped pitch under it. The crowd repeats
# every CROWD_PERIOD pixels so it stays a handful of tiles. Some crowd dots use
# a "flash" twin of their shirt colour (same look, one blue step apart); the ROM
# finds those colours in the palettes and blinks them white: camera flashes.

STAND_TOP, STAND_BOTTOM, STAND_ROWS = 74, 124, 7
PITCH_TOP = 124
CROWD_PERIOD = 48
SMALL_CLOUDS = [(14, 22, 22), (70, 12, 18), (176, 16, 20), (226, 40, 18), (122, 62, 16)]

STADIUMS = {  # sky top/bottom, seats, roof edge, barrier wall, pitch stripes, pitch lines, crowd, clouds, floodlights
    'day': dict(sky=((96, 160, 240), (200, 228, 255)), seats=(150, 156, 180), roof=(232, 236, 244),
                wall=(70, 74, 100), grass=((96, 184, 80), (110, 198, 92)), line=(244, 248, 236),
                crowd=[(232, 64, 64), (64, 112, 224), (248, 208, 40), (240, 240, 240), (60, 60, 74)],
                clouds=((255, 255, 255), (226, 236, 250), (196, 214, 240)), lights=False),
    'dusk': dict(sky=((92, 76, 168), (255, 170, 120)), seats=(120, 104, 150), roof=(236, 200, 190),
                 wall=(60, 44, 84), grass=((84, 160, 84), (96, 174, 92)), line=(248, 236, 220),
                 crowd=[(220, 72, 72), (80, 104, 200), (240, 196, 60), (236, 220, 220), (52, 44, 66)],
                 clouds=((255, 214, 196), (240, 178, 170), (196, 140, 170)), lights=True),
    'night': dict(sky=((10, 12, 34), (38, 42, 86)), seats=(44, 48, 80), roof=(90, 96, 140),
                  wall=(24, 24, 44), grass=((64, 150, 70), (76, 166, 80)), line=(236, 244, 236),
                  crowd=[(150, 60, 70), (60, 80, 150), (170, 150, 60), (140, 140, 170)],
                  clouds=None, lights=True),  # clear sky: clouds read as blobs at night
}
TIMES_OF_DAY = ['day', 'dusk', 'night']  # the order sundial_title.c indexes them in


def flash_twin(c):
    """The same shirt colour one GBA blue step away, so the ROM can find it."""
    r, g, b = c
    return (r, g, b - 8 if b >= 8 else b + 8)


def floodlight(d, x, sky):
    for r, a in [(22, 0.12), (15, 0.22), (9, 0.4)]:  # a soft glow in three steps
        c = tuple(round(s + (255 - s) * a) for s in sky)
        d.ellipse((x - r, 16 - r * 0.7, x + r, 16 + r * 0.7), fill=c + (255,))
    d.rectangle((x - 1, 18, x + 1, STAND_TOP - 4), fill=(50, 52, 76, 255))
    d.rectangle((x - 6, 12, x + 6, 19), fill=(255, 252, 228, 255))


def stadium_back(theme):
    """The opaque back layer: sky, floodlights, stands and crowd, pitch."""
    import random
    t = STADIUMS[theme]
    img = gradient(*t['sky'])
    d = ImageDraw.Draw(img)
    if t['lights']:
        for x in (14, W - 15):
            floodlight(d, x, t['sky'][0])
    d.rectangle((0, STAND_TOP, W, STAND_BOTTOM), fill=t['seats'] + (255,))
    step = (STAND_BOTTOM - STAND_TOP) // STAND_ROWS
    rnd = random.Random(1)
    for r in range(STAND_ROWS):
        y = STAND_TOP + r * step
        d.line((0, y, W, y), fill=tuple(max(0, c - 24) for c in t['seats']) + (255,))
        dots = []  # one period of this row: (x, colour)
        for x in range(rnd.randrange(3), CROWD_PERIOD, 3):
            if rnd.random() < 0.7:
                c = rnd.choice(t['crowd'])
                dots.append((x, flash_twin(c) if rnd.random() < 0.15 else c))
        for x0 in range(0, W, CROWD_PERIOD):
            for x, c in dots:
                d.rectangle((x0 + x, y + 2, x0 + x + 1, y + 3), fill=c + (255,))
    d.rectangle((0, STAND_TOP - 4, W, STAND_TOP), fill=t['roof'] + (255,))
    d.rectangle((0, STAND_BOTTOM - 4, W, STAND_BOTTOM), fill=t['wall'] + (255,))
    a, b = t['grass']
    for i, y in enumerate(range(PITCH_TOP, H, 5)):
        d.rectangle((0, y, W, y + 5), fill=(a if i % 2 else b) + (255,))
    d.rectangle((0, PITCH_TOP, W, PITCH_TOP + 1), fill=t['line'] + (255,))
    d.ellipse((30, PITCH_TOP + 10, W - 30, H + 30), outline=t['line'] + (255,), width=2)
    d.line((W // 2, PITCH_TOP + 2, W // 2, H), fill=t['line'] + (255,), width=2)
    return img


def stadium_clouds(theme):
    global CLOUDS, CLOUD_LIGHT, CLOUD_MID, CLOUD_SHADE
    colours = STADIUMS[theme]['clouds']
    if colours is None:
        return Image.new('RGBA', (CLOUD_W, H), (0, 0, 0, 0))
    saved = CLOUDS, CLOUD_LIGHT, CLOUD_MID, CLOUD_SHADE
    CLOUDS = SMALL_CLOUDS
    CLOUD_LIGHT, CLOUD_MID, CLOUD_SHADE = colours
    img = cloud_layer()
    CLOUDS, CLOUD_LIGHT, CLOUD_MID, CLOUD_SHADE = saved
    return img


def gba_colour(c):
    return (c[0] >> 3, c[1] >> 3, c[2] >> 3)


def layer_tiles(img, opaque):
    """Each 8x8 tile as a list of 64 GBA colours (None = transparent)."""
    px = img.load()
    tiles = []
    for ty in range(img.height // 8):
        for tx in range(img.width // 8):
            cells = []
            for y in range(8):
                for x in range(8):
                    c = px[tx * 8 + x, ty * 8 + y]
                    cells.append(gba_colour(c) if (opaque or c[3] >= 128) else None)
            tiles.append(cells)
    return tiles


def pack_palettes(all_tiles):
    """Greedy: each tile's colour set goes in a palette that can hold it (15
    colours + transparent), preferring the most overlap. Returns the palettes
    and, per tile, its palette number."""
    palettes = []
    sets = [frozenset(c for c in t if c is not None) for t in all_tiles]
    order = sorted(range(len(sets)), key=lambda i: -len(sets[i]))
    choice = [0] * len(sets)
    for i in order:
        need = sets[i]
        if not need:
            continue
        best = None
        for k, pal in enumerate(palettes):
            if len(pal | need) <= 15 and (best is None or len(pal & need) > len(palettes[best] & need)):
                best = k
        if best is None:
            palettes.append(set(need))
            best = len(palettes) - 1
        else:
            palettes[best] |= need
        choice[i] = best
    assert len(palettes) <= 16, f'{len(palettes)} palettes, the GBA has 16'
    return [sorted(p) for p in palettes], choice


def export_gba():
    """Every time of day as its own set (palettes, tiles, maps) in GBA_OUT/<theme>/,
    then the header: the line-up, the sets, and the flash colours to blink."""
    import os
    for theme in TIMES_OF_DAY:
        export_theme(theme)
    write_layout_header()


def export_theme(theme):
    import os
    import struct
    out_dir = GBA_OUT + theme + '/'
    os.makedirs(out_dir, exist_ok=True)
    layers = title_layers(theme)
    per_layer = [layer_tiles(img, opaque) for _, img, opaque in layers]
    flat = [t for tiles in per_layer for t in tiles]
    palettes, choice = pack_palettes(flat)

    pal_bytes = bytearray()
    for k in range(16):
        cols = [(0, 0, 0)] + (palettes[k] if k < len(palettes) else [])
        cols += [(0, 0, 0)] * (16 - len(cols))
        for r, g, b in cols:
            pal_bytes += struct.pack('<H', r | (g << 5) | (b << 10))
    open(out_dir + 'palettes.bin', 'wb').write(pal_bytes)

    base = 0
    for (name, img, _), tiles in zip(layers, per_layer):
        unique = {bytes(32): 0}  # tile 0 is blank
        data = bytearray(32)
        tilemap = [0] * (32 * 32)
        for k, t in enumerate(tiles):
            pal_no = choice[base + k]
            index = {c: i + 1 for i, c in enumerate(palettes[pal_no])} if pal_no < len(palettes) else {}
            nibbles = [index.get(c, 0) if c is not None else 0 for c in t]
            raw = bytes(nibbles[i] | (nibbles[i + 1] << 4) for i in range(0, 64, 2))
            if raw not in unique:
                unique[raw] = len(unique)
                data += raw
            tx, ty = k % (img.width // 8), k // (img.width // 8)
            tilemap[ty * 32 + tx] = unique[raw] | (pal_no << 12)
        base += len(tiles)
        assert len(unique) <= 512, f'{name}: {len(unique)} tiles'
        open(out_dir + f'{name}_tiles.bin', 'wb').write(data)
        open(out_dir + f'{name}_map.bin', 'wb').write(struct.pack(f'<{len(tilemap)}H', *tilemap))
        print(f'{theme} {name}: {len(unique)} tiles')
    print(f'{theme}: {len(palettes)} background palettes')
    # the flash twins must be colours nothing else uses, or the wrong pixels would blink
    twins = {gba_colour(flash_twin(c) + (255,)) for c in STADIUMS[theme]['crowd']}
    plain = {gba_colour(c + (255,)) for c in STADIUMS[theme]['crowd']}
    assert not twins & plain, f'{theme}: a flash colour equals a shirt colour'
    elsewhere = set()
    for name, img, opaque in layers:
        if name == 'back':  # everything but the stands
            img = img.copy()
            ImageDraw.Draw(img).rectangle((0, STAND_TOP, W, STAND_BOTTOM - 5), fill=(0, 0, 0, 0))
        elsewhere |= {c for t in layer_tiles(img, opaque) for c in t if c is not None}
    assert not twins & elsewhere, f'{theme}: a flash colour is used outside the crowd'


def write_layout_header():
    import os
    lines = ['// Generated by wildcard/art/title/build_title.py: do not edit by hand.',
             '// The title screen Pokémon, back to front: species, 64x64 frame centre, mirrored,',
             '// flier, has a second front frame.',
             'static const struct TitleMon sTitleMons[] =', '{']
    flyers = {f[0] for f in FLYERS}
    for name, fx, fy, flip in lineup_placements():
        species = 'SPECIES_' + name.replace('/', '_').upper()
        two = os.path.exists(f'graphics/pokemon/{name}/anim_front.png')
        lines.append(f'    {{ {species}, {fx + 32}, {fy + 32}, {"TRUE" if flip else "FALSE"}, '
                     f'{"TRUE" if name in flyers else "FALSE"}, {"TRUE" if two else "FALSE"} }},')
    lines.append('};')
    lines += ['', '// The stadium for each time of day (TIMES_OF_DAY order): day, dusk, night.']
    for theme in TIMES_OF_DAY:
        for kind in ('back', 'logo', 'press', 'clouds'):
            lines.append(f'static const u32 s{kind.title()}Tiles_{theme}[] = INCBIN_U32("{GBA_OUT}{theme}/{kind}_tiles.bin");')
            lines.append(f'static const u16 s{kind.title()}Map_{theme}[] = INCBIN_U16("{GBA_OUT}{theme}/{kind}_map.bin");')
        lines.append(f'static const u16 sPalettes_{theme}[] = INCBIN_U16("{GBA_OUT}{theme}/palettes.bin");')
        twins = [flash_twin(c) for c in STADIUMS[theme]['crowd']]
        rgb15 = ', '.join(f'RGB({r >> 3}, {g >> 3}, {b >> 3})' for r, g, b in twins)
        lines.append(f'static const u16 sFlashColours_{theme}[] = {{ {rgb15} }};')
    lines += ['', 'static const struct TitleStadium sStadiums[] =', '{']
    for theme in TIMES_OF_DAY:
        t = theme
        lines.append(f'    {{ sPalettes_{t}, sBackTiles_{t}, sizeof(sBackTiles_{t}), sBackMap_{t}, '
                     f'sLogoTiles_{t}, sizeof(sLogoTiles_{t}), sLogoMap_{t}, '
                     f'sPressTiles_{t}, sizeof(sPressTiles_{t}), sPressMap_{t}, '
                     f'sCloudsTiles_{t}, sizeof(sCloudsTiles_{t}), sCloudsMap_{t}, '
                     f'sFlashColours_{t}, ARRAY_COUNT(sFlashColours_{t}) }},')
    lines.append('};')
    open(LAYOUT_HEADER, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
