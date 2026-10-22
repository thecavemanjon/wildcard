#include "global.h"
#include "graphics.h"
#include "pokemon.h"

// Where the web player (wildcard/web/art.js) finds its pictures in the player's own
// patched ROM, so the site hosts no Nintendo art (DECISIONS 2026-10-22). The page
// scans for the magic. Party icons are read through gSpeciesInfo as the game keeps
// them; trainer pictures are smol-compressed in the game, so the ones the page shows
// get an uncompressed copy here (the list is generated: build_data.py --art-table).
// Append fields only: an older ROM in a player's browser still has to read right.

struct WebTrainerPic
{
    const u32 *pixels; // 64x64, 4bpp tiles
    const u16 *palette;
};

#include "data/wildcard_web_art.h"

static const struct WebTrainerPic sWebTrainerPics[] = WEB_TRAINER_PICS;

struct WildcardWebArt
{
    /*0x00*/ char magic[16];
    /*0x10*/ u32 version;
    /*0x14*/ const struct SpeciesInfo *speciesInfo;
    /*0x18*/ const u16 (*monIconPalettes)[16];
    /*0x1C*/ const struct WebTrainerPic *trainerPics;
    /*0x20*/ u32 trainerPicCount;
};

KEEP_SECTION USED static const struct WildcardWebArt sWildcardWebArt =
{
    .magic = "WILDCARD WEB ART",
    .version = 1,
    .speciesInfo = gSpeciesInfo,
    .monIconPalettes = gMonIconPalettes,
    .trainerPics = sWebTrainerPics,
    .trainerPicCount = ARRAY_COUNT(sWebTrainerPics),
};
