import os
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# 📌 قراءة المتغيرات من بيئة Heroku
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 📌 قائمة عملات الميم (١٥٤ عملة)
MEME_COINS = [
    "DOGE","SHIB","PEPE","PENGU","TRUMP","SPX","FLOKI","WIF","FARTCOIN","BRETT",
    "APE","MOG","SNEK","TURBO","MEW","POPCAT","TOSHI","DOG","CHEEMS","PNUT","USELESS",
    "LION","BABYDOGE","REKT","NOT","TROLL","DORA","NPC","MEME","YZY","NEIRO","TIBBIR",
    "BOME","AURA","MOODENG","OSAK","LIBERTY","AI16Z","PYTHIA","GIGA","GOHOME","APEPE",
    "PEOPLE","AIC","BAN","WKC","GOAT","BERT","BITCOIN","VINE","DEGEN","DOGS","APU",
    "BANANAS31","ALI","SIREN","NOBODY","PONKE","ANDY","CAT","ELON","KEYCAT","PEPEONTRON",
    "TUT","SKYAI","URANUS","SKI","CHILLGUY","EGL1","MIM","PEPECOIN","SLERF","USDUC",
    "FWOG","DONKEY","PEP","ACT","WOLF","BONE","SUNDOG","BOBO","COQ","DOGINME","FAIR3",
    "MM","JOE","MORI","MUBARAK","FARTBOY","LIGHT","NUB","MAI","UFD","MIGGLES","WEN",
    "TST","GME","WOJAK","BROCCOLI","ZEREBRO","KEKIUS","CAW","PIKA","MYRO","MOBY",
    "LADYS","LEASH","OMIKAMI","BULLA","DADDY","AIDOGE","RETARDIO","HIPPO","JELLYJELLY",
    "HYPER","SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI","QUACK","KOKOK","KENDU",
    "HOSICO","VINU","HOUSE","BENJI","MICHI","JAGER","TOKEN","DJI6930","CATE","WHY",
    "KOMA","MANEKI","A47","CAR","PIT","STARTUP","SMOG","MAX","GORK","YURU","MASK",
    "MOTHER","RIZZMAS","BOOP","PAIN","MUMU"
]

# ================================
# 📌 CoinMarketCap API
# ================================
def fetch_from_cmc(symbol):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/latest"
    params = {"symbol": symbol, "interval": "1h"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        if "data" not in data or symbol not in data["data"]:
            return None
        quotes = data["data"][symbol]["quotes"]
        df = pd.DataFrame([{
            "time": q["time_open"],
            "close": q["quote"]["USD"]["close"]
        } for q in quotes])
        return df
    except Exception:
        return None

# ================================
# 📌 CoinGecko API
# ================================
def fetch_from_cg(symbol):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart"
    params = {"vs_currency": "usd", "days": "1", "interval": "hourly"}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if "prices" not in data:
            return None
        df = pd.DataFrame({
            "time": [pd.to_datetime(x[0], unit="ms") for x in data["prices"]],
            "close": [x[1] for x in data["prices"]]
        })
        return df
    except Exception:
        return None

# ================================
# 📌 Strategy check
# ================================
def check_signal(symbol):
    df = fetch_from_cmc(symbol)
    source = "CMC"
    if df is None:
        df = fetch_from_cg(symbol)
        source = "CG"
    if df is None or len(df) < 25:
        return None, None, None

    df["MA7"] = df["close"].rolling(window=7).mean()
    df["MA25"] = df["close"].rolling(window=25).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal = None
    if prev["MA7"] < prev["MA25"] and last["MA7"] > last["MA25"]:
        signal = "BUY"
    elif prev["MA7"] > prev["MA25"] and last["MA7"] < last["MA25"]:
        signal = "SELL"

    return signal, source, df

# ================================
# 📌 Chart creation
# ================================
def generate_chart(symbol, df):
    plt.figure(figsize=(8,4))
    plt.plot(df["close"], label="Price", color="black")
    plt.plot(df["MA7"], label="MA7", color="green")
    plt.plot(df["MA25"], label="MA25", color="red")
    plt.legend()
    plt.title(symbol)
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# ================================
# 📌 Main loop
# ================================
def main():
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started with {len(MEME_COINS)} meme coins (CMC+CG).")
    while True:
        signals = []
        for symbol in MEME_COINS:
            signal, source, df = check_signal(symbol)
            if signal:
                chart = generate_chart(symbol, df)
                bot.send_photo(chat_id=CHAT_ID, photo=chart,
                               caption=f"✅ {symbol} ({source}) → {signal} signal!")
                signals.append(symbol)
        if not signals:
            bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات حققت الشرط الآن.")
        time.sleep(300)  # كل 5 دقائق

if __name__ == "__main__":
    main()
