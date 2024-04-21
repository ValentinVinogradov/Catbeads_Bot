from sqlalchemy import select, update, delete
from sqlalchemy import BigInteger

from app.database.models import User, Category, Item, Cart, Promo_codes
from app.database.models import async_session


async def set_user(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def set_item(data: dict):
    async with async_session() as session:
        session.add(Item(**data))
        await session.commit()


async def set_cart(tg_id: BigInteger, item_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        cart_item = await session.scalar(select(Cart).where(Cart.user == user.id, Cart.item == item_id))
        
        if cart_item is not None:
            return False
        
        session.add(Cart(user=user.id, item=item_id))
        await session.commit()
        return True


async def set_promo(data: dict):
    async with async_session() as session:
        session.add(Promo_codes(**data))
        await session.commit()


async def get_cart(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        cart = await session.scalars(select(Cart).where(Cart.user == user.id))
        return cart


async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users


async def get_categories():
    async with async_session() as session:
        categories = await session.scalars(select(Category))
        return categories


async def get_category_by_id(category_id: int):
    async with async_session() as session:
        category = await session.scalar(select(Category).where(Category.id == category_id))
        return category


async def get_items_by_category(category_id: int):
    async with async_session() as session:
        items = await session.scalars(select(Item).where(Item.category == category_id))
        return items


async def get_item_by_id(item_id: int):
    async with async_session() as session:
        item = await session.scalar(select(Item).where(Item.id == item_id))
        return item


async def get_promo():
    async with async_session() as session:
        promo_codes = await session.scalars(select(Promo_codes))
        return promo_codes


async def delete_item_from_cart(tg_id: BigInteger, item_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        await session.execute(delete(Cart).where(Cart.user == user.id, Cart.item == item_id))
        await session.commit()


async def delete_item_from_bot(item_id: int):
    async with async_session() as session:
        await session.execute(delete(Item).where(Item.id == item_id))
        await session.commit()


async def delete_item_from_all_carts(item_id: int):
    async with async_session() as session:
        await session.execute(delete(Cart).where(Cart.item == item_id))
        await session.commit()


async def delete_promo(promo_name: str):
    async with async_session() as session:
        await session.execute(delete(Promo_codes).where(Promo_codes.name == promo_name))
        await session.commit()


async def clear_cart(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        await session.execute(delete(Cart).where(Cart.user == user.id))
        await session.commit()


async def edit_item(data: dict):
    async with async_session() as session:
        await session.execute(update(Item).where(Item.id == data['item_id']).values({data['field']:data['content']}))
        await session.commit()


async def check_cart(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        result = await session.execute(select(Cart).where(Cart.user == user.id))
        return False if not result.scalars().all() else True


async def check_items_in_category(category_id: int):
    async with async_session() as session:
        result = await session.execute(select(Item).where(Item.category == category_id))
        return False if not result.scalars().all() else True


async def decrease_amount_promo(promo_name: str):
    async with async_session() as session:
        amount = await session.scalar(select(Promo_codes.amount).where(Promo_codes.name == promo_name))
        if amount > 1:
            await session.execute(update(Promo_codes).where(Promo_codes.name == promo_name).values(amount=amount-1))
        else:
            await session.execute(delete(Promo_codes).where(Promo_codes.name == promo_name))
        await session.commit()