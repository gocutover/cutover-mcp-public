FROM python:3.13.4-slim

# Install uv (dependency manager)
RUN pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install dependencies using uv
RUN uv sync

# Expose the port the server runs on
EXPOSE 8000

# Command to run the server
CMD ["uv", "run", "python", "src/cutover_mcp/server.py"]
