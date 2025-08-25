import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables (Heroku Config Vars)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة العملات 300 عملة
COINS = [
    "BTC","ETH","USDT","BNB","XRP","ADA","SOL","DOGE","DOT","MATIC","SHIB","TRX","AVAX","UNI","LTC","ATOM",
    "LINK","XMR","ALGO","VET","FIL","ICP","ETC","EOS","AAVE","MANA","NEO","KSM","FLOKI","CHZ","SAND",
    "CRV","MKR","THETA","ZEC","SNX","BAT","DASH","ENJ","DGB","HNT","CEL","OMG","LRC","QTUM","1INCH","KAVA",
    # ... أضف الباقي حتى تصل 300
]

HEADERS = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

async def send_msg(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    response = requests.get(url, headers=HEADERS).json()
    try:
        return response["data"][symbol]["quote"]["USD"]["price"]
    except:
        return None

def check_indicators(price_history):
    df = pd.DataFrame(price_history, columns=["price"])
    df['ema9'] = ta.ema(df['price'], length=9)
    df['ema21'] = ta.ema(df['price'], length=21)
    df['rsi'] = ta.rsi(df['price'], length=14)

    last_row = df.iloc[-1]

    ema_cross = None
    if df['ema9'].iloc[-2] < df['ema21'].iloc[-2] and last_row['ema9'] > last_row['ema21']:
        ema_cross = "bullish"
    elif df['ema9'].iloc[-2] > df['ema21'].iloc[-2] and last_row['ema9'] < last_row['ema21']:
        ema_cross = "bearish"

    rsi_signal = None
    if last_row['rsi'] >= 45:
        rsi_signal = "above 45"

    return ema_cross, rsi_signal

async def main():
    await send_msg("🤖 Bot started (300 coins + EMA & RSI alerts).")

    price_histories = {coin: [] for coin in COINS}

    while True:
        for coin in COINS:
            price = fetch_price(coin)
            if price is None:
                await send_msg(f"❌ Error fetching {coin}")
                continue

            price_histories[coin].append(price)
            if len(price_histories[coin]) > 50:
                price_histories[coin] = price_histories[coin][-50:]

            if len(price_histories[coin]) >= 21:
                try:
                    ema_cross, rsi_signal = check_indicators(price_histories[coin])
                    if ema_cross or rsi_signal:
                        msg = f"📊 {coin} Alert:\n"
                        if ema_cross:
                            msg += f"EMA cross detected ({ema_cross})\n"
                        if rsi_signal:
                            msg += f"RSI reached {rsi_signal}\n"
                        await send_msg(msg)
                except Exception as e:
                    await send_msg(f"❌ Error processing {coin}: {e}")

            await asyncio.sleep(1)  # تأخير 1 ثانية بين كل عملة

if __name__ == "__main__":
    asyncio.run(main())
