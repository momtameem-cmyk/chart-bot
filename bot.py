import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import asyncio
from telegram import Bot

# Telegram credentials from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# ✅ قائمة عملات الميم
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
    "SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI","QUACK","KOKOK","KENDU","HOSICO",
    "VINU","HOUSE","BENJI","MICHI","JAGER","TOKEN","DJI6930","CATE","WHY","KOMA",
    "MANEKI","A47","CAR","PIT","STARTUP","SMOG","MAX","GORK","YURU","MASK",
    "MOTHER","RIZZMAS","BOOP","PAIN","MUMU"
]

BASE_URL = "https://api.binance.com/api/v3/klines"

def fetch_data(symbol, interval="1h", limit=200):
    try:
        url = f"{BASE_URL}?symbol={symbol}USDT&interval={interval}&limit={limit}"
        r = requests.get(url, timeout=10)
        data = r.json()
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

    # Indicators
    df["EMA50"] = ta.ema(df["close"], length=50)
    df["EMA200"] = ta.ema(df["close"], length=200)
    df["RSI"] = ta.rsi(df["close"], length=14)

    last = df.iloc[-1]

    # ✅ الشروط
    condition = (
        last["close"] > last["EMA50"] and
        last["close"] > last["EMA200"] and
        last["RSI"] > 40
    )

    # ✅ قرب من الشرط
    near = []
    if 38 <= last["RSI"] <= 40:
        near.append(f"RSI ≈ {last['RSI']:.2f}")
    if abs(last["EMA50"] - last["EMA200"]) / last["EMA200"] < 0.02:
        near.append("EMA50 قريب من EMA200")

    return condition, near, df

def make_chart(symbol, df):
    plt.figure(figsize=(10,6))
    plt.plot(df.index, df["close"], label="Price", color="blue")
    plt.plot(df.index, df["EMA50"], label="EMA50", color="green")
    plt.plot(df.index, df["EMA200"], label="EMA200", color="red")
    plt.title(f"{symbol} - EMA/RSI Chart")
    plt.legend()
    chart_path = f"{symbol}_chart.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path

async def check_loop():
    while True:
        print(f"🔍 Starting check for {len(MEME_COINS)} coins...")
        await bot.send_message(chat_id=CHAT_ID, text=f"🔍 بدء فحص {len(MEME_COINS)} عملة ميم")

        alerts, near_hits = [], []

        for coin in MEME_COINS:
            condition, near, df = analyze(coin)
            if df is None:
                continue

            if condition:
                alerts.append(coin)
                await bot.send_message(chat_id=CHAT_ID, text=f"🚀 {coin}: الشرط تحقق ✅")
                chart_path = make_chart(coin, df)
                with open(chart_path, "rb") as img:
                    await bot.send_photo(chat_id=CHAT_ID, photo=img)

            elif near:
                near_hits.append(f"{coin}: {', '.join(near)}")

        # نتائج
        if alerts:
            await bot.send_message(chat_id=CHAT_ID, text=f"✅ {len(alerts)} عملة حققت الشرط: {', '.join(alerts)}")
        else:
            await bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات حققت الشرط الآن.")

        if near_hits:
            await bot.send_message(chat_id=CHAT_ID, text="ℹ️ عملات قريبة من الشرط:\n" + "\n".join(near_hits[:10]))

        print("⏳ Waiting 5 minutes for next check...")
        await asyncio.sleep(300)  # 5 دقائق

if __name__ == "__main__":
    asyncio.run(check_loop())
