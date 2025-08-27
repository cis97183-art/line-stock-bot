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
    :param headline: 英文新聞標題
    :param summary: 英文新聞內容
    :return: 由 Gemini 生成的格式化中文回應
    """
    if not GEMINI_API_KEY:
        return "錯誤：尚未設定 Gemini API Key。"

    # 初始化 Gemini Pro 模型
    # 將模型生成設定為更穩定、較少創意的模式
    generation_config = {
      "temperature": 0.2,
      "top_p": 1,
      "top_k": 1,
      "max_output_tokens": 2048,
    }
    model = genai.GenerativeModel(model_name="gemini-pro",
                                  generation_config=generation_config)

    # --- 這就是「提示工程 (Prompt Engineering)」---
    # 我們在一個 prompt 中，給予 AI 清晰的角色、任務和格式指令
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
        print(f"呼叫 Gemini API 時發生錯誤: {e}")
        return "呼叫 AI 時發生錯誤，請稍後再試。"