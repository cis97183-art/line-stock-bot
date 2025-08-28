# =============================================================
# 程式的開頭：引入所有需要的工具
# =============================================================
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, abort, send_from_directory
import uuid
import logging
import sys
import os
import yfinance as yf
import requests
import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import psycopg2
import time

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    ImageSendMessage
)

# 從自訂模組中匯入資料庫、成交量和漲幅相關的函式
from db_utils import get_favorites, add_to_favorites, remove_from_favorites
from stock_volume import get_top_volume_stocks
from stock_ranking import get_top_gainers
from ai_utils import translate_text, summarize_text

# <<<=== 新增！強制設定日誌記錄器 ===>>>
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
    force=True
)
# <<<================================>>>

# =============================================================
# 從環境變數讀取金鑰並初始化服務
# =============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
SERVICE_PUBLIC_URL = os.environ.get('SERVICE_PUBLIC_URL')

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =============================================================
# 資料庫初始化
# =============================================================
def init_db():
    try:
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
    except Exception as e:
        logging.error(f"資料庫初始化失敗: {e}", exc_info=True)

init_db()

# =============================================================
# 功能函式
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
    except Exception as e:
        logging.error(f"查詢股價時發生錯誤 for symbol {symbol}: {e}", exc_info=True)
        return "查詢股價時發生錯誤。"
def get_company_profile(symbol):
    if not FINNHUB_API_KEY: return "錯誤：尚未設定 Finnhub API Key。"
    url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol.upper()}&metric=valuation&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data or 'metric' not in data or not data['metric']: return f"找不到 {symbol.upper()} 的基本面資料。"
        metrics = data['metric']
        pe_ratio = metrics.get('peTTM', 0)
        pb_ratio = metrics.get('pbTTM', 0)
        ps_ratio = metrics.get('psTTM', 0)
        dividend_yield = metrics.get('dividendYieldIndicatedAnnual', 0)
        return (f"📊 {symbol.upper()} 的基本面數據：\n"
                f"--------------------------\n"
                f"本益比 (P/E): {pe_ratio:.2f}\n股價淨值比 (P/B): {pb_ratio:.2f}\n"
                f"股價營收比 (P/S): {ps_ratio:.2f}\n年均殖利率 (%): {dividend_yield:.2f}")
    except Exception as e:
        logging.error(f"查詢基本面時發生錯誤 for symbol {symbol}: {e}", exc_info=True)
        return "查詢基本面時發生錯誤。"
def get_company_news(symbol):
    if not FINNHUB_API_KEY: return "錯誤：尚未設定 Finnhub API Key。"
    today, one_week_ago = datetime.date.today(), datetime.date.today() - datetime.timedelta(days=7)
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol.upper()}&from={one_week_ago.strftime('%Y-%m-%d')}&to={today.strftime('%Y-%m-%d')}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_list = response.json()
        if not news_list: return f"找不到 {symbol.upper()} 在過去一週的相關新聞。"

        news_item = news_list[0]
        headline = news_item.get('headline', '無標題')
        summary = news_item.get('summary', '無摘要')
        news_url = news_item.get('url', '#')

        translated_headline = translate_text(headline)
        summarized_content = summarize_text(summary)

        reply_text = (f"📰 {symbol.upper()} 的 AI 智慧新聞摘要：\n\n"
                      f"【標題】\n{translated_headline}\n\n"
                      f"【AI 摘要】\n{summarized_content}\n\n"
                      f"🔗 原文連結：\n{news_url}")

        return reply_text.strip()
    except Exception as e:
        logging.error(f"處理新聞資料時發生錯誤 for symbol {symbol}: {e}", exc_info=True)
        return "處理新聞資料時發生內部錯誤。"
def get_stock_chart_url(stock_symbol):
    """
    取得股票圖表網址。這裡使用一個簡單的範例。
    """
    return f"https://www.google.com/finance/chart?q={stock_symbol}"

def get_all_favorites_prices(user_id):
    """
    取得使用者所有最愛股票的價格。
    """
    favorites = get_favorites(user_id)
    if not favorites:
        return "您的最愛清單是空的喔！"
    
    response_text = "您最愛的股票即時價格：\n"
    for symbol in favorites:
        price = get_stock_price(symbol)
        if price is not None:
            response_text += f"{symbol}: ${price:.2f}\n"
        else:
            response_text += f"{symbol}: 無法取得價格\n"
    return response_text

def get_stock_industry(stock_symbol):
    """
    使用 yfinance 取得特定股票的產業資訊。
    """
    try:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        industry = info.get('industry', '查無此股票或產業資訊')
        return f"股票『{stock_symbol}』所屬產業為：{industry}"
    except Exception as e:
        logging.error(f"取得產業資訊時發生錯誤 for symbol {stock_symbol}: {e}", exc_info=True)
        return "無法取得產業資訊，請確認股票代碼是否正確。"


# =============================================================
# Webhook 路由
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

# @app.route('/charts/<filename>')
# def serve_chart(filename):
#     return send_from_directory('tmp_charts', filename)


# =============================================================
# 核心訊息處理邏輯
# =============================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    根據使用者的訊息內容回覆。
    """
    user_message = event.message.text.lower().strip()
    user_id = event.source.user_id
    reply_object = None

    if user_message in ['使用說明', 'help']:
        reply_object = TextSendMessage(text="""💡 使用說明 💡\n\n你好！我是你的股市小助理，你可以這樣使用我：\n\n1️⃣ **查詢股價**\n  - 直接輸入美股代碼 (例如: AAPL, TSLA)，我會回覆即時股價。\n  - 查詢成功後可點擊下方按鈕獲取更多資訊。\n\n2️⃣ **我的最愛**\n  - 點擊選單上的「我的最愛」，我會列出你所有自選股的報價。\n  - 看到喜歡的股票，點「加入我的最愛❤️」按鈕即可收藏。""")
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
        chart_url = get_stock_chart_url(stock_symbol)
        reply_object = ImageSendMessage(original_content_url=chart_url, preview_image_url=chart_url)
    elif user_message.startswith('industry ') or user_message.startswith('產業 '):
        try:
            stock_symbol = user_message.split(" ")[1].upper()
            reply_text = get_stock_industry(stock_symbol)
            reply_object = TextSendMessage(text=reply_text)
        except IndexError:
            reply_object = TextSendMessage(text="請輸入正確格式：industry [股票代號] 或 產業 [股票代號]")
    
    # 新增熱門成交量功能
    elif user_message in ['熱門成交量', '爆量', '熱門','成交量排名']:
        reply_object = TextSendMessage(text=get_top_volume_stocks())

    # === 新增漲幅偵測與排名功能 ===
    elif user_message in ['熱門漲幅', '漲幅','漲幅排名']:
        reply_object = TextSendMessage(text=get_top_gainers())

    elif user_message.upper() in ['HI', 'HELLO', '你好', '哈囉']:
        reply_object = TextSendMessage(text="哈囉！我是您的股票機器人。您可以輸入 'list' 來查看最愛股票，或輸入 'add [股票代號]' 來新增股票。")

    else:
        stock_symbol = user_message.upper()
        reply_text = get_stock_price(stock_symbol)
        if "找不到" in reply_text or "錯誤" in reply_text:
            reply_object = TextSendMessage(text="抱歉，我不明白您的意思。您可以試試：'list', 'add [股票代號]', 'remove [股票代號]', 'chart [股票代號]', '產業 [股票代號]', '熱門成交量', 或 '熱門漲幅'。")
        else:
            quick_reply_buttons = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="股價走勢圖 📈", text=f"{stock_symbol} chart")),
                QuickReplyButton(action=MessageAction(label="基本面 📊", text=f"{stock_symbol} profile")),
                QuickReplyButton(action=MessageAction(label="最新新聞 📰", text=f"{stock_symbol} news")),
                QuickReplyButton(action=MessageAction(label="加入我的最愛 ❤️", text=f"add {stock_symbol}")),])
            reply_object = TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)

    if reply_object:
        line_bot_api.reply_message(event.reply_token, messages=reply_object)

    return reply_object

# =============================================================
# 程式的啟動點
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

