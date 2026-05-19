FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data logs \
    && addgroup --system botuser \
    && adduser --system --ingroup botuser botuser \
    && chown -R botuser:botuser /app

USER botuser

CMD ["python", "run.py"]
