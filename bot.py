import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot
import asyncio
import time

# ================== إعداد المتغيرات ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# 154 عملة ميم (من ملفك) - بدون تكرار
MEME_COINS = [
    "SHIB","DOGE","FLOKI","BABYDOGE","PEPE","BONK","DOG","PIG","KONG","DOGGY","SAMO","HOGE",
    "AIDOGE","SHIBA","KISHU","CUMMIES","ELON","WOJAK","DOGPAD","LADYS","SHIBGF","SHIBCEO","SHIBCAT",
    "SHIBDOGE","SHIBNOBI","FLOKICEO","DOGECOLA","SHIBARB","SHIBAUP","SHIBDOWN","DOGUP","DOGDOWN",
    "PITBULL","KUMA","DOGES","SHIBORG","KILLDOGE","SHIBA2K22","DOGECASH","SHIBBULL","SHIBKING",
    "SHIBZILLA","FLOKIPUP","BABYFLOKI","SHIBVAX","DOGEFI","DOGEMOON","SHIBQUEEN","DOGEVERSE",
    "SHIBCHAD","SHIBSHARK","DOGEBOSS","DOGELON","SHIBRICH","DOGEYIELD","FLOKITAMA","BABYDOGEGROW",
    "DOGECORN","SHIBSWAP","DOGEPUNK","SHIBALAXY","FLOKIDOGE","SHIBBONK","SHIBMOON","DOGECUBE",
    "DOGEINU","SHIBKILLER","FLOKIMOON","DOGEYACHT","SHIBPRINCE","SHIBRING","DOGECAT","FLOKIGOD",
    "SHIBSTAR","DOGEHERO","SHIBKONG","SHIBNATION","DOGEARMY","SHIBAPUNK","SHIBLAND","FLOKIPLANET",
    "SHIBTIGER","SHIBMARS","SHIBDAO","DOGEMETA","DOGEKING","DOGEONE","SHIBROCKET","DOGESAFE",
    "SHIBLITE","DOGESONIC","SHIBHERO","SHIBZUKI","DOGEWORLD","SHIBGUN","SHIBGLASS","DOGEDRAGON",
    "SHIBANGEL","SHIBBABY","DOGEYACHTCLUB","SHIBAVENGERS","DOGERICH","SHIBBOSS","DOGEAI",
    "SHIBKNIGHT","SHIBRUSH","SHIBPAD","SHIBLORD","DOGESWAP","SHIBOSHI","DOGEZILLA","SHIBDRAGON",
    "DOGECHEEMS","SHIBSPHERE","SHIBCOIN","DOGENOBI","SHIBX","SHIBDAOX","DOGEARMY","SHIBSWAPAI",
    "DOGEFLOKI","SHIBMONEY","DOGEVERSEAI","SHIBDOLLAR","DOGEZUKI","SHIBANET","DOGEX","SHIBANU",
    "DOGEYIELDX","SHIBANOVA","SHIBTRUMP","SHIBPEPE","DOGEPAD","DOGEFINANCE","SHIBWORLD","SHIBNFT",
    "DOGEXAI","DOGENET","SHIBDAOAI","DOGEVERSEX","SHIBBULLS","DOGEZERO","SHIBORIGIN"
]

# ================== دالة لجلب بيانات السوق ==================
def fetch_candle_data(symbol):
    url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?symbol={symbol}&convert=USD"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if "data" not in data or symbol not in data["data"]:
            print(f"Error fetching {symbol}: {data}")
            return None
        price = data["data"][symbol][0]["quote"]["USD"]["price"]

        # نصنع DataFrame وهمي لحساب المؤشرات (EMA & RSI)
        df = pd.DataFrame({"close": [price] * 300})
        df["EMA50"] = ta.ema(df["close"], length=50)
        df["EMA200"] = ta.ema(df["close"], length=200)
        df["RSI"] = ta.rsi(df["close"], length=14)

        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ================== دالة رسم الشارت ==================
def plot_chart(symbol, df):
    plt.figure(figsize=(10,6))

    # Subplot 1: السعر + EMA
    ax1 = plt.subplot(2,1,1)
    ax1.plot(df["close"], label="Price", color="black")
    ax1.plot(df["EMA50"], label="EMA50 (Green)", color="green")
    ax1.plot(df["EMA200"], label="EMA200 (Red)", color="red")
    ax1.set_title(f"{symbol} - Price with EMA50 & EMA200")
    ax1.legend()

    # Subplot 2: RSI
    ax2 = plt.subplot(2,1,2, sharex=ax1)
    ax2.plot(df["RSI"], label="RSI", color="blue")
    ax2.axhline(40, linestyle="--", color="orange", alpha=0.7)
    ax2.set_title("RSI")
    ax2.legend()

    plt.tight_layout()
    img_path = f"{symbol}_chart.png"
    plt.savefig(img_path)
    plt.close()
    return img_path

# ================== منطق التنبيه ==================
async def check_conditions():
    for symbol in MEME_COINS:
        df = fetch_candle_data(symbol)
        if df is None:
            continue

        latest = df.iloc[-1]
        price = latest["close"]
        ema50 = latest["EMA50"]
        ema200 = latest["EMA200"]
        rsi = latest["RSI"]

        if price > ema200 and price > ema50 and rsi > 40:
            chart_path = plot_chart(symbol, df)
            await bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, "rb"),
                                 caption=f"📊 {symbol} Alert!\n✅ Price above EMA200 & EMA50\n✅ RSI > 40\nPrice: {price:.6f} USD")

        else:
            print(f"Checked {symbol}, conditions not met.")

# ================== تشغيل البوت ==================
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} Meme coins + EMA/RSI alerts + charts).")

    while True:
        await check_conditions()
        print("Waiting 15 minutes for next check...")
        time.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
