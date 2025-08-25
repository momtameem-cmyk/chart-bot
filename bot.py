import os
import asyncio
import pandas as pd
import pandas_ta as ta
import requests
from telegram import Bot

# ======================================
# إعداد المتغيرات من environment
# ======================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CMC_API_KEY = os.environ.get("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة العملات (أو يمكن جلبها من CMC)
COINS = ["BTC", "ETH", "ADA", "XRP", "SOL"]  # مثال، ضع 300 عملة حسب حاجتك

# ======================================
# دالة لجلب الأسعار من CoinMarketCap
# ======================================
async def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10).json()
        price = r["data"][symbol]["quote"]["USD"]["price"]
        return price
    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {symbol}: {e}")
        return None

# ======================================
# دالة لإرسال إشعارات EMA & RSI
# ======================================
async def check_alerts(symbol):
    price = await fetch_price(symbol)
    if price is None:
        return

    df = pd.DataFrame({"close": [price]})  # مثال مبسط على البيانات
    try:
        df["EMA10"] = ta.ema(df["close"], length=10)
        df["EMA50"] = ta.ema(df["close"], length=50)
        df["RSI"] = ta.rsi(df["close"], length=14)

        ema_cross = df["EMA10"].iloc[-1] > df["EMA50"].iloc[-1]
        rsi_condition = df["RSI"].iloc[-1] > 45

        if ema_cross and rsi_condition:
            await bot.send_message(chat_id=CHAT_ID, text=f"✅ {symbol} reached EMA cross + RSI>45")
    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error processing {symbol}: {e}")

# ======================================
# دالة الفحص الدوري لكل العملات
# ======================================
async def main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (EMA & RSI alerts).")
    while True:
        tasks = [check_alerts(symbol) for symbol in COINS]
        await asyncio.gather(*tasks)
        await asyncio.sleep(60)  # تأخير 1 دقيقة بين الفحوصات

if __name__ == "__main__":
    asyncio.run(main())
