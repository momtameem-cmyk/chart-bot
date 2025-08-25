import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# =========================
# المتغيرات من .env
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة 300 عملة (رموزها في CoinMarketCap)
COINS = ["BTC","ETH","USDT","BNB","XRP","ADA","SOL","DOGE","DOT","MATIC"]  # أضف باقي الرموز حتى 300

HEADERS = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

# دالة لجلب الأسعار من CoinMarketCap
def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    response = requests.get(url, headers=HEADERS).json()
    try:
        price = response["data"][symbol]["quote"]["USD"]["price"]
        return price
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {symbol}: {e}")
        return None

# دالة لمراقبة EMA و RSI
def check_indicators(symbol, price_history):
    df = pd.DataFrame(price_history, columns=["price"])
    df['ema9'] = ta.ema(df['price'], length=9)
    df['ema21'] = ta.ema(df['price'], length=21)
    df['rsi'] = ta.rsi(df['price'], length=14)

    last_row = df.iloc[-1]

    # تقاطع EMA
    ema_cross = None
    if df['ema9'].iloc[-2] < df['ema21'].iloc[-2] and last_row['ema9'] > last_row['ema21']:
        ema_cross = "bullish"
    elif df['ema9'].iloc[-2] > df['ema21'].iloc[-2] and last_row['ema9'] < last_row['ema21']:
        ema_cross = "bearish"

    # RSI
    rsi_signal = None
    if last_row['rsi'] >= 45:
        rsi_signal = "above 45"

    return ema_cross, rsi_signal

# =========================
# المراقبة الرئيسية
# =========================
def main():
    bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (300 coins + EMA & RSI alerts).")
    
    # تهيئة بيانات الأسعار لكل عملة
    price_histories = {coin: [] for coin in COINS}

    while True:
        for coin in COINS:
            price = fetch_price(coin)
            if price is None:
                continue

            # إضافة السعر للتاريخ وحفظ آخر 50 نقطة
            price_histories[coin].append(price)
            if len(price_histories[coin]) > 50:
                price_histories[coin] = price_histories[coin][-50:]

            if len(price_histories[coin]) >= 21:  # على الأقل 21 نقطة للـ EMA
                try:
                    ema_cross, rsi_signal = check_indicators(coin, price_histories[coin])
                    if ema_cross or rsi_signal:
                        msg = f"📊 {coin} Alert:\n"
                        if ema_cross:
                            msg += f"EMA cross detected ({ema_cross})\n"
                        if rsi_signal:
                            msg += f"RSI reached {rsi_signal}\n"
                        bot.send_message(chat_id=CHAT_ID, text=msg)
                except Exception as e:
                    bot.send_message(chat_id=CHAT_ID, text=f"❌ Error processing {coin}: {e}")
            time.sleep(1)  # تقليل الضغط على API

if __name__ == "__main__":
    main()
