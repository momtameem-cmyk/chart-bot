import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot
import asyncio

# --- إعداد المتغيرات من Heroku Config Vars ---
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# --- قائمة العملات (من قائمتك) ---
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

# --- دالة جلب الأسعار من CoinMarketCap ---
def fetch_ohlcv(symbol):
    url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
    params = {"symbol": symbol}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        if "data" not in data or symbol not in data["data"]:
            return None
        price = data["data"][symbol][0]["quote"]["USD"]["price"]
        return price
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
        return None

# --- دالة التحليل الفني ---
def analyze(symbol, prices):
    df = pd.DataFrame(prices, columns=["close"])
    df["MA7"] = df["close"].rolling(7).mean()
    df["MA25"] = df["close"].rolling(25).mean()

    if len(df) < 25:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # إشارة: تقاطع MA7 مع MA25
    if prev["MA7"] < prev["MA25"] and last["MA7"] > last["MA25"]:
        return "BUY"
    if prev["MA7"] > prev["MA25"] and last["MA7"] < last["MA25"]:
        return "SELL"
    return None

# --- رسم الشارت ---
def plot_chart(symbol, prices):
    df = pd.DataFrame(prices, columns=["close"])
    df["MA7"] = df["close"].rolling(7).mean()
    df["MA25"] = df["close"].rolling(25).mean()

    plt.figure(figsize=(10,5))
    plt.plot(df["close"], label="Price", color="blue")
    plt.plot(df["MA7"], label="MA7", color="green")
    plt.plot(df["MA25"], label="MA25", color="red")
    plt.title(symbol)
    plt.legend()
    filename = f"{symbol}.png"
    plt.savefig(filename)
    plt.close()
    return filename

# --- المهمة الرئيسية ---
async def main():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started with {len(MEME_COINS)} meme coins.")

    while True:
        await bot.send_message(chat_id=CHAT_ID, text=f"🔍 Starting check for {len(MEME_COINS)} coins...")

        not_found_msgs = []
        signals = []

        for coin in MEME_COINS:
            price = fetch_ohlcv(coin)
            if price is None:
                not_found_msgs.append(coin)
                continue

            # نبني قائمة أسعار وهمية (لتجربة التحليل)
            prices = [price * (1 + (i/100)) for i in range(30)]
            signal = analyze(coin, prices)

            if signal:
                chart = plot_chart(coin, prices)
                await bot.send_photo(chat_id=CHAT_ID, photo=open(chart, "rb"),
                                     caption=f"📈 {coin} Signal: {signal}")
            else:
                print(f"Checked {coin}, no signal.")

        # إرسال العملات غير الموجودة على دفعات
        if not_found_msgs:
            msg = "🚫 عملات غير موجودة على CMC:\n" + ", ".join(not_found_msgs)
            chunk_size = 4000
            for i in range(0, len(msg), chunk_size):
                await bot.send_message(chat_id=CHAT_ID, text=msg[i:i+chunk_size])

        await bot.send_message(chat_id=CHAT_ID, text="⏳ Waiting 5 minutes for next check...")
        time.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
