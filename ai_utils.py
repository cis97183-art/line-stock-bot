# ai_utils.py
import os
import google.generativeai as genai

# 從環境變數讀取 API Key 並進行設定
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini_for_news(headline, summary):
    """
    使用一個精心設計的 prompt 來同時完成翻譯和摘要。
    在偵錯模式下，會直接回傳詳細的 API 錯誤訊息。
    """
    if not GEMINI_API_KEY:
        return "錯誤：尚未設定 Gemini API Key。"

    # 初始化 Gemini Pro 模型
    generation_config = {
      "temperature": 0.2,
      "top_p": 1,
      "top_k": 1,
      "max_output_tokens": 2048,
    }
    model = genai.GenerativeModel(model_name="gemini-pro",
                                  generation_config=generation_config)

    # 提示工程 (Prompt Engineering)
    prompt = f"""
    你現在是一位專業的美股新聞分析師，在為一個股市 Line Bot 提供服務。
    請根據以下提供的英文新聞標題和內容，完成兩項任務：
    1. 將標題翻譯成專業且吸引人的繁體中文。
    2. 用條列式的方式，以繁體中文總結新聞內容的 2-3 個重點。

    請嚴格按照以下格式回覆，不要包含任何額外的前言或結語：

    【標題】
    [此處填寫翻譯後的中文標題]

    【AI 摘要】
    - [此處填寫第一個重點]
    - [此處填寫第二個重點]
    - [此處填寫第三個重點，如果有的話]

    ---
    英文新聞標題: "{headline}"
    英文新聞內容: "{summary}"
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # <<<=== 偵錯模式：直接回傳詳細錯誤 ===>>>
        # 建立一個包含詳細錯誤的訊息
        error_message = f"Gemini API 呼叫失敗，詳細錯誤：\n\n{str(e)}"
        
        # 我們仍然在後端印出日誌，以防萬一
        print(error_message) 
        
        # 直接將詳細的錯誤訊息回傳給使用者（也就是我們自己）
        return error_message