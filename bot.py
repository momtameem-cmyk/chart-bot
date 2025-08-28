import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# ---- متغيرات البيئة ----
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# ---- دالة لجلب أفضل 200 عملة ميم من CoinMarketCap ----
def get_top_meme_coins(limit=200):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"limit": 500, "sort": "market_cap", "sort_dir": "desc"}
    try:
        data = requests.get(url, headers=headers, params=params).json()
        meme_coins = [coin['symbol'] for coin in data.get('data', []) if 'meme' in coin.get('tags', [])]
        return meme_coins[:limit]
    except Exception as e:
        print("Error fetching meme coins:", e)
        return []

# ---- جلب العملات ----
MEME_COINS = get_top_meme_coins()
print(f"Loaded {len(MEME_COINS)} meme coins.")

# ---- دالة للتحقق من EMA & RSI وإرسال إشعار مع chart ----
async def check_and_notify(symbol):
    try:
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        params = {"symbol": symbol}
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        data = requests.get(url, headers=headers, params=params).json()
        price = data['data'][symbol]['quote']['USD']['price']

        df = pd.DataFrame({"close": [price * (1 + i/100) for i in range(50)]})
        df["EMA50"] = ta.ema(df["close"], length=50)
        df["EMA200"] = ta.ema(df["close"], length=200)
        df["RSI"] = ta.rsi(df["close"], length=14)

        last_row = df.iloc[-1]
        if last_row["close"] > last_row["EMA50"] and last_row["close"] > last_row["EMA200"] and last_row["RSI"] >= 40:
            plt.figure(figsize=(8,4))
            plt.plot(df["close"], label="Price")
            plt.plot(df["EMA50"], label="EMA50")
            plt.plot(df["EMA200"], label="EMA200")
            plt.title(f"{symbol} Chart")
            plt.legend()
            buf = BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()
            await bot.send_photo(chat_id=CHAT_ID, photo=buf, caption=f"📈 {symbol} Alert!\nPrice above EMA50 & EMA200, RSI: {last_row['RSI']:.2f}")
        else:
            print(f"{symbol}: conditions not met.")
    except Exception as e:
        print(f"Error checking {symbol}: {e}")

# ---- دالة التشغيل الرئيسية ----
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
    while True:
        tasks = [check_and_notify(symbol) for symbol in MEME_COINS]
        await asyncio.gather(*tasks)
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
