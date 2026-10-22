#!/bin/sh
# Builds a headless mGBA with Lua scripting into wildcard/playtest/mgba (not tracked):
# the commit tools/mgba/README.md names, plus mgba-headless.patch (a screen buffer for
# screenshots, and loading the .sav beside the ROM). Needs: brew install lua cmake libpng
set -e
cd "$(dirname "$0")"
[ -d mgba ] || git clone https://github.com/mgba-emu/mgba.git mgba
cd mgba
git fetch --depth 1 origin daf01b03d5316dac966acd4b05318a225cab12f5
git checkout -q FETCH_HEAD
git apply ../mgba-headless.patch 2>/dev/null || echo "(patch already applied)"
mkdir -p build && cd build
cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DBUILD_HEADLESS=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF -DUSE_LUA=ON \
  -DBUILD_GL=OFF -DBUILD_GLES2=OFF -DBUILD_GLES3=OFF -DUSE_FFMPEG=OFF -DUSE_EDITLINE=OFF -DUSE_DISCORD_RPC=OFF \
  -DUSE_LIBZIP=OFF -DUSE_MINIZIP=OFF -DBUILD_SHARED=OFF -DBUILD_STATIC=ON -DCMAKE_BUILD_TYPE=Release
make -j8 mgba-headless
