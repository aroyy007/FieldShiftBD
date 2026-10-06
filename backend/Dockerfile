# Use the exact Python version the team agreed on.
FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-ml.txt

# The model checkpoint is a local, ignored artifact. Provide it in backend/model
# (or mount it and set DISEASE_MODEL_WEIGHTS_PATH) before building/running.
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
