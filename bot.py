import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot

# 📌 قراءة الـ API Keys من Config Vars في Heroku
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 📌 قائمة العملات (من 154 عملة التي زودتني بها)
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

# 📌 جلب بيانات الأسعار من CoinMarketCap
def fetch_ohlcv(symbol):
    url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical"
    params = {"symbol": symbol, "interval": "5m", "count": 100}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if "data" not in data or "quotes" not in data["data"]:
            print(f"Error fetching {symbol}: {data}")
            return None
        df = pd.DataFrame([{
            "time": q["time_open"],
            "open": q["quote"]["USD"]["open"],
            "high": q["quote"]["USD"]["high"],
            "low": q["quote"]["USD"]["low"],
            "close": q["quote"]["USD"]["close"],
            "volume": q["quote"]["USD"]["volume"]
        } for q in data["data"]["quotes"]])
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# 📌 التحقق من الشروط (MA7 مع MA25 + RSI ≥ 40)
def check_signal(symbol):
    df = fetch_ohlcv(symbol)
    if df is None or df.empty:
        return None
    df["MA7"] = df["close"].rolling(7).mean()
    df["MA25"] = df["close"].rolling(25).mean()
    df["RSI"] = ta.rsi(df["close"], length=14)

    if len(df) < 26:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # شرط التقاطع + RSI
    cross_up = prev["MA7"] < prev["MA25"] and latest["MA7"] > latest["MA25"]
    cross_down = prev["MA7"] > prev["MA25"] and latest["MA7"] < latest["MA25"]

    if (cross_up or cross_down) and latest["RSI"] >= 40:
        return df
    return None

# 📌 رسم الشارت مع MA7 أخضر و MA25 أحمر
def plot_chart(symbol, df):
    plt.figure(figsize=(10,5))
    plt.plot(df["close"], label="Price", color="blue")
    plt.plot(df["MA7"], label="MA7", color="green")
    plt.plot(df["MA25"], label="MA25", color="red")
    plt.title(f"{symbol} - MA7/MA25 + RSI")
    plt.legend()
    img_path = f"{symbol}.png"
    plt.savefig(img_path)
    plt.close()
    return img_path

# 📌 المهمة الرئيسية
def main():
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} coins, MA7/MA25 + RSI≥40)")
    while True:
        print(f"🔍 Starting check for {len(MEME_COINS)} coins...")
        found = 0
        for coin in MEME_COINS:
            df = check_signal(coin)
            if df is not None:
                found += 1
                img = plot_chart(coin, df)
                bot.send_photo(chat_id=CHAT_ID, photo=open(img, "rb"),
                               caption=f"📊 Signal on {coin} ✅ (RSI={df.iloc[-1]['RSI']:.2f})")
                print(f"Signal detected on {coin}")
            else:
                print(f"Checked {coin}, no signal.")
        if found == 0:
            bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات حققت الشرط الآن.")
        print("⏳ Waiting 5 minutes for next check...")
        time.sleep(300)

if __name__ == "__main__":
    main()
