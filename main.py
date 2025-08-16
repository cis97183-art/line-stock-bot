
from dotenv import load_dotenv
load_dotenv()

# 下面才是原本的 from flask import Flask...
from flask import Flask, request, abort
# ...

# ==============================================================================
# 儲存格 1：安裝所需套件
# ==============================================================================
# 每次重新連線 Colab 都需要執行一次這個儲存格，以安裝 line-bot-sdk


print("✅ 所有套件都已成功安裝！")

# ==============================================================================
# 儲存格 2：引入套件並讀取金鑰
# ==============================================================================
# 引入所有需要的工具
# =============================================================
# --- 請用這整塊「正確的開頭區塊範本」取代你檔案的開頭 ---
# =============================================================

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import requests
import os

# --- 從環境變數讀取金鑰 (請確保這三行完整無缺) ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

# --- 初始化 Flask App 和 Line Bot API ---
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =============================================================
# --- 開頭區塊結束，下方應該接著 def get_stock_price(symbol): ---
# =============================================================


# ==============================================================================
# 儲存格 3：核心功能 - 查詢股價的函式
# ==============================================================================
# 這是我們 Bot 的主要邏輯，負責去 Finnhub API 查詢資料並整理成文字

def get_stock_price(symbol):
    """
    使用 Finnhub API 查詢指定股票的即時報價
    :param symbol: 股票代碼 (e.g., "AAPL")
    :return: 格式化後的回覆字串，或錯誤訊息
    """
    # 檢查 API Key 是否存在
    if not FINNHUB_API_KEY:
        return "錯誤：尚未設定 Finnhub API Key。"

    # Finnhub API 的網址
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10) # 設定10秒超時
        response.raise_for_status() # 如果請求失敗 (e.g., 404, 500)，會拋出例外
        data = response.json()

        # Finnhub API 在找不到股票時，價格會回傳 0 或 None
        if data.get('c') == 0 and data.get('d') is None:
            return f"找不到股票代碼 '{symbol.upper()}' 的資料，請確認輸入是否正確 (例如：AAPL, TSLA, NVDA)。"

        # 從 API 回應中提取需要的資訊
        current_price = data.get('c', 'N/A')  # 當前價格
        price_change = data.get('d', 'N/A')  # 價格變動
        percent_change = data.get('dp', 'N/A') # 變動百分比
        high_price = data.get('h', 'N/A')    # 當日最高價
        low_price = data.get('l', 'N/A')     # 當日最低價

        # 根據漲跌決定表情符號
        emoji = "📈" if price_change >= 0 else "📉"

        # 組合回覆訊息
        reply_message = (
            f"{emoji} {symbol.upper()} 的即時股價資訊：\n"
            f"--------------------------\n"
            f"當前價格: ${current_price:,.2f}\n"
            f"漲跌: ${price_change:,.2f}\n"
            f"漲跌幅: {percent_change:.2f}%\n"
            f"最高價: ${high_price:,.2f}\n"
            f"最低價: ${low_price:,.2f}\n"
            f"--------------------------"
        )
        return reply_message

    except requests.exceptions.RequestException as e:
        print(f"API 請求錯誤: {e}")
        return "查詢股價時發生網路錯誤，請稍後再試。"
    except Exception as e:
        print(f"處理資料時發生錯誤: {e}")
        return "處理股價資料時發生內部錯誤。"

print("✅ get_stock_price() 函式已準備就緒！")


# ==============================================================================
# 儲存格 4：在 Colab 中直接測試函式功能
# ==============================================================================
# 由於 Colab 無法接收 LINE 的網路請求，我們不能直接執行 Web Server。
# 但我們可以像這樣，直接呼叫我們的函式，來測試核心邏輯是否正確。

# --- 測試區 ---




# ==============================================================================
# 儲存格 5：完整的 Web Server 程式碼 (僅供未來部署使用)
# ==============================================================================
# !!! 警告：這個儲存格在 Colab 中無法正常運作來接收 LINE 的訊息 !!!
# 這份程式碼是最終要部署到像 Render, Heroku 這種雲端平台的版本。

# --- 初始化 (假設金鑰已從上方儲存格讀取) ---
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Webhook 主要進入點 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# --- 訊息處理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    stock_symbol = user_input.upper()  # 取得股票代碼並轉為大寫

    # 先去查詢股價 (這部分不變)
    reply_text = get_stock_price(stock_symbol)

    # 檢查回覆是否為錯誤訊息，如果是，就不顯示按鈕
    if "找不到股票代碼" in reply_text or "錯誤" in reply_text:
        # 如果是錯誤訊息，就直接用純文字回覆
        reply_message_object = TextSendMessage(text=reply_text)
    else:
        # --- 建立 Quick Reply 按鈕 ---
        quick_reply_buttons = QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")
                ),
                QuickReplyButton(
                    action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")
                ),
                # 你可以繼續增加更多按鈕，但上限是13個
            ]
        )

        # 建立一個「包含文字」和「快速回覆按鈕」的新訊息物件
        reply_message_object = TextSendMessage(
            text=reply_text,
            quick_reply=quick_reply_buttons
        )

    # 使用這個新的、更豐富的訊息物件來回覆
    line_bot_api.reply_message(
        event.reply_token,
        messages=reply_message_object  # 將訊息物件傳遞給 messages 參數
    )

# --- 啟動伺服器 (在 Colab 中不會這樣執行) ---
# if __name__ == "__main__":
#     app.run()

print("✅ Web Server 程式碼已準備好，可供未來部署！")


# 貼到 main.py 的完整程式碼

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os # 改回使用 os 模組

# --- 從環境變數讀取金鑰 ---
# Render 平台會透過環境變數來設定這些值
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

app = Flask(__name__)

# --- 初始化 Line Bot API ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- 核心功能：查詢股價的函式 ---
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
    except requests.exceptions.RequestException as e:
        return "查詢股價時發生網路錯誤。"
    except Exception as e:
        return "處理股價資料時發生內部錯誤。"

# --- Webhook 主要進入點 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# --- 訊息處理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = get_stock_price(user_message)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 啟動伺服器 ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


