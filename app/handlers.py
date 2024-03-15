from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.database.requests import (get_item_by_id, set_user, \
                                    set_cart, get_cart, get_item_by_id, \
                                        delete_item_from_cart, get_category_by_id, \
                                            check_cart, check_items_in_category)
from config import ADMINS



router = Router()


class Order(StatesGroup):
    my_cart = State()

class Navigation(StatesGroup):
    catalog = State()
    yours_category = State()
    custom_ordering = State()
    specific_category = State()
    specific_item = State()


@router.message(CommandStart())
@router.callback_query(F.data == 'to_main')
async def cmd_start(message: Message | CallbackQuery, state:FSMContext):
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer("Привет, котик!",
                            reply_markup=kb.main)
        await state.clear()
    else:
        await message.answer('')
        await message.message.edit_text("Вы вернулись в главное меню!", 
                                        reply_markup=kb.main)
        await state.clear()


@router.callback_query(Navigation.specific_category, F.data == 'to_categories')
@router.callback_query(Navigation.custom_ordering, F.data == 'to_categories')
@router.callback_query(F.data == 'catalog')
@router.callback_query(F.data == 'yours')
async def catalog(callback: CallbackQuery, state: FSMContext):
    if callback.data in ('catalog', 'to_categories'):
        await state.set_state(Navigation.catalog)
    else:
        await state.set_state(Navigation.yours_category)
    await callback.answer('')
    await callback.message.edit_text('Выберите категорию', 
                                    reply_markup=await kb.categories())


@router.callback_query(Navigation.yours_category, F.data.startswith('category_'))
async def yours_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.custom_ordering)
    await callback.answer('')
    chosen_category = await get_category_by_id(callback.data.split('_')[1])
    await state.update_data(yours_category=chosen_category.name)
    await callback.message.edit_text(f'Вы выбрали {chosen_category.name} на заказ\n\nЕсли хотите оформить заказ, нажмите на кнопку внизу', 
                                reply_markup=await kb.ordering(True))


@router.callback_query(Navigation.catalog, F.data.startswith('category_'))
async def category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.specific_category)
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id = category_id)
    await callback.answer('')
    if await check_items_in_category(category_id):
        await callback.message.edit_text(f'Выберите товар',
                                    reply_markup=await kb.items(category_id))
    else:
        chosen_category = await get_category_by_id(callback.data.split('_')[1])
        await callback.message.edit_text(f'Мы изготовляем {chosen_category.name} только на заказ. Если хотите заказать их, это можно сделать на главной странице, нажав кнопку "На заказ" и выбрав "{chosen_category.name}"',
                                        reply_markup=await kb.items(category_id))


@router.callback_query(Navigation.specific_category, F.data.startswith('item_'))
async def show_item(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.specific_item)
    await callback.message.delete()
    item = await get_item_by_id(callback.data.split('_')[1])
    await callback.answer('')
    await callback.message.answer_photo(photo=item.photo, caption=f'{item.name}\n\n{item.description}\n\nЦена: {item.price} руб.',
                                reply_markup=await kb.cart(item.id))


@router.callback_query(Navigation.specific_item, F.data == 'to_spec_category')
async def to_spec_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.specific_category)
    data = await state.get_data()
    spec_category_id = data['category_id']
    await callback.answer('')
    await callback.message.answer('Выберите товар', reply_markup=await kb.items(spec_category_id))


@router.callback_query(F.data.startswith('cart_'))
async def add_to_cart(callback: CallbackQuery):
    if await set_cart(callback.from_user.id, callback.data.split('_')[1]):
        await callback.answer('Товар добавлен в корзину', show_alert=True)
    else:
        await callback.answer("Товар уже был добавлен", show_alert=True)



async def format_product_count(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} товар"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return f"{count} товара"
    else:
        return f"{count} товаров"


@router.callback_query(F.data == 'my_cart')
async def my_cart(callback: CallbackQuery, state:FSMContext):
    await state.set_state(Order.my_cart)
    await callback.answer('')
    cart_full = await check_cart(callback.from_user.id)
    if not cart_full:
        await callback.message.answer("Корзина пуста")
    else:
        cart = await get_cart(callback.from_user.id)
        count_of_items = 0
        price_of_items = 0
        for item_info in cart:
            item = await get_item_by_id(item_info.item)
            count_of_items += 1
            price_of_items += int(item.price)
            await callback.message.answer_photo(photo=item.photo, caption=f'{item.name}\n\n{item.description}\n\nЦена: {item.price} руб.',
                                    reply_markup=await kb.del_from_cart(item.id))
        message_text = f'Всего {await format_product_count(count_of_items)} на сумму {price_of_items} руб.'
        new_message = await callback.message.answer(message_text)
        await state.update_data(count_of_items=count_of_items, price_of_items=price_of_items, last_message_id=new_message.message_id)
        await callback.message.answer('Если хотите оформить заказ, нажмите на кнопку внизу', reply_markup=await kb.ordering(False))
        


@router.callback_query(Order.my_cart, F.data.startswith('delete_'))
async def delete_from_cart(callback: CallbackQuery, state: FSMContext):
    await delete_item_from_cart(callback.from_user.id, callback.data.split('_')[1])
    await callback.message.delete()
    await callback.answer('Вы удалили товар из корзины', show_alert=True)

    state_data = await state.get_data()
    count_of_items = state_data.get('count_of_items')
    price_of_items = state_data.get('price_of_items')
    last_message_id = state_data.get('last_message_id')

    if count_of_items > 1 and last_message_id:
        item = await get_item_by_id(callback.data.split('_')[1])
        count_of_items -= 1
        price_of_items -= int(item.price)

        await state.update_data(count_of_items=count_of_items, price_of_items=price_of_items)
        
        message_text = f'Всего {await format_product_count(count_of_items)} на сумму {price_of_items} руб.'
        await callback.message.bot.edit_message_text(message_text, callback.from_user.id, last_message_id)

    elif count_of_items == 1 and last_message_id:
        await callback.message.bot.delete_message(callback.from_user.id, last_message_id)
        await callback.message.bot.delete_message(callback.from_user.id, last_message_id + 1)
        await state.clear()


@router.callback_query(Navigation.custom_ordering, F.data == 'custom_ordering')
@router.callback_query(Order.my_cart, F.data == 'ordering')
async def order_items(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    final_text = 'Ваш заказик:\n\n'
    order_text = ''
    notification_text = f'@{callback.from_user.username} сделал заказ:'
    if callback.data == 'ordering': 
        info_from_cart = await get_cart(callback.from_user.id)
        number = 0
        price = 0
        for item_info in info_from_cart:
            item = await get_item_by_id(item_info.item)
            number += 1
            price += item.price
            order_text += f'{number}. {item.name} - {item.price} руб.\n'
        final_text += order_text + f'\nИтоговая сумма: {price}\n\nДля оплаты напишите: @i17bs43kzkp0\n\nБлагодарим за ваш заказ! Будем рады видеть вас снова!' 
        await callback.message.answer(final_text)
        await callback.message.answer('Вы вернулись в главное меню!', reply_markup=kb.main)
        notification_text += f'\n\n{order_text}\nНа сумму: {price} руб.'
    else:
        data = await state.get_data()
        order_text = f'{data['yours_category']} на заказ'
        final_text += f'{order_text}\n\nСтоимость украшения и детали обсудите с @i17bs43kzkp0\n\nБлагодарим за ваш заказ! Будем рады видеть вас снова!'
        await callback.message.answer(final_text)
        await callback.message.answer('Вы вернулись в главное меню!', reply_markup=kb.main)
        notification_text += f'\n\n{order_text}'
    for admin in ADMINS:
        await callback.message.bot.send_message(chat_id=admin, text=notification_text)
    await state.clear()

