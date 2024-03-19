from re import search

async def format_product_count(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} товар"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return f"{count} товара"
    else:
        return f"{count} товаров"


async def format_promo(promo) -> int:
    return int(search(r'\d+', promo).group())


async def access_discount(value, discount) -> float:
    return value * (await format_promo(discount) / 100)


async def normal_price(price: int | float) -> int:
    if isinstance(price, float):
        return int(price) + 1
    return price

