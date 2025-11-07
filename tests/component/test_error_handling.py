"""Component tests for error handling across all tools.

Tests error paths and exception handling to achieve 95%+ coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp.exceptions import ToolError

from ids_mcp_server.tools.document import create_ids, load_ids, export_ids, get_ids_info
from ids_mcp_server.tools.facets import (
    add_entity_facet,
    add_property_facet,
    add_attribute_facet,
    add_classification_facet,
    add_material_facet,
    add_partof_facet
)
from ids_mcp_server.tools.validation import validate_ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.session.storage import get_session_storage


@pytest.fixture
def mock_context():
    """Provide mock FastMCP Context for testing."""
    ctx = MagicMock()
    ctx.session_id = "test-error-session"
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


# Document Tool Error Paths
@pytest.mark.asyncio
async def test_create_ids_exception_handling(mock_context):
    """Test create_ids handles unexpected exceptions."""
    # Patch ids.Ids to raise an exception
    with patch('ids_mcp_server.tools.document.ids.Ids', side_effect=RuntimeError("Unexpected error")):
        with pytest.raises(ToolError, match="Failed to create IDS"):
            await create_ids(title="Test", ctx=mock_context)

    # Verify error was logged
    mock_context.error.assert_called_once()


@pytest.mark.asyncio
async def test_load_ids_file_not_found(mock_context):
    """Test load_ids handles file not found."""
    with pytest.raises(ToolError, match="File not found"):
        await load_ids(
            source="/nonexistent/file.ids",
            source_type="file",
            ctx=mock_context
        )


@pytest.mark.asyncio
async def test_load_ids_invalid_xml(mock_context):
    """Test load_ids handles invalid XML."""
    with pytest.raises(ToolError, match="Failed to load IDS"):
        await load_ids(
            source="<invalid>xml",
            source_type="string",
            ctx=mock_context
        )


@pytest.mark.asyncio
async def test_export_ids_to_string(mock_context):
    """Test export_ids exports to string successfully."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Export should work
    result = await export_ids(ctx=mock_context)
    assert "xml" in result
    assert "<ids" in result["xml"]
    assert "Test</title>" in result["xml"]


@pytest.mark.asyncio
async def test_get_ids_info_exception_handling(mock_context):
    """Test get_ids_info handles exceptions."""
    # Create a session with corrupt data
    storage = get_session_storage()

    # Patch the storage to raise an exception
    with patch.object(storage, 'get', side_effect=RuntimeError("Storage error")):
        with pytest.raises(ToolError, match="Failed to get IDS info"):
            await get_ids_info(ctx=mock_context)


# Facet Tool Error Paths
@pytest.mark.asyncio
async def test_entity_facet_exception_in_ifctester(mock_context):
    """Test add_entity_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Patch ids.Entity to raise an exception
    with patch('ids_mcp_server.tools.facets.ids.Entity', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add entity facet"):
            await add_entity_facet(
                spec_id="S1",
                location="applicability",
                entity_name="IFCWALL",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_property_facet_exception_in_ifctester(mock_context):
    """Test add_property_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with patch('ids_mcp_server.tools.facets.ids.Property', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add property facet"):
            await add_property_facet(
                spec_id="S1",
                location="requirements",
                property_name="FireRating",
                property_set="Pset_WallCommon",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_attribute_facet_exception_in_ifctester(mock_context):
    """Test add_attribute_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with patch('ids_mcp_server.tools.facets.ids.Attribute', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add attribute facet"):
            await add_attribute_facet(
                spec_id="S1",
                location="requirements",
                attribute_name="Name",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_classification_facet_exception_in_ifctester(mock_context):
    """Test add_classification_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with patch('ids_mcp_server.tools.facets.ids.Classification', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add classification facet"):
            await add_classification_facet(
                spec_id="S1",
                location="requirements",
                classification_value="Ss_25_10_20",
                classification_system="Uniclass",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_material_facet_exception_in_ifctester(mock_context):
    """Test add_material_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with patch('ids_mcp_server.tools.facets.ids.Material', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add material facet"):
            await add_material_facet(
                spec_id="S1",
                location="requirements",
                material_value="Concrete",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_partof_facet_invalid_location(mock_context):
    """Test add_partof_facet handles invalid location."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError, match="Invalid location"):
        await add_partof_facet(
            spec_id="S1",
            location="invalid_location",
            relation="IFCRELCONTAINEDINSPATIALSTRUCTURE",
            parent_entity="IFCSPACE",
            ctx=mock_context
        )


@pytest.mark.asyncio
async def test_partof_facet_exception_in_ifctester(mock_context):
    """Test add_partof_facet handles IfcTester exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with patch('ids_mcp_server.tools.facets.ids.PartOf', side_effect=RuntimeError("IfcTester error")):
        with pytest.raises(ToolError, match="Failed to add partOf facet"):
            await add_partof_facet(
                spec_id="S1",
                location="applicability",
                relation="IFCRELCONTAINEDINSPATIALSTRUCTURE",
                parent_entity="IFCSPACE",
                ctx=mock_context
            )


# Validation Tool Error Paths
@pytest.mark.asyncio
async def test_validate_ids_xsd_validation_failure(mock_context):
    """Test validate_ids handles XSD validation failures."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Patch from_string to raise XSD validation error
    with patch('ids_mcp_server.tools.validation.ids.from_string', side_effect=Exception("XSD validation failed")):
        result = await validate_ids(ctx=mock_context)

        # Should still return result, but with xsd_valid=False and errors
        assert result["valid"] is False
        assert result["details"]["xsd_valid"] is False
        assert any("XSD validation failed" in err for err in result["errors"])


@pytest.mark.asyncio
async def test_validate_ids_exception_handling(mock_context):
    """Test validate_ids handles unexpected exceptions."""
    # Patch get_or_create_session to raise an exception
    with patch('ids_mcp_server.tools.validation.get_or_create_session', side_effect=RuntimeError("Unexpected")):
        with pytest.raises(ToolError, match="Validation error"):
            await validate_ids(ctx=mock_context)
