import yfinance as yf
import logging
import requests
import datetime
from typing import List, Dict

# 假設的 Finnhub API 設定
# ⚠️ 請將 YOUR_FINNHUB_API_KEY 替換成你自己的 API 金鑰
FINNHUB_API_KEY = "d2f97fpr01qj3egrql4gd2f97fpr01qj3egrql50"
FINNHUB_API_URL = "https://finnhub.io/api/v1"

# 假設的 AI 摘要模組
# 這是為了模擬 AI 分析漲幅原因的功能
def get_ai_summary(stock_symbol: str) -> str:
    """
    模擬 AI 分析，根據股票代碼回傳漲幅原因。
    在真實世界中，你會呼叫一個 AI 模型，例如我們前面討論的 ai_utils.py。
    """
    reasons = {
        "NVDA": "NVIDIA (NVDA) 股價大漲，主因是最新 AI 晶片發表，市場看好其未來營收。",
        "TSLA": "Tesla (TSLA) 近 24 小時漲幅最大，主因是宣布其新電池技術取得重大突破。",
        "MSFT": "Microsoft (MSFT) 股價上漲，主因是雲端服務 Azure 營收超出預期。",
        "GOOGL": "Google (GOOGL) 股價上揚，主因是其母公司 Alphabet 宣布新一輪股票回購計劃。",
        "AAPL": "Apple (AAPL) 漲幅顯著，主因是新產品發布會引發市場熱烈討論。",
        "AMD": "AMD (AMD) 股價上漲，主因是新一代處理器銷售表現強勁。",
    }
    return reasons.get(stock_symbol, "漲幅原因尚不明確。")

def get_top_gainers() -> str:
    """
    獲取漲幅最大的股票排名，並包含簡短分析。
    """
    try:
        # 呼叫 Finnhub Market Movers API
        # 這部分程式碼與 stock_volume.py 相似
        response = requests.get(
            f"{FINNHUB_API_URL}/stock/market-movers?region=US&token={FINNHUB_API_KEY}"
        )
        response.raise_for_status()
        
        finnhub_data = response.json()
        
        if 'mostGainer' not in finnhub_data or not finnhub_data['mostGainer']:
            return "Finnhub API 目前沒有漲幅資料，請稍後再試。"
        
        # 排序並取前10名漲幅最大的股票
        top_gainers_data = sorted(
            finnhub_data['mostGainer'], 
            key=lambda x: x.get('changePercent', 0), 
            reverse=True
        )[:10]
        
        reply_text = "🚀 **熱門漲幅排名** 🚀\n\n"
        for stock in top_gainers_data:
            symbol = stock.get('symbol', 'N/A')
            if symbol == 'N/A':
                continue
            
            price_change = stock.get('changePercent', 0)
            
            # 使用 yfinance 取得公司名稱
            stock_info = yf.Ticker(symbol)
            info = stock_info.info
            company_name = info.get('longName', '無公司名稱')
            
            # 模擬 AI 摘要
            ai_summary = get_ai_summary(symbol)
            
            reply_text += f"▪️ **{company_name} ({symbol})**\n"
            reply_text += f"   - 漲幅：{price_change:.2f}%\n"
            reply_text += f"   - 原因：{ai_summary}\n\n"
        
        return reply_text.strip()
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Finnhub API 呼叫錯誤: {e}", exc_info=True)
        return "抱歉，目前無法從 Finnhub 取得漲幅資料。請確認你的 API 金鑰是否正確。"
    except Exception as e:
        logging.error(f"獲取漲幅排名時發生錯誤: {e}", exc_info=True)
        return "抱歉，獲取資料時發生未知錯誤。"
