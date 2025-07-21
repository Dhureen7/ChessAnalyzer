FROM python:3.11-slim

# Set environment and working directory
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code and Stockfish
COPY ./app ./app
COPY ./stockfish/stockfish ./stockfish/stockfish

# Make Stockfish binary executable
RUN chmod +x ./stockfish/stockfish

# Expose port and start app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
