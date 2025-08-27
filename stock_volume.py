import yfinance as yf
import logging
import requests
from typing import List, Dict

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Finnhub API 的設定
# ⚠️ 注意：請將 YOUR_FINNHUB_API_KEY 替換成你自己的 API 金鑰
FINNHUB_API_KEY = "d2f97fpr01qj3egrql4gd2f97fpr01qj3egrql50"
FINNHUB_API_URL = "https://finnhub.io/api/v1"

def analyze_volume_and_price(price_change_percent: float) -> str:
    """
    分析成交量與股價連動關係並回傳簡短描述。
    """
    if price_change_percent > 1.0:
        return "資金流入強勁，市場有高度共識。"
    elif price_change_percent < -1.0:
        return "賣壓沉重，有大量資金流出。"
    else:
        return "市場關注度高，股價波動不大。"

def get_top_volume_stocks() -> str:
    """
    獲取熱門成交量股票排名，並包含簡短分析。
    """
    try:
        # 這是真實的 Finnhub API 呼叫
        # ⚠️ 需確保 FINNHUB_API_KEY 已設置正確
        response = requests.get(
            f"{FINNHUB_API_URL}/stock/market-movers?region=US&token={FINNHUB_API_KEY}"
        )
        response.raise_for_status()  # 如果請求失敗，拋出錯誤
        
        finnhub_data = response.json()
        
        # 確保回傳的資料包含 'mostActive' 鍵
        if 'mostActive' not in finnhub_data or not finnhub_data['mostActive']:
            return "Finnhub API 目前沒有熱門成交量資料，請稍後再試。"
        
        top_movers_data = finnhub_data['mostActive']
        
        reply_text = "📈 **熱門成交量排名** 📈\n\n"
        for stock in top_movers_data[:10]:
            symbol = stock.get('symbol', 'N/A')
            # 確保資料完整性
            if symbol == 'N/A':
                continue
            
            # Finnhub 回傳的成交量可能需要處理，這裡假設單位是股
            volume_mil = stock.get('volume', 0) / 1000000
            price_change = stock.get('changePercent', 0)
            analysis = analyze_volume_and_price(price_change)
            
            # 使用 yfinance 取得公司名稱和最新價格
            stock_info = yf.Ticker(symbol)
            info = stock_info.info
            company_name = info.get('longName', '無公司名稱')
            
            # 處理 yfinance 可能無法取得資料的情況
            try:
                current_price = stock_info.history(period="1d")['Close'][0]
            except (IndexError, KeyError):
                current_price = "無法取得價格"
                
            reply_text += f"▪️ **{company_name} ({symbol})**\n"
            reply_text += f"   - 最新價格：${current_price:.2f}\n" if isinstance(current_price, (int, float)) else f"   - 最新價格：{current_price}\n"
            reply_text += f"   - 24小時成交量：{volume_mil:.1f} 百萬股\n"
            reply_text += f"   - 股價變動：{price_change:.1f}%\n"
            reply_text += f"   - 分析：{analysis}\n\n"
        
        return reply_text.strip()
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Finnhub API 呼叫錯誤: {e}", exc_info=True)
        return "抱歉，目前無法從 Finnhub 取得熱門成交量資訊。請確認你的 API 金鑰是否正確，或 Finnhub 服務是否正常。"
    except Exception as e:
        logging.error(f"獲取熱門成交量排名時發生錯誤: {e}", exc_info=True)
        return "抱歉，獲取資料時發生未知錯誤。"
