#include "global.h"
#include "test/test.h"
#include "sundial_prices.h"
#include "constants/species.h"

TEST("Sundial prices: tiers for legendaries, strong, starter lines and the rest")
{
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_MEWTWO), SUNDIAL_PRICE_LEGENDARY);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_ARTICUNO), SUNDIAL_PRICE_LEGENDARY);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_MEW), SUNDIAL_PRICE_LEGENDARY);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_DRAGONITE), SUNDIAL_PRICE_STRONG);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_GARCHOMP), SUNDIAL_PRICE_STRONG);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_NIHILEGO), SUNDIAL_PRICE_STRONG);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_CHARMANDER), SUNDIAL_PRICE_STARTER);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_CHARIZARD), SUNDIAL_PRICE_STARTER);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_GRENINJA), SUNDIAL_PRICE_STARTER);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_RAICHU), SUNDIAL_PRICE_STARTER);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_UMBREON), SUNDIAL_PRICE_STARTER);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_DRATINI), SUNDIAL_PRICE_COMMON);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_RATTATA), SUNDIAL_PRICE_COMMON);
    EXPECT_EQ(Sundial_FollowerPrice(SPECIES_SNOM), SUNDIAL_PRICE_COMMON);
}
