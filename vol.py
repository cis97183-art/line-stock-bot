# vol.py (新版 - 使用 yahoo_fin)
import logging
from yahoo_fin import stock_info as si
import pandas as pd

def get_top_volume_stocks() -> str:
    """
    使用 yahoo_fin 獲取當日成交量最大的股票排名 (免費)。
    """
    try:
        most_active_df = si.get_day_most_active()
        
        if most_active_df.empty:
            return "抱歉，目前無法從 Yahoo Finance 取得熱門成交量資料。"

        top_10_active = most_active_df.head(10)

        reply_text = "📈 **熱門成交量排名 (via Yahoo)** 📈\n\n"
        for index, row in top_10_active.iterrows():
            symbol = row.get('Symbol', 'N/A')
            price = row.get('Price (Intraday)', 0)
            change_percent = row.get('% Change', 0)
            volume = row.get('Volume', 0) / 1000000  # 轉換為百萬股

            emoji = "🔼" if change_percent >= 0 else "🔽"

            reply_text += f"▪️ **{symbol}** {emoji}\n"
            reply_text += f"   - 價格：${price:.2f}\n"
            reply_text += f"   - 漲跌：{change_percent:.2f}%\n"
            reply_text += f"   - 成交量：{volume:.1f} 百萬股\n\n"

        return reply_text.strip()

    except Exception as e:
        logging.error(f"使用 yahoo_fin 獲取熱門成交量時發生錯誤: {e}", exc_info=True)
        return "抱歉，獲取熱門成交量資料時發生未知錯誤。"