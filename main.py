# =============================================================
# 程式的開頭：引入需要的工具，並從 .env 讀取環境變數
# =============================================================
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import requests
import os
import datetime
import sqlite3

# =============================================================
# 從環境變數讀取金鑰並初始化服務
# =============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =============================================================
# 資料庫初始化
# =============================================================
def init_db():
    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            stock_symbol TEXT NOT NULL,
            UNIQUE(user_id, stock_symbol)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# =============================================================
# 所有功能函式 (查詢股價、新聞、操作資料庫)
# =============================================================
def get_stock_price(symbol):
    if not FINNHUB_API_KEY:
        return "錯誤：尚未設定 Finnhub API Key。"
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('c') == 0 and data.get('d') is None:
            return f"找不到股票代碼 '{symbol.upper()}' 的資料。"
        current_price = data.get('c', 0)
        price_change = data.get('d', 0)
        percent_change = data.get('dp', 0)
        high_price = data.get('h', 0)
        low_price = data.get('l', 0)
        emoji = "📈" if price_change >= 0 else "📉"
        return (
            f"{emoji} {symbol.upper()} 的即時股價資訊：\n"
            f"--------------------------\n"
            f"當前價格: ${current_price:,.2f}\n"
            f"漲跌: ${price_change:,.2f}\n"
            f"漲跌幅: {percent_change:.2f}%\n"
            f"最高價: ${high_price:,.2f}\n"
            f"最低價: ${low_price:,.2f}\n"
            f"--------------------------"
        )
    except requests.exceptions.RequestException:
        return "查詢股價時發生網路錯誤。"
    except Exception:
        return "處理股價資料時發生內部錯誤。"

def get_company_news(symbol):
    if not FINNHUB_API_KEY:
        return "錯誤：尚未設定 Finnhub API Key。"
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=7)
    start_date = one_week_ago.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol.upper()}&from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_list = response.json()
        if not news_list:
            return f"找不到 {symbol.upper()} 在過去一週的相關新聞。"
        reply_text = f"📰 {symbol.upper()} 的最新新聞 (取3則)：\n\n"
        for news_item in news_list[:3]:
            headline = news_item.get('headline', '無標題')
            news_url = news_item.get('url', '#')
            reply_text += f"🔗 {headline}\n{news_url}\n\n"
        return reply_text.strip()
    except requests.exceptions.RequestException:
        return "查詢新聞時發生網路錯誤。"
    except Exception:
        return "處理新聞資料時發生內部錯誤。"

def add_to_favorites(user_id, stock_symbol):
    try:
        conn = sqlite3.connect('favorites.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO favorites (user_id, stock_symbol) VALUES (?, ?)", (user_id, stock_symbol))
        conn.commit()
        conn.close()
        return f"已將 {stock_symbol} 加入您的最愛清單！ ❤️"
    except sqlite3.IntegrityError:
        conn.close()
        return f"{stock_symbol} 已經在您的最愛清單中了喔！ 😉"
    except Exception as e:
        conn.close()
        return "新增最愛時發生錯誤，請稍後再試。"

def get_favorites(user_id):
    try:
        conn = sqlite3.connect('favorites.db')
        cursor = conn.cursor()
        cursor.execute("SELECT stock_symbol FROM favorites WHERE user_id = ?", (user_id,))
        results = cursor.fetchall()
        conn.close()
        stock_list = [item[0] for item in results]
        return stock_list
    except Exception as e:
        return []

# =============================================================
# Webhook 的進入點
# =============================================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# =============================================================
# 核心訊息處理邏輯 (最終版)
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.lower()
    reply_object = None

    if user_message in ['我的最愛', 'favorite', 'favorites']:
        stock_list = get_favorites(user_id)
        if not stock_list:
            reply_text = "您的最愛清單是空的喔！快去新增吧！"
        else:
            reply_text = "--- 您的最愛清單 ✨ ---\n"
            for symbol in stock_list:
                price_info = get_stock_price(symbol)
                reply_text += f"\n{price_info}\n"
        reply_object = TextSendMessage(text=reply_text.strip())
    elif 'news' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        reply_text = get_company_news(stock_symbol)
        reply_object = TextSendMessage(text=reply_text)
    elif 'add ' in user_message:
        stock_symbol = user_message.split(" ")[1].upper()
        reply_text = add_to_favorites(user_id, stock_symbol)
        reply_object = TextSendMessage(text=reply_text)
    else:
        stock_symbol = user_message.upper()
        reply_text = get_stock_price(stock_symbol)
        if "找不到股票代碼" in reply_text or "錯誤" in reply_text:
            reply_object = TextSendMessage(text=reply_text)
        else:
            quick_reply_buttons = QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")),
                    QuickButton(action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")),
                ]
            )
            reply_object = TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)
    
    if reply_object:
        line_bot_api.reply_message(event.reply_token, messages=reply_object)

# =============================================================
# 程式的啟動點
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)