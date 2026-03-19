FROM python:3.12-slim

WORKDIR /app

# Install curl and dos2unix
RUN apt-get update && apt-get install -y curl dos2unix

# Install nodejs
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# Install uv
RUN pip install uv

# Configure uv to use Aliyun mirror
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# Install dependencies
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy project files
COPY . .

# Set script execution permissions and convert line endings
RUN dos2unix run.sh && chmod +x run.sh

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start command
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 