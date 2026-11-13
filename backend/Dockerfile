# Use the exact Python version the team agreed on.
FROM python:3.12.3-slim

WORKDIR /app

# Package index requests can be slow or briefly unavailable during image builds.
ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-ml.txt

# The checkpoint is versioned with Git LFS. Make sure `git lfs pull` has
# materialized it before building a deployable image.
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
