# Cutover MCP (Model Context Protocol) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP server for interacting with the Cutover API, powered by FastMCP.

## Contents

- [Installation](#installation)
- [Setup](#setup)
- [Environment Configuration](#environment-configuration)
  - [Environment Variables Reference](#environment-variables-reference)
  - [Generating an API Token](#generating-an-api-token)
- [Security & Responsible Use](#security--responsible-use)
- [Project Structure](#project-structure)
- [Notes](#notes)
- [Client Setup](#client-setup)
- [Docker Usage](#docker-usage)
- [Example: Using Docker in MCP Server Configuration](#example-using-docker-in-mcp-server-configuration)
- [FAQs](#faqs)
- [Troubleshooting](#troubleshooting)

## Installation

To set up the project, ensure you have the required dependencies installed. For macOS users, you can install `uv` using Homebrew:

```bash
brew install uv
```

This project requires Python 3.13+ — `uv` installs and manages the right interpreter automatically, so you don't need to install Python separately.

## Setup

1. Copy `.env.example` to `.env` and fill in your Cutover API credentials — see [Environment Configuration](#environment-configuration) below.
2. Install dependencies with uv:
   ```sh
   uv sync
   ```
3. Run the server using:
   ```sh
   uv run python src/cutover_mcp/server.py
   ```
4. Run tests:
   ```sh
   uv run pytest
   ```

## Environment Configuration

### Environment Variables Reference

| Variable            | Required                | Notes                                                          |
| ------------------- | ----------------------- | -------------------------------------------------------------- |
| `CUTOVER_BASE_URL`  | Yes                     | Your Cutover instance's API host.                              |
| `CUTOVER_API_TOKEN` | Yes                     | See [Generating an API Token](#generating-an-api-token) below. |
| `CUTOVER_CORE_URL`  | Yes, for most instances | Your Cutover instance's URL.                                   |

### Generating an API Token

There are two ways to generate a token:

- **Access Management** — an admin generates a token for a specific user (useful if you want the token to act as someone other than yourself, e.g. a global admin, or you don't have self-service access).
- **My Details → User App Tokens** — generate your own token directly, self-service.

## Security & Responsible Use

The MCP server adds no security model of its own — it authenticates to the Cutover API as a single **user app token** over HTTPS and inherits exactly that user's permissions. Scope the token correctly and use the write tools deliberately:

- **Least privilege.** Use a dedicated [non-interactive user](#generating-an-api-token) with the **Developer** role plus only the scoped roles the use case needs (e.g. Workspace manager on one workspace) — not a personal admin token. Rotate the token periodically and revoke it in Cutover when the use case ends.
- **Read-only vs read-write.** This server ships write tools (`create_runbook`, `manage_runbook`, `delete_task`, `start_task`, …) and does not enforce read-only itself. For query-only use cases, omit roles that grant create/update/delete/manage — least privilege is configured in Cutover, not the client.
- **Approve writes.** Keep human approval enabled for mutating or consequential actions — models can act on unexpected content returned by tools, so approval is the real safeguard.
- **Verify critical output.** A tool call returns real data, but the model's summary of it can still be wrong (or answer with no tool call at all). For compliance- or audit-critical output, verify against Cutover as the system of record.
- **Protect the token.** It lives in env config (`.env*` is git-ignored and excluded from Docker images). If a token is compromised, revoke it immediately in Cutover's Access Management — the MCP server holds no independent session, so revoking the token fully cuts off access, and a scoped role confines any impact to that use case.

## Project Structure

- `src/cutover_mcp/` - Main package
- `clients/` - API client
- `resources/` - Resource definitions (MCP endpoints)
- `tools/` - Tool logic
- `server.py` - FastMCP server entrypoint
- `tests/` - Tests

## Notes

- Dependency and environment management is handled by [uv](https://github.com/astral-sh/uv) and [hatchling](https://hatch.pypa.io/).

## Client Setup

### Run in VS Code GitHub Copilot

If you want to use VS Code with GitHub Copilot to call out to this MCP server, you can use `mcp.json.example`.

1. Copy `mcp.json.example` to `.vscode/mcp.json` (create the `.vscode/` directory if not already present)
2. Change the `Users/YOUR-USER-NAME/...` example path to point at your working directory instead (the example uses a macOS-style path — adjust the format for Windows if needed)
3. Restart VS Code for the changes to take effect. In the Copilot Chat box, click the **Configure tools** icon and expand `cutover-mcp` to see its full list of tools. MCP tools only run in Agent mode — switch the mode dropdown from Ask to Agent if nothing happens.

### Run in Claude Desktop

If you'd rather use Claude Desktop instead of an IDE, you can set that up:

1. [Download and install Claude Desktop](https://www.anthropic.com/claude/desktop).
2. Copy `claude_desktop_config.json.example` to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS path shown; on Windows, use `%APPDATA%\Claude\claude_desktop_config.json`).
3. Update the `command` and `args` paths in that file to point at your repo's `.venv/bin/python` and `src/cutover_mcp/server.py`.
4. Restart Claude Desktop. Click the **+** button at the bottom of the chat box, then **Connectors** — `cutover-mcp` should be listed there along with its tools. If it isn't, check Settings → Developer for its connection status and logs.

This will allow Claude Desktop to connect to your MCP server.

## Docker Usage

Docker is optional — the server runs fine without it (see [Setup](#setup)). Use this if you want a self-contained way to run it instead of managing a venv.

From the repository root, build the image:

```sh
docker build -t cutover-mcp .
```

`.env` is excluded from the build via `.dockerignore`, so the image isn't tied to any environment or credential — never bake `.env` into an image you build, push, or share.

Pass your `.env` file in at run time instead, with `--env-file`:

```sh
docker run -i --rm --env-file .env cutover-mcp
```

## Example: Using Docker in MCP Server Configuration

You can configure your MCP server to use the Docker container instead of the venv. The root key differs by client: VS Code (`mcp.json`) uses `servers`; Claude Desktop (`claude_desktop_config.json`) uses `mcpServers`.

VS Code (`.vscode/mcp.json`):

```json
{
  "servers": {
    "cutover-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/path/to/your/repo/.env",
        "cutover-mcp"
      ]
    }
  }
}
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cutover-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/path/to/your/repo/.env",
        "cutover-mcp"
      ]
    }
  }
}
```

To use Docker in the example configuration files (`mcp.json.example` and `claude_desktop_config.json.example`), replace the existing commands with the Docker-based commands shown in the "Docker Usage" section above.

## FAQs

### How can I start the MCP server via Visual Studio Code?

Open up the `.vscode/mcp.json` file. Hover above the name of the server i.e. 'cutover-mcp'. You should have the option to start the server.

## Troubleshooting

### Why is VS Code not giving me the ability to start the MCP server?

Ensure you aren't running the server independently in another terminal. Close and re-open VS Code, and if that doesn't work, restart your machine.

Alternatively, you can use the following approach to start the server:

`View -> Command Palette -> MCP: List Servers -> your mcp server -> start/restart/stop server.`
