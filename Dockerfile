FROM public.ecr.aws/docker/library/python:3.13.4-slim

# Install uv (dependency manager)
RUN pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

# Install dependencies first so this layer only invalidates on lockfile changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy the project files
COPY . /app

# Install the project itself
RUN uv sync --frozen

# Expose the port the server runs on
EXPOSE 8000

# Command to run the server
CMD ["/app/.venv/bin/python", "src/cutover_mcp/server.py"]
