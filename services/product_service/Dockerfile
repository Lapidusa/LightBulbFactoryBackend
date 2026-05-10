FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml README.md ./
COPY shared ./shared
COPY services ./services

RUN poetry install --only main --no-interaction --no-root

EXPOSE 8001

CMD ["uvicorn", "services.product_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

