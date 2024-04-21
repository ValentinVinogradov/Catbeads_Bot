from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import getenv

import app.keyboards as kb
from app.functions import format_act_count
from app.database.requests import (
    get_users, set_item, 
    delete_item_from_bot, 
    check_items_in_category, 
    edit_item, delete_promo,
    delete_item_from_all_carts,
    get_item_by_id, set_promo
)


admin = Router()


class Newsletter(StatesGroup):
    
    message = State()
    confirm = State()


class Promo(StatesGroup):
    
    promo_add = State()
    promo_add_val = State()
    promo_del = State()

class AddItem(StatesGroup):
    
    category = State()
    name = State()
    description = State()
    photo = State()
    price = State()


class DeleteItem(StatesGroup):
    
    category = State()
    item_id = State()
    confirm = State()


class EditItem(StatesGroup):
    
    category = State()
    item_id = State()
    field = State()
    
    photo = State()
    price = State()
    content = State()


class AdminProtect(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in map(int, getenv('ADMINS').split())


# Админ-панель
@admin.callback_query(AdminProtect(), F.data == 'to_apanel')
@admin.message(AdminProtect(), Command('apanel'))
async def apanel(message: Message | CallbackQuery):
    if isinstance(message, Message):
        await message.answer('панелька 🎀', reply_markup=kb.apanel)
    else:
        await message.message.edit_text('панелька 🎀', reply_markup=kb.apanel)


# Добавление промокода
@admin.callback_query(AdminProtect(), F.data == 'add_promo')
async def add_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Promo.promo_add)
    
    await callback.message.edit_text('напишите промокод', reply_markup=await kb.to_apanel_or_main('to_apanel'))


@admin.message(AdminProtect(), Promo.promo_add, F.text)
async def add_promo(message: Message, state: FSMContext):
    await state.set_state(Promo.promo_add_val)
    
    await state.update_data(name=message.text)
    
    await message.answer('напишите количество активаций промокода')


@admin.message(AdminProtect(), Promo.promo_add_val, F.text)
async def adding_promo(message: Message, state: FSMContext):
    try:
        await state.update_data(amount=int(message.text))
        
        data = await state.get_data()
        await set_promo(data)
        
        act = await format_act_count(int(data['amount']))
        
        await message.answer(f'промокод *{data['name']}* на *{act}* был успешно добавлен\\!', parse_mode='MarkdownV2')
        await message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(message.from_user.id))
        
        await state.clear()
    except ValueError:
        await message.answer("введите корректное количество")


# Удаление промокода
@admin.callback_query(AdminProtect(), F.data == 'delete_promo')
async def del_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Promo.promo_del)
    k = await kb.show_promo_codes()
    if len(k.inline_keyboard[0]) == 1:
        await callback.message.edit_text('нет промокодов для удаления', reply_markup=await kb.show_promo_codes())
    else:
        await callback.message.edit_text('выберите промокод, который хотите удалить', reply_markup=await kb.show_promo_codes())


@admin.callback_query(AdminProtect(), Promo.promo_del, F.data.startswith('promo_'))
async def deleting_promo(callback: CallbackQuery, state: FSMContext):
    promo = callback.data.split('_')[1]
    
    await delete_promo(promo)
    
    await callback.message.edit_text(f'промокод *{promo}* успешно был удалён', parse_mode='MarkdownV2')
    await callback.message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
    
    await state.clear()


# Список доступных промокодов
@admin.callback_query(AdminProtect(), F.data == 'promos')
async def show_promos(callback: CallbackQuery):
    k = await kb.show_promo_codes()
    if len(k.inline_keyboard[0]) == 1:
        msg_text = 'нет доступных промокодов'
    else:
        msg_text = 'список всех доступных промокодов'
    await callback.message.edit_text(msg_text, reply_markup=await kb.show_promo_codes())


# Рассылка
@admin.callback_query(AdminProtect(), Newsletter.confirm, F.data == 'cancel')
@admin.callback_query(AdminProtect(), F.data == 'newsletter')
async def newsletter(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Newsletter.message)
    
    await callback.message.edit_text('отправьте сообщение, которые хотите разослать всем пользователям', 
                                    reply_markup=await kb.to_apanel_or_main('to_apanel'))


@admin.message(AdminProtect(), Newsletter.message)
async def confirm_newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.confirm)
    
    await state.update_data(message_id=message.message_id)
    
    await message.answer("отправить рассылку?", reply_markup= await kb.confirmation('newsletter'))


@admin.callback_query(AdminProtect(), Newsletter.confirm, F.data == 'confirmation')
async def newsletter_message(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data['message_id']
    
    await callback.message.answer('подождите... идёт рассылка')
    
    for user in await get_users():
        try:
            await callback.message.bot.copy_message(
                chat_id=user.tg_id, 
                from_chat_id=callback.message.chat.id, 
                message_id=message_id
            )
        except:
            pass
        
    await callback.answer('рассылка успешно завершена!', show_alert=True)
    await callback.message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
    
    await state.clear()


# Добавление товара в БД
@admin.callback_query(AdminProtect(), F.data == 'add_item')
async def add_item(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddItem.category)
    
    await callback.message.edit_text('выберите категорию товара', reply_markup=await kb.categories('apanel'))


@admin.callback_query(AdminProtect(), AddItem.category, F.data.startswith('category_'))
async def add_item_name(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=int(callback.data.split('_')[1]))
    await state.set_state(AddItem.name)
    
    await callback.message.edit_text('введите название товара')


@admin.message(AdminProtect(), AddItem.name, F.text)
async def add_item_category(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItem.description)
    
    await message.answer('введите описание товара')


@admin.message(AdminProtect(), AddItem.description, F.text)
async def add_item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddItem.photo)
    
    await message.answer('отправьте фото товара')


@admin.message(AdminProtect(), AddItem.photo, F.photo)
async def add_item_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddItem.price)
    
    await message.answer('введите цену товара')


@admin.message(AdminProtect(), AddItem.photo, F.text)
async def error_photo(message: Message):
    await message.answer('отправьте фото товара, а не текст')


@admin.message(AdminProtect(), AddItem.price)
async def add_item_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    
    data = await state.get_data()
    await set_item(data)
    
    await message.answer('вы успешно добавили товар!')
    await message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(message.from_user.id))
    
    await state.clear()


# Удаление товара 
@admin.callback_query(AdminProtect(), DeleteItem.item_id, F.data == 'to_categories')
@admin.callback_query(AdminProtect(), F.data == 'delete_item')
async def delete_item(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteItem.category)
    
    await callback.answer('')
    await callback.message.edit_text('выберите категорию товара', 
                                    reply_markup=await kb.categories('apanel'))


@admin.callback_query(AdminProtect(), DeleteItem.category, F.data.startswith('category_'))
async def delete_item_from_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteItem.item_id)
    
    await callback.answer('')
    
    category_id = int(callback.data.split('_')[1])
    await state.update_data(category_id=category_id)
    
    if await check_items_in_category(category_id):
        await callback.message.edit_text('выберите товар, который хотите удалить',
            reply_markup=await kb.items(category_id))
    else:
        await callback.message.edit_text('нет товаров для удаления', 
                                        reply_markup=await kb.items(category_id))


@admin.callback_query(AdminProtect(), DeleteItem.item_id)
async def alert_delete(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteItem.confirm)
    
    await callback.answer('')
    
    item = await get_item_by_id(int(callback.data.split('_')[1]))
    await state.update_data(item_id=item.id)
    
    await callback.message.edit_text(f'вы точно хотите удалить товар {item.name}?', 
                                    reply_markup=await kb.confirmation('delete'))


@admin.callback_query(AdminProtect(), DeleteItem.confirm)
async def deletion_item(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if callback.data == 'confirmation':
        item_id = data['item_id']
        await delete_item_from_bot(item_id)
        await delete_item_from_all_carts(item_id)
        
        await callback.answer('')
        await callback.message.answer('вы успешно удалили товар!')
        await callback.message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(callback.from_user.id))
        
        await state.clear()
    else:
        await state.set_state(DeleteItem.item_id)
        
        category_id = data['category_id']
        await callback.message.edit_text('выберите товар, который хотите удалить',
            reply_markup=await kb.items(category_id))


# Изменение данных о товаре
@admin.callback_query(AdminProtect(), EditItem.item_id, F.data == 'to_categories')
@admin.callback_query(AdminProtect(), F.data == 'edit_item')
async def edit_choose_item(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditItem.category)
    
    await callback.answer('')
    await callback.message.edit_text('выберите категорию товара', 
                                    reply_markup=await kb.categories('apanel'))


@admin.callback_query(AdminProtect(), EditItem.field, F.data == 'to_spec_category')
@admin.callback_query(AdminProtect(), EditItem.category, F.data.startswith('category_'))
async def edit_choose_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditItem.item_id)
    
    if callback.data == 'to_spec_category':
        data = await state.get_data()
        category_id = data['category_id']
    else:
        category_id = int(callback.data.split('_')[1])
        
    await state.update_data(category_id=category_id)
    await callback.answer('')
    
    if await check_items_in_category(category_id):
        await callback.message.edit_text('выберите товар, который хотите изменить',
            reply_markup=await kb.items(category_id))
    else:
        await callback.message.edit_text('нет товаров для изменения', 
                                        reply_markup=await kb.items(category_id))


@admin.callback_query(AdminProtect(), EditItem.item_id, F.data.startswith('item_'))
async def edition_field(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_id=int(callback.data.split('_')[1]))
    await state.set_state(EditItem.field)
    
    await callback.answer('')
    await callback.message.edit_text('выберите раздел, который хотите изменить', reply_markup=kb.edit)


@admin.callback_query(AdminProtect(), EditItem.field)
async def edition_item(callback: CallbackQuery, state: FSMContext):
    await state.update_data(field=callback.data)
    
    await callback.answer('')
    
    if callback.data == 'photo':
        await state.set_state(EditItem.photo)
        await callback.message.edit_text('вставьте фотографию')
    elif callback.data == 'price':
        await state.set_state(EditItem.price)
        await callback.message.edit_text('напишите новую цену товара')
    else:
        await state.set_state(EditItem.content)
        if callback.data == 'name':
            await callback.message.edit_text('напишите новое название товара')
            await state.update_data(pole='название')
        else: 
            await callback.message.edit_text('напишите новое описание товара')
            await state.update_data(pole='описание')


@admin.message(AdminProtect(), EditItem.photo, F.photo)
async def edition_photo(message: Message, state: FSMContext):
    await state.update_data(content=message.photo[-1].file_id)
    
    data = await state.get_data()
    await edit_item(data)
    
    await message.answer('вы успешно изменили фотографию товара!')
    await message.answer('вы вернулись главное меню 💌', reply_markup=await kb.kb_main(message.from_user.id))
    
    await state.clear()


@admin.message(AdminProtect(), EditItem.price)
async def edition_text(message: Message, state: FSMContext):
    await state.update_data(content=int(message.text))
    data = await state.get_data()
    
    await edit_item(data)
    
    await message.answer('вы успешно изменили цену товара!')
    await message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(message.from_user.id))
    
    await state.clear()


@admin.message(AdminProtect(), EditItem.content)
async def edition_text(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    data = await state.get_data()
    
    await edit_item(data)
    
    await message.answer(f'вы успешно изменили {data['pole']} товара!')
    await message.answer('вы вернулись в главное меню 💌', reply_markup=await kb.kb_main(message.from_user.id))
    
    await state.clear()
