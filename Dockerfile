FROM public.ecr.aws/docker/library/python:3.13.4-slim

# Version metadata, passed by build.yml. VERSION is the git tag being built: hatch-vcs cannot
# read git inside the image because .git is dockerignored, so the tag is handed in explicitly
# (empty -> the fallback-version in pyproject.toml). GIT_SHA is reported by /health.
ARG VERSION
ARG GIT_SHA

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
RUN SETUPTOOLS_SCM_PRETEND_VERSION="${VERSION}" uv sync --frozen

ENV CUTOVER_MCP_GIT_SHA=${GIT_SHA}

# Expose the port the server runs on
EXPOSE 8000

# Command to run the server
CMD ["/app/.venv/bin/python", "src/cutover_mcp/server.py"]
