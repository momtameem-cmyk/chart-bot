import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# ======= إعداد المتغيرات =======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# ======= جلب أفضل 200 عملة ميم من CoinGecko =======
def get_top_meme_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    meme_coins = [coin['id'] for coin in data if 'meme' in coin.get('symbol','').lower() or 'doge' in coin['id'] or 'shiba' in coin['id']]
    return meme_coins[:200]

MEME_COINS = get_top_meme_coins()

# ======= إشعار بدء البوت =======
async def send_start_message():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")

# ======= جلب البيانات التاريخية =======
def fetch_price_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "30", "interval": "hourly"}
    resp = requests.get(url, params=params).json()
    prices = resp.get("prices")
    if prices:
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    return None

# ======= توليد الشارت =======
def generate_chart(df, coin_id):
    df["EMA50"] = ta.ema(df["price"], length=50)
    df["EMA200"] = ta.ema(df["price"], length=200)
    df["RSI"] = ta.rsi(df["price"], length=14)
    
    plt.figure(figsize=(10,5))
    plt.plot(df["timestamp"], df["price"], label="Price", color="blue")
    plt.plot(df["timestamp"], df["EMA50"], label="EMA50", color="orange")
    plt.plot(df["timestamp"], df["EMA200"], label="EMA200", color="red")
    plt.title(f"{coin_id.upper()} Price Chart")
    plt.legend()
    
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# ======= التحقق من شروط EMA/RSI =======
async def check_conditions():
    for coin in MEME_COINS:
        df = fetch_price_data(coin)
        if df is None or df.empty:
            continue
        df["EMA50"] = ta.ema(df["price"], length=50)
        df["EMA200"] = ta.ema(df["price"], length=200)
        df["RSI"] = ta.rsi(df["price"], length=14)
        
        if df["price"].iloc[-1] > df["EMA200"].iloc[-1] and df["EMA50"].iloc[-1] > df["EMA200"].iloc[-1] and df["RSI"].iloc[-1] > 40:
            chart_buf = generate_chart(df, coin)
            await bot.send_photo(chat_id=CHAT_ID, photo=chart_buf, caption=f"✅ {coin.upper()} meets EMA/RSI conditions!")

# ======= الحلقة الرئيسية =======
async def main_loop():
    await send_start_message()
    while True:
        try:
            await check_conditions()
        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error: {e}")
        await asyncio.sleep(3600)  # كل ساعة

if __name__ == "__main__":
    asyncio.run(main_loop())
