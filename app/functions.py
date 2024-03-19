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


async def access_discount(value: int, discount: str) -> int:
    result_price = value - value * round(await format_promo(discount) / 100, 2)
    return int(result_price) + 1 if result_price % 1 != 0 else int(result_price)
