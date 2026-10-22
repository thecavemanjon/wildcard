#ifndef GUARD_SUNDIAL_PRICES_H
#define GUARD_SUNDIAL_PRICES_H

// Shop prices for followers (DECISIONS "Shop prices"). Plain C over species
// data, unit-tested in test/sundial_prices.c.

#define SUNDIAL_PRICE_COMMON    1000
#define SUNDIAL_PRICE_STARTER   2000
#define SUNDIAL_PRICE_STRONG    5000
#define SUNDIAL_PRICE_LEGENDARY 10000

u32 Sundial_FollowerPrice(u16 species);

#endif // GUARD_SUNDIAL_PRICES_H
