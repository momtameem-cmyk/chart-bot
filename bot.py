import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import time

# قراءة المفاتيح من env
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

headers = {
    "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
    "Accepts": "application/json"
}

# جلب أفضل 200 عملة ميم
def get_top_meme_coins(limit=200):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=500"
    response = requests.get(url, headers=headers)
    data = response.json()
    meme_coins = [coin['symbol'] for coin in data.get('data', []) if 'meme' in coin.get('tags',[])]
    return meme_coins[:limit]

# جلب البيانات التاريخية مرة واحدة لكل العملة
def get_historical_prices(symbol):
    url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical"
    params = {"symbol": symbol, "interval": "daily", "count": 200}
    try:
        response = requests.get(url, headers=headers, params=params).json()
        quotes = response.get('data', {}).get('quotes', [])
        prices = [float(q['quote']['USD']['close']) for q in quotes]
        return prices
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

# حساب EMA و RSI
def calculate_indicators(prices):
    df = pd.DataFrame(prices, columns=['close'])
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

# إنشاء شارت
def create_chart(df, symbol):
    plt.figure(figsize=(10,5))
    plt.plot(df['close'], label='Close')
    plt.plot(df['EMA50'], label='EMA50')
    plt.plot(df['EMA200'], label='EMA200')
    plt.title(symbol)
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer

# التحقق من كل عملة وإرسال إشعار فقط عند تحقق الشرط
def check_and_alert(MEME_COINS):
    for symbol in MEME_COINS:
        prices = get_historical_prices(symbol)
        if len(prices) < 50:
            continue
        df = calculate_indicators(prices)
        if df['close'].iloc[-1] > df['EMA200'].iloc[-1] and df['close'].iloc[-1] > df['EMA50'].iloc[-1] and df['RSI'].iloc[-1] > 40:
            chart = create_chart(df, symbol)
            try:
                bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=f"✅ {symbol} meets the conditions.\nPrice: {df['close'].iloc[-1]:.4f}")
                print(f"{symbol}: Alert sent.")
            except Exception as e:
                print(f"Error sending alert for {symbol}: {e}")
        else:
            print(f"{symbol}: conditions not met.")

if __name__ == "__main__":
    MEME_COINS = get_top_meme_coins()
    print(f"Loaded {len(MEME_COINS)} meme coins.")
    try:
        bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
    except Exception as e:
        print(f"Error sending start message: {e}")

    while True:
        check_and_alert(MEME_COINS)
        print("Waiting 15 minutes for next check...")
        time.sleep(900)  # 900 ثانية = 15 دقيقة
