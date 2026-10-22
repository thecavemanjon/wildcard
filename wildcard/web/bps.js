// Applies a BPS patch in the browser: the player's own Emerald in, Wild Card out. The same
// format and checks as wildcard/release/bps.py (which makes the patch).

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

export function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

const u32 = (b, at) => (b[at] | b[at + 1] << 8 | b[at + 2] << 16 | b[at + 3] << 24) >>> 0;

// The CRC32 of the ROM a patch expects, so the page can say "wrong ROM" before patching.
export const sourceCrc = (patch) => u32(patch, patch.length - 12);

export function applyBps(source, patch) {
  let p = 4;
  const read = () => {
    let n = 0, shift = 1;
    for (;;) {
      const x = patch[p++];
      n += (x & 0x7F) * shift;
      if (x & 0x80) return n;
      shift *= 128;
      n += shift;
    }
  };
  if (String.fromCharCode(...patch.subarray(0, 4)) !== 'BPS1') throw new Error('That isn\'t a BPS patch.');
  if (crc32(patch.subarray(0, patch.length - 4)) !== u32(patch, patch.length - 4)) throw new Error('The patch is damaged.');
  if (crc32(source) !== sourceCrc(patch)) throw new Error('That isn\'t the Emerald this patch is for.');
  read(); // source size
  const target = new Uint8Array(read());
  const metadata = read(); // not `p += read()`: that adds to p as it was before read() moved it
  p += metadata;
  let o = 0, srcRel = 0, tgtRel = 0;
  const end = patch.length - 12;
  while (p < end) {
    const x = read(), mode = x & 3, n = Math.floor(x / 4) + 1;
    if (mode === 0) {
      target.set(source.subarray(o, o + n), o);
    } else if (mode === 1) {
      target.set(patch.subarray(p, p + n), o);
      p += n;
    } else {
      const d = read(), delta = d & 1 ? -Math.floor(d / 2) : Math.floor(d / 2);
      if (mode === 2) {
        srcRel += delta;
        target.set(source.subarray(srcRel, srcRel + n), o);
        srcRel += n;
      } else {
        tgtRel += delta;
        for (let k = 0; k < n; k++) target[o + k] = target[tgtRel + k]; // overlapping on purpose: runs
        tgtRel += n;
      }
    }
    o += n;
  }
  if (crc32(target) !== u32(patch, patch.length - 8)) throw new Error('The patched game came out wrong.');
  return target;
}
