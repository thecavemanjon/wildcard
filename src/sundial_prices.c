#include "global.h"
#include "pokemon.h"
#include "sundial_prices.h"
#include "constants/species.h"

// First stages that make a whole line cost the starter price: the 27 starters,
// plus Pichu's and Eevee's lines.
static const u16 sStarterLines[] =
{
    SPECIES_BULBASAUR, SPECIES_CHARMANDER, SPECIES_SQUIRTLE,
    SPECIES_CHIKORITA, SPECIES_CYNDAQUIL, SPECIES_TOTODILE,
    SPECIES_TREECKO, SPECIES_TORCHIC, SPECIES_MUDKIP,
    SPECIES_TURTWIG, SPECIES_CHIMCHAR, SPECIES_PIPLUP,
    SPECIES_SNIVY, SPECIES_TEPIG, SPECIES_OSHAWOTT,
    SPECIES_CHESPIN, SPECIES_FENNEKIN, SPECIES_FROAKIE,
    SPECIES_ROWLET, SPECIES_LITTEN, SPECIES_POPPLIO,
    SPECIES_GROOKEY, SPECIES_SCORBUNNY, SPECIES_SOBBLE,
    SPECIES_SPRIGATITO, SPECIES_FUECOCO, SPECIES_QUAXLY,
    SPECIES_PICHU, SPECIES_EEVEE,
};

static u32 BaseStatTotal(u16 species)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[species];

    return info->baseHP + info->baseAttack + info->baseDefense
         + info->baseSpAttack + info->baseSpDefense + info->baseSpeed;
}

static bool32 IsFullyEvolved(u16 species)
{
    const struct Evolution *evolutions = GetSpeciesEvolutions(species);

    return evolutions == NULL || evolutions[0].method == EVOLUTIONS_END;
}

static bool32 IsStarterLine(u16 species)
{
    u16 pre;
    u32 i;

    while ((pre = GetSpeciesPreEvolution(species)) != SPECIES_NONE)
        species = pre;
    for (i = 0; i < ARRAY_COUNT(sStarterLines); i++)
    {
        if (sStarterLines[i] == species)
            return TRUE;
    }
    return FALSE;
}

u32 Sundial_FollowerPrice(u16 species)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[species];

    if (info->isRestrictedLegendary || info->isSubLegendary || info->isMythical)
        return SUNDIAL_PRICE_LEGENDARY;
    // Pseudo-legendaries: the fully evolved 600s (Dragonite, Tyranitar, Garchomp...).
    if (info->isUltraBeast || info->isParadox || (BaseStatTotal(species) == 600 && IsFullyEvolved(species)))
        return SUNDIAL_PRICE_STRONG;
    if (IsStarterLine(species))
        return SUNDIAL_PRICE_STARTER;
    return SUNDIAL_PRICE_COMMON;
}
