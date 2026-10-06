# Use the exact Python version the team agreed on
FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies first (Docker caches this layer separately for faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Uvicorn will run on
EXPOSE 8000

# Start the FastAPI server with hot-reload enabled
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
