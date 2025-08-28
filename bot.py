import os
import time
import io
import pandas as pd
import pandas_ta as ta
import requests
import matplotlib.pyplot as plt
from telegram import Bot

# --- إعداد المتغيرات من env ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# --- جلب أفضل العملات الميمية من CoinGecko (200 عملة) ---
def get_top_meme_coins(limit=200):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False
        }
        response = requests.get(url, params=params)
        coins = response.json()
        meme_coins = [coin['id'] for coin in coins if 'meme' in coin.get('categories', []) or 'meme' in coin.get('name','').lower()]
        return meme_coins
    except Exception as e:
        print(f"Error fetching meme coins: {e}")
        return []

MEME_COINS = get_top_meme_coins()
print(f"Loaded {len(MEME_COINS)} meme coins.")

# --- دالة جلب البيانات التاريخية ---
def get_historical_data(coin_id, days=60):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    r = requests.get(url, params=params)
    data = r.json()
    prices = [p[1] for p in data.get('prices', [])]
    df = pd.DataFrame(prices, columns=['close'])
    return df

# --- دالة إنشاء الشارت ---
def plot_chart(df, coin_id):
    plt.figure(figsize=(10,5))
    plt.plot(df['close'], label='Close Price')
    plt.title(f"{coin_id.upper()} Price Chart")
    plt.xlabel('Time')
    plt.ylabel('Price (USD)')
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# --- تنفيذ البوت ---
def run_bot():
    try:
        bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
    except Exception as e:
        print(f"Failed to send start message: {e}")

    while True:
        for coin_id in MEME_COINS:
            try:
                df = get_historical_data(coin_id)
                if df.empty or len(df) < 50:
                    print(f"Not enough data for {coin_id}.")
                    continue

                df['EMA50'] = ta.ema(df['close'], length=50)
                df['EMA200'] = ta.ema(df['close'], length=200)
                df['RSI'] = ta.rsi(df['close'], length=14)

                latest = df.iloc[-1]
                if latest['close'] > latest['EMA50'] and latest['close'] > latest['EMA200'] and latest['RSI'] >= 40:
                    chart_buf = plot_chart(df, coin_id)
                    bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=chart_buf,
                        caption=f"✅ {coin_id.upper()} met conditions:\nPrice: {latest['close']:.4f}\nEMA50: {latest['EMA50']:.4f}\nEMA200: {latest['EMA200']:.4f}\nRSI: {latest['RSI']:.2f}"
                    )
                    print(f"Alert sent for {coin_id}.")
                else:
                    print(f"Checked {coin_id}, conditions not met.")
            except Exception as e:
                print(f"Error checking {coin_id}: {e}")
        time.sleep(300)  # كل 5 دقائق

if __name__ == "__main__":
    run_bot()
