from unittest.mock import AsyncMock

import pytest

from cutover_mcp.tools import task_types


@pytest.mark.asyncio
async def test_list_task_types(mock_client_manager):
    """Test listing all task types."""
    # Set up mock response
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "tt1",
                "type": "task_type",
                "attributes": {
                    "name": "Manual Task",
                    "description": "A task that requires manual execution",
                    "color": "#ff5733",
                },
            },
            {
                "id": "tt2",
                "type": "task_type",
                "attributes": {
                    "name": "Automated Task",
                    "description": "A task that runs automatically",
                    "color": "#33c3ff",
                },
            },
            {
                "id": "tt3",
                "type": "task_type",
                "attributes": {
                    "name": "Approval Task",
                    "description": "A task requiring approval",
                    "color": "#ffaa33",
                },
            },
        ],
        "meta": {"count": 3},
    }

    # Call the function
    result = await task_types.list_task_types()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/task_types", params={"include_integrations": "true"}
    )

    # Verify the result
    assert len(result["data"]) == 3
    assert result["data"][0]["attributes"]["name"] == "Manual Task"
    assert result["data"][1]["attributes"]["name"] == "Automated Task"
    assert result["data"][2]["attributes"]["name"] == "Approval Task"

    # Verify attributes
    assert result["data"][0]["attributes"]["color"] == "#ff5733"
    assert result["data"][1]["attributes"]["description"] == "A task that runs automatically"
    assert result["meta"]["count"] == 3


@pytest.mark.asyncio
async def test_list_task_types_empty(mock_client_manager):
    """Test handling empty task types list."""
    # Set up mock response with empty data
    mock_client_manager.request.return_value = {
        "data": [],
        "meta": {"count": 0},
    }

    # Call the function
    result = await task_types.list_task_types()

    # Verify the API call
    mock_client_manager.request.assert_called_once_with(
        "GET", "core/task_types", params={"include_integrations": "true"}
    )

    # Verify the result
    assert len(result["data"]) == 0
    assert result["meta"]["count"] == 0


@pytest.mark.asyncio
async def test_list_task_types_minimal_attributes(mock_client_manager):
    """Test task types with minimal attributes."""
    # Set up mock response with minimal data
    mock_client_manager.request.return_value = {
        "data": [
            {
                "id": "tt_minimal",
                "type": "task_type",
                "attributes": {
                    "name": "Basic Task Type",
                },
            }
        ],
    }

    # Call the function
    result = await task_types.list_task_types()

    # Verify the result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "tt_minimal"
    assert result["data"][0]["attributes"]["name"] == "Basic Task Type"

    # Verify optional attributes are not required
    assert (
        "description" not in result["data"][0]["attributes"] or result["data"][0]["attributes"]["description"] is None
    )
    assert "color" not in result["data"][0]["attributes"] or result["data"][0]["attributes"]["color"] is None


@pytest.mark.asyncio
async def test_list_task_types_error_handling(mock_client_manager):
    """Test error handling for task types listing."""
    import httpx

    # Set up mock to raise an error
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Server error '500 Internal Server Error'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await task_types.list_task_types()

    assert exc_info.value.response.status_code == 500


@pytest.mark.asyncio
async def test_list_task_types_authentication_error(mock_client_manager):
    """Test authentication error for task types listing."""
    import httpx

    # Set up mock to raise authentication error
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    mock_client_manager.request.side_effect = httpx.HTTPStatusError(
        "Client error '401 Unauthorized'",
        request=AsyncMock(),
        response=mock_response,
    )

    # Should raise the exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await task_types.list_task_types()

    assert exc_info.value.response.status_code == 401


@pytest.mark.asyncio
async def test_list_task_types_large_response(mock_client_manager):
    """Test handling large number of task types."""
    # Set up mock response with large number of task types
    large_data = []
    for i in range(100):
        large_data.append(
            {
                "id": f"tt{i}",
                "type": "task_type",
                "attributes": {
                    "name": f"Task Type {i}",
                    "description": f"Description for task type {i}",
                },
            }
        )

    mock_client_manager.request.return_value = {
        "data": large_data,
        "meta": {"count": 100},
    }

    # Call the function
    result = await task_types.list_task_types()

    # Verify the result
    assert len(result["data"]) == 100
    assert result["data"][0]["attributes"]["name"] == "Task Type 0"
    assert result["data"][99]["attributes"]["name"] == "Task Type 99"
    assert result["meta"]["count"] == 100


@pytest.mark.asyncio
async def test_list_task_types_can_exclude_integration_types(mock_client_manager):
    mock_client_manager.request.return_value = {"data": []}

    await task_types.list_task_types(include_integration=False)

    mock_client_manager.request.assert_called_once_with("GET", "core/task_types", params=None)


INTEGRATION_ACTION = {
    "data": {
        "id": "6",
        "type": "integration_action",
        "attributes": {
            "name": "Action - Polling",
            "kind": "custom/payload",
            "description": None,
            "hooks": ["task/started"],
            "option_overrides": {},
            "settings": {
                "webhook_url": "http://localhost:3000/mocks/execute_payload",
                "request_type": "GET",
                "use_polling": True,
                "polling_conditions": [{"response_path": "object.id", "target_custom_field": 33}],
                "auth_type": "token",
                "token_auth_value": "s3cr3t",
                "outbound_headers": "Authorization: Bearer abc",
                "polling_headers": "X-Secret: 2",
                "api_key": "k",
                "oauth_client_id": "cid",
                "aws_sqs_role_arn": "arn:aws:iam::1:role/x",
                "state_machine_arn": "arn:aws:states:eu-west-1:1:stateMachine:x",
                "project_key": "PRJ",
                "external_id": "*********************",
                "outbound_parameters": '{"Authorization": "Bearer abc"}',
                "polling_parameters": "Basic dXNlcjpwYXNzd29yZA==",
                "tls_certificate": "-----BEGIN CERTIFICATE-----",
                "deployment_environment": "production",
                "encrypted": True,
                "empty": "",
            },
        },
        "relationships": {
            "integration": {"data": {"id": "3", "type": "integration"}},
            "task_type": {"data": {"id": "14", "type": "task_type"}},
        },
        "meta": {"definition": {"title": "Build a custom integration", "description": "Custom integration builder"}},
    }
}


@pytest.mark.asyncio
async def test_get_integration_task_type_details_forwards_every_setting_except_credentials(mock_client_manager):
    mock_client_manager.request.return_value = INTEGRATION_ACTION

    result = await task_types.get_integration_task_type_details("6")

    mock_client_manager.request.assert_called_once_with("GET", "core/integration_actions/6")
    assert result == {
        "integration_action_id": "6",
        "task_type_id": "14",
        "integration_id": "3",
        "name": "Action - Polling",
        "kind": "custom/payload",
        "title": "Build a custom integration",
        "kind_description": "Custom integration builder",
        "description": None,
        "hooks": ["task/started"],
        "settings": {
            "webhook_url": "http://localhost:3000/mocks/execute_payload",
            "request_type": "GET",
            "use_polling": "true",
            "polling_conditions": '[{"response_path": "object.id", "target_custom_field": 33}]',
            "deployment_environment": "production",
            "encrypted": "true",
        },
        "option_overrides": {},
    }


@pytest.mark.asyncio
async def test_get_integration_task_type_details_never_returns_credentials_embedded_in_allowed_settings(
    mock_client_manager,
):
    mock_client_manager.request.return_value = {
        "data": {
            "id": "9",
            "attributes": {
                "settings": {
                    "connect_route_arguments": {"table": "change_request", "api_key": "example-credential"},
                    "connect_route_name": {"route": "snow", "headers": {"X-Auth": "1"}},
                    "outbound_payload": '{"password": "example-credential"}',
                    "outbound_parameters": "Basic dTpw",
                    "polling_parameters": "Bearer abc123",
                    "webhook_url": "https://example.test/hook?api_key=example-credential",
                    "polling_url": "https://user:pw@example.test/poll",
                    "polling_interval": "page=1&access_token=example-credential",
                    "response_mode": '[{"client_secret": "s"}]',
                    "request_type": '{"description": "{{task.name}}", "url": "https://example.test/a?b=1"}',
                    "polling_conditions": [{"response_path": "token", "target_custom_field": 33}],
                    "deployment_environment": "production",
                },
            },
        }
    }

    result = await task_types.get_integration_task_type_details("9")

    assert result["settings"] == {
        "request_type": '{"description": "{{task.name}}", "url": "https://example.test/a?b=1"}',
        "polling_conditions": '[{"response_path": "token", "target_custom_field": 33}]',
        "deployment_environment": "production",
    }


@pytest.mark.asyncio
async def test_get_integration_task_type_details_truncates_long_values(mock_client_manager):
    mock_client_manager.request.return_value = {
        "data": {"id": "9", "attributes": {"settings": {"webhook_url": "https://example.com/" + "a" * 600}}}
    }

    result = await task_types.get_integration_task_type_details("9")

    assert len(result["settings"]["webhook_url"]) == 503
    assert result["settings"]["webhook_url"].endswith("...")
    assert result["hooks"] == []


@pytest.mark.asyncio
async def test_get_integration_task_type_details_returns_connect_routing_settings(mock_client_manager):
    mock_client_manager.request.return_value = {
        "data": {
            "id": "11",
            "attributes": {
                "settings": {
                    "via_connect": True,
                    "connect_project": "payments",
                    "connect_route_name": "snow/create_change",
                    "connect_route_type": "lambda",
                    "connect_route_arguments": {"table": "change_request"},
                    "connect_response_type": "callback",
                    "outbound_payload": '{"short_description": "{{task.name}}"}',
                    "account_id": "42",
                },
            },
        }
    }

    result = await task_types.get_integration_task_type_details("11")

    assert result["settings"] == {
        "via_connect": "true",
        "connect_project": "payments",
        "connect_route_name": "snow/create_change",
        "connect_route_type": "lambda",
        "connect_route_arguments": '{"table": "change_request"}',
        "connect_response_type": "callback",
        "outbound_payload": '{"short_description": "{{task.name}}"}',
        "account_id": "42",
    }
