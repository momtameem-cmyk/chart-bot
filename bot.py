import os
import asyncio
import aiohttp
import pandas as pd
import pandas_ta as ta
from telegram import Bot

# متغيرات البيئة (Config Vars على Heroku)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة 300 عملة تقريبية (يمكن تعديلها لاحقاً)
coins = [
    "BTC","ETH","BNB","XRP","ADA","SOL","DOGE","DOT","MATIC","LTC",
    "TRX","SHIB","AVAX","WBTC","NEAR","UNI","ATOM","LINK","XLM","ALGO",
    "VET","FIL","ICP","XTZ","MANA","SAND","EGLD","AXS","THETA","FLOW",
    "FTM","AAVE","EOS","KSM","KLAY","CRO","XMR","BCH","ZEC","CAKE",
    "QNT","MIOTA","HNT","BAT","ENJ","CHZ","LRC","GRT","STX","RUNE",
    "KSM","AR","1INCH","ZRX","COMP","SNX","DASH","NANO","RVN","GNO",
    "BTT","HOT","ANKR","KAVA","OKB","CELO","GLM","KNC","ICX","LPT",
    "ONT","DGB","SC","BAND","OCEAN","ZEN","BAL","SXP","RVN","ALPHA",
    "STORJ","REN","KAVA","CEL","NEXO","FET","SRM","RAY","KSM","WAVES",
    "HBAR","ZIL","CTSI","CVC","FLUX","ARDR","MKR","YFI","UMA","PAXG",
    "BNT","OMG","REP","SUSHI","CRV","DCR","SYS","XEM","ONE","ANKR",
    "DODO","LUNA","UST","TWT","PERP","SAND","GALA","TEL","SPELL","GLMR",
    "RNDR","MATIC","APT","PEPE","OP","KLAY","APE","FLOKI","CFX","CVX",
    "GMX","FXS","LDO","ANKR","ENS","STETH","RPL","DYDX","IMX","FET",
    "CELR","SKL","CHR","CTK","MLN","JST","ARPA","TRIBE","RLC","COTI",
    "C98","MIR","NKN","ACA","FLM","NMR","SFP","API3","ROSE","GTC",
    "HIGH","ILV","LINA","PHA","FIS","PERP","PHA","RAD","IDEX","TORN",
    "BADGER","LQTY","KP3R","REN","KEEP","MTA","MATH","LPT","ORCA","OXT",
    "MASK","BTRST","STMX","MLK","FARM","FIDA","TRU","REQ","DENT","AGLD",
    "CSPR","ALCX","AKRO","XVS","KP3R","XEC","DGB","CEL","KDA","FX",
    "VGX","BURGER","RAZ","TWT","AUDIO","IQ","POLS","GNO","HIVE","GLMR",
    "COTI","NU","TVK","PYR","ARV","UOS","CVP","OGN","NFT","BRO","QKC",
    "GTC","TRB","DAR","BADGER","FARM","PHA","ALGO","RNDR","STG","MBOX",
    "WOO","DEXE","OOKI","FXS","XVS","MASK","MLN","HEGIC","TRIBE","ALPHA",
    "IDEX","MLK","KEEP","SFP","RLC","MTA","PERP","ROSE","HIGH","BICO",
    "AKRO","JST","XEC","C98","MIR","TORN","BURGER","PYR","IQ","CVP",
    "VGX","RAZ","AUDIO","UOS","OGN","NFT","BRO","QKC","TVK","ARV"
]

CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
}

async def fetch_price(session, symbol):
    params = {"symbol": symbol}
    try:
        async with session.get(CMC_URL, headers=HEADERS, params=params) as resp:
            data = await resp.json()
            price = data["data"][symbol]["quote"]["USD"]["price"]
            return price
    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {symbol}: {e}")
        return None

async def check_indicators(symbol, prices):
    df = pd.DataFrame(prices, columns=["close"])
    df["ema7"] = ta.ema(df["close"], length=7)
    df["ema25"] = ta.ema(df["close"], length=25)
    df["rsi"] = ta.rsi(df["close"], length=14)

    if len(df) < 2:
        return

    if df["ema7"].iloc[-2] < df["ema25"].iloc[-2] and df["ema7"].iloc[-1] > df["ema25"].iloc[-1]:
        if df["rsi"].iloc[-1] >= 45:
            await bot.send_message(chat_id=CHAT_ID, text=f"📈 {symbol} EMA7 crossed above EMA25 and RSI={df['rsi'].iloc[-1]:.1f}")

async def main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (300 coins + EMA & RSI alerts).")

    async with aiohttp.ClientSession() as session:
        while True:
            for coin in coins:
                price = await fetch_price(session, coin)
                if price:
                    await check_indicators(coin, [price]*30)
                await asyncio.sleep(0.2)
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
