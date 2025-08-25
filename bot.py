import os
import time
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot

# ====== Environment variables ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# ====== Coin list (300 coins) ======
coins = [
    "BTC","ETH","BNB","XRP","ADA","SOL","DOGE","DOT","MATIC","LTC",
    "TRX","AVAX","SHIB","UNI","ATOM","XLM","ETC","LINK","XMR","VET",
    "FIL","EOS","AAVE","THETA","NEO","KSM","DASH","ZEC","MKR","COMP",
    "SUSHI","YFI","OMG","BAT","ENJ","CHZ","QTUM","RVN","ONT","ICX",
    "ALGO","CRO","NANO","DGB","ZIL","WAVES","HOT","STX","KAVA","CEL",
    "SC","LRC","1INCH","ANKR","FTM","MANA","RUNE","OCEAN","GRT","CHSB",
    "XEC","HNT","CELO","IOTX","KNC","GLM","RSR","SXP","REN","DENT",
    "CVC","PAXG","SRM","BAL","NMR","COTI","LPT","BNT","UMA","WOO",
    "AR","CVX","TRB","KLAY","RAY","API3","HARD","FET","ALPHA","STORJ",
    "ROSE","FLOW","CHR","SKL","REQ","AKRO","OGN","TOMO","ORN","INJ",
    "POLS","CTSI","POLY","BAND","FARM","MIR","FXS","SPELL","JST","ONE",
    "RSV","GLMR","MOVR","RLC","AKT","XVG","REEF","TWT","ORN","ORN",
    "ANKR","STMX","CTK","HIVE","LINA","SUN","STRAX","ATA","VGX","TOMO",
    "UOS","NKN","OXT","TRIBE","RDN","AVA","IDEX","AKRO","PERP","KAI",
    "NFTX","KP3R","DODO","FIO","CVNT","ORN","GNO","BAND","LPT","BTRST",
    "SAND","AXS","THETA","ILV","ENS","GMX","LOOKS","DYDX","RLY","FXS",
    "SPELL","APE","MAGIC","IMX","CRO","QNT","MINA","LDO","ANKR","KAVA",
    "BTRST","GTC","FARM","1INCH","REN","SUSHI","AAVE","COMP","MKR","SNX",
    "YFI","BAL","UMA","CRV","NMR","ALPHA","RUNE","FTM","TWT","CAKE",
    "KSM","DOT","NEO","EOS","ADA","SOL","VET","THETA","MANA","CHZ",
    "ENJ","SXP","NMR","GRT","RLC","OCEAN","REN","RSR","STORJ","WAVES",
    "ZIL","HOT","CELO","IOTX","KNC","GLM","DENT","CVC","ANKR","FET",
    "ALPHA","BNT","UMA","LRC","1INCH","TRB","API3","HARD","XEC","HNT",
    "ROSE","CHR","SKL","REQ","AKRO","OGN","INJ","CTSI","POLY","BAND",
    "FARM","MIR","FXS","SPELL","JST","ONE","RSV","GLMR","MOVR","AKT",
    "XVG","REEF","TWT","ORN","STMX","CTK","HIVE","LINA","SUN","STRAX",
    "ATA","VGX","UOS","NKN","OXT","TRIBE","RDN","AVA","IDEX","PERP",
    "KAI","NFTX","KP3R","DODO","FIO","CVNT","GNO","BAND","LPT","BTRST",
    "SAND","AXS","ILV","ENS","GMX","LOOKS","DYDX","RLY","FXS","SPELL",
    "APE","MAGIC","IMX","CRO","QNT","MINA","LDO","ANKR","KAVA","BTRST",
    "GTC","FARM","1INCH","REN","SUSHI","AAVE","COMP","MKR","SNX","YFI"
]

# ====== Function to fetch historical data ======
def fetch_historical(symbol, limit=50):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol + "USDT", "interval": "1m", "limit": limit}
    try:
        response = requests.get(url, params=params).json()
        df = pd.DataFrame(response, columns=[
            "Open_time","Open","High","Low","Close","Volume",
            "Close_time","Quote_asset_volume","Number_of_trades",
            "Taker_buy_base","Taker_buy_quote","Ignore"
        ])
        df["Close"] = df["Close"].astype(float)
        return df
    except Exception as e:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching historical for {symbol}: {e}"))
        return None

# ====== Function to check EMA & RSI conditions ======
def check_conditions(df, symbol):
    df["EMA7"] = ta.ema(df["Close"], length=7)
    df["EMA25"] = ta.ema(df["Close"], length=25)
    df["RSI"] = ta.rsi(df["Close"], length=14)

    if len(df) < 2:
        return False

    ema_cross = df["EMA7"].iloc[-2] <= df["EMA25"].iloc[-2] and df["EMA7"].iloc[-1] > df["EMA25"].iloc[-1]
    rsi_condition = df["RSI"].iloc[-1] >= 45

    if ema_cross and rsi_condition:
        return True
    return False

# ====== Main loop ======
async def main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (300 coins + EMA & RSI alerts).")
    while True:
        for symbol in coins:
            df = fetch_historical(symbol)
            if df is None:
                continue
            if check_conditions(df, symbol):
                msg = f"✅ {symbol} EMA7 crossed above EMA25 and RSI >= 45"
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                print(msg)
            else:
                print(f"Checked {symbol}, conditions not met.")
            time.sleep(1)
        print("Batch scan done. Waiting 60s...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
