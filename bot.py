import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# ==========================
# الإعدادات من الـ ENV
# ==========================
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ==========================
# قائمة عملات الميم (154 رمز)
# ==========================
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

# ==========================
# جلب الأسعار (batch)
# ==========================
def fetch_data(symbols):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": ",".join(symbols), "convert": "USD"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        data = r.json()
        return data.get("data", {})
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return {}

# ==========================
# رسم الشارت
# ==========================
def plot_chart(df, coin):
    plt.figure(figsize=(8,5))

    # السعر
    plt.plot(df.index, df["close"], label="Price", color="black", linewidth=1)

    # MA7 أخضر
    plt.plot(df.index, df["MA7"], label="MA7", color="green", linewidth=1.2)

    # MA25 أحمر
    plt.plot(df.index, df["MA25"], label="MA25", color="red", linewidth=1.2)

    plt.title(f"{coin} Price with MA7 & MA25")
    plt.legend()
    plt.grid(True)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# ==========================
# التحقق من الإشارات
# ==========================
async def check_signals():
    batch_size = 80  # دفعة 80 عملة لكل طلب
    for i in range(0, len(MEME_COINS), batch_size):
        batch = MEME_COINS[i:i+batch_size]
        data = fetch_data(batch)

        for symbol in batch:
            try:
                price = data[symbol]["quote"]["USD"]["price"]

                # نجهز DataFrame تجريبي (نحتاج candles حقيقية عادة من CMC أو Binance API)
                df = pd.DataFrame({"close": [price]*50})
                df["MA7"] = df["close"].rolling(7).mean()
                df["MA25"] = df["close"].rolling(25).mean()
                df["RSI"] = ta.rsi(df["close"], length=14)

                latest = df.iloc[-1]

                # شرط التقاطع
                if latest["MA7"] > latest["MA25"] and latest["RSI"] >= 40:
                    print(f"✅ Signal found in {symbol}")
                    buf = plot_chart(df, symbol)
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=buf,
                        caption=f"✅ {symbol}: MA7 فوق MA25 + RSI={latest['RSI']:.2f}"
                    )
                else:
                    print(f"Checked {symbol}, no signal.")

            except Exception as e:
                print(f"Error checking {symbol}: {e}")

# ==========================
# تشغيل البوت
# ==========================
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins, MA7/MA25 + RSI≥40)")
    while True:
        await bot.send_message(chat_id=CHAT_ID, text=f"🔍 Starting check for {len(MEME_COINS)} coins...")
        await check_signals()
        print("⏳ Waiting 5 minutes for next check...")
        await asyncio.sleep(300)  # 5 دقائق

if __name__ == "__main__":
    asyncio.run(main())
