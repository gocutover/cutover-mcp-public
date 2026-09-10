# Cutover MCP (Model Context Protocol) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP server for interacting with the Cutover API, powered by FastMCP.

## Contents

- [Capabilities](#capabilities)
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

## Capabilities

The server exposes 33 tools over MCP, grouped into 13 categories.

### Tool Groups

| Group | Description |
| --- | --- |
| `runbooks` | Create, read, update, and control the lifecycle of runbooks and templates |
| `runbook_types` | Look up runbook types |
| `tasks` | Read, add, update, and progress (start/complete/skip/delete) tasks within a runbook |
| `task_types` | Look up task types |
| `streams` | Create, read, update, and delete streams and substreams within a runbook |
| `workspaces` | List, search, fetch, and create workspaces |
| `teams` | Look up teams associated with a runbook |
| `users` | Look up and search for users |
| `custom_fields` | Discover custom fields and their metadata/valid options |
| `folders` | List folders within a workspace |
| `comments` | Post comments on a runbook or task |
| `activities` | Read a runbook's activity trail |
| `action_logs` | Read the platform audit log |

### Tools

#### Runbooks

<details>

<summary>list_runbooks - List all runbooks in a specific workspace</summary>

- `workspace_id`: The unique identifier for the workspace (string, required)
- `is_template`: Filter by template status — false excludes templates, true shows only templates (boolean, optional)
- `archived`: Filter by archived status — false excludes archived runbooks, true shows only archived (boolean, optional)
- `source_runbook_id`: Filter to only runbooks created from this template ID (string, optional)
- `folder_id`: Filter to only runbooks in this folder ID (string, optional)
- `extra_params`: Additional query parameters to pass to the API, e.g. `{"stage": "active"}` (object, optional)

</details>

<details>

<summary>get_runbook_by_id - Fetch details for a specific runbook by its ID</summary>

- `runbook_id`: The unique identifier for the runbook (string, required)

</details>

<details>

<summary>create_runbook - Create a new runbook in a workspace, or as a copy of an existing runbook/template</summary>

- `name`: The name of the new runbook (string, required)
- `workspace_id`: The workspace to create the runbook in — required unless `copy_source_runbook_id` is passed (string, optional)
- `description`: Description for the runbook (string, optional)
- `status`: RAG status — off, red, amber, green (string, optional)
- `is_template`: Whether the runbook is a template (boolean, optional)
- `template_type`: off, default, or snippet (string, optional)
- `rto`: Recovery Time Objective in seconds (integer, optional)
- `timezone`: IANA timezone name (string, optional)
- `runbook_type_id`: Runbook type to associate (string, optional)
- `rto_start_task` / `rto_end_task`: Start/end task IDs for the RTO/RTA feature (string, optional)
- `folder_id`: Folder to place the runbook in — defaults to the workspace's default location (string, optional)
- `custom_field_values`: Custom field values to set, e.g. `{"name": "Field Name", "value": "value"}` (array of object, optional)
- `master_template`: Whether this runbook can generate app-specific templates — requires `is_template=true`, and the API rejects it otherwise; on rejection, surface it rather than silently setting `is_template=true` (boolean, optional)
- `start_scheduled`: ISO 8601 timestamp, or the literal `"now"`, to schedule the start (string, optional)
- `end_scheduled`: ISO 8601 timestamp for the scheduled end — must be omitted if `start_scheduled` isn't set (string, optional)
- `auto_start`: Whether to auto-start once `start_scheduled` is reached (runs live, comms on) (boolean, optional)
- `copy_source_runbook_id`: ID of an existing runbook/template to copy from (string, optional)
- `copy_tasks` / `copy_teams` / `copy_users`: What to include in the copy — each defaults to true; teams copied without members unless `copy_users` is also true (boolean, optional)
- `shift_fixed_times`: When copying, recalculate fixed task times relative to the new runbook's start (boolean, optional)

</details>

<details>

<summary>update_runbook - Update a specific runbook's fields</summary>

- `runbook_id`: The unique identifier for the runbook (string, required)
- `name` / `description`: New name/description (string, optional)
- `status`: RAG status — off, red, amber, green (string, optional)
- `is_template`: Whether the runbook is a template (boolean, optional)
- `rto`: Recovery Time Objective in seconds (integer, optional)
- `timezone`: IANA timezone name (string, optional)
- `rto_start_task` / `rto_end_task`: Start/end task IDs for the RTO/RTA feature (string, optional)
- `custom_field_values`: Custom field values to update (array of object, optional)
- `folder_id`: Folder to move the runbook to (string, optional)
- `master_template`: Requires `is_template=true`; the API rejects it on a non-template runbook — surface the rejection instead of auto-flipping `is_template` (boolean, optional)
- `start_scheduled` / `end_scheduled`: ISO 8601 timestamps (or `"now"` for start) to (re)schedule the runbook (string, optional)
- `auto_start`: Whether to auto-start once `start_scheduled` is reached (boolean, optional)

</details>

<details>

<summary>manage_runbook - Start, cancel, pause, or resume a runbook</summary>

- `runbook_id`: The unique identifier for the runbook (string, required)
- `action`: start, cancel, pause, or resume — the only supported actions (string, required)
- `comms`: off, test, on — start only (string, optional, default "off")
- `disable_task_notify`: Disable task start notifications — start only (boolean, optional)
- `run_type`: live or rehearsal — start only (string, optional, default "rehearsal")
- `rebaseline`: Recalculate all planned times based on current time — start only (boolean, optional)
- `shift_fixed_times`: Shift fixed-time tasks relative to current time — start only (boolean, optional)
- `validation_level`: warning or error — start only (string, optional, default "error")
- `message`: Note attached to the action — cancel/pause/resume only (string, optional)
- `notify`: Notify users about the action — cancel/pause/resume only (boolean, optional)

</details>

<details>

<summary>get_runbook_template_copies - Get all runbooks created from a specific runbook template</summary>

- `runbook_id`: The template runbook ID to find copies of (string, required)

</details>

#### Runbook Types

<details>

<summary>list_runbook_types - List all runbook types in the instance</summary>

_No parameters._

</details>

#### Tasks

<details>

<summary>get_runbook_tasks - Fetch tasks for a specific runbook, with optional filtering and sorting</summary>

- `runbook_id`: The unique identifier for the runbook (string, required)
- `forecast`: Return all tasks with computed timing (`start_display`/`end_display`) and dependency graph fields, overriding pagination/filters (boolean, optional)
- `fields_task`: Specific task fields to return, e.g. `["name", "stage"]` (array of string, optional)
- `stage`: Filter by stage — default, startable, in_progress, complete (array of string, optional)
- `stream_id`: Filter to tasks in these stream IDs (array of string, optional)
- `completion_type`: complete_normal, complete_skipped, complete_abandoned, complete_auto (string, optional)
- `task_type_id`: Filter to tasks of these task type IDs (array of string, optional)
- `level`: Filter by task level (string, optional)
- `search_term`: Match against task name (string, optional)
- `has_comments`: Only return tasks that have comments (boolean, optional)
- `runbook_team_id`: Filter to tasks assigned to these runbook team IDs (array of string, optional)
- `user_id`: Filter to tasks assigned to these user IDs (array of string, optional)
- `source_runbook_id`: Filter to tasks originating from these source runbook IDs (array of string, optional)
- `sort`: Sort field, e.g. `start_planned` or `-start_planned` for descending (string, optional)

</details>

<details>

<summary>add_task_to_runbook - Add a new task to an existing runbook</summary>

- `runbook_id`: The runbook to add the task to (string, required)
- `name`: Task name (string, required)
- `description`: Task description (string, optional)
- `task_type_id`: Task type to associate (string, optional)
- `stream_id`: Stream (or substream) to assign the task to (string, optional)
- `predecessors`: Task IDs that are predecessors to this task (array of string, optional)
- `duration`: Planned duration in seconds (integer, optional)
- `task_links`: Links to other resources — `link_type="runbook"` links to a template runbook (target must be a template with ≥1 task and the task's `task_type_id` must be the tenant's `linked` type, or the link is silently dropped); `link_type="snippet"` attaches snippets (array of object, optional)
- `message`: Message body for an Email/SMS/Call task, or initial prompt for an agentic task (string, optional)
- `recipients`: Recipients for a comms task (array of object, optional)
- `assignees`: Assignees to add — only users/teams already participating on the runbook are honored, others are silently ignored (array of object, optional)
- `custom_field_values`: Custom field values to set (array of object, optional)
- `start_fixed` / `end_fixed`: ISO 8601 timestamps fixing start/end (string, optional)
- `level`: level_1, level_2, or level_3 (string, optional, default level_3)
- `auto_start`: Start automatically once predecessors complete (boolean, optional)
- `auto_finish`: Complete automatically once started (boolean, optional)

</details>

<details>

<summary>update_runbook_task - Update an existing task (dependencies, description, stream, duration, etc.)</summary>

- `runbook_id` / `task_id`: The runbook and task to update (string, required)
- `name` / `description`: New name/description (string, optional)
- `predecessors`: Task IDs that are predecessors to this task (array of string, optional)
- `task_type_id`: Task type to associate (string, optional)
- `stream_id`: Stream (or substream) to assign the task to (string, optional)
- `duration`: Planned duration in seconds (integer, optional)
- `custom_field_values`: Custom field values to update (array of object, optional)
- `assignees`: Assignees to add — only existing runbook participants are honored; additive by default (array of object, optional)
- `delete_excluded_assignees`: When true, replaces the full assignee list with only those provided instead of adding to it (boolean, optional, default false)
- `task_links`: Replaces the task's links entirely — pass an empty list to clear all links (array of object, optional)
- `message`: Message body for an Email/SMS/Call task, or initial prompt for an agentic task (string, optional)
- `recipients`: Recipients for a comms task (array of object, optional)
- `start_fixed` / `end_fixed`: ISO 8601 timestamps fixing start/end (string, optional)
- `level`: level_1, level_2, or level_3 (string, optional)
- `auto_start` / `auto_finish`: Auto-start on predecessor completion / auto-finish on start (boolean, optional)

</details>

<details>

<summary>start_task - Start a specific task in a runbook</summary>

- `runbook_id` / `task_id`: The runbook and task to start (string, required)

</details>

<details>

<summary>complete_task - Complete a specific task in a runbook</summary>

- `runbook_id` / `task_id`: The runbook and task to complete (string, required)

</details>

<details>

<summary>skip_task - Skip a specific task in a runbook</summary>

- `runbook_id` / `task_id`: The runbook and task to skip (string, required)
- `comment`: Reason for skipping — required by the API and posted as a runbook comment (string, required)

</details>

<details>

<summary>delete_task - Delete a single task from a runbook</summary>

- `runbook_id` / `task_id`: The runbook and task to delete (string, required)

</details>

#### Task Types

<details>

<summary>list_task_types - List all task types</summary>

_No parameters._

</details>

#### Streams

<details>

<summary>list_streams - List all streams for a runbook, including substreams</summary>

- `runbook_id`: The runbook to list streams for (string, required)
- `forecast`: Include computed forecast fields (`start_display`, `end_display`, etc.) (boolean, optional)

</details>

<details>

<summary>get_stream - Get details of a specific stream or substream</summary>

- `runbook_id` / `stream_id`: The runbook and stream to fetch (string, required)

</details>

<details>

<summary>create_stream - Create a new stream or substream in a runbook</summary>

- `runbook_id`: The runbook to create the stream in (string, required)
- `name`: Stream name (string, required)
- `description`: Stream description (string, optional)
- `color`: CSS-friendly color, e.g. `#f0f0f0` or `rgb(0,0,0)` (string, optional)
- `parent_stream_id`: Parent stream ID, if creating a substream (string, optional)

</details>

<details>

<summary>update_stream - Update an existing stream in a runbook</summary>

- `runbook_id` / `stream_id`: The runbook and stream to update (string, required)
- `name` / `description` / `color`: New values (string, optional)

</details>

<details>

<summary>delete_stream - Delete a stream from a runbook</summary>

- `runbook_id` / `stream_id`: The runbook and stream to delete (string, required)

</details>

#### Workspaces

<details>

<summary>list_workspaces - List all workspaces</summary>

- `limit`: Maximum workspaces to return (integer, optional, default 50)
- `offset`: Number of workspaces to skip (integer, optional, default 0)

</details>

<details>

<summary>query_workspaces - Search for workspaces by name or query string</summary>

- `query`: Search string (string, required)

</details>

<details>

<summary>get_workspace_by_id - Fetch details for a specific workspace by its ID</summary>

- `workspace_id`: The unique identifier for the workspace (string, required)

</details>

<details>

<summary>create_workspace - Create a new account/workspace</summary>

- `name`: Workspace/account name (string, required)
- `key`: Shortened version of the name (string, required)
- `description`: Workspace/account description (string, optional)

</details>

#### Teams

<details>

<summary>get_runbook_teams - Get all teams associated with a runbook</summary>

- `runbook_id`: The runbook to fetch teams for (string, required)

</details>

#### Users

<details>

<summary>get_user - Get user details by user ID</summary>

- `user_id`: The user ID to fetch (string, required)

</details>

<details>

<summary>search_users - Search for users by name or email (fuzzy match)</summary>

- `query`: Search string — name or email, partial match (string, required)

</details>

#### Custom Fields

<details>

<summary>list_custom_fields - List all available custom fields, to discover fields that may not have values yet</summary>

- `workspace_id`: Filter to a workspace — omit to return fields from all accessible workspaces (string, optional)
- `include_global`: When `workspace_id` is set, also include globally available fields alongside the workspace's own (boolean, optional, default true)
- `scope`: task, runbook, or all (string, optional, default "all")

</details>

<details>

<summary>get_custom_field - Get a custom field's metadata including its type and valid options</summary>

- `custom_field_id`: The custom field to retrieve (string, required)

</details>

#### Folders

<details>

<summary>list_folders - List all folders in a specific workspace</summary>

- `workspace_id`: The workspace to list folders for (string, required)

</details>

#### Comments

<details>

<summary>add_comment - Post a comment on a runbook, optionally attached to a specific task</summary>

- `runbook_id`: The runbook to comment on (string, required)
- `content`: Comment text — a limited set of HTML tags is supported (e.g. `<p>`, `<b>`, `<ul>`, `<code>`); markdown is not rendered and disallowed tags are stripped (string, required)
- `task_id`: Task to attach the comment to — omit to post at runbook level (string, optional)

</details>

#### Activities

<details>

<summary>get_activities - Get activities for an incident runbook, to track recent actions and events</summary>

- `runbook_id`: The runbook to retrieve activities for (string, required)
- `created_after` / `created_before`: ISO 8601 date bounds (string, optional)

</details>

#### Action Logs

<details>

<summary>get_action_logs - Retrieve action logs (audit logs), paginated</summary>

- `runbook_id` / `user_id` / `workspace_id`: Filter by runbook, user, or workspace (string, optional)
- `created_after` / `created_before`: ISO 8601 date bounds (string, optional)
- `max_pages`: Maximum pages to fetch — response flags `truncated: true` if more remain (integer, optional, default 10)

</details>

This includes both read and write tools — see [Security & Responsible Use](#security--responsible-use) for how to scope access appropriately.

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
- Versioned releases and the changelog live under [Releases](https://github.com/gocutover/cutover-mcp-public/releases). The server reports its version as `serverInfo.version` and from `GET /health` when running over HTTP.

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
