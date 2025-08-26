# =============================================================
# 程式的開頭：引入所有需要的工具
# =============================================================
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, abort, send_from_directory
import uuid

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    ImageSendMessage
)
import requests
import os
import datetime
import psycopg2
import time
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf # <<<=== 新增！yfinance 的工具

# =============================================================
# 從環境變數讀取金鑰並初始化服務
# =============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
# <<<=== 已移除 ALPHA_VANTAGE_API_KEY ===>>>

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =============================================================
# 資料庫初始化
# =============================================================
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            stock_symbol VARCHAR(50) NOT NULL,
            UNIQUE(user_id, stock_symbol)
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# =============================================================
# 功能函式
# =============================================================
# (get_stock_price, get_company_profile, get_company_news, add_to_favorites, get_favorites 這些函式都不變)
# ...

# <<<=== 最終版！使用 yfinance 產生圖表的函式 ===>>>
def generate_stock_chart(symbol):
    try:
        # 1. 使用 yfinance 抓取歷史股價
        # 抓取最近一個月的歷史資料 (period='1mo')
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1mo')
        
        if data.empty:
            print(f"yfinance 找不到 {symbol} 的歷史資料")
            return None

        # 2. 使用 Matplotlib 繪圖
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(data.index, data['Close'], color='cyan', linewidth=2)
        ax.set_title(f'{symbol.upper()} - 30-Day Price Chart', fontsize=20, color='white')
        ax.set_ylabel('Price (USD)', fontsize=14, color='white')
        ax.tick_params(axis='x', colors='white', rotation=30)
        ax.tick_params(axis='y', colors='white')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        # 3. 儲存圖片到本地暫存
        if not os.path.exists('tmp_charts'): os.makedirs('tmp_charts')
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join('tmp_charts', filename)
        plt.savefig(filepath, facecolor='#1E1E1E')
        plt.close(fig)
        
        return filename

    except Exception as e:
        print(f"圖表生成失敗 (yfinance): {e}")
        return None

# =============================================================
# Webhook 路由 (維持不變)
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

@app.route('/charts/<filename>')
def serve_chart(filename):
    return send_from_directory('tmp_charts', filename)

# =============================================================
# 功能函式一：查詢股價
# =============================================================
def get_stock_price(symbol):
    if not FINNHUB_API_KEY: return "錯誤：尚未設定 Finnhub API Key。"
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data or data.get('c') == 0: return f"找不到股票代碼 '{symbol.upper()}' 的資料。"
        current_price, price_change, percent_change = data.get('c', 0), data.get('d', 0), data.get('dp', 0)
        high_price, low_price = data.get('h', 0), data.get('l', 0)
        emoji = "📈" if price_change >= 0 else "📉"
        return (f"{emoji} {symbol.upper()} 的即時股價資訊：\n"
                f"--------------------------\n"
                f"當前價格: ${current_price:,.2f}\n漲跌: ${price_change:,.2f}\n"
                f"漲跌幅: {percent_change:.2f}%\n最高價: ${high_price:,.2f}\n"
                f"最低價: ${low_price:,.2f}\n--------------------------")
    except Exception: return "查詢股價時發生錯誤。"

# =============================================================
# 核心訊息處理邏輯 (維持不變)
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.lower()
    reply_object = None

    if user_message in ['使用說明', 'help']:
        reply_object = TextSendMessage(text="""💡 使用說明 💡\n\n你好！我是你的股市小助理，你可以這樣使用我：\n\n1️⃣ **查詢股價**\n   - 直接輸入美股代碼 (例如: AAPL, TSLA)，我會回覆即時股價。\n   - 查詢成功後可點擊下方按鈕獲取更多資訊。\n\n2️⃣ **我的最愛**\n   - 點擊選單上的「我的最愛」，我會列出你所有自選股的報價。\n   - 看到喜歡的股票，點「加入我的最愛❤️」按鈕即可收藏。""")
    elif user_message in ['查詢股價', 'stock', 'query']:
        reply_object = TextSendMessage(text="請直接輸入您想查詢的美股代碼喔！\n(例如: NVDA)")
    elif user_message in ['我的最愛', 'favorite', 'favorites']:
        stock_list = get_favorites(user_id)
        if not stock_list: reply_text = "您的最愛清單是空的喔！快去新增吧！"
        else:
            reply_text = "--- 您的最愛清單 ✨ ---\n"
            for symbol in stock_list:
                reply_text += f"\n{get_stock_price(symbol)}\n"
        reply_object = TextSendMessage(text=reply_text.strip())
    elif 'profile' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        reply_object = TextSendMessage(text=get_company_profile(stock_symbol))
    elif 'news' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        reply_object = TextSendMessage(text=get_company_news(stock_symbol))
    elif 'add ' in user_message:
        stock_symbol = user_message.split(" ")[1].upper()
        reply_object = TextSendMessage(text=add_to_favorites(user_id, stock_symbol))
    elif 'chart' in user_message:
        stock_symbol = user_message.split(" ")[0].upper()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"正在為您產生 {stock_symbol} 的股價走勢圖，請稍候..."))
        filename = generate_stock_chart(stock_symbol)
        if filename and RENDER_EXTERNAL_URL:
            image_url = f"{RENDER_EXTERNAL_URL}/charts/{filename}"
            line_bot_api.push_message(user_id, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
        else:
            line_bot_api.push_message(user_id, TextSendMessage(text=f"抱歉，無法產生 {stock_symbol} 的圖表。"))
        return
    else:
        stock_symbol = user_message.upper()
        reply_text = get_stock_price(stock_symbol)
        if "找不到" in reply_text or "錯誤" in reply_text:
            reply_object = TextSendMessage(text=reply_text)
        else:
            quick_reply_buttons = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="股價走勢圖 📈", text=f"{stock_symbol} chart")),
                QuickReplyButton(action=MessageAction(label="基本面 📊", text=f"{stock_symbol} profile")),
                QuickReplyButton(action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")),
                QuickReplyButton(action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")),])
            reply_object = TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)
    
    if reply_object:
        line_bot_api.reply_message(event.reply_token, messages=reply_object)

# =============================================================
# 程式的啟動點
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)