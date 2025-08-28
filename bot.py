import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# جلب أفضل 200 عملة ميم من CoinGecko
def get_top_meme_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False,
    }
    resp = requests.get(url, params=params).json()
    meme_coins = [coin['id'] for coin in resp if 'meme' in coin.get('categories',[])]
    return meme_coins[:200]  # أعلى 200

MEME_COINS = get_top_meme_coins()

async def send_start_message():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts)."
    )

# جلب بيانات الأسعار
def fetch_price_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "30", "interval": "1h"}
    resp = requests.get(url, params=params).json()
    prices = resp.get("prices")
    if not prices:
        return None
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df['price'] = pd.to_numeric(df['price'])
    return df

# رسم chart
def generate_chart(df, coin):
    df['EMA50'] = df['price'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['price'].ewm(span=200, adjust=False).mean()
    df['RSI'] = ta.rsi(df['price'], length=14)

    plt.figure(figsize=(10,5))
    plt.plot(df['price'], label='Price')
    plt.plot(df['EMA50'], label='EMA50')
    plt.plot(df['EMA200'], label='EMA200')
    plt.title(f"{coin} Price Chart")
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# تحقق من الشروط
async def check_coin(coin_id):
    df = fetch_price_data(coin_id)
    if df is None or df.empty:
        return
    df['EMA50'] = df['price'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['price'].ewm(span=200, adjust=False).mean()
    df['RSI'] = ta.rsi(df['price'], length=14)
    
    # تحقق من الشرط على آخر سعر
    last = df.iloc[-1]
    if last['price'] > last['EMA200'] and last['price'] > last['EMA50'] and last['RSI'] >= 40:
        chart_img = generate_chart(df, coin_id)
        await bot.send_photo(chat_id=CHAT_ID, photo=chart_img, caption=f"✅ {coin_id.upper()} met the condition!")

# الحلقة الرئيسية
async def main_loop():
    await send_start_message()
    while True:
        for coin in MEME_COINS:
            try:
                await check_coin(coin)
            except Exception as e:
                print(f"Error checking {coin}: {e}")
        await asyncio.sleep(60*5)  # تحقق كل 5 دقائق

if __name__ == "__main__":
    asyncio.run(main_loop())
