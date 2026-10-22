// The page's pictures, read out of the player's own patched ROM (src/wildcard_web_art.c), so
// the site hosts no Nintendo art. build_data.py says which picture is which (schedule.art);
// the ROM says where they are: a table found by its magic, pointers into the ROM from there.
// Until there's a ROM the page shows names and colours only.

const MAGIC = 'WILDCARD WEB ART';
const ROM = 0x08000000;
const HEAD = 30; // the face crop on the week's line

function findTable(bytes) {
  const first = MAGIC.charCodeAt(0);
  outer: for (let i = 0; i + 64 < bytes.length; i += 4) {
    if (bytes[i] !== first) continue;
    for (let k = 1; k < MAGIC.length; k++) if (bytes[i + k] !== MAGIC.charCodeAt(k)) continue outer;
    return i;
  }
  return -1;
}

// 4bpp tiles, row by row, low nibble first, onto a canvas; colour 0 is see-through.
function drawTiles(bytes, at, widthTiles, heightTiles, palette) {
  const w = widthTiles * 8, h = heightTiles * 8;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  const img = ctx.createImageData(w, h);
  const rgb = palette.map((c) => [(c & 31) * 255 / 31, (c >> 5 & 31) * 255 / 31, (c >> 10 & 31) * 255 / 31]);
  for (let t = 0; t < widthTiles * heightTiles; t++) {
    const tx = (t % widthTiles) * 8, ty = Math.floor(t / widthTiles) * 8;
    for (let p = 0; p < 64; p++) {
      const byte = bytes[at + t * 32 + (p >> 1)];
      const index = p & 1 ? byte >> 4 : byte & 15;
      if (!index) continue;
      const o = ((ty + (p >> 3)) * w + tx + (p & 7)) * 4;
      img.data.set(rgb[index], o);
      img.data[o + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas;
}

function crop(src, x, y, w, h) {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  canvas.getContext('2d').drawImage(src, x, y, w, h, 0, 0, w, h);
  return canvas;
}

// Whether a canvas has something drawn at (x, y).
const opaque = (canvas) => {
  const { data } = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
  return (x, y) => data[(y * canvas.width + x) * 4 + 3] > 0;
};

// A square crop round the trainer's face, centred on the head just under its top.
function face(pic, [dx, dy] = [0, 0]) {
  const on = opaque(pic);
  let top = 0;
  while (top < pic.height && ![...Array(pic.width).keys()].some((x) => on(x, top))) top++;
  const xs = [];
  for (let y = top + 6; y < Math.min(pic.height, top + 20); y++) for (let x = 0; x < pic.width; x++) if (on(x, y)) xs.push(x);
  const cx = Math.round(xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length)) + dx;
  return crop(pic, cx - HEAD / 2, top + dy, HEAD, HEAD);
}

// A party icon's two frames, both lifted so the first one's middle is the frame's: icons stand
// low in their frames, and the mascot should line up with the wordmark.
function centred(sheet) {
  const on = opaque(sheet);
  const rows = [...Array(32).keys()].filter((y) => [...Array(32).keys()].some((x) => on(x, y)));
  const lift = rows.length ? Math.floor((rows[0] + rows[rows.length - 1] + 1) / 2) - 16 : 0;
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  for (const frame of [0, 32]) ctx.drawImage(sheet, 0, frame, 32, 32, 0, frame - lift, 32, 32);
  return canvas;
}

// Reads a ROM (bytes) with the page's index (schedule.art); null if it has no table (Emerald, or
// a Wild Card from before it). Each picture comes back as a data URL, made once.
export function readArt(bytes, index) {
  const table = findTable(bytes);
  if (table < 0 || !index) return null;
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const u32 = (o) => v.getUint32(o, true);
  const ptr = (o) => u32(o) - ROM;
  const palette = (o) => Array.from({ length: 16 }, (_, i) => v.getUint16(o + i * 2, true));
  const [species, iconPals, pics, picCount] = [ptr(table + 0x14), ptr(table + 0x18), ptr(table + 0x1C), u32(table + 0x20)];
  const layout = index.species;
  const cache = new Map();
  const once = (key, make) => {
    if (!cache.has(key)) {
      try { cache.set(key, make()); } catch { cache.set(key, ''); }
    }
    return cache.get(key);
  };
  const trainerCanvas = (row) => once(`t${row}`, () => drawTiles(bytes, ptr(pics + row * 8), 8, 8, palette(ptr(pics + row * 8 + 4))));
  const iconCanvas = (n) => once(`i${n}`, () => {
    const at = species + n * layout.size;
    const pal = (bytes[at + layout.palByte] >> layout.palShift) & 7;
    return drawTiles(bytes, ptr(at + layout.icon), 4, 8, palette(iconPals + pal * 32));
  });
  const url = (key, make) => once(key, () => make().toDataURL());
  const row = (r) => (r === undefined || r >= picCount ? null : r);
  return {
    trainer: (r) => (row(r) === null ? '' : url(`T${r}`, () => trainerCanvas(r))),
    head: (r) => (row(r) === null ? '' : url(`H${r}`, () => face(trainerCanvas(r), index.nudge[r]))),
    icon: (n) => url(`I${n}`, () => crop(iconCanvas(n), 0, 0, 32, 32)),
    mascot: (n) => (n === undefined ? '' : url(`M${n}`, () => centred(iconCanvas(n)))),
  };
}
