FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
COPY weather_app/ ./weather_app/
COPY static/ ./static/

RUN pip install --no-cache-dir -e .

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn weather_app.main:app --host 0.0.0.0 --port ${PORT}"]
