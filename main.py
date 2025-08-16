# =============================================================
# 程式的開頭：引入需要的工具，並從 .env 讀取環境變數
# =============================================================
from dotenv import load_dotenv
load_dotenv() # 這兩行會讀取 .env 檔案中的金鑰

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
    # ... (此函式內容不變，為求簡潔此處省略，請保留你原本的) ...
def get_company_news(symbol):
    # ... (此函式內容不變，為求簡潔此處省略，請保留你原本的) ...

def add_to_favorites(user_id, stock_symbol):
    # ... (此函式內容不變，為求簡潔此處省略，請保留你原本的) ...

# <<<=== 新增！讀取最愛清單的函式 ===>>>
def get_favorites(user_id):
    """從資料庫讀取指定使用者的最愛清單"""
    try:
        conn = sqlite3.connect('favorites.db')
        cursor = conn.cursor()
        
        # 執行 SQL SELECT 指令，找出符合 user_id 的所有 stock_symbol
        cursor.execute("SELECT stock_symbol FROM favorites WHERE user_id = ?", (user_id,))
        
        # fetchall() 會回傳一個列表，其中每個元素是一個元組(tuple)，例如 [('AAPL',), ('TSLA',)]
        results = cursor.fetchall()
        conn.close()
        
        # 我們將結果轉換成一個單純的字串列表，例如 ['AAPL', 'TSLA']
        stock_list = [item[0] for item in results]
        return stock_list
        
    except Exception as e:
        print(f"資料庫讀取錯誤: {e}")
        return [] # 如果出錯，回傳一個空列表

# =============================================================
# Webhook 的進入點
# =============================================================
@app.route("/callback", methods=['POST'])
def callback():
    # ... (此函式內容不變，為求簡潔此處省略，請保留你原本的) ...

# =============================================================
# 核心訊息處理邏輯 (最終版)
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.lower()
    reply_object = None

    # 指令一：查詢最愛清單
    if user_message == '我的最愛':
        stock_list = get_favorites(user_id)
        if not stock_list:
            reply_text = "您的最愛清單是空的喔！快去新增吧！"
        else:
            reply_text = "--- 您的最愛清單 ✨ ---\n"
            # 透過迴圈，一次查詢所有股票的價格
            for symbol in stock_list:
                # 直接呼叫我們現有的 get_stock_price 函式
                price_info = get_stock_price(symbol)
                reply_text += f"\n{price_info}\n"
        reply_object = TextSendMessage(text=reply_text.strip())

    # 指令二：查詢新聞
    elif 'news' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        reply_text = get_company_news(stock_symbol)
        reply_object = TextSendMessage(text=reply_text)

    # 指令三：新增最愛
    elif 'add ' in user_message:
        stock_symbol = user_message.split(" ")[1].upper()
        reply_text = add_to_favorites(user_id, stock_symbol)
        reply_object = TextSendMessage(text=reply_text)

    # 預設行為：查詢單一股票
    else:
        stock_symbol = user_message.upper()
        reply_text = get_stock_price(stock_symbol)
        if "找不到股票代碼" in reply_text or "錯誤" in reply_text:
            reply_object = TextSendMessage(text=reply_text)
        else:
            quick_reply_buttons = QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")),
                    QuickReplyButton(action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")),
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