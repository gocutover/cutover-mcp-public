# AGENTS.md

Guidance for AI coding agents working in this repository. For human-oriented detail (FAQs, troubleshooting, MCP client configuration), see `README.md`.

## What this is

An MCP server for interacting with the Cutover API, powered by FastMCP. Source lives in `src/cutover_mcp/`.

## Prerequisites

- [`uv`](https://github.com/astral-sh/uv) for dependency and environment management (`brew install uv` on macOS).
- Python 3.13+ — `uv` installs and manages this automatically, no separate install needed.

## Setup

End users don't clone this repository: each release is published to PyPI and MCP clients run it as `uvx cutover-mcp` with credentials in the client's `env` block (see `mcp.json.example` / `claude_desktop_config.json.example`). The steps below are for working on the server itself.

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

Over HTTP (`MCP_TRANSPORT` other than `stdio`, or any call made while serving an HTTP request) there are rules that new code must keep:

- Every request goes through `APIClient.request`. It pins the host to the client's API host and re-checks it against the `TRUSTED_API_HOSTS` allowlist in `src/cutover_mcp/security/host_policy.py`; a request sent any other way skips both.
- `/mcp` requires an `Authorization: Bearer` header (`src/cutover_mcp/security/bearer.py`, 401 otherwise). The token comes only from that header: no `CUTOVER_API_TOKEN` fallback and no elicitation.
- Never log the token, request headers or response bodies.
- The server is stateless (`stateless_http` in `server.py`): no session survives a request, so `ctx.get_state`/`set_state`, `ctx.elicit` and other server-to-client requests cannot be relied on.
- Tests run as stdio unless they set `MCP_TRANSPORT` (`tests/conftest.py`).

`MCP_READ_ONLY=true` (optional) exposes only the tools annotated read-only (`src/cutover_mcp/read_only.py`). It is read once, when `cutover_mcp.app` builds the server.

If you don't have real credentials available, ask the user for values rather than inventing them — the first tool call raises a clear `ValueError` if `CUTOVER_API_TOKEN` is missing, or if neither `CUTOVER_CORE_URL` nor `CUTOVER_BASE_URL` is set.

## Running the server

```sh
uv run cutover-mcp
```

This is the `cutover-mcp` console script (`cutover_mcp.server:main`, declared in `pyproject.toml`) that `uvx cutover-mcp` and the Docker image run; `uv run python src/cutover_mcp/server.py` is equivalent.

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
- `server.json` — MCP Registry entry (`io.github.gocutover/cutover-mcp`); `.github/workflows/publish.yml` stamps the release version in and publishes it after the PyPI upload
- `tests/` — Tests

## Conventions

- Formatting/linting via `ruff` (see `pyproject.toml`); a pre-commit config (`.pre-commit-config.yaml`) enforces this.
- If a change adds, removes, renames, or changes the parameters/behavior of a `@mcp.tool()` in `src/cutover_mcp/tools/`, update the **Capabilities** section in both `README.md` and `README-PUBLIC.md` in the same PR — the group table, the tool's own `<details>` entry, and the tool/group counts in the section's opening sentence. Keep the two files in sync with each other (see [Project Structure](README.md#project-structure) for how they relate).
- Every `@mcp.tool()` passes `annotations=` from `src/cutover_mcp/tools/annotations.py`: `READ_ONLY` for a tool that only reads, otherwise `writes(destructive=..., idempotent=...)`. `destructive=True` only when the change cannot be undone (deleting, archiving, replacing a data source's file or records, moving a runbook or task to another state); creating and updating are not destructive. Pass `open_world=True` if the tool reaches beyond the Cutover instance: it runs integrations, sends communications or fetches a URL. `tests/unit/test_tool_annotations.py` fails on a tool without annotations. List the tool in the **Tool annotations** table of both READMEs and update its counts.
