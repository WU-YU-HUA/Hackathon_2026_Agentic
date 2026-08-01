FROM public.ecr.aws/lambda/python:3.11

# 1. 先升級 pip，確保能順利下載 pandas/numpy/ta 的預編譯 Wheel 包
RUN pip install --upgrade pip

# 2. 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 複製主要程式碼至 Lambda Task 根目錄
COPY getData.py ${LAMBDA_TASK_ROOT}

# 4. 設定 Lambda Handler 進入點
CMD [ "getData.handler" ]