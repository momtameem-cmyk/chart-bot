import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot

# إعداد المتغيرات البيئية
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# جلب قائمة العملات الميم من CoinMarketCap
def get_top_meme_coins(limit=200):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"limit": 500, "sort": "market_cap", "sort_dir": "desc"}
    response = requests.get(url, headers=headers, params=params).json()

    meme_coins = []
    for coin in response.get("data", []):
        if "meme" in coin.get("tags", []):
            meme_coins.append(coin["symbol"])
            if len(meme_coins) >= limit:
                break
    return meme_coins

MEME_COINS = get_top_meme_coins()

# دالة للتحقق من EMA و RSI
def check_signals(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=300"
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=[
            "Open time", "Open", "High", "Low", "Close", "Volume",
            "Close time", "Quote asset volume", "Number of trades",
            "Taker buy base", "Taker buy quote", "Ignore"
        ])
        df["Close"] = pd.to_numeric(df["Close"])
        
        # حساب EMA و RSI
        df["EMA50"] = ta.ema(df["Close"], length=50)
        df["EMA200"] = ta.ema(df["Close"], length=200)
        df["RSI"] = ta.rsi(df["Close"], length=14)

        latest = df.iloc[-1]
        condition_met = latest["Close"] > latest["EMA50"] and latest["Close"] > latest["EMA200"] and latest["RSI"] >= 40
        return condition_met, df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return False, None

# دالة لرسم الشارت
def plot_chart(symbol, df):
    plt.figure(figsize=(10,5))
    plt.plot(df["Close"], label="Close")
    plt.plot(df["EMA50"], label="EMA50")
    plt.plot(df["EMA200"], label="EMA200")
    plt.title(f"{symbol} Price Chart")
    plt.legend()
    filename = f"{symbol}_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

# حفظ حالة الشرط لكل عملة لتجنب التكرار
coin_status = {symbol: False for symbol in MEME_COINS}

# إرسال رسالة بدء البوت
bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
print(f"Bot started ({len(MEME_COINS)} meme coins).")

# الحلقة الرئيسية
while True:
    for symbol in MEME_COINS:
        signal, df = check_signals(symbol)
        if df is None:
            continue  # تخطي العملة إذا حدث خطأ
        previous_status = coin_status[symbol]
        if signal and not previous_status:
            # الشرط تحقق لأول مرة
            chart_file = plot_chart(symbol, df)
            msg = f"✅ {symbol} EMA50/200 & RSI≥40\nPrice: {df['Close'].iloc[-1]}\nRSI: {df['RSI'].iloc[-1]}"
            bot.send_photo(chat_id=CHAT_ID, photo=open(chart_file, 'rb'), caption=msg)
            print(msg)
            coin_status[symbol] = True
        elif not signal and previous_status:
            # الشرط أصبح غير محقق، إعادة الحالة
            coin_status[symbol] = False
            print(f"{symbol} conditions no longer met.")
        else:
            print(f"Checked {symbol}, no change.")
    time.sleep(300)  # تحقق كل 5 دقائق
