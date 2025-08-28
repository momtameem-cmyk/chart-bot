import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# ==== المتغيرات البيئية ====
CMC_API_KEY = os.getenv("CMC_API_KEY")      # مفتاح CoinMarketCap
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ==== قائمة أفضل 200 عملة ميم (رموز) ====
MEME_COINS = [
    "SHIB","DOGE","PEPE","FLOKI","AKITA","KISHU","HOGE","ELON","SAMO","MONA",
    "BABYDOGE","SANTOS","MOON","CATE","DOGEZ","WOOFY","DOG","PIG","KONG","DOGGY",
    # ... أكمل حتى 200 رمز
]

# ==== الإعدادات العامة ====
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
HEADERS = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

CHECK_INTERVAL = 15 * 60  # 15 دقيقة

def fetch_price(symbol):
    try:
        params = {"symbol": symbol, "convert": "USD"}
        response = requests.get(CMC_URL, headers=HEADERS, params=params)
        data = response.json()
        price = data['data'][symbol]['quote']['USD']['price']
        return price
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def check_indicators(symbol):
    price = fetch_price(symbol)
    if price is None:
        return None

    # لإنشاء DataFrame وهمي لتوضيح EMA و RSI
    # في حال أردت بيانات تاريخية حقيقية، يجب جلب OHLC من API آخر
    df = pd.DataFrame({"close": [price]*250})
    df["EMA50"] = ta.ema(df["close"], length=50)
    df["EMA200"] = ta.ema(df["close"], length=200)
    df["RSI"] = ta.rsi(df["close"], length=14)
    
    ema50 = df["EMA50"].iloc[-1]
    ema200 = df["EMA200"].iloc[-1]
    rsi = df["RSI"].iloc[-1]

    if price > ema50 and price > ema200 and rsi >= 40:
        return df
    return None

def send_alert(symbol, df):
    plt.figure(figsize=(6,4))
    plt.plot(df["close"], label="Price")
    plt.plot(df["EMA50"], label="EMA50")
    plt.plot(df["EMA200"], label="EMA200")
    plt.title(symbol)
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    bot.send_photo(chat_id=CHAT_ID, photo=buf, caption=f"✅ {symbol} met conditions!\nPrice above EMA50 & EMA200, RSI≥40")

def main():
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
    print(f"Bot started with {len(MEME_COINS)} meme coins.")

    while True:
        for coin in MEME_COINS:
            df = check_indicators(coin)
            if df is not None:
                try:
                    send_alert(coin, df)
                except Exception as e:
                    print(f"Error sending alert for {coin}: {e}")
            else:
                print(f"Checked {coin}, conditions not met.")
        print(f"Waiting {CHECK_INTERVAL//60} minutes for next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
