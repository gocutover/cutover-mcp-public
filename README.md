# Cutover MCP (Model Context Protocol)

An MCP server for interacting with the Cutover API, powered by FastMCP.

## Installation

To set up the project, ensure you have the required dependencies installed. For macOS users, you can install `uv` using Homebrew:

```bash
brew install uv
```

## Setup

1. Copy `.env.example` to `.env` and fill in your Cutover API credentials.
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

## Project Structure

- `src/cutover_mcp/` - Main package
- `clients/` - API client
- `resources/` - Resource definitions (MCP endpoints)
- `tools/` - Tool logic
- `server.py` - FastMCP server entrypoint
- `tests/` - Tests

## Notes
- Dependency and environment management is handled by [uv](https://github.com/astral-sh/uv) and [hatchling](https://hatch.pypa.io/).

## MCP Server Configuration Example

### Run in VSCode Github Copilot

If you want to use VS Code with Github Copilot as a way to use to call out to this MCP server you can use `mcp.json.example`.

1. Copy `mcp.json.example` to `.vscode/mcp.json` (create the `.vscode/` directory if not already present)
2. Change the `Users/YOUR-USER-NAME/...` example path to be pointing at your working directory instead (this is for MacOSX)
3. Restart VS Code for the changes to take effect, you should be able to see the MCP server and all the defined tools from the little hammer icon inside the Github Copilot chat.

### Run in Claude Desktop

If you prefer to use a standalone LLM, you can set up Claude Desktop:

1. [Download and install Claude Desktop](https://www.anthropic.com/claude/desktop).
2. Copy `claude_desktop_config.json.example` to `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Update the configuration file as needed for your environment.
4. Restart Claude Desktop, you should now see `cutover-mcp` when clicking on the settings cog in the chat window.

This will allow Claude Desktop to connect to your MCP server.

## Docker Usage

To build and run the Docker container, specify the repository root as the build context. For example:

```sh
docker build -t cutover-mcp /path/to/your/repo
```

This ensures all necessary files are included in the image.

## Example: Using Docker in MCP Server Configuration

You can configure your MCP server to use the Docker container as follows:

```json
{
  "mcpServers": {
    "cutover-mcp-2": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "cutover-mcp"
      ]
    }
  }
}
```

To use Docker in the example configuration files (`mcp.json.example` and `claude_desktop_config.json.example`), replace the existing commands with the Docker-based commands shown in the "Docker Usage" section above.