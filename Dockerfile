FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml uv.lock /app/

# Install dependencies
RUN pip install -e .

# Copy the application code
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run when container starts
ENTRYPOINT ["python", "mcp_server.py"]