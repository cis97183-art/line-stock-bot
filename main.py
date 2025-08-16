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
import datetime # <<<=== 新增 datetime 工具
import sqlite3

# =============================================================
# 從環境變數讀取金鑰並初始化服務
# =============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

# =============================================================
# <<<=== 新增區塊：資料庫初始化 ===>>>
# =============================================================
def init_db():
    """初始化資料庫，建立 favorites 資料表"""
    conn = sqlite3.connect('favorites.db') # 這會建立或連接到一個名為 favorites.db 的資料庫檔案
    cursor = conn.cursor()

    # 建立一個名為 favorites 的資料表，如果它不存在的話
    # 包含 id (主鍵), user_id (LINE 的使用者ID), stock_symbol (股票代碼) 三個欄位
    # UNIQUE(user_id, stock_symbol) 是一個約束，確保同一個使用者不會重複加入同一支股票
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            stock_symbol TEXT NOT NULL,
            UNIQUE(user_id, stock_symbol)
        )
    ''')

    conn.commit() # 提交變更
    conn.close() # 關閉資料庫連線

# 在程式的最一開始（啟動 App 前）就執行一次這個函式
# 這樣可以確保每次啟動時，資料庫和資料表都已經準備就緒
init_db()
# =============================================================

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =============================================================
# 查詢股價的函式 (這部分不變)
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

# =============================================================
# <<<=== 新增一個查詢新聞的函式 ===>>>
# =============================================================
def get_company_news(symbol):
    if not FINNHUB_API_KEY:
        return "錯誤：尚未設定 Finnhub API Key。"
        
    # 設定查詢日期範圍 (例如：過去7天)
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=7)
    
    # 格式化成 YYYY-MM-DD
    start_date = one_week_ago.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol.upper()}&from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_list = response.json()
        
        if not news_list:
            return f"找不到 {symbol.upper()} 在過去一週的相關新聞。"
            
        # 組裝回覆訊息，只取最新的3則新聞
        reply_text = f"📰 {symbol.upper()} 的最新新聞 (取3則)：\n\n"
        for news_item in news_list[:3]:
            headline = news_item.get('headline', '無標題')
            news_url = news_item.get('url', '#')
            reply_text += f"🔗 {headline}\n{news_url}\n\n"
            
        return reply_text.strip() # 去掉結尾多餘的換行
        
    except requests.exceptions.RequestException:
        return "查詢新聞時發生網路錯誤。"
    except Exception:
        return "處理新聞資料時發生內部錯誤。"


# =============================================================
# <<<=== 新增區塊：操作資料庫的函式 ===>>>
# =============================================================
def add_to_favorites(user_id, stock_symbol):
    """將股票加入指定使用者的最愛清單"""
    try:
        conn = sqlite3.connect('favorites.db')
        cursor = conn.cursor()
        
        # 執行 SQL INSERT 指令，將 user_id 和 stock_symbol 寫入資料表
        # 我們使用 (?, ?) 這種參數化查詢，可以防止 SQL 注入攻擊，更安全
        cursor.execute("INSERT INTO favorites (user_id, stock_symbol) VALUES (?, ?)", (user_id, stock_symbol))
        
        conn.commit()
        conn.close()
        return f"已將 {stock_symbol} 加入您的最愛清單！ ❤️"
        
    except sqlite3.IntegrityError:
        # 這會捕捉到當你試圖插入重複資料時的錯誤 (因為我們設定了 UNIQUE)
        conn.close()
        return f"{stock_symbol} 已經在您的最愛清單中了喔！ 😉"
    except Exception as e:
        # 捕捉其他可能的錯誤
        conn.close()
        print(f"資料庫錯誤: {e}")
        return "新增最愛時發生錯誤，請稍後再試。"


# =============================================================
# Webhook 的進入點 (這部分不變)
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
# 核心訊息處理邏輯 (升級版：呼叫新聞函式)
# =============================================================
# =============================================================
# 核心訊息處理邏輯 (升級版：具備寫入資料庫功能)
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id  # <<<=== 取得使用者的 LINE User ID
    user_message = event.message.text.lower()
    reply_object = None

    if 'news' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        reply_text = get_company_news(stock_symbol)
        reply_object = TextSendMessage(text=reply_text)

    elif 'add' in user_message:
        stock_symbol = user_message.split(" ")[1].upper()
        # <<<=== 呼叫我們的新函式，並傳入 user_id 和股票代碼 ===>>>
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
                    QuickReplyButton(action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")),
                ]
            )
            reply_object = TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)
    
    if reply_object:
        line_bot_api.reply_message(event.reply_token, messages=reply_object)

# =============================================================
# 程式的啟動點 (這部分不變)
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)