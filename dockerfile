FROM python:3.12-slim
WORKDIR /{MICROSERVICE_NAME}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x ./uvicorn.sh
ENV PYTHONPATH=/{MICROSERVICE_NAME}/app
CMD ["/bin/bash", "./uvicorn.sh"]
