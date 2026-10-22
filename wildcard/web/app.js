// The web player: today's page from data/schedule.json (read out of the ROM by
// build_data.py), and the game itself in mGBA via Nostalgist. The ROM and the
// save stay in this browser (IndexedDB); nothing is uploaded.
import { Nostalgist } from 'https://cdn.jsdelivr.net/npm/nostalgist@0.22.0/+esm';
import { applyBps, crc32 } from './bps.js';

const $ = (id) => document.getElementById(id);
const pad = (n) => String(n).padStart(2, '0');
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const titleCase = (s) => s.toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const SAVE_EVERY_MS = 2000;

// ---- the page: today, the week, your six ----

async function loadSchedule() {
  const res = await fetch('data/schedule.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('No data/schedule.json: run python3 wildcard/web/build_data.py');
  return res.json();
}

function banner(now) {
  const h = now.getHours();
  const theme = h >= 6 && h < 17 ? 'day' : h >= 17 && h < 20 ? 'dusk' : 'night';
  $('top').style.backgroundImage = `url(art/stadium_${theme}.png)`;
}

// A stop on a metro line of faces: a day of the week, or a round of the gauntlet.
function stop(slot, trainer, label, note, colour, big) {
  const el = document.createElement('div');
  el.className = 'stop' + (big ? ' today' : '');
  el.style.setProperty('--c', colour);
  el.innerHTML = `<span class="head" style="background-image:url(art/head_${slot}.png)"></span>
    <span class="d"><span class="day"></span><span class="nm"></span>${note ? '<span class="rule"></span>' : ''}</span>`;
  el.querySelector('.day').textContent = label;
  el.querySelector('.nm').textContent = titleCase(trainer);
  if (note) el.querySelector('.rule').textContent = note;
  return el;
}

function day(day, label, colour, isToday) {
  const el = stop(day.slot, day.trainer, isToday ? `${label} · today` : label,
                  day.event ? `${day.event} event` : day.rule ? titleCase(day.rule) : '', colour, isToday);
  el.classList.toggle('event', Boolean(day.event));
  return el;
}

function party(team, list = $('party')) {
  list.replaceChildren();
  for (const mon of team) {
    const li = document.createElement('li');
    li.title = (mon.moves || []).join(', ');
    li.innerHTML = `<img class="ic" src="art/icon_${mon.species}.png" alt="">
      <span class="nm"><span></span><small>Lv 50</small></span>
      <span class="ty">${mon.types.map((t) => `<img src="art/type_${t.toLowerCase()}.png" alt="${t}">`).join('')}</span>`;
    li.querySelector('.nm span').textContent = mon.name;
    list.append(li);
  }
}

// This week's gauntlet (build_data.py, from the ROM): the ladder to Red takes the week's place
// on the left, and the draft of six takes your daily six's.
const SHINY_ROUND = 5; // GAUNTLET_REWARD_ROUND: get this far and a shiny line unlocks
function gauntlet(week, colour) {
  if (!week) return;
  $('g-title').textContent = `Gauntlet · week ${week.week}`;
  $('g-ladder').replaceChildren(...week.ladder.map((r) => {
    const type = r.type === 'None' ? '' : r.type;
    const note = r.round === SHINY_ROUND ? [type, 'shiny line'].filter(Boolean).join(' · ') : type;
    const el = stop(r.slot, r.trainer, `Round ${r.round}`, note, colour(r.slot), r.round === week.ladder.length);
    el.dataset.round = r.round;
    return el;
  }));
  party(week.draft, $('g-draft'));
}

// Daily or Gauntlet, from the menu: the same page either way, so the game keeps running.
function setMode(mode) {
  document.body.classList.toggle('gauntlet', mode === 'gauntlet');
  for (const a of document.querySelectorAll('.menu [data-mode]')) a.classList.toggle('on', a.dataset.mode === mode);
  history.replaceState(null, '', location.pathname + location.search + (mode === 'gauntlet' ? '#gauntlet' : ''));
  if (mode === 'gauntlet') showYou(); // the ladder was hidden, so centre it on your round now
}
for (const a of document.querySelectorAll('.menu [data-mode]')) {
  a.addEventListener('click', (e) => { e.preventDefault(); setMode(a.dataset.mode); });
}
setMode(location.hash === '#gauntlet' ? 'gauntlet' : 'daily');

function render(schedule, now) {
  const today = schedule.days[iso(now)];
  banner(now);
  if (!today) {
    $('stops').innerHTML = '<p class="note">No data for today. Run build_data.py again.</p>';
    return;
  }
  const colour = (slot) => schedule.colours[slot] || '#945221';
  document.documentElement.style.setProperty('--t', colour(today.slot));
  $('opp-name').textContent = titleCase(today.trainer);
  $('opp-pic').src = `art/trainer_${today.slot}.png`;
  $('mascot').style.backgroundImage = `url(art/mascot_${today.slot}.png)`;
  document.title = `Wild Card: ${titleCase(today.trainer)} today`;

  const stops = $('stops');
  stops.replaceChildren();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
    const entry = schedule.days[iso(d)];
    if (entry) stops.append(day(entry, `${DAYS[d.getDay()]} ${d.getDate()}`, colour(entry.slot), i === 0));
  }
  party(today.team);
  gauntlet(schedule.gauntlet && schedule.gauntlet[today.week], colour);
}

// The game's own text encoding (include/constants/characters.h), enough for a player's name.
const GAME_CHARS = { 0x00: ' ', 0x1B: 'é', 0x2D: '&', 0xAB: '!', 0xAC: '?', 0xAD: '.', 0xAE: '-', 0xB0: '…',
                     0xB1: '“', 0xB2: '”', 0xB3: '‘', 0xB4: '’', 0xB5: '♂', 0xB6: '♀', 0xB8: ',', 0xBA: '/', 0xF0: ':' };
function gameText(bytes) {
  let out = '';
  for (const b of bytes) {
    if (b === 0xFF) break; // end of string
    if (b >= 0xBB && b <= 0xD4) out += String.fromCharCode(65 + b - 0xBB);
    else if (b >= 0xD5 && b <= 0xEE) out += String.fromCharCode(97 + b - 0xD5);
    else if (b >= 0xA1 && b <= 0xAA) out += String.fromCharCode(48 + b - 0xA1);
    else out += GAME_CHARS[b] ?? '';
  }
  return out.trim();
}

// Name, gender and wardrobe costume out of an Emerald save: two slots of 14 4 KB sectors, each
// with its id, a signature and a save counter in the footer; the newer slot wins. SaveBlock2
// is sector 0, SaveBlock1 runs on from sector 1, 3968 bytes of data per sector. The offsets
// come from the game's headers (build_data.py).
function readPlayer(buf, layout) {
  const v = new DataView(buf);
  let best = null;
  for (const base of [0, 14]) {
    const sectors = {};
    let counter = -1;
    for (let i = 0; i < 14; i++) {
      const o = (base + i) * 0x1000;
      if (o + 0x1000 > buf.byteLength || v.getUint32(o + 0xFF8, true) !== 0x08012025) continue;
      sectors[v.getUint16(o + 0xFF4, true)] = o;
      counter = Math.max(counter, v.getUint32(o + 0xFFC, true));
    }
    if (sectors[0] !== undefined && (!best || counter > best.counter)) best = { sectors, counter };
  }
  if (!best) return null;
  const u16 = (offset) => {
    const at = best.sectors[1 + Math.floor(offset / 3968)];
    return at === undefined ? 0 : v.getUint16(at + (offset % 3968), true);
  };
  const sector = best.sectors[1 + Math.floor(layout.costume / 3968)];
  return {
    gauntletWeek: layout.gauntletWeek ? u16(layout.gauntletWeek) : 0,
    gauntletBest: layout.gauntletBest ? u16(layout.gauntletBest) : 0,
    name: gameText(new Uint8Array(buf, best.sectors[0] + layout.name, 8)), // 7 letters and the end mark
    gender: v.getUint8(best.sectors[0] + layout.gender),
    costume: sector === undefined ? 0 : v.getUint16(sector + (layout.costume % 3968), true),
  };
}

// You in the VS bar: your name (else YOU), and your costume, else your gender's look, else
// (no save yet) Emerald's boy.
let schedule = null;
async function showYou() {
  if (!schedule) return;
  const sram = await getFile('sram');
  const me = sram && schedule.save ? readPlayer(await sram.arrayBuffer(), schedule.save) : null;
  $('you-pic').src = me && schedule.costumes.includes(me.costume) ? `art/costume_${me.costume}.png`
    : `art/player_${me && me.gender ? 'may' : 'brendan'}.png`;
  $('you-name').textContent = me && me.name ? me.name : 'You';
  // the gauntlet: your furthest round this week, as the PC shows it (the save keeps it with its week)
  const today = schedule.days[iso(new Date())];
  const best = me && today && String(me.gauntletWeek) === today.week ? me.gauntletBest : 0;
  $('g-best').hidden = !best;
  $('g-best').textContent = `Your best this week: round ${best}`;
  for (const li of $('g-ladder').children) li.classList.toggle('beaten', Number(li.dataset.round) < best);
  // where the ladder is a sideways strip (phones), open it at the round you're on
  const at = $('g-ladder').children[Math.max(best, 1) - 1];
  if (at) $('g-ladder').scrollLeft = at.offsetLeft - ($('g-ladder').clientWidth - at.offsetWidth) / 2;
}

// ---- the ROM and the save, kept in IndexedDB ----

function db() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('wildcard', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('files');
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function getFile(key) {
  const store = (await db()).transaction('files').objectStore('files');
  return new Promise((resolve) => {
    const req = store.get(key);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => resolve(null);
  });
}

async function putFile(key, blob) {
  const tx = (await db()).transaction('files', 'readwrite');
  tx.objectStore('files').put(blob, key);
  return new Promise((resolve, reject) => { tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); });
}

// ---- the game: the player's own Emerald, patched into Wild Card here ----

let patchInfo = null; // data/patch.json: the patch's CRCs and size (make_patch.py); none in a dev setup

async function loadPatchInfo() {
  const res = await fetch('data/patch.json', { cache: 'no-store' }).catch(() => null);
  patchInfo = res && res.ok ? await res.json() : null;
}

// 'ready' (Wild Card, current), 'update' (an older Wild Card, and the Emerald to patch the new one
// from), 'emerald' (only the Emerald so far) or 'none'.
async function gameState() {
  const [rom, romCrc, emerald] = await Promise.all([getFile('rom'), getFile('rom-crc'), getFile('emerald')]);
  if (rom && (!patchInfo || romCrc === patchInfo.target_crc || !emerald)) return 'ready';
  if (emerald) return rom ? 'update' : 'emerald';
  return 'none';
}

// A GBA ROM has 0x96 at 0xB2 and a game code at 0xAC: Emerald's is BPEE, and Wild Card keeps it.
// The CRC tells a clean Emerald (kept, to patch) from Wild Card already patched (used as it is).
async function takeRom(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  if (bytes.length < 0x100000 || bytes[0xB2] !== 0x96) return 'That doesn\'t look like a GBA ROM.';
  const code = String.fromCharCode(...bytes.subarray(0xAC, 0xB0));
  if (code !== 'BPEE') return `That isn't Pokémon Emerald (its game code is ${code}).`;
  if (!patchInfo) { await putFile('rom', file); return ''; } // a dev setup with no patch: take it as Wild Card
  const crc = crc32(bytes);
  if (crc === patchInfo.source_crc) { await putFile('emerald', file); return ''; }
  if (crc === patchInfo.target_crc) { await putFile('rom', file); await putFile('rom-crc', crc); return ''; }
  return 'That Emerald has been changed (a hack, another version or a bad dump). Wild Card needs a clean English Pokémon Emerald.';
}

async function patchEmerald() {
  const emerald = new Uint8Array(await (await getFile('emerald')).arrayBuffer());
  const res = await fetch('data/wildcard.bps');
  if (!res.ok) throw new Error('The Wild Card patch didn\'t download. Try again in a moment.');
  const reader = res.body.getReader(), parts = [];
  for (let got = 0; ;) {
    const { done, value } = await reader.read();
    if (done) break;
    parts.push(value);
    got += value.length;
    $('loader-note').textContent = `Downloading the patch: ${(got / 1e6).toFixed(1)} of ${(patchInfo.size / 1e6).toFixed(1)} MB`;
  }
  const patch = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  parts.reduce((o, p) => (patch.set(p, o), o + p.length), 0);
  $('loader-note').textContent = 'Patching…';
  await new Promise((r) => setTimeout(r, 50)); // let that show before the work
  const rom = applyBps(emerald, patch); // checks the Emerald, the patch and the result
  await putFile('rom', new Blob([rom]));
  await putFile('rom-crc', patchInfo.target_crc);
}

// ---- the emulator ----

let emu = null;
let saving = false;
let lastSram = null;

const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

// Copies the game's save out of the emulator into IndexedDB when it has changed. A reload
// can't wait for this, so it runs every couple of seconds: at 15 s an in-game save followed
// by a quick refresh was lost.
async function saveNow() {
  if (!emu || saving) return;
  saving = true;
  try {
    const sram = await emu.saveSRAM();
    const bytes = new Uint8Array(await sram.arrayBuffer());
    if (bytes.length > 0 && !(lastSram && same(bytes, lastSram))) {
      await putFile('sram', sram);
      lastSram = bytes;
      showYou(); // a new costume from the wardrobe shows up here too
    }
  } catch (e) {
    console.warn('save failed', e);
  } finally {
    saving = false;
  }
}

// Play: patch first if the game needs making or updating, then start it.
async function launch() {
  $('play-btn').hidden = true;
  $('rom-label').hidden = true;
  $('sav-label').hidden = true;
  $('loader-error').textContent = '';
  if (['emerald', 'update'].includes(await gameState())) {
    $('loader-title').textContent = 'Making Wild Card…';
    try {
      await patchEmerald();
    } catch (e) {
      showLoader(await gameState(), e.message);
      return;
    }
  }
  start();
}

async function start() {
  const rom = await getFile('rom');
  if (!rom) return;
  const sram = await getFile('sram');
  $('loader-title').textContent = 'Starting…';
  $('loader-note').textContent = 'The first time takes a few seconds while the emulator downloads.';
  try {
    emu = await Nostalgist.launch({
      element: $('game'),
      core: 'mgba',
      rom: { fileName: 'wildcard.gba', fileContent: rom },
      sram: sram ? { fileName: 'wildcard.srm', fileContent: sram } : undefined,
      retroarchConfig: {
        input_player1_a: 'x', input_player1_b: 'z',
        input_player1_start: 'enter', input_player1_select: 'shift',
        input_player1_l: 'a', input_player1_r: 's',
        input_toggle_fast_forward: 'space',
        input_exit_emulator: 'nul', input_menu_toggle: 'nul', input_toggle_fullscreen: 'nul',
        video_smooth: false,
      },
    });
  } catch (e) {
    showLoader('ready', `The emulator didn't start: ${e.message || e}`);
    return;
  }
  $('loader').hidden = true;
  $('save-btn').disabled = false;
  // RetroArch draws at the box's size times devicePixelRatio, so the canvas buffer has to be that
  // size too: at CSS size on a Retina screen the game showed zoomed 2x into the bottom left.
  // Nostalgist sets it back to CSS size as it starts, hence the repeats.
  const fit = () => {
    const box = $('screen').getBoundingClientRect();
    emu.resize({ width: Math.round(box.width * devicePixelRatio), height: Math.round(box.height * devicePixelRatio) });
  };
  new ResizeObserver(fit).observe($('screen'));
  for (const ms of [0, 250, 1000, 3000]) setTimeout(fit, ms);
  setInterval(saveNow, SAVE_EVERY_MS);
}

const LOADER = {
  none: ['Bring your Pokémon Emerald', 'Your own English Emerald (.gba). Wild Card is patched onto it here, in this browser; nothing is uploaded.'],
  emerald: ['Ready to make Wild Card', 'Press Play: the patch downloads once and goes onto your Emerald here.'],
  update: ['Wild Card has an update', 'Press Play to patch the new version onto your Emerald. Your save carries over.'],
  ready: ['Ready when you are', 'Your game and save are kept in this browser.'],
};

function showLoader(state, error = '') {
  const [title, note] = LOADER[state];
  const ready = state !== 'none';
  $('loader').hidden = false;
  $('loader-title').textContent = title;
  $('loader-note').textContent = note;
  $('play-btn').hidden = !ready;
  $('rom-label').hidden = false;
  $('rom-label').firstChild.textContent = ready ? 'Use a different ROM' : 'Choose Emerald (.gba)';
  $('rom-label').classList.toggle('big', !ready);
  $('rom-label').classList.toggle('small', ready);
  $('sav-label').hidden = false;
  $('loader-error').textContent = error;
}

$('rom-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const problem = await takeRom(file);
  showLoader(await gameState(), problem);
});

$('sav-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  await putFile('sram', file);
  showYou();
  showLoader(await gameState(), '');
  $('loader-note').textContent = `Save loaded (${file.name}). It replaces the one kept here.`;
});

$('play-btn').addEventListener('click', launch);

$('save-btn').addEventListener('click', async () => {
  await saveNow();
  const sram = await getFile('sram');
  if (!sram) return;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(sram);
  a.download = 'wildcard.sav';
  a.click();
  URL.revokeObjectURL(a.href);
});

$('full-btn').addEventListener('click', () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else $('screen').requestFullscreen();
});

document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') saveNow(); });
window.addEventListener('pagehide', saveNow);

// ---- the on-screen buttons (touch screens only; .pad in style.css) ----

function hold(button, down) {
  if (!emu) return;
  emu[down ? 'pressDown' : 'pressUp'](button); // the names are retroarchConfig's input_player1_*
  if (down && navigator.vibrate) navigator.vibrate(8);
}

for (const el of document.querySelectorAll('.pad [data-btn]')) {
  const up = () => {
    if (!el.classList.contains('down')) return;
    el.classList.remove('down');
    hold(el.dataset.btn, false);
  };
  el.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    el.setPointerCapture(e.pointerId);
    el.classList.add('down');
    hold(el.dataset.btn, true);
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) el.addEventListener(type, up);
}

// The D-pad is one surface: the thumb's angle from its centre picks one of eight directions,
// so sliding round it changes direction without lifting.
const dpad = $('dpad');
let dirs = new Set();
function steer(e) {
  const box = dpad.getBoundingClientRect();
  const x = e.clientX - (box.left + box.width / 2), y = e.clientY - (box.top + box.height / 2);
  const next = new Set();
  if (Math.hypot(x, y) > box.width * 0.12) { // a small dead zone in the middle
    const angle = Math.atan2(y, x) * 180 / Math.PI; // 0 is right, 90 is down
    if (angle > -67.5 && angle < 67.5) next.add('right');
    if (angle > 22.5 && angle < 157.5) next.add('down');
    if (angle > 112.5 || angle < -112.5) next.add('left');
    if (angle > -157.5 && angle < -22.5) next.add('up');
  }
  for (const d of dirs) if (!next.has(d)) { hold(d, false); dpad.classList.remove(`go-${d}`); }
  for (const d of next) if (!dirs.has(d)) { hold(d, true); dpad.classList.add(`go-${d}`); }
  dirs = next;
}
function letGo() {
  for (const d of dirs) { hold(d, false); dpad.classList.remove(`go-${d}`); }
  dirs = new Set();
}
dpad.addEventListener('pointerdown', (e) => { e.preventDefault(); dpad.setPointerCapture(e.pointerId); steer(e); });
dpad.addEventListener('pointermove', (e) => { if (dpad.hasPointerCapture(e.pointerId)) steer(e); });
for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) dpad.addEventListener(type, letGo);
$('pad').addEventListener('contextmenu', (e) => e.preventDefault());
// iPhone Safari zooms on a double tap of the D-pad (a plain div) whatever touch-action says;
// cancelling the touch itself stops it, and the buttons run on pointer events, which still come.
for (const type of ['touchstart', 'touchend']) $('pad').addEventListener(type, (e) => e.preventDefault(), { passive: false });

// ---- start ----

// ?dev (serve.py only): the repo's dev build and its save (if this browser has none), straight in.
// ?dev=patch: the player's way in, from the Emerald serve.py --emerald hands over: forgets the
// game, takes the Emerald as if picked, and patches it on Play.
async function devStart(mode) {
  if (mode === 'patch') {
    const emerald = await fetch('dev/emerald.gba');
    if (!emerald.ok) { showLoader('none', 'Start serve.py with --emerald PATH for ?dev=patch.'); return; }
    await putFile('rom', null);
    await putFile('rom-crc', null);
    const problem = await takeRom(await emerald.blob()); // before gameState(), which should see it
    showLoader(await gameState(), problem);
    return;
  }
  const rom = await fetch('dev/rom.gba');
  if (!rom.ok) return;
  await putFile('rom', await rom.blob());
  if (!(await getFile('sram'))) {
    const sav = await fetch('dev/save.sav');
    if (sav.ok) { await putFile('sram', await sav.blob()); showYou(); }
  }
  start();
}

const now = new Date();
loadSchedule()
  .then((s) => { schedule = s; render(s, now); showYou(); })
  .catch((e) => { $('stops').innerHTML = `<p class="note"></p>`; $('stops').firstChild.textContent = e.message; });
const dev = new URLSearchParams(location.search).get('dev');
loadPatchInfo().then(async () => {
  showLoader(await gameState());
  if (dev !== null) devStart(dev);
});
