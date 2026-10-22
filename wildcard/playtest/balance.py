# The balance farm: plays thousands of dailies and gauntlet runs headlessly, on
# pretend dates, and writes one CSV line per battle. The game side is
# src/wildcard_sim.c; this boots copies of the ROM and save, hands the sim jobs,
# and collects what it reports. Your real pokeemerald.sav is only ever read.
#
#   python3 balance.py run NAME --mode daily --start 2026-11-01 --count 200 [--policy smart,lazy] [--workers 6]
#   python3 balance.py run NAME --mode gauntlet --start 2026-11-02 --count 100 --step 7
#   python3 balance.py report NAME            (summary; report.json for the page)
#
# Policies: expert (the battle AI's Smart Trainer plays your side: switching,
# prediction), smart (the opponents' own Basic Trainer AI), both drafting and
# swapping by base stats; lazy (the first move with PP, no swaps).
# Results land in runs/balance/NAME/results.csv.
import argparse, datetime, json, os, re, shutil, subprocess, sys, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playtest import SYM, MG, GAME, HERE

def sym(name):
    out = subprocess.run(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-nm', os.path.join(GAME, 'pokeemerald.elf')], capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3 and p[2] == name: return int(p[0], 16)
    raise SystemExit(f'{name} not in pokeemerald.elf: build first')

COLUMNS = ['mode', 'date', 'smart', 'round', 'slot', 'rule', 'event', 'won', 'turns', 'yours_left', 'theirs_left', 'yours', 'theirs']

def lua(jobs, outdir):
    sim, idle = sym('gWildcardSim'), sym('CB2_WildcardSimIdle') | 1
    rows = ','.join(f'{{{m},{s},{r},{y},{mo},{d}}}' for m, s, r, y, mo, d in jobs)
    return f'''
local jobs = {{{rows}}}
local SIM, IDLE, CB2 = {sim}, {idle}, {SYM['gMain']} + 4
local OVERWORLD, PARTY = {SYM['CB2_Overworld']}, {SYM['CB2_UpdatePartyMenu']}
local out = io.open("{os.path.join(outdir, 'results.csv')}", "a")
local frame, booted, job, ow, t, q, qt = 0, false, 0, 0, 0, {{}}, 0
local CTRL0, CHOOSE_MOVE, CURSOR = {sym('gBattlerControllerFuncs') - 0x3000000}, {sym('HandleInputChooseMove') | 1}, {sym('gMoveSelectionCursor')}
local INSTR, NOPP, nopp, target = {sym('gBattlescriptCurrInstr')}, {sym('BattleScript_SelectingMoveWithNoPP')}, false, 0
local boot = {{{{400, 3}}, {{520, 0}}}} -- START at the title, then A for CONTINUE
callbacks:add("frame", function()
  frame = frame + 1
  if frame % 240 == 0 then -- for a peek when stuck: the screen and what the battle engine is waiting on
    emu:screenshot("{os.path.join(outdir, 'now.png')}")
    local d = io.open("{os.path.join(outdir, 'now.txt')}", "w")
    local iw = function(name_off) return emu.memory.iwram:read32(name_off) end
    d:write(string.format("cb2 %x main %x ctrl %x %x exec %x instr %x outcome %d\\n", emu:read32(CB2), iw({sym('gBattleMainFunc') - 0x3000000}),
      iw({sym('gBattlerControllerFuncs') - 0x3000000}), iw({sym('gBattlerControllerFuncs') - 0x3000000 + 4}),
      emu:read32({sym('gBattleControllerExecFlags')}), emu:read32({sym('gBattlescriptCurrInstr')}), emu:read8({sym('gBattleOutcome')})))
    d:write(string.format("pc %x lr %x sp %x\\n", emu:readRegister("pc"), emu:readRegister("lr"), emu:readRegister("sp")))
    local first, last = nil, nil
    for a = 0, 0x7ffc, 4 do if emu.memory.iwram:read32(a) == 0x04e3a020 then first = first or a; last = a end end
    d:write(string.format("fill %s..%s\\n", tostring(first), tostring(last)))
    d:close()
  end
  if not booted then
    for _, b in ipairs(boot) do
      if frame == b[1] then emu:addKey(b[2]) elseif frame == b[1] + 4 then emu:clearKey(b[2]) end
    end
    if frame > 600 and (emu:read32(CB2) & 0xFFFFFFFE) == OVERWORLD then ow = ow + 1 end
    if ow > 120 then booted = true; emu:write32(CB2, IDLE) end
    return
  end
  local state = emu:read8(SIM)
  if state == 3 or job == 0 then
    if job > 0 then
      local n = emu:read16(SIM + 8)
      local s = {{}}
      for k = 0, n - 1 do s[#s + 1] = string.char(emu:read8(SIM + 10 + k)) end
      out:write(table.concat(s)); out:flush()
    end
    job = job + 1
    local j = jobs[job]
    if j == nil then
      local f = io.open("{os.path.join(outdir, 'DONE')}", "w"); f:write("ok"); f:close()
      out:close(); emu:write8(SIM, 0); job = 1e9
      return
    end
    emu:write8(SIM + 1, j[1]); emu:write8(SIM + 2, j[2]); emu:write8(SIM + 3, j[3])
    emu:write16(SIM + 4, j[4]); emu:write8(SIM + 6, j[5]); emu:write8(SIM + 7, j[6])
    emu:write8(SIM, 1)
    return
  end
  if job > #jobs then return end
  -- the lazy player: A every 16 frames (the first move with PP left); after a
  -- faint, in the party menu, step to the next one and send it out.
  -- START every 5s clears a debug assert screen (the build has asserts on; they
  -- fall back and carry on). A moves the text along; for the smart player the AI
  -- picks the moves, so A only matters to the lazy one.
  t = t + 1
  local cb = emu:read32(CB2) & 0xFFFFFFFE
  if #q == 0 and t % 300 == 0 then q = {{3}}
  elseif #q == 0 and t % 16 == 0 then
    if cb == PARTY and jobs[job][2] == 0 then q = {{1, 7, 0, 0}}
    elseif jobs[job][2] == 0 and (emu.memory.iwram:read32(CTRL0) == CHOOSE_MOVE or emu.memory.iwram:read32(CTRL0 + 8) == CHOOSE_MOVE) then
      -- choosing a move: the first one, or after "no PP left" the next one along
      -- (battler 0, or 2 in doubles)
      local b = emu.memory.iwram:read32(CTRL0) == CHOOSE_MOVE and 0 or 2
      if nopp then target = (target + 1) % 4 else target = 0 end
      nopp = false
      local cur = emu:read8(CURSOR + b)
      q = {{}}
      if (cur % 2) ~= (target % 2) then q[#q + 1] = (target % 2 == 1) and 4 or 5 end
      if (cur // 2) ~= (target // 2) then q[#q + 1] = (target >= 2) and 7 or 6 end
      q[#q + 1] = 0
    else q = {{0}} end
  end
  local instr = emu:read32(INSTR)
  if instr >= NOPP and instr < NOPP + 16 then nopp = true end
  if #q > 0 then
    qt = qt + 1
    if qt == 1 then emu:addKey(q[1]) elseif qt == 4 then emu:clearKey(q[1]) elseif qt >= 10 then qt = 0; table.remove(q, 1) end
  end
end)
'''

def dates(start, count, step):
    d = datetime.date.fromisoformat(start)
    return [d + datetime.timedelta(days=i * step) for i in range(count)]

def launch(wdir, jobs):
    os.makedirs(wdir, exist_ok=True)
    rom = os.path.join(wdir, 'game.gba')
    shutil.copy(os.path.join(GAME, 'pokeemerald.gba'), rom)
    shutil.copy(os.path.join(GAME, 'pokeemerald.sav'), os.path.join(wdir, 'game.sav'))
    if os.path.exists(os.path.join(wdir, 'DONE')): os.remove(os.path.join(wdir, 'DONE'))
    open(os.path.join(wdir, 'drive.lua'), 'w').write(lua(jobs, wdir))
    return subprocess.Popen(['nice', '-n', '10', MG, '-l', '0', '--script', os.path.join(wdir, 'drive.lua'), rom],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def jobs_done(wdir, slotted=False):
    # a gauntlet job writes several lines; count jobs by (mode, date, smart) keys, plus the slot when forced
    path = os.path.join(wdir, 'results.csv')
    if not os.path.exists(path): return set()
    return {tuple(l.split(',')[:3] + (l.split(',')[4:5] if slotted else [])) for l in open(path) if l.count(',') >= 12}

def run(args):
    root = os.path.join(HERE, 'runs', 'balance', args.name)
    os.makedirs(root, exist_ok=True)
    mode = {'daily': 0, 'gauntlet': 1, 'practice': 2}[args.mode]
    if mode == 2 and not args.slots: sys.exit('practice needs --slots (it has no opponent of its own)')
    pols = [{'lazy': 0, 'smart': 1, 'expert': 2}[p] for p in args.policy.split(',')]
    slots = [int(x) for x in args.slots.split(',')] if args.slots else []
    # the sim reads the third field as the gauntlet's last round, or for a daily the forced arena slot + 1
    extra = [args.max_round] if mode == 1 else [x + 1 for x in slots] or [0]
    all_jobs = [(mode, s, e, d.year, d.month, d.day) for d in dates(args.start, args.count, args.step) for s in pols for e in extra]
    key = lambda j: (args.mode, f'{j[3]}-{j[4]}-{j[5]}', str(j[1])) + ((str(j[2] - 1),) if slots else ())
    shards = [all_jobs[i::args.workers] for i in range(args.workers)]
    procs, last, sizes = {}, {}, {}
    t0 = time.time()
    while True:
        alive = 0
        for w, shard in enumerate(shards):
            wdir = os.path.join(root, f'w{w}')
            left = [j for j in shard if key(j) not in jobs_done(wdir, bool(slots))]
            p = procs.get(w)
            if not left:
                if p and p.poll() is None: p.kill(); p.wait()
                continue
            alive += 1
            size = os.path.getsize(os.path.join(wdir, 'results.csv')) if os.path.exists(os.path.join(wdir, 'results.csv')) else 0
            if p is None or p.poll() is not None or time.time() - last.get(w, 0) > args.stall:
                if p and p.poll() is None: p.kill(); p.wait()
                if p is not None: print(f'w{w}: {"exited" if p.poll() is not None else "stalled"}, restarting with {len(left)} jobs left', flush=True)
                procs[w] = launch(wdir, left); last[w] = time.time(); sizes[w] = size
            elif size != sizes.get(w):
                sizes[w] = size; last[w] = time.time()
        done = sum(len(jobs_done(os.path.join(root, f'w{w}'), bool(slots))) for w in range(args.workers))
        print(f'\r{done}/{len(all_jobs)} jobs, {time.time() - t0:.0f}s', end='', flush=True)
        if alive == 0: break
        time.sleep(5)
    print()
    with open(os.path.join(root, 'results.csv'), 'w') as f:
        f.write(','.join(COLUMNS) + '\n')
        for w in range(args.workers):
            p = os.path.join(root, f'w{w}', 'results.csv')
            if os.path.exists(p): f.write(open(p).read())
    print('wrote', os.path.join(root, 'results.csv'))

def names():
    species = {int(v): n.replace('SPECIES_', '').replace('_', ' ').title()
               for n, v in re.findall(r'(SPECIES_\w+) = (\d+),', open(os.path.join(GAME, 'include/constants/species.h')).read())}
    slots = {}
    for m in re.finditer(r'\[\s*(\d+)\] = \{ MAP_UNDERDOG_ARENA_\w+,\s*\d+,\s*\d+ \}, // ([^:,]+)', open(os.path.join(GAME, 'src/daily_underdog.c')).read()):
        slots[int(m.group(1))] = m.group(2).strip()
    return species, slots

def report(args):
    root = os.path.join(HERE, 'runs', 'balance', args.name)
    rows = [dict(zip(COLUMNS, l.strip().split(','))) for l in open(os.path.join(root, 'results.csv')).readlines()[1:] if l.strip()]
    species, slots = names()
    out = {'name': args.name, 'battles': len(rows)}
    pol = lambda r: {'0': 'lazy', '1': 'smart', '2': 'expert'}[r['smart']]
    daily = [r for r in rows if r['mode'] in ('daily', 'practice')]
    if daily:
        by = defaultdict(lambda: defaultdict(list))
        for r in daily: by[pol(r)][slots.get(int(r['slot']), r['slot'])].append(int(r['won']))
        out['daily'] = {p: {o: [sum(v), len(v)] for o, v in sorted(d.items())} for p, d in by.items()}
        for p, d in by.items():
            allw = [x for v in d.values() for x in v]
            print(f'DAILY {p}: won {sum(allw)}/{len(allw)} ({100 * sum(allw) / len(allw):.0f}%)')
            for o, v in sorted(d.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
                print(f'  {o:12s} {sum(v):3d}/{len(v):3d}  {100 * sum(v) / len(v):3.0f}%')
    g = [r for r in rows if r['mode'] == 'gauntlet']
    if g:
        runs = defaultdict(int)
        for r in g:
            k = (r['date'], pol(r))
            runs[k] = max(runs[k], int(r['round']) + (1 if r['won'] == '1' else 0))
        out['gauntlet'] = {}
        for p in ('expert', 'smart', 'lazy'):
            reached = [v for (d, q), v in runs.items() if q == p]
            if not reached: continue
            # reached = the round you lost in (or one past the last you won)
            survive = {n: sum(1 for v in reached if v > n) for n in range(1, 16)}
            out['gauntlet'][p] = {'runs': len(reached), 'cleared': survive}
            print(f'GAUNTLET {p}: {len(reached)} runs; share that cleared round n:')
            print('  ' + '  '.join(f'{n}:{100 * survive[n] / len(reached):.0f}%' for n in range(1, 11)))
        lost = defaultdict(lambda: defaultdict(int))
        for r in g:
            if r['won'] == '0': lost[pol(r)][f"{int(r['round']):2d} {slots.get(int(r['slot']), r['slot'])}"] += 1
        out['gauntlet_losses'] = {p: dict(sorted(d.items())) for p, d in lost.items()}
    json.dump(out, open(os.path.join(root, 'report.json'), 'w'), indent=1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    r = sp.add_parser('run'); r.add_argument('name'); r.add_argument('--mode', default='daily', choices=['daily', 'gauntlet', 'practice'])
    r.add_argument('--start', default='2026-11-01'); r.add_argument('--count', type=int, default=20); r.add_argument('--step', type=int, default=1)
    r.add_argument('--policy', default='expert,smart,lazy'); r.add_argument('--workers', type=int, default=6)
    r.add_argument('--max-round', type=int, default=12); r.add_argument('--stall', type=int, default=300)
    r.add_argument('--slots', default='', help='daily: fight these arena slots on every date instead of the date\'s opponent')
    q = sp.add_parser('report'); q.add_argument('name')
    a = ap.parse_args()
    run(a) if a.cmd == 'run' else report(a)
