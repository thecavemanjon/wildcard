// The web player: today's page from data/schedule.json (read out of the ROM by
// build_data.py), and the game itself in mGBA via Nostalgist. The ROM and the
// save stay in this browser (IndexedDB); nothing is uploaded.
import { Nostalgist } from 'https://cdn.jsdelivr.net/npm/nostalgist@0.22.0/+esm';

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
  $('hero').style.backgroundImage = `url(art/clouds_${theme}.png), url(art/stadium_${theme}.png)`;
}

function stop(day, date, label, colour, isToday) {
  const el = document.createElement('div');
  el.className = 'stop' + (isToday ? ' today' : '') + (day.event ? ' event' : '');
  el.style.setProperty('--c', colour);
  const rule = day.event ? `${day.event} event` : day.rule ? titleCase(day.rule) : '';
  el.innerHTML = `<span class="head" style="background-image:url(art/head_${day.slot}.png)"></span>
    <span class="d"><span class="day"></span><span class="nm"></span>${rule ? '<span class="rule"></span>' : ''}</span>`;
  el.querySelector('.day').textContent = isToday ? `${label} · today` : label;
  el.querySelector('.nm').textContent = titleCase(day.trainer);
  if (rule) el.querySelector('.rule').textContent = rule;
  return el;
}

function party(team) {
  const list = $('party');
  list.replaceChildren();
  for (const mon of team) {
    const li = document.createElement('li');
    li.title = mon.moves.join(', ');
    li.innerHTML = `<img class="ic" src="art/icon_${mon.species}.png" alt="">
      <span class="nm"><span></span><small>Lv 50</small></span>
      <span class="ty">${mon.types.map((t) => `<img src="art/type_${t.toLowerCase()}.png" alt="${t}">`).join('')}</span>`;
    li.querySelector('.nm span').textContent = mon.name;
    list.append(li);
  }
}

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
  document.title = `Wild Card: ${titleCase(today.trainer)} today`;

  const stops = $('stops');
  stops.replaceChildren();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
    const day = schedule.days[iso(d)];
    if (day) stops.append(stop(day, d, `${DAYS[d.getDay()]} ${d.getDate()}`, colour(day.slot), i === 0));
  }
  party(today.team);
}

// Gender and wardrobe costume out of an Emerald save: two slots of 14 4 KB sectors, each
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
  const sector = best.sectors[1 + Math.floor(layout.costume / 3968)];
  return {
    gender: v.getUint8(best.sectors[0] + layout.gender),
    costume: sector === undefined ? 0 : v.getUint16(sector + (layout.costume % 3968), true),
  };
}

// You in the VS bar: your costume, else your gender's look, else (no save yet) Emerald's boy.
let schedule = null;
async function showYou() {
  if (!schedule) return;
  const sram = await getFile('sram');
  const me = sram && schedule.save ? readPlayer(await sram.arrayBuffer(), schedule.save) : null;
  $('you-pic').src = me && schedule.costumes.includes(me.costume) ? `art/costume_${me.costume}.png`
    : `art/player_${me && me.gender ? 'may' : 'brendan'}.png`;
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

// A GBA ROM has 0x96 at 0xB2 and a game code at 0xAC; Wild Card keeps Emerald's (BPEE).
async function checkRom(file) {
  const head = new Uint8Array(await file.slice(0, 0xC0).arrayBuffer());
  if (file.size < 0x100000 || head[0xB2] !== 0x96) return 'That doesn\'t look like a GBA ROM.';
  const code = String.fromCharCode(...head.slice(0xAC, 0xB0));
  if (code !== 'BPEE') return `That ROM's game code is ${code}; Wild Card's is BPEE.`;
  return '';
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

async function launch() {
  const rom = await getFile('rom');
  if (!rom) return;
  const sram = await getFile('sram');
  $('loader-title').textContent = 'Starting…';
  $('loader-note').textContent = 'The first time takes a few seconds while the emulator downloads.';
  $('play-btn').hidden = true;
  $('rom-label').hidden = true;
  $('sav-label').hidden = true;
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
    showLoader(true, `The emulator didn't start: ${e.message || e}`);
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

function showLoader(hasRom, error = '') {
  $('loader').hidden = false;
  $('loader-title').textContent = hasRom ? 'Ready when you are' : 'Bring your Wild Card ROM';
  $('loader-note').textContent = hasRom
    ? 'Your ROM and save are kept in this browser.'
    : 'It stays in this browser. Nothing is uploaded.';
  $('play-btn').hidden = !hasRom;
  $('rom-label').hidden = false;
  $('rom-label').firstChild.textContent = hasRom ? 'Use a different ROM' : 'Choose ROM (.gba)';
  $('rom-label').classList.toggle('big', !hasRom);
  $('rom-label').classList.toggle('small', hasRom);
  $('sav-label').hidden = false;
  $('loader-error').textContent = error;
}

$('rom-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const problem = await checkRom(file);
  if (problem) { showLoader(Boolean(await getFile('rom')), problem); return; }
  await putFile('rom', file);
  showLoader(true);
});

$('sav-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  await putFile('sram', file);
  showYou();
  showLoader(Boolean(await getFile('rom')), '');
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

// ---- start ----

// ?dev (serve.py only): the repo's built ROM, and its save if this browser has none, then straight in.
async function devStart() {
  const rom = await fetch('dev/rom.gba');
  if (!rom.ok) return;
  await putFile('rom', await rom.blob());
  if (!(await getFile('sram'))) {
    const sav = await fetch('dev/save.sav');
    if (sav.ok) { await putFile('sram', await sav.blob()); showYou(); }
  }
  launch();
}

const now = new Date();
loadSchedule()
  .then((s) => { schedule = s; render(s, now); showYou(); })
  .catch((e) => { $('stops').innerHTML = `<p class="note"></p>`; $('stops').firstChild.textContent = e.message; });
getFile('rom').then((rom) => showLoader(Boolean(rom)));
if (new URLSearchParams(location.search).has('dev')) devStart();
