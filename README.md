# Cutover MCP (Model Context Protocol) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP server for interacting with the Cutover API, powered by FastMCP.

<!-- mcp-name: io.github.gocutover/cutover-mcp -->

## Contents

- [Capabilities](#capabilities)
- [Installation](#installation)
- [Setup](#setup)
- [Environment Configuration](#environment-configuration)
  - [Which URLs do I need?](#which-urls-do-i-need)
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

The server exposes 52 tools over MCP, grouped into 14 categories. 27 of them are read-only; see [Tool annotations](#tool-annotations).

### Tool Groups

| Group | Description |
| --- | --- |
| `runbooks` | Create, read, update, and control the lifecycle of runbooks and templates |
| `runbook_types` | List, fetch, and query runbook types |
| `tasks` | Read, add, update, and progress (start/complete/skip/delete) tasks within a runbook |
| `task_types` | Look up task types, including integration-backed and agentic (AI agent) task types |
| `streams` | Create, read, update, and delete streams and substreams within a runbook |
| `workspaces` | List, search, fetch, and create workspaces |
| `teams` | Look up teams associated with a runbook |
| `users` | Look up and search for users |
| `custom_fields` | Discover custom fields and their metadata/valid options, and create, update and archive field definitions and groups, including searchable fields linked to a data source |
| `data_sources` | Upload the file a data source reads from; create, read, update and archive JSON data sources; test, refresh and sync them, and list their imported records |
| `folders` | List folders within a workspace |
| `comments` | Post and read comments on a runbook or task |
| `activities` | Read a runbook's activity trail |
| `action_logs` | Read the platform audit log |

### Tool annotations

Every tool declares the MCP tool annotations `readOnlyHint`, `destructiveHint`, `idempotentHint` and `openWorldHint`, so an MCP client can tell the 27 read-only tools from the 25 that change data, and ask for approval only where it is needed. A tool is destructive when its change cannot be undone; creating and updating are not destructive. Set `MCP_READ_ONLY=true` to run the server with only the read-only tools.

| Kind | `readOnlyHint` | `destructiveHint` | `idempotentHint` | Tools |
| --- | --- | --- | --- | --- |
| Reads | true | false | true | `get_action_logs`, `get_activities`, `get_comments`, `get_custom_field`, `get_data_source`, `get_integration_task_type_details`, `get_runbook_by_id`, `get_runbook_tasks`, `get_runbook_teams`, `get_runbook_template_copies`, `get_runbook_type_by_id`, `get_stream`, `get_user`, `get_workspace_by_id`, `list_custom_field_groups`, `list_custom_fields`, `list_data_source_values`, `list_data_sources`, `list_folders`, `list_runbook_types`, `list_runbooks`, `list_streams`, `list_task_types`, `list_workspaces`, `query_runbook_types`, `query_workspaces`, `search_users` |
| Creates and adds | false | false | false | `add_comment`, `add_task_to_runbook`, `create_custom_field`, `create_custom_field_group`, `create_data_source`, `create_runbook`, `create_stream`, `create_workspace` |
| Updates | false | false | true | `update_custom_field`, `update_custom_field_group`, `update_data_source`, `update_runbook_task`, `update_stream` |
| Updates (not idempotent) | false | false | false | `update_runbook` |
| Archives and deletes | false | true | true | `archive_custom_field`, `archive_custom_field_group`, `archive_data_source`, `delete_stream`, `delete_task` |
| Changes state or replaces data | false | true | false | `complete_task`, `get_data_source_upload_url`, `manage_data_source`, `manage_runbook`, `skip_task`, `start_task` |

`openWorldHint` is true for the tools that reach beyond Cutover: `manage_runbook`, `start_task`, `complete_task` and `skip_task`, which can run integrations or send communications, and `manage_data_source`, which fetches the data source's URL. It is false for every other tool. `update_runbook` is not idempotent because `start_scheduled` accepts `"now"`. `get_data_source_upload_url` reads nothing from Cutover but returns a URL that can replace the file behind a data source, so it counts as a write.

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
- `custom_field_values`: Custom field values to set, including runbook dashboard fields — see [Custom Fields](#custom-fields) (array of object, optional)
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
- `custom_field_values`: Custom field values to update, including runbook dashboard fields — see [Custom Fields](#custom-fields) (array of object, optional)
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

<details>

<summary>get_runbook_type_by_id - Fetch details for a specific runbook type by its ID</summary>

- `runbook_type_id`: The unique identifier for the runbook type (string, required)

</details>

<details>

<summary>query_runbook_types - Find runbook types matching text and/or capability flags</summary>

- `query`: Case-insensitive text matched against the runbook type name, key, and description (string, optional)
- `incident`: Filter by whether the type is for incidents (boolean, optional)
- `enable_rto`: Filter by whether the type supports the RTO/RTA feature (boolean, optional)
- `dynamic`: Filter by whether the type is dynamic (boolean, optional)
- `ai_create_enabled`: Filter by whether AI-assisted creation is enabled for the type (boolean, optional)
- `include_archived`: Include archived runbook types; archived types are excluded by default (boolean, optional)
- `include_disabled`: Include disabled runbook types; disabled types are excluded by default (boolean, optional)

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
- `task_type_id`: Task type id from `list_task_types`, which includes integration-backed and agentic types (string, optional)
- `stream_id`: Stream (or substream) to assign the task to (string, optional)
- `predecessors`: Task IDs that are predecessors to this task (array of string, optional)
- `duration`: Planned duration in seconds (integer, optional)
- `task_links`: Links to other resources — `link_type="runbook"` links to a template runbook (target must be a template with ≥1 task and the task's `task_type_id` must be the tenant's `linked` type, or the link is silently dropped); `link_type="snippet"` attaches snippets (array of object, optional)
- `message`: Message body for an Email/SMS/Call task, or initial prompt for an agentic task (string, optional)
- `recipients`: Recipients for a comms task (array of object, optional)
- `assignees`: Assignees to add — only users/teams already participating on the runbook are honored, others are silently ignored (array of object, optional)
- `custom_field_values`: Custom field values to set — see [Custom Fields](#custom-fields) (array of object, optional)
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
- `task_type_id`: Task type id from `list_task_types`, which includes integration-backed and agentic types (string, optional)
- `stream_id`: Stream (or substream) to assign the task to (string, optional)
- `duration`: Planned duration in seconds (integer, optional)
- `custom_field_values`: Custom field values to update — see [Custom Fields](#custom-fields) (array of object, optional)
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

<summary>list_task_types - List all task types, including integration-backed ones (Jenkins, ServiceNow, webhooks, AI agent tasks); each carries a `meta.integration_action` object (`kind`, `description`, `hooks`, `definition`)</summary>

- `include_integration`: Include task types backed by an integration action (boolean, optional, default true)

</details>

<details>

<summary>get_integration_task_type_details - Summarise how an integration-backed task type is configured (descriptive settings only, never credentials); needs an integrations-admin or stakeholder role</summary>

- `integration_action_id`: The integration action id from the task type's `integration_action` relationship (string, required)

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

The runbook and task tools accept `custom_field_values` as a list of `{"custom_field_id": "123", "value": ...}` entries, where the id comes from `list_custom_fields`. A field's internal `name` can be used in place of the id, but its `display_name` cannot. Each `value` is a string, or a list of strings for multi-select fields. Malformed entries are rejected before any request is sent to Cutover.

<details>

<summary>list_custom_fields - List all available custom fields, to discover fields that may not have values yet</summary>

- `workspace_id`: Filter to a workspace — omit to return fields from all accessible workspaces (string, optional)
- `include_global`: When `workspace_id` is set, also include globally available fields alongside the workspace's own (boolean, optional, default true)
- `scope`: task, runbook, or all (string, optional, default "all") — runbook also covers dashboard fields on the runbook homepage, PIR and Incident Review

A searchable field's dependent fields are nested under it, each with the `value_key` it is filled from.

</details>

<details>

<summary>get_custom_field - Get a custom field's metadata including its type, valid options, group, constraints and, for searchable fields, data source</summary>

- `custom_field_id`: The custom field to retrieve (string, required)

</details>

The tools below change field definitions (the Custom Fields admin page), not the values on a runbook or task. They need the Custom Fields Admin or Global Admin role.

<details>

<summary>create_custom_field - Create a custom field definition</summary>

- `name`: The field's name (string, required). The API sets the UI label to the same value
- `field_type`: text, textarea, select_menu, radiobox, checkboxes, datetime, user_select, searchable or multi_searchable (string, required). A searchable field picks one record of a data source, a multi_searchable field several
- `apply_to`: runbook_add_edit, runbook_edit, runbook_page, task_add_edit, task_edit, task_start or task_end (string, required)
- `workspace_id`: The workspace that owns the field (string, required unless `global_field` is true)
- `global_field`: Create the field for every workspace (boolean, optional, default false)
- `field_options`: Option names — required for select_menu, radiobox and checkboxes, rejected otherwise (array of string, optional)
- `data_source_id`: The data source whose records the field searches — required for searchable and multi_searchable, rejected otherwise (integer, optional)
- `value_key`: The key of each record the field shows: the `mapping` of one of the data source's mappings, for example `app_id` — required for searchable and multi_searchable, rejected otherwise (string, optional)
- `display_data_view`: Show the data source's records in the workspace — searchable and multi_searchable only (boolean, optional)
- `dependent_fields`: Text fields filled from the other keys of the picked record, one per key, each `{name, value_key, display_search}`; Cutover puts the field's name in front of each name, so pass short names. Searchable and multi_searchable only, and a `value_key` can fill only one of them (array of object, optional)
- `required`, `allow_field_creation`, `display_list`, `display_search`, `display_table`: Field settings (boolean, optional)
- `default_value`: The value a new runbook or task starts with (string, optional)
- `custom_field_group_id`: The group to show the field in (string, optional)
- `task_type_ids`, `runbook_type_ids`: Limit the field to these task or runbook types (array of string, optional)

</details>

<details>

<summary>update_custom_field - Update a custom field definition</summary>

- `custom_field_id`: The field to update (string, required)
- `name`: The new name (string, optional)
- `add_field_options`: Option names to add to a select_menu, radiobox or checkboxes field; existing options are kept, and other field types are rejected (array of string, optional)
- `data_source_id`, `value_key`, `display_data_view`: Link a searchable or multi_searchable field to another data source, change the key it shows, or show or hide its records in the workspace; other field types are rejected (integer, string, boolean, optional)
- `dependent_fields`: The complete set of a searchable field's dependent fields, each `{name, value_key, display_search}`: one left out is archived, an archived one listed again is restored, `[]` archives them all, and an active one keeps its name and `display_search`. Start from the current set in `list_custom_fields` (array of object, optional)
- `required`, `allow_field_creation`, `display_list`, `display_search`, `display_table`: Field settings (boolean, optional)
- `default_value`: The value a new runbook or task starts with (string, optional)
- `custom_field_group_id`: Move the field to this group, or `""` to take it out of its group; omitted, the field stays in its current group (string, optional)
- `task_type_ids`, `runbook_type_ids`: Replace the constraints of that type; the other type is kept, and an empty list is rejected because the API cannot clear them (array of string, optional)

</details>

<details>

<summary>archive_custom_field - Archive a custom field definition</summary>

- `custom_field_id`: The field to archive (string, required)

</details>

<details>

<summary>list_custom_field_groups - List custom field groups</summary>

Takes no parameters. Archived groups are not returned; the API does not list them.

</details>

<details>

<summary>create_custom_field_group - Create a custom field group</summary>

- `name`: The group's name (string, required)

</details>

<details>

<summary>update_custom_field_group - Rename a custom field group</summary>

- `custom_field_group_id`: The group to rename (string, required)
- `name`: The new name (string, required)

</details>

<details>

<summary>archive_custom_field_group - Archive a custom field group</summary>

- `custom_field_group_id`: The group to archive (string, required)

</details>

#### Data Sources

<details>

<summary>list_data_sources - List JSON data sources</summary>

- `archived`: Return archived data sources instead of active ones (boolean, optional, default false)
- `query`: Only return data sources whose name contains this text, case insensitive (string, optional)

Data sources created by an integration are not returned. Requires the Custom Fields Admin or Global Stakeholder role.

</details>

<details>

<summary>get_data_source - Get a data source</summary>

- `data_source_id`: The data source's ID (integer, required)

Returns its settings, `mappings`, whether it is `archivable` (false while an active custom field uses it, or once archived), and the last import's `last_sync_status` (`queued`, `running`, `succeeded` or `failed`), `last_sync_error` and times.

</details>

<details>

<summary>create_data_source - Create a JSON data source</summary>

- `name`: The data source's name (string, required)
- `url`: The endpoint searched for records, or the `datasource_endpoint_url` returned by `get_data_source_upload_url` for an uploaded file (string, required)
- `mappings`: The fields of each record, as `{mapping, type, primary}`; `type` defaults to `text` and exactly one mapping is `primary` (list, required)
- `persist_mode`: `persist_all` to import every record, or `query_cache` to store only the records a search returns (string, optional)
- `http_method`: `get` or `post` (string, optional)
- `records_path`: Path to the array of records in the search response (string, optional)
- `search_parameter_name`: Query string parameter the search term is sent in (string, optional)
- `attributes_path`: Path, relative to each record, to the object holding the mapped keys (string, optional)

A searchable custom field's `value_key` must equal one of the `mapping` names. For an uploaded file, Cutover sets `records_path` and `search_parameter_name` itself. Authentication settings cannot be set through the API. Requires the Custom Fields Admin role; `persist_all` also requires Global Admin.

</details>

<details>

<summary>update_data_source - Rename a data source or change its persist mode</summary>

- `data_source_id`: The data source's ID (integer, required)
- `name`: The new name (string, optional)
- `persist_mode`: `persist_all` or `query_cache` (string, optional)

No other setting can be changed after creation. Requires the Custom Fields Admin role; changing `persist_mode` also requires Global Admin.

</details>

<details>

<summary>archive_data_source - Archive a data source</summary>

- `data_source_id`: The data source's ID (integer, required)

Fails while an active custom field uses the data source; archive those fields first. Requires the Custom Fields Admin role.

</details>

<details>

<summary>manage_data_source - Test, refresh or sync a data source</summary>

- `data_source_id`: The data source's ID (integer, required)
- `action`: `test`, `refresh` or `sync` (string, required)
- `query`: The search term for `test` and `refresh` (string, optional, default `*`, which matches every record of an uploaded file)
- `wait_seconds`: For `sync`, how long to wait for the import to finish, from 0 to 50 (integer, optional, default 30)

`test` searches the data source's URL and returns the HTTP status, URL and body it answered with (the body cut to 2000 characters), without storing anything; run it after an upload, before the first sync, since the file cannot be read until its malware scan finishes. `refresh` adds every key of the returned records that is not yet in `mappings` and returns `total_added`. `sync` imports every record of a `persist_all` data source and waits for the import to finish, returning `finished`, `last_sync_status`, `last_sync_error` and the import times, or a message when it has not finished after `wait_seconds`. If an import is already in progress, `sync` waits for that one and returns `already_running: true`. Data sources reached through Cutover Connect do not support `test` or `refresh`.

</details>

<details>

<summary>list_data_source_values - List the data source records stored for a searchable custom field</summary>

- `custom_field_id`: The ID of a searchable or multi searchable custom field (string, required)
- `page`: The page to return, starting at 1 (integer, optional, default 1)

Returns `values` (each `{key, values}`, where `key` is the value of the data source's primary mapping), `page`, `total_records` and `has_more`. Each record's `values` holds only the keys of the custom field and of its active dependent custom fields.

</details>

<details>

<summary>get_data_source_upload_url - Get a signed URL to upload a file for a data source</summary>

- `file_name`: Name of the file to upload, e.g. `cmdb.csv` (string, required)
- `data_source_id`: A data source created over an uploaded file, to upload a new version of its file; omit for the first upload (integer, optional)

The server cannot read files on your machine, so the agent uploads the file itself with an HTTP `PUT` to the returned `url` before it expires (`expires_in` seconds), then calls `create_data_source` with the returned `datasource_endpoint_url` as its URL. With `data_source_id`, fails before any upload unless that data source already reads from the returned `datasource_endpoint_url`, since a data source's URL cannot be changed; after uploading a new version, refresh and sync it with `manage_data_source`. Fails with a clear error if the instance's data source search service is not configured.

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

<details>

<summary>get_comments - List the comments on a runbook, optionally filtered to a specific task</summary>

- `runbook_id`: The runbook to read comments from (string, required)
- `task_id`: Return only the comments attached to this task — omit for every comment on the runbook, including runbook-level ones (string, optional)

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

The server is published on PyPI as [`cutover-mcp`](https://pypi.org/project/cutover-mcp/) and runs with [`uv`](https://docs.astral.sh/uv/), which downloads Python 3.13+ on demand, so `uv` is the only prerequisite. On macOS:

```bash
brew install uv
```

Other platforms: see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

Then point your MCP client at `uvx cutover-mcp` with your credentials in its `env` block — see [Client Setup](#client-setup). `uvx` downloads the latest release on first run and caches it; pin a version with `uvx cutover-mcp@1.2.3`. No clone, no virtualenv.

To start it from a terminal instead (it waits for an MCP client on stdin, so it will look idle; Ctrl+C to stop):

```sh
CUTOVER_BASE_URL=https://api.cutover.net CUTOVER_API_TOKEN=your_token_here CUTOVER_CORE_URL=https://YOUR-INSTANCE-NAME.cutover.com uvx cutover-mcp
```

## Setup

Only needed to work on the server itself or to run an unreleased build; to just use it, see [Installation](#installation) above.

1. Copy `.env.example` to `.env` and fill in your Cutover API credentials — see [Environment Configuration](#environment-configuration) below.
2. Install dependencies with uv:
   ```sh
   uv sync
   ```
3. Run the server using:
   ```sh
   uv run cutover-mcp
   ```
   That is the same console script `uvx cutover-mcp` runs; `uv run python src/cutover_mcp/server.py` works too.
4. Run tests:
   ```sh
   uv run pytest
   ```

## Environment Configuration

### Which URLs do I need?

For most instances, one URL and a token:

```
CUTOVER_CORE_URL=https://your-instance.cutover.com
CUTOVER_API_TOKEN=MY_TOKEN_VALUE
```

`CUTOVER_CORE_URL` is your Cutover instance URL, the one you open in the browser. The API host (`CUTOVER_BASE_URL`) defaults to `https://api.cutover.net`, which serves every shared production instance, so leave it unset unless your instance has its own API host (single-tenant deployments, typically `https://api.your-instance.cutover.com`). The default only applies to Cutover-hosted instance URLs; for any other instance URL the server asks you to set `CUTOVER_BASE_URL` rather than guess. If a call fails with an authorization error the message says how to override it; ask your Cutover contact if you are unsure which applies.

### Environment Variables Reference

| Variable            | Required | Notes                                                                                                                                                        |
| ------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CUTOVER_CORE_URL`  | Yes      | Your Cutover instance URL, e.g. `https://your-instance.cutover.com`. Sent as the `Core-Url` header so the API routes to your instance.                        |
| `CUTOVER_API_TOKEN` | Yes      | See [Generating an API Token](#generating-an-api-token) below.                                                                                               |
| `CUTOVER_BASE_URL`  | No       | The Cutover API host. Defaults to `https://api.cutover.net`. Set it only for an instance with its own API host, e.g. `https://api.your-instance.cutover.com`. |
| `MCP_READ_ONLY` | No | `true` exposes only the [read-only tools](#tool-annotations); write tools are neither listed nor callable. Any value other than true/false, 1/0 or yes/no stops the server from starting. |

### Generating an API Token

There are two ways to generate a token:

- **Access Management** — an admin generates a token for a specific user (useful if you want the token to act as someone other than yourself, e.g. a global admin, or you don't have self-service access).
- **My Details → User App Tokens** — generate your own token directly, self-service.

## Security & Responsible Use

The MCP server adds no security model of its own — it authenticates to the Cutover API as a single **user app token** over HTTPS and inherits exactly that user's permissions. Scope the token correctly and use the write tools deliberately:

- **Least privilege.** Use a dedicated [non-interactive user](#generating-an-api-token) with the **Developer** role plus only the scoped roles the use case needs (e.g. Workspace manager on one workspace) — not a personal admin token. Rotate the token periodically and revoke it in Cutover when the use case ends.
- **Read-only vs read-write.** This server ships write tools (`create_runbook`, `manage_runbook`, `delete_task`, `start_task`, …). For query-only use cases, set `MCP_READ_ONLY=true` so only the read-only tools are exposed, and also omit roles that grant create/update/delete/manage: the Cutover role is what the API enforces.
- **Approve writes.** Keep human approval enabled for mutating or consequential actions — models can act on unexpected content returned by tools, so approval is the real safeguard. Every tool is [annotated](#tool-annotations), so a client that gates on `readOnlyHint` or `destructiveHint` can ask for approval on writes only.
- **Verify critical output.** A tool call returns real data, but the model's summary of it can still be wrong (or answer with no tool call at all). For compliance- or audit-critical output, verify against Cutover as the system of record.
- **Protect the token.** It lives in env config (`.env*` is git-ignored and excluded from Docker images). If a token is compromised, revoke it immediately in Cutover's Access Management — the MCP server holds no independent session, so revoking the token fully cuts off access, and a scoped role confines any impact to that use case.

## Project Structure

- `src/cutover_mcp/` - Main package
- `clients/` - API client
- `resources/` - Resource definitions (MCP endpoints)
- `tools/` - Tool logic
- `server.py` - FastMCP server entrypoint (`main()` is the `cutover-mcp` console script)
- `server.json` - The server's [MCP Registry](https://registry.modelcontextprotocol.io) entry
- `tests/` - Tests

## Notes

- Dependency and environment management is handled by [uv](https://github.com/astral-sh/uv) and [hatchling](https://hatch.pypa.io/).
- Versioned releases and the changelog live under [Releases](https://github.com/gocutover/cutover-mcp-public/releases). Each release is published to [PyPI](https://pypi.org/project/cutover-mcp/) and listed in the [MCP Registry](https://registry.modelcontextprotocol.io) as `io.github.gocutover/cutover-mcp`. The server reports its version as `serverInfo.version` and from `GET /health` when running over HTTP.

## Client Setup

### Run in VS Code GitHub Copilot

If you want to use VS Code with GitHub Copilot to call out to this MCP server, you can use `mcp.json.example`.

1. Copy `mcp.json.example` to `.vscode/mcp.json` (create the `.vscode/` directory if not already present). It runs `uvx cutover-mcp` and prompts for your API token the first time the server starts, so the token is never written into the project.
2. Set `CUTOVER_BASE_URL` and `CUTOVER_CORE_URL` in its `env` block for your instance — see [Environment Configuration](#environment-configuration).
3. Restart VS Code for the changes to take effect. In the Copilot Chat box, click the **Configure tools** icon and expand `cutover-mcp` to see its full list of tools. MCP tools only run in Agent mode — switch the mode dropdown from Ask to Agent if nothing happens.

### Run in Claude Desktop

If you'd rather use Claude Desktop instead of an IDE, you can set that up:

1. [Download and install Claude Desktop](https://www.anthropic.com/claude/desktop).
2. Copy `claude_desktop_config.json.example` to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS path shown; on Windows, use `%APPDATA%\Claude\claude_desktop_config.json`).
3. Fill in the `env` block with your credentials — see [Environment Configuration](#environment-configuration). Claude Desktop does not inherit your shell's `PATH`, so if it reports that `uvx` cannot be found, set `command` to the full path from `which uvx` (typically `/opt/homebrew/bin/uvx` on macOS).
4. Restart Claude Desktop. Click the **+** button at the bottom of the chat box, then **Connectors** — `cutover-mcp` should be listed there along with its tools. If it isn't, check Settings → Developer for its connection status and logs.

This will allow Claude Desktop to connect to your MCP server.

## Docker Usage

Docker is optional — the server runs fine without it (see [Installation](#installation)). Use this if you want a self-contained way to run it instead of `uvx`.

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

You can configure your MCP server to use the Docker container instead of `uvx`. The root key differs by client: VS Code (`mcp.json`) uses `servers`; Claude Desktop (`claude_desktop_config.json`) uses `mcpServers`.

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
