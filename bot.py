import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة العملات
coins = ["BTC", "ETH", "ADA"]  # ضع هنا 300 عملة أو أكثر حسب احتياجك

# إعداد EMA و RSI
EMA_PERIOD = 20
RSI_PERIOD = 14
RSI_THRESHOLD = 45

# دالة لجلب الأسعار من CoinMarketCap
def get_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    response = requests.get(url, headers=headers).json()
    return float(response["data"][symbol]["quote"]["USD"]["price"])

# دالة لفحص التقاطع
def check_signals(df):
    ema = df['close'].ewm(span=EMA_PERIOD).mean()
    rsi = ta.rsi(df['close'], length=RSI_PERIOD)
    last_price = df['close'].iloc[-1]
    last_ema = ema.iloc[-1]
    last_rsi = rsi.iloc[-1]
    return last_price >= last_ema and last_rsi >= RSI_THRESHOLD

# الدالة الرئيسية
async def main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started.")
    while True:
        for coin in coins:
            try:
                price = get_price(coin)
                df = pd.DataFrame({"close": [price]})  # لو عندك تاريخ الأسعار ضعها هنا
                if check_signals(df):
                    await bot.send_message(chat_id=CHAT_ID, text=f"✅ {coin} crossed EMA and RSI >= {RSI_THRESHOLD}")
            except Exception as e:
                await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {coin}: {e}")
        await asyncio.sleep(60)  # تأخير 1 دقيقة

# تشغيل البوت
if __name__ == "__main__":
    asyncio.run(main())
