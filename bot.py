import os
import time
import io
import requests
import pandas as pd
import matplotlib.pyplot as plt

# إعداد المفاتيح
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# قائمة العملات
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
    "GME", "WOJAK", "BROCCOLI", "ZEREBRO", "KEKIUS", "CAW", "PIKA", "MYRO", "MOBY",
    "LADYS", "LEASH", "OMIKAMI", "BULLA", "DADDY", "AIDOGE", "RETARDIO", "HIPPO",
    "JELLYJELLY", "HYPER", "SAN", "PORK", "HOSKY", "PIPPIN", "PURPE", "LOFI",
    "QUACK", "KOKOK", "KENDU", "HOSICO", "VINU", "HOUSE", "BENJI", "MICHI", "JAGER",
    "TOKEN", "DJI6930", "CATE", "WHY", "KOMA", "MANEKI", "A47", "CAR", "PIT",
    "STARTUP", "SMOG", "MAX", "GORK", "YURU", "MASK", "MOTHER", "RIZZMAS", "BOOP",
    "PAIN", "MUMU"
]

# ------------------ Telegram ------------------
def send_text(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def send_photo(buf, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": buf}
    data = {"chat_id": CHAT_ID, "caption": caption}
    requests.post(url, data=data, files=files)

# ------------------ CoinMarketCap ------------------
def fetch_cmc_data(symbol, interval="5m", limit=200):
    url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical"
    params = {"symbol": symbol, "interval": interval, "count": limit}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    if "data" not in data:
        return None
    quotes = data["data"]["quotes"]
    df = pd.DataFrame([{
        "time": q["time_open"],
        "close": q["quote"]["USD"]["close"],
    } for q in quotes])
    return df

# ------------------ Signals ------------------
def check_signals(symbol):
    df = fetch_cmc_data(symbol)
    if df is None or df.empty:
        return None, None, None

    df["MA7"] = df["close"].rolling(7).mean()
    df["MA25"] = df["close"].rolling(25).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # تنبيه مبكر (لو الفرق أقل من 1%)
    diff = abs(latest["MA7"] - latest["MA25"]) / latest["MA25"] * 100
    if diff < 1:
        early_alert = f"⚠️ {symbol} قريب من التقاطع (فرق {diff:.2f}%)"
    else:
        early_alert = None

    # إشارة شراء / بيع
    if prev["MA7"] < prev["MA25"] and latest["MA7"] > latest["MA25"]:
        signal = f"✅ BUY Signal on {symbol} (MA7 ↑ فوق MA25)"
    elif prev["MA7"] > prev["MA25"] and latest["MA7"] < latest["MA25"]:
        signal = f"❌ SELL Signal on {symbol} (MA7 ↓ تحت MA25)"
    else:
        signal = None

    return signal, early_alert, df

def plot_chart(symbol, df):
    plt.figure(figsize=(8, 5))
    plt.plot(df["time"], df["close"], label="Price", color="black")
    plt.plot(df["time"], df["MA7"], label="MA7", color="green")
    plt.plot(df["time"], df["MA25"], label="MA25", color="red")
    plt.title(f"{symbol} Price with MA7 & MA25")
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# ------------------ Main ------------------
if __name__ == "__main__":
    send_text(f"🤖 Bot started with {len(MEME_COINS)} meme coins (CMC).")

    while True:
        signals = []
        alerts = []

        for coin in MEME_COINS:
            try:
                signal, early_alert, df = check_signals(coin)
                if early_alert:
                    alerts.append(early_alert)
                if signal:
                    signals.append(signal)
                    chart = plot_chart(coin, df)
                    send_photo(chart, caption=signal)
            except Exception as e:
                print(f"Error checking {coin}: {e}")

        if alerts:
            send_text("🔔 إشعارات مبكرة (قريبة من التقاطع):\n" + "\n".join(alerts))
        if signals:
            send_text("🚀 إشارات مؤكدة (تقاطع تم):\n" + "\n".join(signals))
        if not alerts and not signals:
            send_text("❌ لا يوجد عملات حققت أو اقتربت من الشرط الآن.")

        time.sleep(300)  # 5 دقائق
