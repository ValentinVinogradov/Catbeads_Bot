from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                        InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.requests import get_categories, get_items_by_category, check_items_in_category


# Кнопки(список кнопок в 1 ряд), input... - подсказка
main = InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text='Каталог', 
                                                                callback_data='catalog'),
                                            InlineKeyboardButton(text='На заказ',
                                                                callback_data='yours')],
                                            [InlineKeyboardButton(text='Корзина', 
                                                                callback_data='my_cart'),
                                            InlineKeyboardButton(text='Контакты', 
                                                                callback_data='contacts')]],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите пункт меню')


to_main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='На главную', 
                                                                    callback_data='to_main')]],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите пункт меню')


edit = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Название', callback_data='edit_name'),
                                            InlineKeyboardButton(text="Описание", callback_data='edit_description')],
                                            [InlineKeyboardButton(text='Фото', callback_data='edit_photo'),
                                            InlineKeyboardButton(text='Цена', callback_data='edit_price')],
                                            [InlineKeyboardButton(text='Назад', callback_data='to_spec_category')]] ,
                                resize_keyboard=True,
                                input_field_placeholder='Выберите пункт меню')


confirmation = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Да, отправить',
                                                                        callback_data='confirmation')],
                                                    [InlineKeyboardButton(text='Нет, вернуться назад',
                                                                        callback_data='cancel_newsletter')]],
                                    resize_keyboard=True,
                                    input_field_placeholder='Выберите пункт меню')


async def ordering(is_customizing):
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


async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, 
                                        callback_data=f'category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()


async def items(category_id: int):
    if check_items_in_category(category_id):
        items = await get_items_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        for item in items:
            keyboard.add(InlineKeyboardButton(text=item.name,
                                            callback_data=f"item_{item.id}"))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='to_categories'))
    return keyboard.adjust(2).as_markup()

