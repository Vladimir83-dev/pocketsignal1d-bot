# --- АНАЛИЗ РЫНКА (ICHIMOKU) ---
# Расширенный список активов (выбираем самые волатильные, которые есть на Pocket Option)
assets = [
    "BTC/USDT", "ETH/USDT", "LTC/USDT", "SOL/USDT", 
    "XRP/USDT", "DOGE/USDT", "ADA/USDT", "DOT/USDT",
    "EUR/USDT", "GBP/USDT", "AUD/USDT"  # Фиатные пары к стейблкоину на бирже
]

# Используем биржу KuCoin — на ней есть и крипта, и пары EUR/USDT, GBP/USDT
exchange = ccxt.kucoin({'enableRateLimit': True})

async def analyze_ichimoku(symbol):
    try:
        # Запрашиваем последние 100 минутных свечей
        bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        if not bars:
            return None
            
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Расчет Ишимоку
        ichimoku, period = ta.ichimoku(df['high'], df['low'], df['close'])
        
        if ichimoku is None or df.empty:
            return None

        # Берём последние значения индикаторов
        last_close = df['close'].iloc[-1]
        tenkan = ichimoku['ITS_9'].iloc[-1]
        kijun = ichimoku['IKS_26'].iloc[-1]
        span_a = ichimoku['ISA_9'].iloc[-1]
        span_b = ichimoku['ISB_26'].iloc[-1]
        
        # Предыдущие значения для фиксации пересечения
        prev_tenkan = ichimoku['ITS_9'].iloc[-2]
        prev_kijun = ichimoku['IKS_26'].iloc[-2]

        # Условия стратегии (Линии Ишимоку)
        if prev_tenkan <= prev_kijun and tenkan > kijun and last_close > max(span_a, span_b):
            return "UP"
        
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
                # Делаем красивое имя для Pocket Option (например, EUR/USDT -> EUR/USD)
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
            
            # Небольшая пауза между запросами к разным активам, чтобы биржа не заблокировала
            await asyncio.sleep(2)
                        
        # Пауза перед следующим полным кругом сканирования рынка
        await asyncio.sleep(20)
