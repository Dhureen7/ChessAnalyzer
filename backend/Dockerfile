# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app and Stockfish binary
COPY ./app ./app
COPY ./stockfish/stockfish ./stockfish/stockfish

# Give execute permissions to Stockfish binary
RUN chmod +x ./stockfish/stockfish

# Set environment and expose port
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
