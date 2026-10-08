import pytest
from pydantic import ValidationError

from cutover_mcp.models import CustomFieldValueInput, serialize_custom_field_values


def test_serialize_custom_field_values_passes_valid_entries_through():
    """Valid entries are sent unchanged, including an empty string used to clear a field."""
    values = [
        {"custom_field_id": "72", "value": "Yes"},
        {"name": "Executive summary", "value": "<p>Summary</p>"},
        {"custom_field_id": "110", "value": ["Cardiff", "Lisbon"]},
        {"custom_field_id": "72", "value": ""},
    ]

    assert serialize_custom_field_values(values) == values


def test_serialize_custom_field_values_coerces_integers_to_strings():
    """The API requires string ids, so integer ids and values are converted before sending."""
    assert serialize_custom_field_values([{"custom_field_id": 72, "value": 5}]) == [
        {"custom_field_id": "72", "value": "5"}
    ]


def test_serialize_custom_field_values_accepts_model_instances():
    """Values already validated by the MCP layer arrive as model instances."""
    value = CustomFieldValueInput(custom_field_id="72", value="Yes")

    assert serialize_custom_field_values([value]) == [{"custom_field_id": "72", "value": "Yes"}]


def test_serialize_custom_field_values_keeps_both_identifiers():
    """The API resolves fields by custom_field_id first, so a name sent alongside it is ignored."""
    values = [{"custom_field_id": "72", "name": "Task Edit CF", "value": "Yes"}]

    assert serialize_custom_field_values(values) == values


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        # An unsupported key in place of an identifier, with a list of objects as the value.
        ({"field": "Task Edit CF", "value": [{"name": "Yes"}]}, "Extra inputs are not permitted"),
        ({"value": "Yes"}, "must identify the field with custom_field_id"),
        ({"name": "  ", "value": "Yes"}, "must identify the field with custom_field_id"),
        ({"custom_field_id": "72", "value": {"name": "Yes"}}, "value must be a string"),
        ({"custom_field_id": "72", "value": [{"name": "Yes"}]}, "value must be a string"),
        ({"custom_field_id": "72", "value": True}, "value must be a string"),
        ({"custom_field_id": "72"}, "Field required"),
        ({"custom_field_id": "cf-72", "value": "Yes"}, "custom_field_id must be a numeric id"),
        ({"custom_field_id": True, "value": "Yes"}, "custom_field_id"),
        ({"custom_field_id": "72", "value": "Yes", "read_only": False}, "Extra inputs are not permitted"),
    ],
)
def test_serialize_custom_field_values_rejects_invalid_entries(entry, message):
    """Entries the API would reject fail validation with a message explaining what to fix."""
    with pytest.raises(ValidationError, match=message):
        serialize_custom_field_values([entry])
