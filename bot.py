import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import time

# إعداد متغيرات البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# إعداد الرؤوس لطلب CoinMarketCap
headers = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

def get_top_300_memes():
    params = {"start": "1", "limit": "300", "convert": "USD"}
    response = requests.get(CMC_URL, headers=headers, params=params).json()
    coins = []
    for coin in response.get("data", []):
        symbol = coin["symbol"]
        coins.append(symbol)
    return coins

def fetch_ohlcv(symbol, limit=200):
    url = f"https://min-api.cryptocompare.com/data/v2/histoday"
    params = {"fsym": symbol, "tsym": "USD", "limit": limit}
    r = requests.get(url, params=params).json()
    data = r.get("Data", {}).get("Data", [])
    if not data:
        return None
    df = pd.DataFrame(data)
    df['close'] = df['close'].astype(float)
    return df

def generate_chart(df, symbol):
    plt.figure(figsize=(10,4))
    plt.plot(df['close'], label='Close')
    plt.plot(df['close'].ta.ema(length=50), label='EMA50')
    plt.plot(df['close'].ta.ema(length=200), label='EMA200')
    plt.title(f"{symbol} Price Chart")
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def check_conditions_and_alert():
    coins = get_top_300_memes()
    for symbol in coins:
        try:
            df = fetch_ohlcv(symbol)
            if df is None or df.empty:
                continue
            ema50 = df['close'].ta.ema(length=50).iloc[-1]
            ema200 = df['close'].ta.ema(length=200).iloc[-1]
            rsi = df['close'].ta.rsi(length=14).iloc[-1]
            price = df['close'].iloc[-1]
            
            if price > ema50 > ema200 and rsi >= 40:
                chart = generate_chart(df, symbol)
                bot.send_photo(chat_id=CHAT_ID, photo=chart,
                               caption=f"✅ {symbol} met the condition!\nPrice: {price:.2f}\nEMA50: {ema50:.2f}\nEMA200: {ema200:.2f}\nRSI: {rsi:.2f}")
            else:
                print(f"Checked {symbol}, conditions not met.")
        except Exception as e:
            print(f"Error with {symbol}: {e}")

if __name__ == "__main__":
    print("🤖 Bot started (300 coins + EMA & RSI alerts).")
    while True:
        check_conditions_and_alert()
        time.sleep(300)  # كل 5 دقائق
