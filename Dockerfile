FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE $PORT
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker "run:get_application()" --bind 0.0.0.0:$PORT