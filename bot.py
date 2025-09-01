import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from telegram import Bot
import asyncio

# ========= الإعدادات =========
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة عملات الميم (154 عملة)
MEME_COINS = [
    "DOGE","SHIB","PEPE","PENGU","TRUMP","SPX","FLOKI","WIF","FARTCOIN","BRETT","APE","MOG",
    "SNEK","TURBO","MEW","POPCAT","TOSHI","DOG","CHEEMS","PNUT","USELESS","LION","BABYDOGE",
    "REKT","NOT","TROLL","DORA","NPC","MEME","YZY","NEIRO","TIBBIR","BOME","AURA","MOODENG",
    "OSAK","LIBERTY","AI16Z","PYTHIA","GIGA","GOHOME","APEPE","PEOPLE","AIC","BAN","WKC","GOAT",
    "BERT","BITCOIN","VINE","DEGEN","DOGS","APU","BANANAS31","ALI","SIREN","NOBODY","PONKE",
    "ANDY","CAT","ELON","KEYCAT","PEPEONTRON","TUT","SKYAI","URANUS","SKI","CHILLGUY","EGL1",
    "MIM","PEPECOIN","SLERF","USDUC","FWOG","DONKEY","PEP","ACT","WOLF","BONE","SUNDOG","BOBO",
    "COQ","DOGINME","FAIR3","MM","JOE","MORI","MUBARAK","FARTBOY","LIGHT","NUB","MAI","UFD",
    "MIGGLES","WEN","TST","GME","WOJAK","BROCCOLI","ZEREBRO","KEKIUS","CAW","PIKA","MYRO","MOBY",
    "LADYS","LEASH","OMIKAMI","BULLA","DADDY","AIDOGE","RETARDIO","HIPPO","JELLYJELLY","HYPER",
    "SAN","PORK","HOSKY","PIPPIN","PURPE","LOFI","QUACK","KOKOK","KENDU","HOSICO","VINU","HOUSE",
    "BENJI","MICHI","JAGER","TOKEN","DJI6930","CATE","WHY","KOMA","MANEKI","A47","CAR","PIT",
    "STARTUP","SMOG","MAX","GORK","YURU","MASK","MOTHER","RIZZMAS","BOOP","PAIN","MUMU"
]

# قائمة لحفظ العملات غير الموجودة
not_found_cache = set()

# ========= دوال =========

def fetch_ohlcv(symbol):
    """جلب بيانات السعر التاريخي من CoinMarketCap"""
    url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical"
    params = {
        "symbol": symbol,
        "interval": "5m",
        "count": 100
    }
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, params=params, headers=headers)
    data = r.json()

    if "data" not in data:
        raise ValueError(data.get("status", {}).get("error_message", "No data"))

    quotes = data["data"]["quotes"]
    df = pd.DataFrame([{
        "time": q["time_open"],
        "close": q["quote"]["USD"]["close"]
    } for q in quotes])
    return df


def analyze_coin(symbol):
    """تحليل العملة: MA7 و MA25"""
    try:
        df = fetch_ohlcv(symbol)
    except Exception as e:
        if symbol not in not_found_cache:
            not_found_cache.add(symbol)
            return f"⚠️ {symbol} غير موجود على CMC ({e})", None
        return None, None

    # حساب MA
    df["MA7"] = df["close"].rolling(7).mean()
    df["MA25"] = df["close"].rolling(25).mean()

    # شرط: MA7 يتقاطع مع MA25
    if df["MA7"].iloc[-2] < df["MA25"].iloc[-2] and df["MA7"].iloc[-1] > df["MA25"].iloc[-1]:
        signal = f"✅ {symbol} أعطى إشارة تقاطع صعودية (MA7 فوق MA25)"
    elif df["MA7"].iloc[-2] > df["MA25"].iloc[-2] and df["MA7"].iloc[-1] < df["MA25"].iloc[-1]:
        signal = f"⚠️ {symbol} أعطى إشارة تقاطع هبوطية (MA7 تحت MA25)"
    else:
        return None, None

    # رسم الشارت
    plt.figure(figsize=(8, 4))
    plt.plot(df["time"], df["close"], label="Price", color="blue")
    plt.plot(df["time"], df["MA7"], label="MA7", color="green")
    plt.plot(df["time"], df["MA25"], label="MA25", color="red")
    plt.title(f"{symbol} - MA7/MA25")
    plt.legend()
    chart_path = f"{symbol}_chart.png"
    plt.savefig(chart_path)
    plt.close()

    return signal, chart_path


async def main_loop():
    await bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started with {len(MEME_COINS)} meme coins")

    while True:
        print(f"🔍 Checking {len(MEME_COINS)} coins...")
        signals = []
        charts = []
        not_found_msgs = []

        for coin in MEME_COINS:
            signal, chart = analyze_coin(coin)
            if signal and chart:
                signals.append(signal)
                charts.append(chart)
            elif signal and not chart:  # حالة "عملة غير موجودة"
                not_found_msgs.append(signal)

        # إرسال إشعارات العملات اللي أعطت إشارة
        if signals:
            for sig, chart in zip(signals, charts):
                await bot.send_photo(chat_id=CHAT_ID, photo=open(chart, "rb"), caption=sig)
        else:
            await bot.send_message(chat_id=CHAT_ID, text="❌ لا يوجد عملات أعطت إشارة الآن.")

        # إرسال قائمة العملات غير الموجودة (مرة واحدة لكل عملة)
        if not_found_msgs:
            msg = "\n".join(not_found_msgs)
            await bot.send_message(chat_id=CHAT_ID, text=f"🚫 عملات غير موجودة على CMC:\n{msg}")

        print("⏳ Waiting 5 minutes for next check...")
        time.sleep(300)


if __name__ == "__main__":
    asyncio.run(main_loop())
