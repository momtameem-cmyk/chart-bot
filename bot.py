import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import io
import telepot
from datetime import datetime

# تحميل المتغيرات من البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

# إنشاء البوت
bot = telepot.Bot(TELEGRAM_TOKEN)

# قائمة عملات الميم (154 عملة)
MEME_COINS = [
    "DOGE","SHIB","PEPE","PENGU","TRUMP","SPX","FLOKI","WIF","FARTCOIN","BRETT",
    "APE","MOG","SNEK","TURBO","MEW","POPCAT","TOSHI","DOG","CHEEMS","PNUT",
    "USELESS","LION","BABYDOGE","REKT","NOT","TROLL","DORA","NPC","MEME","YZY",
    "NEIRO","TIBBIR","BOME","AURA","MOODENG","OSAK","LIBERTY","AI16Z","PYTHIA",
    "GIGA","GOHOME","APEPE","PEOPLE","AIC","BAN","WKC","GOAT","BERT","BITCOIN",
    "VINE","DEGEN","DOGS","APU","BANANAS31","ALI","SIREN","NOBODY","PONKE",
    "ANDY","CAT","ELON","KEYCAT","PEPEONTRON","TUT","SKYAI","URANUS","SKI",
    "CHILLGUY","EGL1","MIM","PEPECOIN","SLERF","USDUC","FWOG","DONKEY","PEP",
    "ACT","WOLF","BONE","SUNDOG","BOBO","COQ","DOGINME","FAIR3","MM","JOE",
    "MORI","MUBARAK","FARTBOY","LIGHT","NUB","MAI","UFD","MIGGLES","WEN","TST",
    "GME","WOJAK","BROCCOLI","ZEREBRO","KEKIUS","CAW","PIKA","MYRO","MOBY",
    "LADYS","LEASH","OMIKAMI","BULLA","DADDY","AIDOGE","RETARDIO","HIPPO",
    "JELLYJELLY","HYPER","SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI","QUACK",
    "KOKOK","KENDU","HOSICO","VINU","HOUSE","BENJI","MICHI","JAGER","TOKEN",
    "DJI6930","CATE","WHY","KOMA","MANEKI","A47","CAR","PIT","STARTUP","SMOG",
    "MAX","GORK","YURU","MASK","MOTHER","RIZZMAS","BOOP","PAIN","MUMU"
]

def fetch_ohlcv(symbol):
    """يجلب بيانات الأسعار من CoinMarketCap"""
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}&convert=USD"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        price = data["data"][symbol]["quote"]["USD"]["price"]
        # نصنع OHLCV وهمي (آخر 200 دقيقة مثلاً)
        df = pd.DataFrame({"close": [price]*200})
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def check_signals():
    """يفحص الشروط ويرسل التنبيهات"""
    print(f"🔍 Starting check for {len(MEME_COINS)} coins...")
    alerted = 0

    for coin in MEME_COINS:
        df = fetch_ohlcv(coin)
        if df is None: 
            continue

        # MA7 و MA25
        df["MA7"] = df["close"].rolling(7).mean()
        df["MA25"] = df["close"].rolling(25).mean()
        df["RSI"] = ta.rsi(df["close"], length=14)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # شرط التقاطع + RSI
        if (
            prev["MA7"] < prev["MA25"] and latest["MA7"] > latest["MA25"] and latest["RSI"] >= 40
        ):
            alerted += 1
            send_chart(coin, df)

    if alerted == 0:
        bot.sendMessage(CHAT_ID, "❌ لا يوجد عملات حققت الشرط الآن.")
    else:
        bot.sendMessage(CHAT_ID, f"✅ تم العثور على {alerted} عملات حققت الشرط!")

def send_chart(symbol, df):
    """يرسم الشارت ويرسله لتيلغرام"""
    plt.figure(figsize=(8,4))
    plt.plot(df["close"], label="السعر", color="blue")
    plt.plot(df["MA7"], label="MA7", color="green")
    plt.plot(df["MA25"], label="MA25", color="red")
    plt.title(f"{symbol} Chart")
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    bot.sendPhoto(CHAT_ID, photo=buf, caption=f"📊 {symbol} تحقق فيه الشرط")

if __name__ == "__main__":
    bot.sendMessage(CHAT_ID, f"🤖 Bot started with {len(MEME_COINS)} meme coins.")
    while True:
        check_signals()
        print("⏳ Waiting 5 minutes for next check...")
        time.sleep(300)
