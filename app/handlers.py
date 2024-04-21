from asyncio import sleep

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import getenv

import app.keyboards as kb
from app.database.requests import (
    get_item_by_id, get_cart, get_item_by_id,
    get_category_by_id, get_promo,
    set_user, set_cart, check_cart, 
    check_items_in_category,
    clear_cart, decrease_amount_promo,
    delete_item_from_cart,
)
from app.functions import (
    format_product_count,
    format_promo,
    access_discount
)



router = Router()


class Order(StatesGroup):
    my_cart = State()
    promo = State()

class Navigation(StatesGroup):
    main_menu = State()
    catalog = State()
    custom_ordering = State()
    yours_category = State()
    specific_category = State()
    specific_item = State()


@router.message(CommandStart())
@router.callback_query(F.data == 'to_main')
async def cmd_start(message: Message | CallbackQuery, state:FSMContext):
    await state.clear()
    await state.set_state(Navigation.main_menu)
    
    main_text = 'привет, котик\\!\\! рад приветствовать тебя в нашем \
уютном магазинчике\\! 💒\n\nздесь каждый найдет для себя *особенное* украшение, \
которое идеально дополнит образ ‧₊˚❀༉\n\nвыбирай готовое украшение или закажи \
новое, с твоим *уникальным* дизайном ──★ ˙🎀'

    main_menu_text = 'главное меню 💌'
    
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer(main_text, parse_mode='MarkdownV2')
        await message.answer(main_menu_text,
                            reply_markup=await kb.kb_main(message.from_user.id))
    else:
        await message.answer('')
        await message.message.edit_text('вы вернулись в ' + main_menu_text, 
                                        reply_markup=await kb.kb_main(message.from_user.id))
        await state.update_data(to_menu=True)


@router.message(F.text.startswith('/'))
async def wrong_command(message: Message):
    if message.text not in ['/start', '/apanel']:
        await message.answer('такой команды не существует!')


@router.callback_query(F.data == 'delivery')
async def contacts(callback: CallbackQuery):
    await callback.answer('')
    delivery_text = '\
    *информация* *о* *доставке*\n\n\
осуществляем доставку почтой России по всей стране\\.\n*бесплатная* *доставка* при заказе от *1300* *руб*\\.\n\n\
в среднем заказик едет около недели до пункта назначения\\.\n\n\
если вы из Комсомольска\\-на\\-Амуре \\- личная встреча с предоплатой\\.'
    await callback.message.edit_text(
        delivery_text, 
        reply_markup=await kb.to_apanel_or_main(),
        parse_mode='MarkdownV2')


@router.callback_query(F.data == 'contacts')
async def contacts(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('по всем вопросам - @i17bs43kzkp0', 
                                    reply_markup=await kb.to_apanel_or_main())


@router.callback_query(Navigation.specific_category, F.data == 'to_categories')
@router.callback_query(Navigation.custom_ordering, F.data == 'yours')
@router.callback_query(F.data == 'catalog')
@router.callback_query(F.data == 'yours')
async def catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    if callback.data in ('catalog', 'to_categories'):
        await state.set_state(Navigation.catalog)
    else:
        await state.set_state(Navigation.yours_category)
    
    await callback.message.edit_text('какие украшения ты хочешь посмотреть? 🐾', 
                                    reply_markup=await kb.categories())


@router.callback_query(Navigation.yours_category, F.data.startswith('category_'))
async def yours_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.custom_ordering)
    
    await callback.answer('')
    
    chosen_category = await get_category_by_id(int(callback.data.split('_')[1]))
    await state.update_data(yours_category=chosen_category.name)
    
    await callback.message.edit_text(f'вы выбрали *{chosen_category.name}* на заказ\n\nдля оформления заказа, нажмите на кнопку внизу', 
                                reply_markup=await kb.ordering(), parse_mode='MarkdownV2')


@router.callback_query(Navigation.specific_item, F.data == 'to_spec_category')
@router.callback_query(Navigation.catalog, F.data.startswith('category_'))
async def category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.specific_category)
    
    if callback.data == 'to_spec_category':
        data = await state.get_data()
        category_id = data['category_id']
        flag = True
    else:
        category_id = int(callback.data.split('_')[1])
        flag = False
        
    await state.update_data(category_id=category_id)
    await callback.answer('')
    
    chosen_category = await get_category_by_id(category_id)
    items_kb = await kb.items(category_id)
    
    if await check_items_in_category(category_id):
        msg_text = 'смотри, что у нас есть!! 🛍'
        if flag:
            await callback.message.answer(msg_text,
                                        reply_markup=items_kb)
        else:
            await callback.message.edit_text(msg_text,
                                        reply_markup=items_kb)
    else:
        msg_text = f'мы изготовляем *{chosen_category.name}* только на заказ\\ \n\nдля заказа нажмите в главном меню "*на* *заказ*" и выберите "{chosen_category.name}" ⋆˚'
        
        if flag:
            await callback.message.answer(
                msg_text, 
                reply_markup=items_kb, 
                parse_mode='MarkdownV2'
            )
        else:
            await callback.message.edit_text(
                msg_text, 
                reply_markup=items_kb, 
                parse_mode='MarkdownV2'
            )


@router.callback_query(Navigation.specific_category, F.data.startswith('item_'))
async def show_item(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Navigation.specific_item)
    
    await callback.bot.delete_message(
        chat_id=callback.message.chat.id, 
        message_id=callback.message.message_id
    )
    
    await callback.answer('')
    
    item = await get_item_by_id(int(callback.data.split('_')[1]))
    await callback.message.answer_photo(photo=item.photo, \
        caption=f'{item.name}\n\n{item.description}\n\nцена: {item.price} руб.',
        reply_markup=await kb.cart(item.id))


@router.callback_query(F.data.startswith('cart_'))
async def add_to_cart(callback: CallbackQuery):
    if await set_cart(callback.from_user.id, int(callback.data.split('_')[1])):
        await callback.answer('товар был добавлен в корзину', show_alert=True)
    else:
        await callback.answer("товар уже был добавлен", show_alert=True)


@router.callback_query(F.data == 'my_cart')
async def my_cart(callback: CallbackQuery, state:FSMContext):
    if await state.get_state() == Order.my_cart:
        return
    
    await state.set_state(Order.my_cart)
    
    cart_full = await check_cart(callback.from_user.id)
    
    if not cart_full:
        await callback.answer("корзина пуста, добавь в неё товары из каталога", show_alert=True)
    else:
        await callback.answer('')
        await callback.message.bot.delete_message(
            callback.message.chat.id,
            callback.message.message_id
            )
        try:
            await callback.message.bot.delete_message(
                callback.message.chat.id,
                callback.message.message_id - 1
                )
        except:
            pass
        
        cart = await get_cart(callback.from_user.id)
        count_of_items = 0
        price_of_items = 0
        
        for item_info in cart:
            item = await get_item_by_id(item_info.item)
            count_of_items += 1
            price_of_items += int(item.price)
            item = await callback.message.answer_photo(photo=item.photo, caption=f'{item.name}\n\nцена: {item.price} руб.',
                                    reply_markup=await kb.del_from_cart(item.id))
        
        message_text = f'всего {await format_product_count(count_of_items)} на сумму {price_of_items} руб.'
        new_message = await callback.message.answer(message_text)
        await callback.message.answer('есть ли у вас промокод?', reply_markup=await kb.promo_code(False))
        
        await state.update_data(count_of_items=count_of_items, price_of_items=price_of_items, cart_info_id=new_message.message_id)


@router.callback_query(Order.promo, F.data == 'promo_skip')
@router.callback_query(Order.my_cart, F.data.startswith('promo_'))
async def promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    
    if callback.data == 'promo_write':
        await state.set_state(Order.promo)
        
        promo_msg = await callback.message.edit_text('введите промокод', 
                                                    reply_markup=await kb.promo_code())
        await state.update_data(promo_msg=promo_msg.message_id)        
    else:
        await state.set_state(Order.my_cart)
        await callback.message.edit_text('для оформления заказа, нажмите на кнопку внизу', reply_markup=await kb.ordering(False))


@router.message(Order.promo, F.text)
async def access_promo(message: Message, state: FSMContext):
    
    promo_code = message.text
    state_data = await state.get_data()
    promo_msg_id = state_data['promo_msg']
    msg_id = message.message_id
    promo_codes = [promo_code.name for promo_code in await get_promo()]

    if promo_code in promo_codes:
        success_msg = await message.answer('промокод успешно применен!')
        
        await state.set_state(Order.my_cart)
        
        cart_info_id = state_data['cart_info_id']
        count_of_items = state_data['count_of_items']
        price_of_items = state_data['price_of_items']
        price_of_items = await access_discount(price_of_items, promo_code)
        
        await message.bot.delete_message(message.chat.id, msg_id)
        await message.bot.delete_message(message.chat.id, promo_msg_id)
        await sleep(1.5)
        await message.bot.delete_message(message.chat.id, success_msg.message_id)
        
        message_text = f'Всего {await format_product_count(count_of_items)} на сумму {price_of_items} руб.'
        
        await message.bot.edit_message_text(message_text, message.chat.id, cart_info_id)
        await state.update_data(promo_code=promo_code)
        
        order_msg = await message.answer('для оформления заказа, нажмите на кнопку внизу', reply_markup=await kb.ordering(False))
        await state.update_data(order_msg_id=order_msg.message_id)
    else:
        alert_msg = await message.answer('такого промокода не существует')
        await state.set_state(Order.my_cart)
        
        await message.bot.delete_message(message.chat.id, msg_id)
        
        await sleep(1.5)
        
        await message.bot.delete_message(message.chat.id, alert_msg.message_id)
        await state.set_state(Order.promo)



@router.callback_query(Order.my_cart, F.data.startswith('delete_'))
async def delete_from_cart(callback: CallbackQuery, state: FSMContext):
    await delete_item_from_cart(callback.from_user.id, int(callback.data.split('_')[1]))
    
    await callback.answer('вы удалили товар из корзины', show_alert=True)
    
    await callback.message.delete()

    state_data = await state.get_data()
    count_of_items = state_data['count_of_items']
    price_of_items = state_data['price_of_items']
    cart_info_id = state_data['cart_info_id']

    if count_of_items > 1 and cart_info_id:
        item = await get_item_by_id(int(callback.data.split('_')[1]))
        count_of_items -= 1
        price_of_items -= int(item.price)

        await state.update_data(count_of_items=count_of_items, price_of_items=price_of_items)
        
        if 'promo_code' in state_data:
            price_of_items = await access_discount(price_of_items, state_data['promo_code'])
        
        message_text = f'всего {await format_product_count(count_of_items)} на сумму {price_of_items} руб.'
        await callback.message.bot.edit_message_text(message_text, callback.from_user.id, cart_info_id)

    elif count_of_items == 1 and cart_info_id:
        try:
            order_msg_id = state_data['order_msg_id']
            await callback.message.bot.delete_message(callback.from_user.id, order_msg_id)
            await callback.message.bot.delete_message(callback.from_user.id, cart_info_id)
        except KeyError:
            await callback.message.bot.delete_message(callback.from_user.id, cart_info_id + 1)
            await callback.message.bot.delete_message(callback.from_user.id, cart_info_id)
        await callback.message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
        
        await state.clear()


@router.callback_query(Navigation.custom_ordering, F.data == 'custom_ordering')
@router.callback_query(Order.my_cart, F.data == 'ordering')
async def order_items(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    
    data = await state.get_data()
    final_text = 'ваш заказик:\n\n'
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
            order_text += f'{number}\\. {item.name}\n'
        
        if 'promo_code' in data:
            price = await access_discount(price, data['promo_code'])
            await decrease_amount_promo(data['promo_code'])
        
        
        final_text += order_text + f'\nитоговая сумма: *{price}* *руб*\\.\n\nдля оплаты напишите: *@i17bs43kzkp0*\n\nблагодарим за ваш заказ\\! будем рады видеть вас снова\\!'
        await callback.message.answer(final_text, parse_mode='MarkdownV2')
        await callback.message.answer('главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
        
        notification_text += f'\n\n{order_text}\nна сумму: *{price}* *руб*\\.\n\nдоставка: '
        
        if price < 1300:
            notification_text += '*платная*\n\nколечко в подарок: *нет*'
        elif 1300 <= price < 1500:
            notification_text += '*бесплатная*\n\nколечко в подарок: *нет*'
        elif price >= 1500:
            notification_text += '*бесплатная*\n\nколечко в подарок: *да*'
        
        if 'promo_code' in data:
            notification_text += f'\n\nбыл использован промокод: *{data['promo_code']}* на скидку *{await format_promo(data['promo_code'])}**%*'
        else:
            notification_text += '\n\nпромокод *не* *был* *использован*'

    else:
        data = await state.get_data()
        order_text = f'*{data['yours_category']}* на заказ'
        final_text += f'{order_text}\n\nстоимость украшения и детали обсудите с *@i17bs43kzkp0*\n\nблагодарим за ваш заказ\\! будем рады видеть вас снова\\!'
        await callback.message.answer(final_text, parse_mode='MarkdownV2')
        await callback.message.answer('главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
        notification_text += f'\n\n{order_text}'
        
    await clear_cart(callback.from_user.id)
    
    for admin in map(int, getenv('ADMINS').split()):
        await callback.message.bot.send_message(chat_id=admin, text=notification_text, parse_mode='MarkdownV2')
        
    await state.clear()

