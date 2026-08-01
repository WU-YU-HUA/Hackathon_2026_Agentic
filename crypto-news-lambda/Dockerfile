# 使用 AWS Lambda 官方 Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# 複製 requirements 並安裝依賴
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY news.py ${LAMBDA_TASK_ROOT}
COPY app.py ${LAMBDA_TASK_ROOT}

# 設定 Lambda handler
CMD [ "app.handler" ]