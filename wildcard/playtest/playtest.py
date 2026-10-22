# Plays a COPY of the built ROM and of the save headlessly, from a list of steps,
# taking screenshots. Your real pokeemerald.sav is only ever read.
#
#   ./build_mgba.sh                      (once: headless mGBA with Lua, in mgba/)
#   python3 playtest.py NAME steps/FILE.txt [timeout seconds]
#   python3 sheet.py runs/NAME           (contact sheet of the screenshots)
#
# Steps, one per line: "wait N" (frames), "A" / "B" / "START" / "UP 3" (presses),
# "hold RIGHT 40" (frames), "shot NAME", "autobattle MAXFRAMES" (A to attack; in
# the party menu after a faint, send out the next one; stops back in the
# overworld), "setvar 40FC 5" (test only: write a save var, in hex), "shiny 170"
# (test only: unlock that species as a shiny follower).
import sys, os, subprocess, time, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
SP = HERE
GAME = os.path.expanduser('~/games/wildcard/')
MG = os.environ.get('MGBA_HEADLESS', os.path.join(HERE, 'mgba', 'build', 'mgba-headless'))
KEYS = {'A': 0, 'B': 1, 'SELECT': 2, 'START': 3, 'RIGHT': 4, 'LEFT': 5, 'UP': 6, 'DOWN': 7, 'R': 8, 'L': 9}

def symbols():
    import subprocess
    out = subprocess.run(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-nm', os.path.expanduser('~/games/wildcard/pokeemerald.elf')], capture_output=True, text=True).stdout
    sym = {}
    for line in out.splitlines():
        a, _, n = line.split(' ', 2) if line.count(' ') >= 2 else (None, None, None)
        if n in ('CB2_UpdatePartyMenu', 'CB2_Overworld', 'BattleMainCB2', 'gSaveBlock1Ptr', 'gSaveBlock2Ptr', 'gMain'): sym[n] = '0x' + a
    return sym
SYM = symbols()

def lua(steps, outdir):
    ops = []
    for s in steps:
        p = s.split()
        if p[0] == 'wait': ops.append(('wait', int(p[1])))
        elif p[0] == 'shot': ops.append(('shot', os.path.join(outdir, p[1] + '.png')))
        elif p[0] == 'hold': ops.append(('hold', KEYS[p[1]], int(p[2])))
        elif p[0] == 'autobattle': ops.append(('auto', int(p[1])))
        elif p[0] == 'setvar': ops.append(('setvar', int(p[1], 16), int(p[2])))
        elif p[0] == 'shiny': ops.append(('shiny', int(p[1])))
        else:
            n = int(p[1]) if len(p) > 1 else 1
            for _ in range(n): ops.append(('press', KEYS[p[0]]))
    body = []
    for o in ops:
        if o[0] == 'wait': body.append(f'{{"wait",{o[1]}}}')
        elif o[0] == 'shot': body.append(f'{{"shot","{o[1]}"}}')
        elif o[0] == 'hold': body.append(f'{{"hold",{o[1]},{o[2]}}}')
        elif o[0] == 'auto': body.append(f'{{"auto",{o[1]}}}')
        elif o[0] == 'setvar': body.append(f'{{"setvar",{o[1]},{o[2]}}}')
        elif o[0] == 'shiny': body.append(f'{{"shiny",{o[1]}}}')
        else: body.append(f'{{"press",{o[1]}}}')
    done = os.path.join(outdir, 'DONE')
    return f'''
local ops = {{{",".join(body)}}}
local CB2 = {SYM['gMain']} + 4
local PARTY, OVERWORLD, BATTLE = {SYM['CB2_UpdatePartyMenu']}, {SYM['CB2_Overworld']}, {SYM['BattleMainCB2']}
local q, qt, ow, fought = {{}}, 0, 0, false
local i, t, phase = 1, 0, 0
callbacks:add("frame", function()
  local o = ops[i]
  if o == nil then
    if phase ~= 99 then local f = io.open("{done}", "w"); f:write("ok"); f:close(); phase = 99 end
    return
  end
  if o[1] == "wait" then
    t = t + 1; if t >= o[2] then t = 0; i = i + 1 end
  elseif o[1] == "shot" then
    emu:screenshot(o[2]); i = i + 1
  elseif o[1] == "press" then
    t = t + 1
    if t == 1 then emu:addKey(o[2]) elseif t == 5 then emu:clearKey(o[2]) elseif t >= 14 then t = 0; i = i + 1 end
  elseif o[1] == "auto" then
    -- battle autopilot: A to attack; in the party menu after a faint, step to the
    -- next Pokemon and send it out. Ends after 4s back in the overworld, or the cap.
    t = t + 1
    local cb = emu:read32(CB2) & 0xFFFFFFFE
    if cb == BATTLE then fought = true end
    if cb == OVERWORLD then ow = ow + 1 else ow = 0 end
    if (fought and ow > 30 and #q == 0) or t >= o[2] then t = 0; ow = 0; fought = false; i = i + 1; return end
    if #q == 0 and t % 16 == 0 then
      if cb == PARTY then q = {{1, 7, 0, 0}} else q = {{0}} end
    end
    if #q > 0 then
      qt = qt + 1
      if qt == 1 then emu:addKey(q[1]) elseif qt == 4 then emu:clearKey(q[1]) elseif qt >= 10 then qt = 0; table.remove(q, 1) end
    end
  elseif o[1] == "setvar" then
    -- test-only: write a save var (gSaveBlock1Ptr->vars, 5024 bytes in: offsetof(struct SaveBlock1, vars))
    local base = emu:read32({SYM['gSaveBlock1Ptr']})
    emu:write16(base + 5024 + (o[2] - 0x4000) * 2, o[3]); i = i + 1
  elseif o[1] == "shiny" then
    -- test-only: gSaveBlock2Ptr->frontier.wildcardShinyLines is 0x738 bytes in (rerun the offsetof if global.h moves it)
    local at = emu:read32({SYM['gSaveBlock2Ptr']}) + 0x738 + (o[2] // 8)
    emu:write8(at, emu:read8(at) | (1 << (o[2] % 8))); i = i + 1
  elseif o[1] == "hold" then
    t = t + 1
    if t == 1 then emu:addKey(o[2]) elseif t >= o[3] then emu:clearKey(o[2]); t = 0; i = i + 1 end
  end
end)
'''

def run(name, steps, save_from=None, keep_save=False, timeout=300):
    outdir = os.path.join(SP, 'runs', name); os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir): os.remove(os.path.join(outdir, f))
    rom = os.path.join(outdir, 'game.gba'); shutil.copy(os.path.join(GAME, 'pokeemerald.gba'), rom)
    shutil.copy(save_from or os.path.join(GAME, 'pokeemerald.sav'), os.path.join(outdir, 'game.sav'))
    open(os.path.join(outdir, 'drive.lua'), 'w').write(lua(steps, outdir))
    p = subprocess.Popen([MG, '-l', '0', '--script', os.path.join(outdir, 'drive.lua'), rom], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < timeout and not os.path.exists(os.path.join(outdir, 'DONE')): time.sleep(0.5)
    p.kill(); p.wait()
    print(name, 'done' if os.path.exists(os.path.join(outdir, 'DONE')) else 'TIMED OUT', f'{time.time()-t0:.0f}s')
    return outdir

if __name__ == '__main__':
    steps = [l.strip() for l in open(sys.argv[2]) if l.strip() and not l.startswith('#')]
    run(sys.argv[1], steps, timeout=int(sys.argv[3]) if len(sys.argv) > 3 else 300)
