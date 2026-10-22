# Serves the web player for testing: python3 wildcard/web/serve.py [port] [--lan] [--emerald PATH]
# Then open http://localhost:8000 (or http://<this-mac>.local:8000 from a phone
# on the same Wi-Fi). Run build_data.py first.
#
# For testing only, /dev/rom.gba and /dev/save.sav are the repo's built ROM and
# save (read-only), and http://localhost:8000/?dev loads them and starts the game
# without the file pickers. Only this Mac gets them, unless --lan also lets devices
# on the home network have them (a phone test without AirDrop). --emerald PATH also
# serves a clean Emerald for ?dev=patch, which goes the player's way: Emerald in,
# patched in the browser. The public site has no such thing.
import functools, http.server, ipaddress, os, socket, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(os.path.join(HERE, '..', '..'))
DEV = {'/dev/rom.gba': 'pokeemerald.gba', '/dev/save.sav': 'pokeemerald.sav'}
PORT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8000)  # a number among the arguments
LAN = '--lan' in sys.argv
if '--emerald' in sys.argv:  # a clean Emerald for ?dev=patch, the player's way in
    DEV['/dev/emerald.gba'] = os.path.abspath(sys.argv[sys.argv.index('--emerald') + 1])


def may_have_dev(ip):
    address = ipaddress.ip_address(ip)
    return address.is_loopback or (LAN and address.is_private)


class NoCache(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        dev = DEV.get(path.split('?')[0])
        if dev and may_have_dev(self.client_address[0]):
            return os.path.join(GAME, dev)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')  # so a rebuilt schedule or page shows on reload
        super().end_headers()


if not os.path.exists(os.path.join(HERE, 'data', 'schedule.json')):
    sys.exit('No data yet: run python3 wildcard/web/build_data.py first.')
print(f'Wild Card on http://localhost:{PORT} (phone: http://{socket.gethostname()}:{PORT})'
      f'{"; the dev ROM and save go to the home network too" if LAN else ""}; Ctrl+C to stop')
http.server.ThreadingHTTPServer(('', PORT), functools.partial(NoCache, directory=HERE)).serve_forever()
