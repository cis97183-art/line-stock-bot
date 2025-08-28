# rank.py
import yfinance as yf
import logging
import requests
from typing import List, Dict

# 模擬 AI 摘要模組
def get_ai_summary(stock_symbol: str) -> str:
    """
    模擬 AI 分析，根據股票代碼回傳漲幅原因。
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

def get_top_gainers(api_url: str, api_key: str) -> str:
    """
    獲取漲幅最大的股票排名，並包含簡短分析。
    """
    if not api_key:
        return "錯誤：尚未設定 Finnhub API Key。"

    try:
        response = requests.get(
            f"{api_url}/stock/market-movers?region=US&token={api_key}"
        )
        response.raise_for_status()
        
        finnhub_data = response.json()
        
        if 'mostGainer' not in finnhub_data or not finnhub_data['mostGainer']:
            return "Finnhub API 目前沒有漲幅資料，請稍後再試。"
        
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
            
            stock_info = yf.Ticker(symbol)
            info = stock_info.info
            company_name = info.get('longName', '無公司名稱')
            
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