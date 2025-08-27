import os
import psycopg2
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從環境變數中讀取設定
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_favorites(user_id):
    """
    從資料庫中取得使用者的最愛股票清單。
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("SELECT stock_symbol FROM favorites WHERE user_id = %s", (user_id,))
        favorites = [row[0] for row in cursor.fetchall()]
        conn.close()
        return favorites
    except Exception as e:
        logging.error(f"取得最愛清單時發生錯誤 for user {user_id}: {e}", exc_info=True)
        return []

def add_to_favorites(user_id, stock_symbol):
    """
    將股票代號新增到使用者的最愛清單。
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM favorites WHERE user_id = %s AND stock_symbol = %s", (user_id, stock_symbol))
        exists = cursor.fetchone()
        if exists:
            conn.close()
            return f"『{stock_symbol}』已經在您的最愛清單中了喔！"
        else:
            cursor.execute("INSERT INTO favorites (user_id, stock_symbol) VALUES (%s, %s)", (user_id, stock_symbol))
            conn.commit()
            conn.close()
            return f"已將『{stock_symbol}』新增到您的最愛清單中！❤️"
    except Exception as e:
        logging.error(f"新增最愛時發生錯誤 for user {user_id}, symbol {stock_symbol}: {e}", exc_info=True)
        return "新增最愛時發生錯誤。"

def remove_from_favorites(user_id, stock_symbol):
    """
    從使用者的最愛清單中移除股票。
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        # 執行 DELETE 語法
        cursor.execute("DELETE FROM favorites WHERE user_id = %s AND stock_symbol = %s", (user_id, stock_symbol))
        conn.commit()
        # 檢查是否有資料被刪除
        if cursor.rowcount > 0:
            conn.close()
            return f"已將『{stock_symbol}』從您的最愛中移除！🗑️"
        else:
            conn.close()
            return f"『{stock_symbol}』不在您的最愛清單中喔！"
    except Exception as e:
        # 捕捉並記錄任何例外
        logging.error(f"移除最愛時發生錯誤 for user {user_id}, symbol {stock_symbol}: {e}", exc_info=True)
        return "移除最愛時發生錯誤。"
