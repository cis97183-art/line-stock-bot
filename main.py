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
# 核心功能：查詢股價的函式
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
# Webhook 的進入點，負責接收 LINE 的訊息
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
# 核心訊息處理邏輯 (豪華版)
# =============================================================
# =============================================================
# 核心訊息處理邏輯 (升級版：能聽懂指令)
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()  # 先把使用者訊息轉成小寫，方便判斷
    reply_object = None  # 先準備一個空的物件來裝回覆

    # 判斷訊息是否為新聞查詢指令
    if 'news' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        # (未來這裡可以接上新聞 API)
        reply_text = f"好的，正在為您查詢 {stock_symbol} 的最新新聞..."
        reply_object = TextSendMessage(text=reply_text)

    # 判斷訊息是否為加入我的最愛指令
    elif 'add' in user_message:
        stock_symbol = user_message.split(" ")[1].upper()
        # (未來這裡可以接上資料庫)
        reply_text = f"已將 {stock_symbol} 加入您的最愛清單！ ❤️"
        reply_object = TextSendMessage(text=reply_text)

    # 如果都不是以上指令，才當作是股票查詢
    else:
        stock_symbol = user_message.upper()
        reply_text = get_stock_price(stock_symbol)

        # 檢查回覆是否為錯誤訊息
        if "找不到股票代碼" in reply_text or "錯誤" in reply_text:
            reply_object = TextSendMessage(text=reply_text)
        else:
            # 成功查到股價，才加上 Quick Reply 按鈕
            quick_reply_buttons = QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")
                    ),
                ]
            )
            reply_object = TextSendMessage(
                text=reply_text,
                quick_reply=quick_reply_buttons
            )
    
    # 最後，統一發送訊息 (如果 reply_object 有內容的話)
    if reply_object:
        line_bot_api.reply_message(event.reply_token, messages=reply_object)

# =============================================================
# 程式的啟動點
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

