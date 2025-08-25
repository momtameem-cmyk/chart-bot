# bot.py
import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot

# إعداد متغيرات البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة 300 عملة رمزية عامة
coins = [
    "BTC","ETH","XRP","LTC","BCH","ADA","DOT","LINK","XLM","DOGE",
    "UNI","SOL","MATIC","ATOM","VET","THETA","TRX","FIL","EOS","ALGO",
    "XTZ","AAVE","KSM","NEO","DASH","ZEC","MKR","BAT","COMP","YFI",
    "SNX","DCR","OMG","QTUM","LSK","NANO","ICX","ZIL","BTT","HOT",
    "ENJ","KNC","REP","1INCH","CHZ","SUSHI","CRV","CAKE","FTM","HEGIC",
    "STMX","MANA","GRT","ANKR","BAL","CVC","RUNE","OCEAN","NMR","KAVA",
    "CELO","UMA","LRC","RVN","ARV","HNT","GLM","KSM","ALPHA","SRM",
    "WAVES","ZEN","SC","COTI","CHSB","AR","FET","STORJ","CEL","XEM",
    "IOTA","KMD","ONG","ONT","NEXO","PAX","VTHO","XVG","ICX","RVN",
    "BNT","ZEN","DGB","XVS","CVX","FXS","MKR","RPL","INJ","API3",
    "AKRO","MIR","SAND","AXS","THOR","LUNA","ANC","MITH","DODO","CEEK",
    "WTC","RSR","REN","ZRX","UMA","STMX","RLC","KNC","SXP","FTT",
    "YFII","OXT","NKN","MCO","REP","NMR","BAND","TWT","ANKR","FARM",
    "LPT","GNO","SRM","REEF","HIVE","COTI","KAVA","TRB","FIS","POND",
    "FX","PERP","ARDR","CVC","MITH","BTS","NULS","LBC","CRO","WAVES",
    "SYS","IOST","STORJ","GALA","CTSI","REN","POLY","CELO","KLAY",
    "MINA","GRT","COTI","AKRO","SUSHI","CRV","1INCH","UNI","BAL","YFI",
    "AAVE","SNX","COMP","MKR","LINK","LRC","OMG","ZRX","BNT","KNC",
    "REP","NMR","OCEAN","SXP","RSR","RUNE","NMR","DGB","FET","RVN",
    "SC","ICX","BTT","VET","THETA","TRX","XTZ","ALGO","FIL","ATOM",
    "MATIC","SOL","DOT","ADA","BCH","LTC","XRP","ETH","BTC","DOGE",
    "AVAX","FTM","EGLD","NEAR","ONE","KSM","CELR","ANKR","CHZ","AR",
    "CEL","HNT","GLM","ALPHA","SAND","AXS","MANA","FLOKI","LUNA2",
    "GMT","PEOPLE","MASK","APT","OP","ARB","ENS","IMX","GODS","RNDR",
    "APE","LOOKS","DYDX","GMX","STG","MAGIC","PEPE","KDA","IOTX","CVX",
    "FXS","BAL","CRV","SUSHI","1INCH","LDO","RPL","INJ","API3","AKRO",
    "MIR","ANC","ANCX","FARM","LPT","GNO","SRM","REEF","HIVE","COTI",
    "KAVA","TRB","FIS","POND","FX","PERP","ARDR","CVC","MITH","BTS"
]

CMC_HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    response = requests.get(url, headers=CMC_HEADERS, timeout=10).json()
    if "data" in response and symbol in response["data"]:
        return response["data"][symbol]["quote"]["USD"]["price"]
    return None

def fetch_historical(symbol, limit=50):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical?symbol={symbol}&time_start=2023-01-01&interval=1d"
    try:
        response = requests.get(url, headers=CMC_HEADERS, timeout=10).json()
        if "data" in response and "quotes" in response["data"]:
            quotes = response["data"]["quotes"][-limit:]
            df = pd.DataFrame([{"close": q["quote"]["USD"]["close"]} for q in quotes])
            return df
    except:
        return None
    return None

def check_signals(symbol):
    df = fetch_historical(symbol)
    if df is None or df.empty:
        return
    df["EMA7"] = ta.ema(df["close"], length=7)
    df["EMA25"] = ta.ema(df["close"], length=25)
    df["RSI"] = ta.rsi(df["close"], length=14)
    if df["EMA7"].iloc[-2] < df["EMA25"].iloc[-2] and df["EMA7"].iloc[-1] > df["EMA25"].iloc[-1]:
        if df["RSI"].iloc[-1] >= 45:
            bot.send_message(chat_id=CHAT_ID, text=f"✅ {symbol} crossed EMA7>EMA25 & RSI={df['RSI'].iloc[-1]:.2f}")

while True:
    for coin in coins:
        try:
            check_signals(coin)
        except Exception as e:
            # تجاهل الأخطاء وعدم إرسال إشعار عند الخطأ
            pass
    time.sleep(60)
