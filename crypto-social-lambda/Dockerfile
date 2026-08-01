FROM public.ecr.aws/lambda/python:3.11

# 1. 先升級 pip
RUN pip install --upgrade pip

# 2. 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 複製主要程式碼至 Lambda Task 根目錄
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# 4. 設定 Lambda Handler 進入點 (指向 lambda_function.py 裡的 handler 函式)
CMD [ "lambda_function.handler" ]