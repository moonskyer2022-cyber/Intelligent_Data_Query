FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=demo DEMO_MODE=true

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY frontend ./frontend
COPY scripts ./scripts
COPY run.py ./run.py

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["python", "run.py", "--server"]
