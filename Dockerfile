# ---- 基礎映像 ----
FROM python:3.14-slim

# ---- 環境變數 ----
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Streamlit 相關設定 (設定 ENV 後，啟動指令就不需要重複帶參數)
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ---- 系統相依套件 ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- 建立非 root 使用者 (提前建立) ----
RUN useradd -m -u 1000 appuser

# ---- 工作目錄 ----
WORKDIR /app

# ---- 安裝 Python 相依套件 ----
# 利用 --chown 直接指定權限，避免產生額外 Layer
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---- 複製專案程式碼 ----
COPY --chown=appuser:appuser . .

# ---- 切換使用者 ----
USER appuser

# ---- 開放連接埠 ----
EXPOSE 8501

# ---- 健康檢查 ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ---- 啟動指令 ----
CMD ["streamlit", "run", "app.py"]