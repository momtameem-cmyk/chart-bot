import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import numpy as np
from telegram import Bot

# قراءة المتغيرات من البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# إرسال رسالة بدء التشغيل
bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started with CMC API (batch mode, 300 coins + daily report @00:00 UTC).")

# قائمة العملات (كمثال، ضع العملات التي تريد متابعتها)
coins = ["BTC", "ETH", "XRP", "ADA"]  # ضع 300 عملة هنا حسب الحاجة

def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    price = data["data"][symbol]["quote"]["USD"]["price"]
    return price

def send_alert(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

def analyze():
    for coin in coins:
        try:
            price = fetch_price(coin)
            # هنا يمكنك إضافة الحسابات لـ EMA و RSI
            # مثال على EMA و RSI باستخدام pandas_ta
            df = pd.DataFrame([price], columns=["Close"])
            df['EMA10'] = ta.ema(df['Close'], length=10)
            df['RSI'] = ta.rsi(df['Close'], length=14)

            ema_cross = df['Close'].iloc[-1] > df['EMA10'].iloc[-1]
            rsi_condition = df['RSI'].iloc[-1] >= 45

            if ema_cross and rsi_condition:
                send_alert(f"✅ {coin} reached EMA cross and RSI>=45. Price: {price}")

        except Exception as e:
            bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {coin}: {e}")

while True:
    analyze()
    time.sleep(60)  # تأخير دقيقة بين كل فحص
