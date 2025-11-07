"""Tests for specification management tools."""

import pytest
from ifctester import ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.document import create_ids
from ids_mcp_server.session.storage import get_session_storage
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_add_specification_minimal(mock_context):
    """Test adding specification with minimal required fields."""
    # Create IDS first
    await create_ids(title="Test IDS", ctx=mock_context)

    # Add specification
    result = await add_specification(
        name="Test Specification",
        ifc_versions=["IFC4"],
        ctx=mock_context
    )

    assert result["status"] == "added"
    assert result["spec_id"] == "Test Specification"
    assert result["ifc_versions"] == ["IFC4"]

    # Verify in session
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    assert len(session_data.ids_obj.specifications) == 1
    assert session_data.ids_obj.specifications[0].name == "Test Specification"


@pytest.mark.asyncio
async def test_add_specification_with_all_fields(mock_context):
    """Test adding specification with all optional fields."""
    await create_ids(title="Test IDS", ctx=mock_context)

    result = await add_specification(
        name="Complete Specification",
        ifc_versions=["IFC4", "IFC4X3_ADD2"],
        ctx=mock_context,
        identifier="S1",
        description="Test description",
        instructions="Test instructions",
        min_occurs=1,
        max_occurs=5
    )

    assert result["status"] == "added"
    assert result["spec_id"] == "S1"

    # Verify all fields
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = session_data.ids_obj.specifications[0]

    assert spec.name == "Complete Specification"
    assert spec.identifier == "S1"
    assert spec.description == "Test description"
    assert spec.instructions == "Test instructions"
    assert spec.minOccurs == 1
    assert spec.maxOccurs == 5


@pytest.mark.asyncio
async def test_add_specification_normalizes_ifc_versions(mock_context):
    """Test that IFC versions are normalized to uppercase."""
    await create_ids(title="Test IDS", ctx=mock_context)

    result = await add_specification(
        name="Test Spec",
        ifc_versions=["ifc4", "Ifc4x3"],  # lowercase/mixed case
        ctx=mock_context
    )

    # Should normalize to uppercase
    assert result["ifc_versions"] == ["IFC4", "IFC4X3_ADD2"]


@pytest.mark.asyncio
async def test_add_specification_invalid_ifc_version(mock_context):
    """Test that invalid IFC versions raise error."""
    await create_ids(title="Test IDS", ctx=mock_context)

    with pytest.raises(ToolError) as exc_info:
        await add_specification(
            name="Test Spec",
            ifc_versions=["IFC5"],  # Invalid version
            ctx=mock_context
        )

    assert "Invalid IFC version" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_specification_multiple_ifc_versions(mock_context):
    """Test adding specification with multiple IFC versions."""
    await create_ids(title="Test IDS", ctx=mock_context)

    result = await add_specification(
        name="Multi-Version Spec",
        ifc_versions=["IFC2X3", "IFC4", "IFC4X3_ADD2"],
        ctx=mock_context
    )

    assert result["ifc_versions"] == ["IFC2X3", "IFC4", "IFC4X3_ADD2"]

    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = session_data.ids_obj.specifications[0]
    assert set(spec.ifcVersion) == {"IFC2X3", "IFC4", "IFC4X3_ADD2"}


@pytest.mark.asyncio
async def test_add_specification_unbounded_max_occurs(mock_context):
    """Test adding specification with unbounded max_occurs."""
    await create_ids(title="Test IDS", ctx=mock_context)

    result = await add_specification(
        name="Unbounded Spec",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        max_occurs="unbounded"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = session_data.ids_obj.specifications[0]
    assert spec.maxOccurs == "unbounded"


@pytest.mark.asyncio
async def test_add_multiple_specifications(mock_context):
    """Test adding multiple specifications to same IDS."""
    await create_ids(title="Test IDS", ctx=mock_context)

    # Add first specification
    await add_specification(
        name="Spec 1",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="S1"
    )

    # Add second specification
    await add_specification(
        name="Spec 2",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="S2"
    )

    # Verify both exist
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    assert len(session_data.ids_obj.specifications) == 2
    assert session_data.ids_obj.specifications[0].name == "Spec 1"
    assert session_data.ids_obj.specifications[1].name == "Spec 2"


@pytest.mark.asyncio
async def test_add_specification_validates_in_export(mock_context):
    """Test that specification validates when exporting IDS."""
    from ids_mcp_server.tools.document import export_ids

    await create_ids(title="Test IDS", ctx=mock_context)

    await add_specification(
        name="Validation Test",
        ifc_versions=["IFC4"],
        ctx=mock_context
    )

    # Add entity to make it valid
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = session_data.ids_obj.specifications[0]
    spec.applicability.append(ids.Entity(name="IFCWALL"))

    # Should export and validate successfully
    result = await export_ids(ctx=mock_context, validate=True)

    assert result["validation"]["valid"] is True
    assert result["validation"]["errors"] == []
