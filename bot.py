import asyncio
import logging
import random
import os
import ccxt
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

API_TOKEN = os.getenv('BOT_TOKEN', '7776421169:AAHvwjNRCzadSmR2KMraUJNRxWpehK3K5mc')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Кнопки
register_url = "https://u3.shortink.io/register?utm_campaign=819083&utm_source=affiliate&utm_medium=sr&a=Df4ek3JlsrzSid&ac=tgchanel&code=50START"

lang_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
    InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
)

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
        msg_text = "Привіт! Це PocketSignal1D 🤖\n\nЯ надсилатиму тобі реальні сигнали на основі Облака Ішимоку.\n\nПочни із реєстрації:"
        await bot.send_message(callback_query.from_user.id, msg_text, reply_markup=register_btn)
        await bot.send_message(callback_query.from_user.id, "📘 Хочеш дізнатися просту стратегію?", reply_markup=strategy_btn_uk)
    else:
        msg_text = "Hi! This is PocketSignal1D 🤖\n\nI will send you real signals based on Ichimoku Cloud.\n\nStart with registration:"
        await bot.send_message(callback_query.from_user.id, msg_text, reply_markup=register_btn_en)
        await bot.send_message(callback_query.from_user.id, "📘 Want a simple strategy?", reply_markup=strategy_btn_en)

@dp.callback_query_handler(lambda c: c.data == 'strategy_uk')
async def strategy_info_uk(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    strategy_text = (
        "Стратегія 'Ichimoku Скальпінг':\n\n"
        "1. Бот аналізує графік крипти (Таймфрейм 1м).\n"
        "2. Пересічення ліній Тенкан і Кіджун дає точний імпульс.\n"
        "3. Сигнал 'ВГОРУ' — купуємо, коли ціна вище хмари.\n"
        "4. Сигнал 'ВНИЗ' — продаємо, коли ціна нижче хмари.\n"
        "5. Час угоди на Pocket Option: 1-3 хвилини."
    )
    await bot.send_message(callback_query.from_user.id, strategy_text)

@dp.callback_query_handler(lambda c: c.data == 'strategy_en')
async def strategy_info_en(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    strategy_text = (
        "'Ichimoku Scalping' Strategy:\n\n"
        "1. The bot analyzes crypto charts (1m timeframe).\n"
        "2. Tenkan and Kijun lines crossing gives a precise impulse.\n"
        "3. 'UP' signal — trade when the price is above the cloud.\n"
        "4. 'DOWN' signal — trade when the price is below the cloud.\n"
        "5. Trade expiration on Pocket Option: 1-3 minutes."
    )
    await bot.send_message(callback_query.from_user.id, strategy_text)

# --- АНАЛИЗ РЫНКА (ICHIMOKU РУЧНОЙ РАСЧЕТ) ---
assets = [
    "BTC/USDT", "ETH/USDT", "LTC/USDT", "SOL/USDT", 
    "XRP/USDT", "DOGE/USDT", "ADA/USDT", "DOT/USDT"
]

exchange = ccxt.kucoin({'enableRateLimit': True})

async def analyze_ichimoku(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        if not bars or len(bars) < 60:
            return None
            
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Чистая математика индикатора Ишимоку без сторонних библиотек
        # Tenkan-sen (9-period high + 9-period low) / 2
        nine_high = df['high'].rolling(window=9).max()
        nine_low = df['low'].rolling(window=9).min()
        df['tenkan'] = (nine_high + nine_low) / 2

        # Kijun-sen (26-period high + 26-period low) / 2
        twentysix_high = df['high'].rolling(window=26).max()
        twentysix_low = df['low'].rolling(window=26).min()
        df['kijun'] = (twentysix_high + twentysix_low) / 2

        # Senkou Span A (Tenkan + Kijun) / 2, сдвинутый вперед на 26 периодов
        df['span_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)

        # Senkou Span B (52-period high + 52-period low) / 2, сдвинутый вперед на 26 периодов
        fiftytwo_high = df['high'].rolling(window=52).max()
        fiftytwo_low = df['low'].rolling(window=52).min()
        df['span_b'] = ((fiftytwo_high + fiftytwo_low) / 2).shift(26)

        # Проверяем, что все строки рассчитались
        if df['span_b'].isna().iloc[-1] or df['span_a'].isna().iloc[-1]:
            return None

        # Текущие значения
        last_close = df['close'].iloc[-1]
        tenkan = df['tenkan'].iloc[-1]
        kijun = df['kijun'].iloc[-1]
        span_a = df['span_a'].iloc[-1]
        span_b = df['span_b'].iloc[-1]
        
        # Предыдущие значения для фиксации пересечения (кросса)
        prev_tenkan = df['tenkan'].iloc[-2]
        prev_kijun = df['kijun'].iloc[-2]

        # Логика сигналов
        # Золотой крест выше Облака
        if prev_tenkan <= prev_kijun and tenkan > kijun and last_close > max(span_a, span_b):
            return "UP"
        
        # Мертвый крест ниже Облака
        elif prev_tenkan >= prev_kijun and tenkan < kijun and last_close < min(span_a, span_b):
            return "DOWN"
            
    except Exception as e:
        logging.error(f"Ошибка анализа {symbol}: {e}")
    return None

async def market_scanner():
    while True:
        if not registered_users:
            await asyncio.sleep(10)
            continue
            
        for asset in assets:
            direction = await analyze_ichimoku(asset)
            
            if direction:
                clean_asset = asset.replace('USDT', 'USD')
                
                for chat_id in list(registered_users):
                    try:
                        lang = user_lang.get(chat_id, 'uk')
                        time_exp = random.randint(1, 3)
                        if lang == 'uk':
                            dir_text = "ВГОРУ 📈" if direction == "UP" else "ВНИЗ 📉"
                            signal = f"📊 *НОВИЙ СИГНАЛ (Ichimoku)*\n\n🔹 *Актив:* {clean_asset}\n🔹 *Напрям:* {dir_text}\n🔹 *Час експірації:* {time_exp} хв.\n\n⚠️ _Аналіз проведено на 1-хвилинному таймфреймі фінансових ринків._"
                        else:
                            dir_text = "UP 📈" if direction == "UP" else "DOWN 📉"
                            signal = f"📊 *NEW SIGNAL (Ichimoku)*\n\n🔹 *Asset:* {clean_asset}\n🔹 *Direction:* {dir_text}\n🔹 *Expiration:* {time_exp} min.\n\n⚠️ _Analysis executed on 1m timeframe._"
                        
                        await bot.send_message(chat_id, signal, parse_mode="Markdown")
                    except Exception as e:
                        logging.error(f"Ошибка отправки сообщения {chat_id}: {e}")
            
            await asyncio.sleep(2)
                        
        await asyncio.sleep(20)

@dp.message_handler()
async def handle_all(message: types.Message):
    registered_users.add(message.chat.id)

async def on_startup(_):
    asyncio.create_task(market_scanner())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
