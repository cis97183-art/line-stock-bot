# ai_utils.py
from transformers import pipeline
import datetime

# 這些 print 訊息在雲端第一次部署時有助於偵錯，部署成功後可以移除
print(f"[{datetime.datetime.now()}] 1. 開始載入 ai_utils.py 模組...")

# 初始化模型
# --- 使用輕量級的英翻中模型 ---
print(f"[{datetime.datetime.now()}] 2. 準備初始化翻譯模型 (translator)...")
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-zh")
print(f"[{datetime.datetime.now()}] 3. 翻譯模型初始化完成！")


# --- 使用輕量級的摘要模型 (DistilBART) ---
print(f"[{datetime.datetime.now()}] 4. 準備初始化摘要模型 (summarizer)...")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
print(f"[{datetime.datetime.now()}] 5. 摘要模型初始化完成！")


def translate_text(text_to_translate):
    """
    將英文文本翻譯成中文。
    """
    if not text_to_translate:
        return ""
    try:
        translated = translator(text_to_translate)
        return translated[0]['translation_text']
    except Exception as e:
        print(f"翻譯時發生錯誤: {e}")
        return text_to_translate

def summarize_text(text_to_summarize, min_length=20, max_length=100):
    """
    將長文本生成摘要。
    """
    if not text_to_summarize:
        return "無法生成摘要，內容為空。"
    try:
        summary = summarizer(text_to_summarize, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"生成摘要時發生錯誤: {e}")
        return "處理摘要時發生錯誤。"