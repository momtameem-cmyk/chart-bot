import os
import time
import io
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot

# ===============================
# إعداد التوكن و الشات من ENV
# ===============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ===============================
# قائمة العملات (بدون تكرار)
# ===============================
MEME_COINS = list(set([
    "DOGE","SHIB","PEPE","PENGU","TRUMP","SPX","FLOKI","WIF","FARTCOIN","BRETT","APE","MOG","SNEK","TURBO",
    "MEW","POPCAT","TOSHI","DOG","CHEEMS","PNUT","USELESS","LION","BABYDOGE","REKT","NOT","TROLL","DORA","NPC",
    "MEME","YZY","NEIRO","TIBBIR","BOME","AURA","MOODENG","OSAK","LIBERTY","AI16Z","PYTHIA","GIGA","GOHOME",
    "APEPE","PEOPLE","AIC","BAN","WKC","GOAT","BERT","BITCOIN","VINE","DEGEN","DOGS","APU","BANANAS31","ALI",
    "SIREN","NOBODY","PONKE","ANDY","CAT","ELON","KEYCAT","PEPEONTRON","TUT","SKYAI","URANUS","SKI","CHILLGUY",
    "EGL1","MIM","PEPECOIN","SLERF","USDUC","FWOG","DONKEY","PEP","ACT","WOLF","BONE","SUNDOG","BOBO","COQ",
    "DOGINME","FAIR3","MM","JOE","MORI","MUBARAK","FARTBOY","LIGHT","NUB","MAI","UFD","MIGGLES","WEN","TST",
    "GME","WOJAK","BROCCOLI","ZEREBRO","KEKIUS","CAW","PIKA","MYRO","MOBY","LADYS","LEASH","OMIKAMI","BULLA",
    "DADDY","AIDOGE","RETARDIO","HIPPO","JELLYJELLY","HYPER","SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI",
    "QUACK","KOKOK","KENDU","HOSICO","VINU","HOUSE","BENJI","MICHI","JAGER","TOKEN","DJI6930","CATE","WHY",
    "KOMA","MANEKI","A47","CAR","PIT","STARTUP","SMOG","MAX","GORK","YURU","MASK","MOTHER","RIZZMAS","BOOP",
    "PAIN","MUMU"
]))

# ===============================
# فلتر التنبيهات
# ===============================
alerted = {}

# ===============================
# جلب بيانات السعر من Binance
# ===============================
def fetch_klines(symbol, interval="1h", limit=200):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": f"{symbol}USDT", "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if isinstance(data, list):
            df = pd.DataFrame(data, columns=[
                "time","o","h","l","c","v","ct","qav","nt","tb","qtb","ignore"
            ])
            df["c"] = df["c"].astype(float)
            return df
        else:
            return None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ===============================
# رسم الشارت
# ===============================
def plot_chart(symbol, df):
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8,6), gridspec_kw={'height_ratios':[3,1]}, sharex=True)

        # السعر + EMA
        ax1.plot(df.index, df["c"], label="Price", color="black")
        ax1.plot(df.index, df["EMA50"], label="EMA50", color="green")
        ax1.plot(df.index, df["EMA200"], label="EMA200", color="red")
        ax1.set_title(f"{symbol}/USDT")
        ax1.legend(loc="upper left")

        # RSI
        ax2.plot(df.index, df["RSI"], label="RSI", color="blue")
        ax2.axhline(40, color="orange", linestyle="--", label="RSI 40")  # خط أفقي عند RSI=40
        ax2.set_ylim(0,100)
        ax2.legend(loc="upper left")

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        print(f"Error plotting {symbol}: {e}")
        return None

# ===============================
# التحقق من الشروط
# ===============================
def check_conditions(symbol):
    df = fetch_klines(symbol)
    if df is None or df.empty: 
        return False, None

    df["EMA50"] = ta.ema(df["c"], length=50)
    df["EMA200"] = ta.ema(df["c"], length=200)
    df["RSI"] = ta.rsi(df["c"], length=14)

    last = df.iloc[-1]
    if last["c"] > last["EMA50"] and last["c"] > last["EMA200"] and last["RSI"] > 40:
        return True, df
    return False, df

# ===============================
# بدء البوت
# ===============================
print(f"Loaded {len(MEME_COINS)} meme coins.")

try:
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
except Exception as e:
    print(f"Error sending start message: {e}")

# ===============================
# حلقة التشغيل
# ===============================
while True:
    for coin in MEME_COINS:
        ok, df = check_conditions(coin)

        if ok:
            if not alerted.get(coin, False):
                last = df.iloc[-1]
                chart = plot_chart(coin, df)
                caption = (
                    f"📈 Alert for {coin}/USDT\n\n"
                    f"💵 Price: {last['c']:.5f}\n"
                    f"📊 EMA50 (green): {last['EMA50']:.5f}\n"
                    f"📊 EMA200 (red): {last['EMA200']:.5f}\n"
                    f"📉 RSI: {last['RSI']:.2f}"
                )

                if chart:
                    bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=caption)
                else:
                    bot.send_message(chat_id=CHAT_ID, text=caption)

                alerted[coin] = True
                print(f"Alert sent for {coin}")
            else:
                print(f"Already alerted {coin}, skipping.")
        else:
            alerted[coin] = False
            print(f"Checked {coin}, conditions not met.")

    print("⏳ Waiting 15 minutes for next check...")
    time.sleep(900)
