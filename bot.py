import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot
import time
from io import BytesIO

# ========= إعدادات من ENV =========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ========= قائمة العملات (154 عملة) =========
MEME_COINS = [
    "DOGE", "SHIB", "PEPE", "PENGU", "TRUMP", "SPX", "FLOKI", "WIF", "FARTCOIN",
    "BRETT", "APE", "MOG", "SNEK", "TURBO", "MEW", "POPCAT", "TOSHI", "DOG",
    "CHEEMS", "PNUT", "USELESS", "LION", "BABYDOGE", "REKT", "NOT", "TROLL",
    "DORA", "NPC", "MEME", "YZY", "NEIRO", "TIBBIR", "BOME", "AURA", "MOODENG",
    "OSAK", "LIBERTY", "AI16Z", "PYTHIA", "GIGA", "GOHOME", "APEPE", "PEOPLE",
    "AIC", "BAN", "WKC", "GOAT", "BERT", "BITCOIN", "VINE", "DEGEN", "DOGS",
    "APU", "BANANAS31", "ALI", "SIREN", "NOBODY", "PONKE", "ANDY", "CAT", "ELON",
    "KEYCAT", "PEPEONTRON", "TUT", "SKYAI", "URANUS", "SKI", "CHILLGUY", "EGL1",
    "MIM", "PEPECOIN", "SLERF", "USDUC", "FWOG", "DONKEY", "PEP", "ACT", "WOLF",
    "BONE", "SUNDOG", "BOBO", "COQ", "DOGINME", "FAIR3", "MM", "JOE", "MORI",
    "MUBARAK", "FARTBOY", "LIGHT", "NUB", "MAI", "UFD", "MIGGLES", "WEN", "TST",
    "GME", "WOJAK", "BROCCOLI", "ZEREBRO", "KEKIUS", "CAW", "PIKA", "MYRO",
    "MOBY", "LADYS", "LEASH", "OMIKAMI", "BULLA", "DADDY", "AIDOGE", "RETARDIO",
    "HIPPO", "JELLYJELLY", "HYPER", "SAN", "PORK", "HOSKY", "PIPPIN", "PURPE",
    "LOFI", "QUACK", "KOKOK", "KENDU", "HOSICO", "VINU", "HOUSE", "BENJI",
    "MICHI", "JAGER", "TOKEN", "DJI6930", "CATE", "WHY", "KOMA", "MANEKI",
    "A47", "CAR", "PIT", "STARTUP", "SMOG", "MAX", "GORK", "YURU", "MASK",
    "MOTHER", "RIZZMAS", "BOOP", "PAIN", "MUMU"
]

# ========= دالة لجلب البيانات =========
def fetch_ohlcv(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=15m&limit=100"
        data = requests.get(url).json()
        if isinstance(data, dict) and data.get("code"):
            return None
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "c1", "c2", "c3", "c4", "c5", "c6"
        ])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ========= فحص العملة =========
def check_coin(symbol):
    df = fetch_ohlcv(symbol)
    if df is None or df.empty:
        return None, None

    df["MA7"] = ta.sma(df["close"], length=7)
    df["MA25"] = ta.sma(df["close"], length=25)
    df["RSI"] = ta.rsi(df["close"], length=14)

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # الشرط: تقاطع MA7 مع MA25 لأعلى + RSI ≥ 40
    crossed = prev["MA7"] <= prev["MA25"] and latest["MA7"] > latest["MA25"]
    condition = crossed and latest["RSI"] >= 40

    # توليد شارت
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(df.index, df["close"], label="Price", color="blue", alpha=0.6)
    ax.plot(df.index, df["MA7"], label="MA7", color="green", linewidth=2)
    ax.plot(df.index, df["MA25"], label="MA25", color="red", linewidth=2)
    ax.legend()
    ax.set_title(f"{symbol} - MA7/MA25 & RSI")
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    return condition, (buf, latest["RSI"])

# ========= تشغيل البوت =========
def run_bot():
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} Meme coins, MA7/MA25 + RSI alerts).")
    while True:
        print(f"🔍 Checking {len(MEME_COINS)} coins...")
        matches = 0
        for coin in MEME_COINS:
            condition, extra = check_coin(coin)
            if condition:
                matches += 1
                buf, rsi = extra
                bot.send_photo(chat_id=CHAT_ID, photo=buf,
                               caption=f"✅ {coin} | MA7 تقاطع MA25 لأعلى\nRSI = {rsi:.2f}")
                print(f"Alert sent for {coin}")
            else:
                print(f"Checked {coin}, no signal.")
        if matches == 0:
            bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات حققت الشرط الآن.")
        print("⏳ Waiting 5 minutes for next check...")
        time.sleep(300)

if __name__ == "__main__":
    run_bot()
