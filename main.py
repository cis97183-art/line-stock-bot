
# ==============================================================================
# 儲存格 1：安裝所需套件
# ==============================================================================
# 每次重新連線 Colab 都需要執行一次這個儲存格，以安裝 line-bot-sdk


print("✅ 所有套件都已成功安裝！")

# ==============================================================================
# 儲存格 2：引入套件並讀取金鑰
# ==============================================================================
# 引入所有需要的工具
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
from google.colab import userdata # Colab 讀取密鑰的專用工具
import os # 雖然 Colab 不用 os.environ，但為了未來部署方便，先引入

# --- 從 Colab Secrets 安全地讀取金鑰 ---
# 執行前，請確保你已經在左側的「鑰匙」圖示中設定好這三個密鑰
try:
    LINE_CHANNEL_ACCESS_TOKEN = userdata.get('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = userdata.get('LINE_CHANNEL_SECRET')
    FINNHUB_API_KEY = userdata.get('FINNHUB_API_KEY')
    print("🔑 金鑰已成功讀取！")
    
    # 簡單驗證一下金鑰是否為空
    if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, FINNHUB_API_KEY]):
        print("⚠️ 警告：有部分金鑰是空的，請檢查 Colab 密鑰設定！")
        
except Exception as e:
    print(f"❌ 讀取金鑰時發生錯誤，請確認你已在 Colab Secrets 中設定好所有金鑰: {e}")


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
test_symbol_1 = "AAPL"  # 蘋果
test_symbol_2 = "GOOG"  # Google
test_symbol_3 = "NONEXISTENT" # 一個不存在的股票

print(f"--- 正在測試 {test_symbol_1} ---")
print(get_stock_price(test_symbol_1))
print("\n" + "="*30 + "\n")

print(f"--- 正在測試 {test_symbol_2} ---")
print(get_stock_price(test_symbol_2))
print("\n" + "="*30 + "\n")

print(f"--- 正在測試 {test_symbol_3} ---")
print(get_stock_price(test_symbol_3))



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
    user_message = event.message.text
    reply_text = get_stock_price(user_message) # 直接呼叫我們測試好的函式
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
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


