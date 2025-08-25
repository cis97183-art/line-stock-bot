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
    for key in stock_dict:
        if key.lower() == name.lower():
            return stock_dict[key]
    return None
