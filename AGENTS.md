# AGENTS.md

Guidance for AI coding agents working in this repository. For human-oriented detail (FAQs, troubleshooting, MCP client configuration), see `README.md`.

## What this is

An MCP server for interacting with the Cutover API, powered by FastMCP. Source lives in `src/cutover_mcp/`.

## Prerequisites

- [`uv`](https://github.com/astral-sh/uv) for dependency and environment management (`brew install uv` on macOS).
- Python 3.13+ — `uv` installs and manages this automatically, no separate install needed.

## Setup

1. Copy `.env.example` to `.env` and fill in the required values (see "Environment variables" below).
2. Install dependencies:
   ```sh
   uv sync
   ```

## Environment variables

Three variables, all read from `.env` at runtime (see `src/cutover_mcp/clients/api.py`):

- `CUTOVER_BASE_URL` (required) — the Cutover API host to call.
- `CUTOVER_API_TOKEN` (required) — an API token for that host. On hosted instances, generate via Access Management (an admin generates a token for a specific user) or My Details → User App Tokens (self-service).
- `CUTOVER_CORE_URL` (required for most hosted instances) — set to the instance's own URL. Sent as the `Core-Url` request header, telling `CUTOVER_BASE_URL` which instance to route to. Leave blank only if `CUTOVER_BASE_URL` already identifies a single instance unambiguously.

If you don't have real credentials available, ask the user for values rather than inventing them — the server cannot start without a valid `CUTOVER_BASE_URL`/`CUTOVER_API_TOKEN` pair, and it will raise a clear `ValueError` if either is missing.

## Running the server

```sh
uv run python src/cutover_mcp/server.py
```

## Running via Docker

Optional — prefer "Running the server" above unless the user specifically asks for Docker.

```sh
docker build -t cutover-mcp .
docker run -i --rm --env-file .env cutover-mcp
```

`.env` is excluded from the build context via `.dockerignore` — always pass credentials at run time with `--env-file`, never bake them into the image.

## Tests

```sh
uv run pytest
```

## Project structure

- `src/cutover_mcp/clients/` — API client
- `src/cutover_mcp/resources/` — Resource definitions (MCP endpoints)
- `src/cutover_mcp/tools/` — Tool logic
- `src/cutover_mcp/server.py` — FastMCP server entrypoint
- `tests/` — Tests

## Conventions

- Formatting/linting via `ruff` (see `pyproject.toml`); a pre-commit config (`.pre-commit-config.yaml`) enforces this.
