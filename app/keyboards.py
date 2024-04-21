from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from os import getenv
from dotenv import load_dotenv

from app.database.requests import (
    get_categories, 
    get_items_by_category, 
    get_promo,
    check_items_in_category
)

# from config import ADMINS


edit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='название', callback_data='name'),
    InlineKeyboardButton(text="описание", callback_data='description')],

    [InlineKeyboardButton(text='фото',callback_data='photo'),
    InlineKeyboardButton(text='цена',callback_data='price')],

    [InlineKeyboardButton(text='<< назад',callback_data='to_spec_category')]
],
    resize_keyboard=True,
    input_field_placeholder='выберите пункт меню')


apanel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📌 добавить товар', callback_data='add_item'),
    InlineKeyboardButton(text='✏️ изменить товар ', callback_data='edit_item')],
    
    [InlineKeyboardButton(text='🗑 удалить товар', callback_data='delete_item'),
    InlineKeyboardButton(text='📄 создать рассылку', callback_data='newsletter')],
    
    [InlineKeyboardButton(text='📌 добавить промокод', callback_data='add_promo'),
    InlineKeyboardButton(text='🗑 удалить промокод', callback_data='delete_promo')],
    
    [InlineKeyboardButton(text='🗂 список промокодов', callback_data='promos'),
    InlineKeyboardButton(text='<< в главное меню', callback_data='to_main')]
],
    resize_keyboard=True,
    input_field_placeholder='выберите пункт меню')


async def kb_main(tg_id):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='каталог', callback_data='catalog'))
    keyboard.add(InlineKeyboardButton(text='на заказ', callback_data='yours'))
    keyboard.add(InlineKeyboardButton(text='корзина', callback_data='my_cart'))
    keyboard.add(InlineKeyboardButton(text='написать нам', callback_data='contacts'))
    keyboard.add(InlineKeyboardButton(text='доставка', callback_data='delivery'))
    keyboard.add(InlineKeyboardButton(text='отзывы', url='https://vk.com/topic-217319908_49283641'))
    
    if tg_id in map(int, getenv('ADMINS').split()):
        keyboard.add(InlineKeyboardButton(text='в админ-панельку >>', callback_data = 'to_apanel'))
    
    return keyboard.adjust(2).as_markup()


async def to_apanel_or_main(place_to: str = 'to_main'):
    keyboard = InlineKeyboardBuilder()
    
    if place_to == 'to_main':
        keyboard.add(InlineKeyboardButton(text='<< на главную', callback_data='to_main'))
    else:
        keyboard.add(InlineKeyboardButton(text='<< в панельку', callback_data='to_apanel'))
    
    return keyboard.adjust(1).as_markup()


async def confirmation(state: str):
    keyboard = InlineKeyboardBuilder()
    
    if state == 'newsletter':
        keyboard.add(InlineKeyboardButton(text='да, отправить', callback_data='confirmation'))
    else:
        keyboard.add(InlineKeyboardButton(text='да, удалить', callback_data='confirmation'))
    keyboard.add(InlineKeyboardButton(text='<< нет, вернуться назад', callback_data='cancel'))
    
    return keyboard.adjust(1).as_markup()


async def promo_code(is_writing: bool = True):
    keyboard = InlineKeyboardBuilder()
    
    if is_writing:
        keyboard.add(InlineKeyboardButton(text='дальше >>', callback_data='promo_skip'))
    else:
        keyboard.add(InlineKeyboardButton(text='да, ввести промокод',
                                            callback_data='promo_write'))
        keyboard.add(InlineKeyboardButton(text='нет',
                                            callback_data='promo_skip'))
    
    return keyboard.adjust(1).as_markup()


async def ordering(is_customizing: bool = True):
    keyboard = InlineKeyboardBuilder()
    
    if is_customizing:
        keyboard.add(InlineKeyboardButton(text='оформить заказ', callback_data='custom_ordering'))
        keyboard.add(InlineKeyboardButton(text=' << назад', callback_data='yours'))
    else:
        keyboard.add(InlineKeyboardButton(text='оформить заказ', callback_data='ordering'))
        keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_main'))
    
    return keyboard.adjust(2).as_markup(resize_keyboard=True)


async def del_from_cart(cart_id):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='удалить из корзины', callback_data=f'delete_{cart_id}'))
    
    return keyboard.adjust(2).as_markup()


async def cart(cart_id):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='добавить в корзину', callback_data=f'cart_{cart_id}'))
    keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_spec_category'))
    
    return keyboard.adjust(2).as_markup()


async def categories(place_from:str = 'catalog'):
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, 
                                        callback_data=f'category_{category.id}'))
    
    if place_from == 'catalog':
        keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_main'))
    else:
        keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_apanel'))
    
    return keyboard.adjust(2).as_markup()


async def items(category_id: int):
    if check_items_in_category(category_id):
        items = await get_items_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        for item in items:
            keyboard.add(InlineKeyboardButton(text=item.name,
                                            callback_data=f"item_{item.id}"))
    
    keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_categories'))
    
    return keyboard.adjust(1).as_markup()


async def show_promo_codes():
    keyboard = InlineKeyboardBuilder()
    
    promo_codes = await get_promo()
    
    for promo_code in promo_codes:
        keyboard.add(InlineKeyboardButton(text=f'{promo_code.name} : {promo_code.amount} ост.', callback_data=f'promo_{promo_code.name}'))
    
    keyboard.add(InlineKeyboardButton(text='<< назад', callback_data='to_apanel'))
    
    return keyboard.adjust(2).as_markup()
