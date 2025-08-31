import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot

# إعدادات التوكن والتشات
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة العملات (من رسالتك)
MEME_COINS = [
    "DOGE","SHIB","PEPE","PENGU","TRUMP","SPX","FLOKI","WIF","FARTCOIN","BRETT",
    "APE","MOG","SNEK","TURBO","MEW","POPCAT","TOSHI","DOG","CHEEMS","PNUT",
    "USELESS","LION","BABYDOGE","REKT","NOT","TROLL","DORA","NPC","MEME","YZY",
    "NEIRO","TIBBIR","BOME","AURA","MOODENG","OSAK","LIBERTY","AI16Z","PYTHIA",
    "GIGA","GOHOME","APEPE","PEOPLE","AIC","BAN","WKC","GOAT","BERT","BITCOIN",
    "VINE","DEGEN","DOGS","APU","BANANAS31","ALI","SIREN","NOBODY","PONKE","ANDY",
    "CAT","ELON","KEYCAT","PEPEONTRON","TUT","SKYAI","URANUS","SKI","CHILLGUY",
    "EGL1","MIM","PEPECOIN","SLERF","USDUC","FWOG","DONKEY","PEP","ACT","WOLF",
    "BONE","SUNDOG","BOBO","COQ","DOGINME","FAIR3","MM","JOE","MORI","MUBARAK",
    "FARTBOY","LIGHT","NUB","MAI","UFD","MIGGLES","WEN","TST","GME","WOJAK",
    "BROCCOLI","ZEREBRO","KEKIUS","CAW","PIKA","MYRO","MOBY","LADYS","LEASH",
    "OMIKAMI","BULLA","DADDY","AIDOGE","RETARDIO","HIPPO","JELLYJELLY","HYPER",
    "SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI","QUACK","KOKOK","KENDU",
    "HOSICO","VINU","HOUSE","BENJI","MICHI","JAGER","TOKEN","DJI6930","CATE",
    "WHY","KOMA","MANEKI","A47","CAR","PIT","STARTUP","SMOG","MAX","GORK",
    "YURU","MASK","MOTHER","RIZZMAS","BOOP","PAIN","MUMU"
]

# إعداد Binance API
BASE_URL = "https://api.binance.com/api/v3/klines"

def fetch_data(symbol, interval="1h", limit=200):
    try:
        url = f"{BASE_URL}?symbol={symbol}USDT&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if not isinstance(data, list):
            return None
        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume","close_time",
            "qav","trades","tbbav","tbqav","ignore"
        ])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def analyze(symbol):
    df = fetch_data(symbol)
    if df is None:
        return None, None, None

    df["EMA50"] = ta.ema(df["close"], length=50)
    df["EMA200"] = ta.ema(df["close"], length=200)
    df["RSI"] = ta.rsi(df["close"], length=14)

    last = df.iloc[-1]

    # الشرط الأساسي
    condition = last["close"] > last["EMA50"] and last["close"] > last["EMA200"] and last["RSI"] > 40

    # تقريب من الشرط
    near = []
    if 38 <= last["RSI"] <= 40:
        near.append(f"RSI قريب: {last['RSI']:.2f}")
    if abs(last["EMA50"] - last["EMA200"]) / last["EMA200"] < 0.02:
        near.append("EMA50 قريب من EMA200")

    return condition, near, df

def send_chart(symbol, df):
    plt.figure(figsize=(10,6))

    # الشموع (close)
    plt.plot(df.index, df["close"], label="Price", color="blue")

    # EMA50 أخضر
    plt.plot(df.index, df["EMA50"], label="EMA50", color="green")

    # EMA200 أحمر
    plt.plot(df.index, df["EMA200"], label="EMA200", color="red")

    plt.title(f"{symbol} - Price with EMA50/EMA200")
    plt.legend()

    # حفظ الصورة
    chart_path = f"{symbol}_chart.png"
    plt.savefig(chart_path)
    plt.close()

    # إرسال للتلغرام
    with open(chart_path, "rb") as img:
        bot.send_photo(chat_id=CHAT_ID, photo=img)

def main():
    while True:
        print(f"🔍 Starting check for {len(MEME_COINS)} coins...")
        bot.send_message(chat_id=CHAT_ID, text=f"🔍 بدء فحص {len(MEME_COINS)} عملة ميم")

        near_hits = []
        alerts = []

        for coin in MEME_COINS:
            condition, near, df = analyze(coin)
            if df is None:
                continue

            if condition:
                alerts.append(coin)
                bot.send_message(chat_id=CHAT_ID, text=f"🚀 {coin}: الشرط تحقق! السعر فوق EMA200/EMA50 و RSI > 40")
                send_chart(coin, df)  # إرسال الصورة
            elif near:
                near_hits.append(f"{coin}: {', '.join(near)}")

        # إرسال ملخص
        if alerts:
            bot.send_message(chat_id=CHAT_ID, text=f"✅ عدد العملات التي حققت الشرط: {len(alerts)}")
        else:
            bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات حققت الشرط الآن.")

        if near_hits:
            bot.send_message(chat_id=CHAT_ID, text="ℹ️ عملات قريبة من الشرط:\n" + "\n".join(near_hits[:10]))

        print("⏳ Waiting 5 minutes for next check...")
        time.sleep(300)

if __name__ == "__main__":
    main()
