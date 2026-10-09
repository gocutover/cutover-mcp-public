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

- `CUTOVER_CORE_URL` (required for hosted instances) — the instance's own URL, e.g. `https://your-instance.cutover.com`. Sent as the `Core-Url` request header so the API routes to that instance. Leave blank only for local public-api, or when `CUTOVER_BASE_URL` already identifies a single instance.
- `CUTOVER_API_TOKEN` (required) — an API token for that instance. On hosted instances, generate via Access Management (an admin generates a token for a specific user) or My Details → User App Tokens (self-service).
- `CUTOVER_BASE_URL` (optional) — the Cutover API host. Derived from `CUTOVER_CORE_URL` when unset (`https://api.cutover.net` for production instances; other environments get `https://api.<environment domain>`). Only Cutover-hosted instance URLs are derived; anything else (e.g. a local `core` on `localhost`) raises a `ValueError` asking for `CUTOVER_BASE_URL`. Set it for a single-tenant instance with its own API host, or for local public-api (`http://localhost:9292`).

If you don't have real credentials available, ask the user for values rather than inventing them — the first tool call raises a clear `ValueError` if `CUTOVER_API_TOKEN` is missing, or if neither `CUTOVER_CORE_URL` nor `CUTOVER_BASE_URL` is set.

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
- If a change adds, removes, renames, or changes the parameters/behavior of a `@mcp.tool()` in `src/cutover_mcp/tools/`, update the **Capabilities** section in both `README.md` and `README-PUBLIC.md` in the same PR — the group table, the tool's own `<details>` entry, and the tool/group counts in the section's opening sentence. Keep the two files in sync with each other (see [Project Structure](README.md#project-structure) for how they relate).
