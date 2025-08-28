import os
import time
import asyncio
import pandas as pd
import pandas_ta as ta
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# ===========================
# إعداد المتغيرات من البيئة
# ===========================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CMC_API_KEY = os.environ.get("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# ===========================
# أفضل 200 عملة ميم (تجنب التكرار)
# ===========================
MEME_COINS = [
    "DOGE","SHIB","PEPE","FLUF","ELON","AKITA","KISHU","SAFE","SAMO",
    "MONA","CULT","WOJ","HOGE","PIG","BABYDOGE","MIST","HOKK","KAWA",
    "SHIBX","FLOKI","SMILE","BONE","LEASH","KISHUINU","POM","HUSKY",
    # ... أكمل بقية الرموز حتى تصل 200 رمز ...
]

# ===========================
# دالة جلب الأسعار
# ===========================
def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbol, "convert": "USD"}
    try:
        response = requests.get(url, headers=headers, params=params).json()
        price = response["data"][symbol]["quote"]["USD"]["price"]
        return price
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ===========================
# دالة إنشاء الشارت
# ===========================
def create_chart(df, symbol):
    plt.figure(figsize=(10,5))
    plt.plot(df['close'], label='Close Price')
    plt.plot(df['EMA50'], label='EMA50')
    plt.plot(df['EMA200'], label='EMA200')
    plt.title(f"{symbol} Chart")
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# ===========================
# فحص كل عملة
# ===========================
async def check_coin(symbol):
    try:
        # جلب آخر 200 سعر افتراضي
        prices = []
        for i in range(200):
            price = fetch_price(symbol)
            if price:
                prices.append(price)
            time.sleep(1)
        df = pd.DataFrame(prices, columns=['close'])
        df['EMA50'] = ta.ema(df['close'], length=50)
        df['EMA200'] = ta.ema(df['close'], length=200)
        df['RSI'] = ta.rsi(df['close'], length=14)

        # تحقق الشرط
        if df['EMA50'].iloc[-1] > df['EMA200'].iloc[-1] and df['RSI'].iloc[-1] >= 40:
            chart = create_chart(df, symbol)
            await bot.send_photo(chat_id=CHAT_ID, photo=chart,
                                 caption=f"✅ {symbol} meets conditions:\nEMA50 > EMA200\nRSI: {df['RSI'].iloc[-1]:.2f}")
        else:
            print(f"{symbol} conditions not met.")
    except Exception as e:
        print(f"Error processing {symbol}: {e}")

# ===========================
# دالة رئيسية للتشغيل المستمر
# ===========================
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
    while True:
        tasks = [check_coin(symbol) for symbol in MEME_COINS]
        await asyncio.gather(*tasks)
        print("Waiting 15 minutes for next check...")
        await asyncio.sleep(900)  # 15 دقيقة

# ===========================
# تشغيل البوت
# ===========================
if __name__ == "__main__":
    asyncio.run(main())
