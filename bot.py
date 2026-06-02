import asyncio
import logging
import random
import os
import ccxt
import pandas as pd

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = os.getenv('BOT_TOKEN', '7776421169:AAHvwjNRCzadSmR2KMraUJNRxWpehK3K5mc')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# База данных пользователей (сохраняется в оперативной памяти)
registered_users = set()
user_lang = {}

# Клавиатуры выбора языка
lang_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
    InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
)

# Список активов (самые ликвидные, которые есть на Pocket Option)
assets = ["BTC/USDT", "ETH/USDT", "LTC/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT"]

# Подключение к бирже KuCoin
exchange = ccxt.kucoin({'enableRateLimit': True})

# --- МАТЕМАТИЧЕСКИЙ АНАЛИЗ (RSI + СКОЛЬЗЯЩИЕ СРЕДНИЕ) ---
async def generate_market_signal(symbol):
    try:
        # Запрашиваем 50 минутных свечей
        bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        if not bars or len(bars) < 20:
            return None
            
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 1. Расчет RSI (период 14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 2. Расчет быстрой Скользящей Средней (SMA 5)
        df['sma'] = df['close'].rolling(window=5).mean()
        
        # Получаем самые свежие значения
        last_rsi = df['rsi'].iloc[-1]
        last_close = df['close'].iloc[-1]
        last_sma = df['sma'].iloc[-1]
        
        if pd.isna(last_rsi) or pd.isna(last_sma):
            return None

        # Логика стратегии скальпинга:
        # Сигнал ВВЕРХ: рынок перепродан (RSI < 35) И цена начинает разворот вверх (выше SMA)
        if last_rsi < 35 and last_close > last_sma:
            return "UP"
            
        # Сигнал ВНИЗ: рынок перекуплен (RSI > 65) И цена начинает разворот вниз (ниже SMA)
        elif last_rsi > 65 and last_close < last_sma:
            return "DOWN"
            
    except Exception as e:
        logging.error(f"Ошибка при анализе актива {symbol}: {e}")
    return None

# --- ФОНОВЫЙ СКАНЕР РЫНКА ---
async def market_scanner():
    logging.info("Фоновый сканер рынка успешно запущен!")
    while True:
        try:
            if not registered_users:
                logging.info("Сканер спит: в боте еще нет активных чатов. Напишите /start")
                await asyncio.sleep(10)
                continue
                
            logging.info(f"Начало круга сканирования для {len(assets)} активов...")
            
            for asset in assets:
                direction = await generate_market_signal(asset)
                
                if direction:
                    clean_asset = asset.replace('USDT', 'USD')
                    logging.info(f"🔥 НАЙДЕН СИГНАЛ: {clean_asset} -> {direction}")
                    
                    for chat_id in list(registered_users):
                        try:
                            lang = user_lang.get(chat_id, 'uk')
                            time_exp = random.randint(1, 3)
                            
                            if lang == 'uk':
                                dir_text = "ВГОРУ 📈" if direction == "UP" else "ВНИЗ 📉"
                                signal = f"📊 *НОВИЙ СИГНАЛ (Скальпінг)*\n\n🔹 *Актив:* {clean_asset}\n🔹 *Напрям:* {dir_text}\n🔹 *Час експірації:* {time_exp} хв.\n\n⚠️ _Аналіз проведено автоматично за індикаторами RSI та SMA._"
                            else:
                                dir_text = "UP 📈" if direction == "UP" else "DOWN 📉"
                                signal = f"📊 *NEW SIGNAL (Scalping)*\n\n🔹 *Asset:* {clean_asset}\n🔹 *Direction:* {dir_text}\n🔹 *Expiration:* {time_exp} min.\n\n⚠️ _Executed via RSI + SMA mathematical model._"
                            
                            await bot.send_message(chat_id, signal, parse_mode="Markdown")
                        except Exception as e:
                            logging.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
                
                # Защита от бана со стороны биржи (пауза между запросами)
                await asyncio.sleep(2)
                
            logging.info("Круг завершен. Пауза 30 секунд перед следующей проверкой.")
            await asyncio.sleep(30)
            
        except Exception as e:
            logging.error(f"Критическая ошибка в цикле сканера: {e}")
            await asyncio.sleep(10)

# --- ОБРАБОТЧИКИ КОМАНД TELEGRAM ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    registered_users.add(message.chat.id)
    logging.info(f"Пользователь {message.chat.id} добавился в базу.")
    await message.answer("Обери мову / Choose language:", reply_markup=lang_kb)

@dp.message_handler(commands=['test'])
async def cmd_test(message: types.Message):
    """Принудительный моментальный сигнал для проверки работоспособности"""
    registered_users.add(message.chat.id)
    test_asset = random.choice(assets).replace('USDT', 'USD')
    test_dir = random.choice(["UP", "DOWN"])
    dir_text = "ВГОРУ 📈" if test_dir == "UP" else "ВНИЗ 📉"
    
    test_msg = f"⚙️ *ТЕСТ СВЯЗИ — БОТ РАБОТАЕТ*\n\n🔹 *Актив:* {test_asset}\n🔹 *Напрям:* {dir_text}\n🔹 *Час експірації:* 2 хв.\n\n_Если вы видите это сообщение, значит бот успешно подключен к Telegram и сканирует рынок в фоне._"
    await message.answer(test_msg, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def cb_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_lang[callback_query.from_user.id] = lang
    registered_users.add(callback_query.from_user.id)
    await bot.answer_callback_query(callback_query.id)
    
    if lang == 'uk':
        await bot.send_message(callback_query.from_user.id, "✅ Мову встановлено! Сканер запущено. Очікуйте на автоматичні сигнали.\n\nВы можете в будь-який момент ввести команду /test щоб перевірити роботу.")
    else:
        await bot.send_message(callback_query.from_user.id, "✅ Language set successfully! Scanner is active. Wait for automatic signals.\n\nType /test anytime to check status.")

@dp.message_handler()
async def handle_text_messages(message: types.Message):
    # Если пользователь просто что-то пишет, фиксируем его ID, чтобы он получал сигналы
    registered_users.add(message.chat.id)

async def on_startup(_):
    # Запуск сканера рынка отдельной фоновой задачей
    asyncio.create_task(market_scanner())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

