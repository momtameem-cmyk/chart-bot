import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
import asyncio
from telegram import Bot

# --- إعداد المفاتيح من env ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# --- قائمة عملات الميم (154 رمز) ---
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

# --- دالة لجلب البيانات من CoinMarketCap ---
def fetch_data(symbols):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": ",".join(symbols), "convert": "USD"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("data", {})

# --- رسم الشارت ---
def plot_chart(df, symbol):
    plt.figure(figsize=(8, 5))
    plt.plot(df.index, df["close"], label="Price", color="blue")
    plt.plot(df.index, df["MA7"], label="MA7", color="green", linewidth=2)
    plt.plot(df.index, df["MA25"], label="MA25", color="red", linewidth=2)
    plt.title(f"{symbol} MA7 vs MA25")
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# --- التحقق من الاشارات ---
async def check_signals():
    batch_size = 80  # دفعات حتى نتجنب Rate Limit
    for i in range(0, len(MEME_COINS), batch_size):
        batch = MEME_COINS[i:i+batch_size]
        data = fetch_data(batch)

        for symbol in batch:
            try:
                if symbol not in data:
                    print(f"⚠️ Coin not found on CMC: {symbol}")
                    continue

                price = data[symbol]["quote"]["USD"]["price"]

                # نصنع DataFrame صغير لاختبار MA
                df = pd.DataFrame({"close": [price]*50})
                df["MA7"] = df["close"].rolling(7).mean()
                df["MA25"] = df["close"].rolling(25).mean()

                latest = df.iloc[-1]

                # الشرط: MA7 > MA25 (بدون RSI)
                if latest["MA7"] > latest["MA25"]:
                    print(f"✅ Signal found in {symbol}")
                    buf = plot_chart(df, symbol)
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=buf,
                        caption=f"✅ {symbol}: MA7 فوق MA25"
                    )
                else:
                    print(f"Checked {symbol}, no signal.")

            except Exception as e:
                print(f"❌ Error checking {symbol}: {e}")

# --- التشغيل المستمر ---
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins, MA7/MA25 alerts).")
    while True:
        print(f"🔍 Starting check for {len(MEME_COINS)} coins...")
        await check_signals()
        print("⏳ Waiting 5 minutes for next check...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
