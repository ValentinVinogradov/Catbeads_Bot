from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.database.requests import (
    get_users, set_item, 
    delete_item_from_bot, 
    check_items_in_category, 
    edit_item, 
    delete_item_from_all_carts
)
from config import ADMINS


admin = Router()


class Newsletter(StatesGroup):
    message = State()
    confirm = State()


class AddItem(StatesGroup):
    
    name = State()
    category = State()
    description = State()
    photo = State()
    price = State()


class DeleteItem(StatesGroup):
    
    category = State()
    item_id = State()


class EditItem(StatesGroup):
    
    category = State()
    item_id = State()
    field = State()
    
    photo = State()
    text = State()


class AdminProtect(Filter):
    async def __call__(self, message: Message):
        
        # Наши айди
        return message.from_user.id in ADMINS


# Админ-панель

# Рассылка
@admin.message(AdminProtect(), Command('apanel'))
async def apanel(message: Message):
    await message.answer('Возможные команды:\n\n/newsletter - Запустить рассылку\n\n/add_item - Добавить товар\
        \n\n/edit_item - Изменить товар\n\n/delete_item - Удалить товар')


@admin.callback_query(AdminProtect(), Newsletter.confirm, F.data == 'cancel_newsletter')
@admin.message(AdminProtect(), Command('newsletter'))
async def newsletter(message: Message | CallbackQuery, state: FSMContext):
    await state.set_state(Newsletter.message)
    text = 'Отправьте сообщение, которые хотите разослать всем пользователям'
    if isinstance(message, Message):
        await message.answer(text, reply_markup=kb.to_main)
    else:
        await message.message.edit_text(text, reply_markup=kb.to_main)


@admin.message(AdminProtect(), Newsletter.message)
async def confirm_newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.confirm)
    await state.update_data(message_id=message.message_id)
    await message.answer("Отправить рассылку?", reply_markup=kb.confirmation)


@admin.callback_query(AdminProtect(), Newsletter.confirm, F.data == 'confirmation')
async def newsletter_message(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data['message_id']
    await callback.message.answer('Подождите... идёт рассылка.')
    for user in await get_users():
        try:
            await callback.message.bot.copy_message(chat_id=user.tg_id, from_chat_id=callback.message.chat.id, message_id=message_id)
        except:
            pass
    await callback.answer('Рассылка успешно завершена.', show_alert=True)
    await callback.message.answer('Вы вернулись в главное меню!', reply_markup=kb.main)
    await state.clear()


# Добавление товара в БД
@admin.message(AdminProtect(), Command('add_item'))
async def add_item(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddItem.name)
    await message.answer('Введите название товара', reply_markup=kb.to_main)


@admin.message(AdminProtect(), AddItem.name)
async def add_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItem.category)
    await message.answer('Выберите категорию товара', reply_markup=await kb.categories())


@admin.callback_query(AdminProtect(), AddItem.category)
async def add_item_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data.split('_')[1])
    await state.set_state(AddItem.description)
    await callback.answer('')
    await callback.message.answer('Введите описание товара')


@admin.message(AdminProtect(), AddItem.description)
async def add_item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddItem.photo)
    await message.answer('Отправьте фото товара')


@admin.message(AdminProtect(), AddItem.photo, F.photo)
async def add_item_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddItem.price)
    await message.answer('Введите цену товара товара')


@admin.message(AdminProtect(), AddItem.photo, F.text)
async def error_photo(message: Message):
    await message.answer('Отправьте фото товара, а не текст')


@admin.message(AdminProtect(), AddItem.price)
async def add_item_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    data = await state.get_data()
    await set_item(data)
    await message.answer('Вы успешно добавили товар', reply_markup=kb.to_main)
    await state.clear()


# Удаление товара 
@admin.callback_query(AdminProtect(), DeleteItem.item_id, F.data == 'to_categories')
@admin.message(AdminProtect(), Command('delete_item'))
async def delete_item(message: Message | CallbackQuery, state: FSMContext):
    await state.set_state(DeleteItem.category)
    if isinstance(message, Message):
        await message.answer('Выберите категорию товара', reply_markup=await kb.categories())
    else:
        await message.answer('')
        await message.message.edit_text('Выберите категорию товара', reply_markup=await kb.categories())


@admin.callback_query(AdminProtect(), DeleteItem.category, F.data.startswith('category_'))
async def delete_item_from_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteItem.item_id)
    await callback.answer('')
    if await check_items_in_category(callback.data.split('_')[1]):
        await callback.message.edit_text('Выберите товар, который хотите удалить',
            reply_markup=await kb.items(callback.data.split('_')[1]))
    else:
        await callback.message.edit_text('Нет товаров для удаления', reply_markup=await kb.items(callback.data.split('_')[1]))


@admin.callback_query(AdminProtect(), DeleteItem.item_id, F.data.startswith('item_'))
async def deletion_item(callback: CallbackQuery, state: FSMContext):
    await delete_item_from_bot(callback.data.split('_')[1])
    await delete_item_from_all_carts(callback.data.split('_')[1])
    await callback.answer('')
    await callback.message.edit_text('Вы успешно удалили товар', reply_markup=kb.to_main)
    await state.clear()


# Измение данных о товаре
@admin.callback_query(AdminProtect(), EditItem.item_id, F.data == 'to_categories')
@admin.message(AdminProtect(), Command('edit_item'))
async def edit_choose_item(message: Message | CallbackQuery, state: FSMContext):
    await state.set_state(EditItem.category)
    if isinstance(message, Message):
        await message.answer('Выберите категорию товара', reply_markup=await kb.categories())
    else:
        await message.answer('')
        await message.message.edit_text('Выберите категорию товара', reply_markup=await kb.categories())


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
        await callback.message.edit_text('Выберите товар, который хотите изменить',
            reply_markup=await kb.items(category_id))
    else:
        await callback.message.edit_text('Нет товаров для изменения', reply_markup=await kb.items(callback.data.split('_')[1]))


@admin.callback_query(AdminProtect(), EditItem.item_id, F.data.startswith('item_'))
async def edition_field(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_id=callback.data.split('_')[1])
    await state.set_state(EditItem.field)
    await callback.answer('')
    await callback.message.edit_text('Выберите раздел, который хотите изменить', reply_markup=kb.edit)


@admin.callback_query(AdminProtect(), EditItem.field, F.data.startswith('edit_'))
async def edition_item(callback: CallbackQuery, state: FSMContext):
    await state.update_data(field=callback.data.split('_')[1])
    await callback.answer('')
    if callback.data == 'edit_photo':
        await state.set_state(EditItem.photo)
        await callback.message.edit_text('Вставьте фотографию')
    else:
        await state.set_state(EditItem.text)
        if callback.data == 'edit_name':
            await callback.message.edit_text('Напишите измененное название товара')
        elif callback.data == 'edit_description':
            await callback.message.edit_text('Напишите измененное описание товара')
        else:
            await callback.message.edit_text('Напишите измененную цену товара')


@admin.message(AdminProtect(), EditItem.photo, F.photo)
async def edition_photo(message: Message, state: FSMContext):
    await state.update_data(text=message.photo[-1].file_id)
    data = await state.get_data()
    await edit_item(data)
    await message.answer('Вы успешно изменили товар', reply_markup=kb.to_main)
    await state.clear()


@admin.message(AdminProtect(), EditItem.text)
async def edition_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    await edit_item(data)
    await message.answer('Вы успешно изменили товар', reply_markup=kb.to_main)
    await state.clear()
    