from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
from os import getenv

from typing import List

load_dotenv()

engine = create_async_engine(url=getenv('ENGINE'), echo=True)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    
    cart_rel: Mapped[List['Cart']] = relationship(back_populates='user_rel')


class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    item_rel: Mapped[List['Item']] = relationship(back_populates='category_rel')


class Item(Base):
    __tablename__ = 'items'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(250))
    photo: Mapped[str] = mapped_column(String(200))
    price: Mapped[int] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))

    category_rel: Mapped['Category'] = relationship(back_populates='item_rel')
    cart_rel: Mapped[List['Cart']] = relationship(back_populates='item_rel')


class Cart(Base):
    __tablename__ = 'cart'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user:Mapped[int] = mapped_column(ForeignKey('users.id'))
    item:Mapped[int] = mapped_column(ForeignKey('items.id'))
    
    user_rel: Mapped['User'] = relationship(back_populates='cart_rel')
    item_rel: Mapped['Item'] = relationship(back_populates='cart_rel')


class Promo_codes(Base):
    __tablename__ = 'promo_codes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    amount: Mapped[int] = mapped_column()


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
