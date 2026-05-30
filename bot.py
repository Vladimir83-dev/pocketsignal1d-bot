import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Берем токен из настроек Render, которые мы только что заполнили
API_TOKEN = os.getenv('BOT_TOKEN', '7776421169:AAHvwjNRCzadSmR2KMraUJNRxWpehK3K5mc')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Кнопки
register_url = "https://u3.shortink.io/register?utm_campaign=819083&utm_source=affiliate&utm_medium=sr&a=Df4ek3JlsrzSid&ac=tgchanel&code=50START"

# Кнопки языков
lang_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
    InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
)

# Кнопки стратегий
strategy_btn_uk = InlineKeyboardMarkup().add(
    InlineKeyboardButton("📘 Отримати стратегію", callback_data="strategy_uk")
)
strategy_btn_en = InlineKeyboardMarkup().add(
    InlineKeyboardButton("📘 Get strategy", callback_data="strategy_en")
)

register_btn = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🔗 Зареєструватися", url=register_url)
)
register_btn_en = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🔗 Register", url=register_url)
)

# Состояния пользователей
user_lang = {}
registered_users = set()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    registered_users.add(message.chat.id)
    await message.answer("Choose your language / Обери мову:", reply_markup=lang_kb)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_lang[callback_query.from_user.id] = lang
    await bot.answer_callback_query(callback_query.id)
    
    if lang == 'uk':
        msg_text = "Привіт! Це PocketSignal1D 🤖\n\nЯ надсилатиму тобі сигнали для торгівлі на Pocket Option.\n\nПочни із реєстрації:"
        await bot.send_message(callback_query.from_user.id, msg_text, reply_markup=register_btn)
        await bot.send_message(callback_query.from_user.id, "📘 Хочеш дізнатися просту стратегію?", reply_markup=strategy_btn_uk)
    else:
        msg_text = "Hi! This is PocketSignal1D 🤖\n\nI will send you trading signals for Pocket Option.\n\nStart with registration:"
        await bot.send_message(callback_query.from_user.id, msg_text, reply_markup=register_btn_en)
        await bot.send_message(callback_query.from_user.id, "📘 Want a simple strategy?", reply_markup=strategy_btn_en)

@dp.callback_query_handler(lambda c: c.data == 'strategy_uk')
async def strategy_info_uk(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    strategy_text = (
        "Стратегія '3 із 5':\n\n"
        "1. Обери EUR/USD.\n"
        "2. Увімкни індикатор RSI.\n"
        "3. Якщо RSI < 30 — став ВГОРУ.\n"
        "4. Якщо RSI > 70 — став ВНИЗ.\n"
        "5. Зроби 5 угод по $1.\n"
        "3+ угоди в плюс — ти в заробітку 💸"
    )
    await bot.send_message(callback_query.from_user.id, strategy_text)

@dp.callback_query_handler(lambda c: c.data == 'strategy_en')
async def strategy_info_en(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    strategy_text = (
        "'3 of 5' Strategy:\n\n"
        "1. Choose EUR/USD.\n"
        "2. Enable RSI indicator.\n"
        "3. If RSI < 30 — trade UP.\n"
        "4. If RSI > 70 — trade DOWN.\n"
        "5. Make 5 trades of $1.\n"
        "If 3+ are in profit — you win 💸"
    )
    await bot.send_message(callback_query.from_user.id, strategy_text)

# Фейковые сигналы (рандом)
assets = ["EUR/USD", "GBP/USD", "BTC/USD", "ETH/USD"]
directions = ["ВГОРУ", "ВНИЗ"]
directions_en = ["UP", "DOWN"]

async def send_fake_signals():
    while True:
        await asyncio.sleep(600)  # каждые 10 минут
        if not registered_users:
            continue
        for chat_id in list(registered_users):
            try:
                lang = user_lang.get(chat_id, 'uk')
                if lang == 'uk':
                    signal = f"💡 Сигнал:\nАктив: {random.choice(assets)}\nНапрям: {random.choice(directions)}\nЧас: {random.randint(1,3)} хвилини\nСтавка: $1"
                else:
                    signal = f"💡 Signal:\nAsset: {random.choice(assets)}\nDirection: {random.choice(directions_en)}\nTime: {random.randint(1,3)} minutes\nAmount: $1"
                await bot.send_message(chat_id, signal)
            except Exception as e:
                logging.error(f"Ошибка отправки сигнала пользователю {chat_id}: {e}")

@dp.message_handler()
async def handle_all(message: types.Message):
    registered_users.add(message.chat.id)

# Запуск бота
async def on_startup(_):
    asyncio.create_task(send_fake_signals())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
