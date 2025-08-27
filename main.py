import os
import yfinance as yf
import logging
from linebot.models import TextSendMessage, ImageSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, BubbleStyle, ButtonComponent, URIAction, FlexSendMessage

# 從自訂模組中匯入資料庫、成交量和漲幅相關的函式
from db_utils import get_favorites, add_to_favorites, remove_from_favorites
from stock_volume import get_top_volume_stocks
from stock_ranking import get_top_gainers

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_stock_price(stock_symbol):
    """
    使用 yfinance 取得股票即時價格。
    """
    try:
        stock = yf.Ticker(stock_symbol)
        price = stock.history(period="1d")['Close'][0]
        return price
    except Exception as e:
        logging.error(f"取得股價時發生錯誤 for symbol {stock_symbol}: {e}", exc_info=True)
        return None

def get_stock_chart(stock_symbol):
    """
    取得股票圖表網址。這裡使用一個簡單的範例。
    """
    return f"https://www.google.com/finance/chart?q={stock_symbol}"

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

def handle_message(event):
    """
    根據使用者的訊息內容回覆。
    """
    user_message = event.message.text.lower().strip()
    user_id = event.source.user_id
    reply_object = None

    if user_message == 'list':
        reply_object = TextSendMessage(text=get_all_favorites_prices(user_id))

    elif user_message.startswith('add '):
        try:
            stock_symbol = user_message.split(" ")[1].upper()
            reply_object = TextSendMessage(text=add_to_favorites(user_id, stock_symbol))
        except IndexError:
            reply_object = TextSendMessage(text="請輸入正確格式：add [股票代號]")

    elif user_message.startswith('remove '):
        try:
            stock_symbol = user_message.split(" ")[1].upper()
            reply_object = TextSendMessage(text=remove_from_favorites(user_id, stock_symbol))
        except IndexError:
            reply_object = TextSendMessage(text="請輸入正確格式：remove [股票代號]")

    elif user_message.startswith('chart '):
        try:
            stock_symbol = user_message.split(" ")[1].upper()
            chart_url = get_stock_chart(stock_symbol)
            reply_object = ImageSendMessage(original_content_url=chart_url, preview_image_url=chart_url)
        except IndexError:
            reply_object = TextSendMessage(text="請輸入正確格式：chart [股票代號]")

    elif user_message.startswith('industry ') or user_message.startswith('產業 '):
        try:
            stock_symbol = user_message.split(" ")[1].upper()
            reply_text = get_stock_industry(stock_symbol)
            reply_object = TextSendMessage(text=reply_text)
        except IndexError:
            reply_object = TextSendMessage(text="請輸入正確格式：industry [股票代號] 或 產業 [股票代號]")
    
    # 新增熱門成交量功能
    elif user_message in ['熱門成交量', '爆量', '熱門']:
        reply_object = TextSendMessage(text=get_top_volume_stocks())

    # === 新增漲幅偵測與排名功能 ===
    elif user_message in ['熱門漲幅', '漲幅']:
        reply_object = TextSendMessage(text=get_top_gainers())

    elif user_message.upper() in ['HI', 'HELLO', '你好', '哈囉']:
        reply_object = TextSendMessage(text="哈囉！我是您的股票機器人。您可以輸入 'list' 來查看最愛股票，或輸入 'add [股票代號]' 來新增股票。")

    else:
        reply_object = TextSendMessage(text="抱歉，我不明白您的意思。您可以試試：'list', 'add [股票代號]', 'remove [股票代號]', 'chart [股票代號]', '產業 [股票代號]', '熱門成交量', 或 '熱門漲幅'。")

    return reply_object
