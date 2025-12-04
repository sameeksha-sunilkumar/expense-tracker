FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
VOLUME ["/data"]
ENV DB_URL="sqlite:////data/expenses.db"
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "app.py"]
CMD ["init-db"]
