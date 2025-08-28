# stock_lookup.py

# 這是一個專門用來存放和查詢股票代號的模組

stock_dict = {
    "Apple": "AAPL", "蘋果": "AAPL",
    "Microsoft": "MSFT", "微軟": "MSFT",
    "Amazon": "AMZN", "亞馬遜": "AMZN",
    "Alphabet": "GOOGL", "谷歌": "GOOGL",
    "Meta": "META", "臉書": "META",
    "Tesla": "TSLA", "特斯拉": "TSLA",
    "NVIDIA": "NVDA", "輝達": "NVDA",
    "Netflix": "NFLX", "網飛": "NFLX",
    "Intel": "INTC", "英特爾": "INTC",
    "AMD": "AMD", "超微": "AMD",
    "Qualcomm": "QCOM", "高通": "QCOM",
    "Adobe": "ADBE", "奧多比": "ADBE",
    "Oracle": "ORCL", "甲骨文": "ORCL",
    "Cisco": "CSCO", "思科": "CSCO",
    "IBM": "IBM", "國際商業機器": "IBM",
    "PayPal": "PYPL", "貝寶": "PYPL",
    "Visa": "V", "維薩": "V",
    "Mastercard": "MA", "萬事達": "MA",
    "JP Morgan": "JPM", "摩根大通": "JPM",
    "Goldman Sachs": "GS", "高盛": "GS",
    "Bank of America": "BAC", "美國銀行": "BAC",
    "Coca-Cola": "KO", "可口可樂": "KO",
    "PepsiCo": "PEP", "百事可樂": "PEP"
}

def get_stock_code(name: str):
    """
    根據公司名稱（英文或中文），回傳對應的股票代號。
    忽略大小寫進行比對。
    如果找不到，則回傳 None。
    """
    # 遍歷字典中的每一個鍵 (公司名稱)
    for key in stock_dict:
        # 將輸入的名稱和字典中的鍵都轉成小寫來比對
        if key.lower() == name.lower():
            # 如果找到符合的，回傳對應的股票代號
            return stock_dict[key]
    
    # 如果整個字典都找完了還是沒有，回傳 None
    return None