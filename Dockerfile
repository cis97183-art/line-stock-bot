# 使用一個輕量的 Python 3.10 官方映像檔作為基礎
FROM python:3.10-slim

# 設定程式碼將會運行的工作目錄
WORKDIR /app

# 將需求清單檔案複製到工作目錄中
COPY requirements.txt .

# <<<=== 修改這裡，強制清除快取並重新安裝 ===>>>
# 我們加入了 "pip install --upgrade pip &&" 這個新指令
# 任何對 RUN 指令的修改都會讓 Cloud Build 快取失效，強制重新執行
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# <<<========================================>>>

# 將專案中的所有檔案複製到工作目錄中
COPY . .

# 定義容器運行的 Port，Cloud Run 預設使用 8080
ENV PORT 8080

# 啟動應用程式的指令
CMD exec gunicorn --bind :$PORT --workers 1 main:app