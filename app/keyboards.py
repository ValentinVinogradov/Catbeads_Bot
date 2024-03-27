from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import (
    get_categories, 
    get_items_by_category, 
    get_promo,
    check_items_in_category
)


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Каталог', callback_data='catalog'),
    InlineKeyboardButton(text='На заказ', callback_data='yours')],

    [InlineKeyboardButton(text='Корзина', callback_data='my_cart'),
    InlineKeyboardButton(text='Написать нам', callback_data='contacts')],
    
    [InlineKeyboardButton(text='Доставка', callback_data='delivery'),
    InlineKeyboardButton(text='Отзывы', url='https://vk.com/topic-217319908_49283641')]
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')


edit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Название', callback_data='name'),
    InlineKeyboardButton(text="Описание", callback_data='description')],

    [InlineKeyboardButton(text='Фото',callback_data='photo'),
    InlineKeyboardButton(text='Цена',callback_data='price')],

    [InlineKeyboardButton(text='Назад',callback_data='to_spec_category')]
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')


apanel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить товар', callback_data='add_item'),
    InlineKeyboardButton(text='Изменить товар', callback_data='edit_item')],
    
    [InlineKeyboardButton(text='Удалить товар', callback_data='delete_item'),
    InlineKeyboardButton(text='Создать рассылку', callback_data='newsletter')],
    
    [InlineKeyboardButton(text='Добавить промокод', callback_data='add_promo'),
    InlineKeyboardButton(text='Удалить промокод', callback_data='delete_promo')],
    
    [InlineKeyboardButton(text='Список промокодов', callback_data='promos'),
    InlineKeyboardButton(text='В главное меню', callback_data='to_main')]
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')


async def to_apanel_or_main(place_to: str = 'to_main'):
    keyboard = InlineKeyboardBuilder()
    if place_to == 'to_main':
        keyboard.add(InlineKeyboardButton(text='На главную', callback_data='to_main'))
    else:
        keyboard.add(InlineKeyboardButton(text='В панельку', callback_data='to_apanel'))
    return keyboard.adjust(1).as_markup()


async def confirmation(state: str):
    keyboard = InlineKeyboardBuilder()
    if state == 'newsletter':
        keyboard.add(InlineKeyboardButton(text='Да, отправить', callback_data='confirmation'))
    else:
        keyboard.add(InlineKeyboardButton(text='Да, удалить', callback_data='confirmation'))
    keyboard.add(InlineKeyboardButton(text='Нет, вернуться назад', callback_data='cancel'))
    return keyboard.adjust(1).as_markup()


async def promo_code(is_writing: bool = True):
    keyboard = InlineKeyboardBuilder()
    if is_writing:
        keyboard.add(InlineKeyboardButton(text='Дальше', callback_data='promo_skip'))
    else:
        keyboard.add(InlineKeyboardButton(text='Да, ввести промокод',
                                            callback_data='promo_write'))
        keyboard.add(InlineKeyboardButton(text='Нет',
                                            callback_data='promo_skip'))
    return keyboard.adjust(1).as_markup()


async def ordering(is_customizing: bool = True):
    keyboard = InlineKeyboardBuilder()
    if is_customizing:
        keyboard.add(InlineKeyboardButton(text='Оформить заказ', callback_data='custom_ordering'))
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='yours'))
    else:
        keyboard.add(InlineKeyboardButton(text='Оформить заказ', callback_data='ordering'))
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_main'))
    return keyboard.adjust(2).as_markup(resize_keyboard=True)


async def del_from_cart(cart_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Удалить из корзины', callback_data=f'delete_{cart_id}'))
    return keyboard.adjust(2).as_markup()


async def cart(cart_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Добавить в корзину', callback_data=f'cart_{cart_id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_spec_category'))
    return keyboard.adjust(2).as_markup()


async def categories(place_from:str = 'catalog'):
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, 
                                        callback_data=f'category_{category.id}'))
    if place_from == 'catalog':
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_main'))
    else:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_apanel'))
    return keyboard.adjust(2).as_markup()


async def items(category_id: int):
    if check_items_in_category(category_id):
        items = await get_items_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        for item in items:
            keyboard.add(InlineKeyboardButton(text=item.name,
                                            callback_data=f"item_{item.id}"))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_categories'))
    return keyboard.adjust(1).as_markup()


async def show_promo_codes():
    keyboard = InlineKeyboardBuilder()
    promo_codes = await get_promo()
    for promo_code in promo_codes:
        keyboard.add(InlineKeyboardButton(text=promo_code.name, callback_data=f'promo_{promo_code.name}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_apanel'))
    return keyboard.adjust(2).as_markup()
