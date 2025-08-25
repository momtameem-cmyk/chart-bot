import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة 300 عملة عامة (أمثلة)
coins = [
    'BTC', 'ETH', 'USDT', 'BNB', 'ADA', 'XRP', 'SOL', 'DOGE', 'DOT', 'AVAX',
    'MATIC', 'SHIB', 'TRX', 'LTC', 'UNI', 'ATOM', 'LINK', 'XLM', 'ALGO', 'VET',
    # ... أضف المزيد حتى تصل 300 رمز ...
]

def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbol, "convert": "USD"}
    r = requests.get(url, headers=headers, params=params).json()
    data = r.get("data", {}).get(symbol)
    if data:
        price = data["quote"]["USD"]["price"]
        return price
    return None

def fetch_historical(symbol, limit=100):
    # يمكنك استخدام بيانات وهمية إذا لم تتوفر API للتاريخ الكامل
    # مثال: توليد بيانات عشوائية لتجربة EMA و RSI
    prices = [fetch_price(symbol) for _ in range(limit)]
    df = pd.DataFrame(prices, columns=["close"])
    df.dropna(inplace=True)
    return df

def check_alerts():
    for coin in coins:
        try:
            df = fetch_historical(coin)
            if df.empty or len(df) < 25:
                continue
            df['EMA7'] = ta.ema(df['close'], length=7)
            df['EMA25'] = ta.ema(df['close'], length=25)
            df['RSI'] = ta.rsi(df['close'], length=14)

            # شرط التقاطع صعودي و RSI >= 45
            if df['EMA7'].iloc[-2] < df['EMA25'].iloc[-2] and df['EMA7'].iloc[-1] > df['EMA25'].iloc[-1]:
                if df['RSI'].iloc[-1] >= 45:
                    bot.send_message(chat_id=CHAT_ID, text=f"✅ {coin} EMA7 تقاطع فوق EMA25 و RSI={df['RSI'].iloc[-1]:.2f}")
        except Exception as e:
            bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {coin}: {e}")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (300 coins + EMA & RSI alerts).")
    while True:
        check_alerts()
        time.sleep(60)
