# 使用一個輕量的 Python 3.10 官方映像檔作為基礎
FROM python:3.10-slim

# 設定程式碼將會運行的工作目錄
WORKDIR /app

# 將需求清單檔案複製到工作目錄中
COPY requirements.txt .

# 安裝程式碼所需的所有 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 將專案中的所有檔案複製到工作目錄中
COPY . .

# 定義容器運行的 Port，Cloud Run 預設使用 8080
ENV PORT 8080

# 啟動應用程式的指令
# 我們使用 gunicorn 來啟動 Flask App，這是正式環境的標準做法
CMD exec gunicorn --bind :$PORT --workers 1 main:app