# Serves the web player for testing: python3 wildcard/web/serve.py [port]
# Then open http://localhost:8000 (or http://<this-mac>.local:8000 from a phone
# on the same Wi-Fi). Run build_data.py first.
#
# For testing only, /dev/rom.gba and /dev/save.sav are the repo's built ROM and
# save (read-only), and http://localhost:8000/?dev loads them and starts the game
# without the file pickers. The public site has no such thing.
import functools, http.server, os, socket, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(os.path.join(HERE, '..', '..'))
DEV = {'/dev/rom.gba': 'pokeemerald.gba', '/dev/save.sav': 'pokeemerald.sav'}
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class NoCache(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        dev = DEV.get(path.split('?')[0])
        if dev and self.client_address[0] in ('127.0.0.1', '::1'):  # this Mac only, never the Wi-Fi
            return os.path.join(GAME, dev)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')  # so a rebuilt schedule or page shows on reload
        super().end_headers()


if not os.path.exists(os.path.join(HERE, 'data', 'schedule.json')):
    sys.exit('No data yet: run python3 wildcard/web/build_data.py first.')
print(f'Wild Card on http://localhost:{PORT} (phone: http://{socket.gethostname()}:{PORT}); Ctrl+C to stop')
http.server.ThreadingHTTPServer(('', PORT), functools.partial(NoCache, directory=HERE)).serve_forever()
