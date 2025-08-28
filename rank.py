# rank.py (新版 - 使用 yahoo_fin)
import logging
from yahoo_fin import stock_info as si
import pandas as pd

def get_top_gainers() -> str:
    """
    使用 yahoo_fin 獲取當日漲幅最大的股票排名 (免費)。
    """
    try:
        # get_day_gainers() 會回傳一個 pandas DataFrame
        gainers_df = si.get_day_gainers()
        
        # 檢查 DataFrame 是否為空
        if gainers_df.empty:
            return "抱歉，目前無法從 Yahoo Finance 取得漲幅排名資料。"

        # 篩選掉股價低於 $2 且成交量小於 500k 的股票，讓排名更有參考價值
        gainers_df = gainers_df[gainers_df['Price (Intraday)'] > 2]
        gainers_df = gainers_df[gainers_df['Volume'] > 500000]

        # 取前 5 名
        top_5_gainers = gainers_df.head(5)

        reply_text = "🚀 **熱門漲幅排名 (via Yahoo)** 🚀\n\n"
        for index, row in top_5_gainers.iterrows():
            symbol = row.get('Symbol', 'N/A')
            price = row.get('Price (Intraday)', 0)
            change_percent = row.get('% Change', 0)
            
            reply_text += f"▪️ **{symbol}**\n"
            reply_text += f"   - 價格：${price:.2f}\n"
            reply_text += f"   - 漲幅：+{change_percent:.2f}%\n\n"
            
        return reply_text.strip()

    except Exception as e:
        logging.error(f"使用 yahoo_fin 獲取漲幅排名時發生錯誤: {e}", exc_info=True)
        return "抱歉，獲取漲幅排名資料時發生未知錯誤。"