"""Component tests for edge cases and validation warnings.

Tests validation warnings, edge cases, and specific code paths to reach 95%+ coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp.exceptions import ToolError

from ids_mcp_server.tools.document import load_ids, export_ids, get_ids_info, create_ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.validation import validate_ids, validate_ifc_model
from ids_mcp_server.tools.facets import (
    add_property_facet,
    add_attribute_facet,
    add_material_facet
)
from ids_mcp_server.tools.restrictions import (
    add_enumeration_restriction,
    add_pattern_restriction,
    add_bounds_restriction,
    add_length_restriction
)


@pytest.fixture
def mock_context():
    """Provide mock FastMCP Context for testing."""
    ctx = MagicMock()
    ctx.session_id = "test-edge-case-session"
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


# Validation Edge Cases
@pytest.mark.asyncio
async def test_validate_ids_specification_without_name(mock_context):
    """Test validate_ids warns about specifications without names."""
    await create_ids(title="Test", ctx=mock_context)

    # Add specification without name (name=None)
    from ids_mcp_server.session.storage import get_session_storage
    from ifctester import ids

    storage = get_session_storage()
    ids_obj = storage.get(mock_context.session_id).ids_obj

    # Manually create spec without name
    spec = ids.Specification(ifcVersion=["IFC4"])
    spec.name = None  # Explicitly set to None
    spec.applicability = [ids.Entity(name="IFCWALL")]
    ids_obj.specifications.append(spec)

    result = await validate_ids(ctx=mock_context)

    # Should have warning about missing name
    assert len(result["warnings"]) > 0
    assert any("no name" in w.lower() for w in result["warnings"])


@pytest.mark.asyncio
async def test_validate_ids_invalid_ifc_version(mock_context):
    """Test validate_ids warns about non-standard IFC versions."""
    await create_ids(title="Test", ctx=mock_context)

    from ids_mcp_server.session.storage import get_session_storage
    from ifctester import ids

    storage = get_session_storage()
    ids_obj = storage.get(mock_context.session_id).ids_obj

    # Manually create spec with invalid IFC version
    spec = ids.Specification(name="Test Spec", ifcVersion=["IFC5"])  # Non-standard
    spec.applicability = [ids.Entity(name="IFCWALL")]
    ids_obj.specifications.append(spec)

    result = await validate_ids(ctx=mock_context)

    # Should have warning about non-standard version
    assert len(result["warnings"]) > 0
    assert any("non-standard" in w.lower() or "ifc5" in w.lower() for w in result["warnings"])


@pytest.mark.asyncio
async def test_validate_ids_missing_title(mock_context):
    """Test validate_ids errors on missing title."""
    from ids_mcp_server.session.storage import get_session_storage
    from ifctester import ids

    # Create IDS manually without title
    ids_obj = ids.Ids()
    ids_obj.info = {}  # No title

    storage = get_session_storage()
    from ids_mcp_server.session.models import SessionData
    storage.set(mock_context.session_id, SessionData(ids_obj=ids_obj))

    result = await validate_ids(ctx=mock_context)

    # Should have error about missing title
    assert result["valid"] is False
    assert any("title" in e.lower() for e in result["errors"])
    assert result["details"]["has_title"] is False


# Document Tool Edge Cases
@pytest.mark.asyncio
async def test_load_ids_exception_during_parsing(mock_context):
    """Test load_ids handles parsing exceptions."""
    with patch('ids_mcp_server.tools.document.ids.open', side_effect=RuntimeError("Parse error")):
        with pytest.raises(ToolError, match="Failed to load IDS"):
            await load_ids(
                source="/some/file.ids",
                source_type="file",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_load_ids_from_string_exception(mock_context):
    """Test load_ids from string handles exceptions."""
    with patch('ids_mcp_server.tools.document.ids.from_string', side_effect=RuntimeError("Parse error")):
        with pytest.raises(ToolError, match="Failed to load IDS"):
            await load_ids(
                source="<ids></ids>",
                source_type="string",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_export_ids_to_file_exception(mock_context):
    """Test export_ids to file handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)

    # Patch write to raise exception
    import builtins
    original_open = builtins.open

    def mock_open(*args, **kwargs):
        if args[0] == "/invalid/path/file.ids":
            raise PermissionError("Cannot write")
        return original_open(*args, **kwargs)

    with patch('builtins.open', side_effect=mock_open):
        with pytest.raises(ToolError, match="Failed to export IDS"):
            await export_ids(
                file_path="/invalid/path/file.ids",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_get_ids_info_empty_session(mock_context):
    """Test get_ids_info with empty session."""
    # This should create a new IDS
    result = await get_ids_info(ctx=mock_context)

    # Should return info about empty IDS
    assert "specifications_count" in result


# Specification Tool Edge Cases
@pytest.mark.asyncio
async def test_add_specification_exception_handling(mock_context):
    """Test add_specification handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)

    with patch('ids_mcp_server.tools.specification.ids.Specification', side_effect=RuntimeError("Spec error")):
        with pytest.raises(ToolError, match="Failed to add specification"):
            await add_specification(
                name="Test Spec",
                ifc_versions=["IFC4"],
                ctx=mock_context
            )


# Facet Edge Cases (uncovered lines)
@pytest.mark.asyncio
async def test_property_facet_without_property_set(mock_context):
    """Test add_property_facet without property_set raises ToolError."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add property without property_set should now raise ToolError
    with pytest.raises(ToolError) as exc_info:
        await add_property_facet(
            spec_id="S1",
            location="requirements",
            property_name="SomeProperty",
            ctx=mock_context
            # Note: no property_set parameter
        )

    assert "property_set" in str(exc_info.value).lower()
    assert "required" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_attribute_facet_without_value(mock_context):
    """Test add_attribute_facet without value (line 171 coverage)."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add attribute without value
    result = await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Description",
        ctx=mock_context
        # Note: no value parameter
    )

    assert result["status"] == "added"


@pytest.mark.asyncio
async def test_material_facet_without_cardinality(mock_context):
    """Test add_material_facet without explicit cardinality (line 284 coverage)."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add material to applicability (no cardinality)
    result = await add_material_facet(
        spec_id="S1",
        location="applicability",
        material_value="Concrete",
        ctx=mock_context
    )

    assert result["status"] == "added"


# Restriction Tool Error Paths
@pytest.mark.asyncio
async def test_enumeration_restriction_exception(mock_context):
    """Test add_enumeration_restriction handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="FireRating",
        property_set="Pset_WallCommon",
        ctx=mock_context
    )

    with patch('ids_mcp_server.tools.restrictions.ids.Restriction', side_effect=RuntimeError("Restriction error")):
        with pytest.raises(ToolError, match="Failed to add enumeration restriction"):
            await add_enumeration_restriction(
                spec_id="S1",
                location="requirements",
                facet_index=0,
                parameter="value",
                allowed_values=["REI60", "REI90"],
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_pattern_restriction_exception(mock_context):
    """Test add_pattern_restriction handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Name",
        ctx=mock_context
    )

    with patch('ids_mcp_server.tools.restrictions.ids.Restriction', side_effect=RuntimeError("Restriction error")):
        with pytest.raises(ToolError, match="Failed to add pattern restriction"):
            await add_pattern_restriction(
                spec_id="S1",
                location="requirements",
                facet_index=0,
                parameter="value",
                pattern="WALL.*",
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_bounds_restriction_exception(mock_context):
    """Test add_bounds_restriction handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="Height",
        property_set="Pset_WallCommon",
        ctx=mock_context
    )

    with patch('ids_mcp_server.tools.restrictions.ids.Restriction', side_effect=RuntimeError("Restriction error")):
        with pytest.raises(ToolError, match="Failed to add bounds restriction"):
            await add_bounds_restriction(
                spec_id="S1",
                location="requirements",
                facet_index=0,
                parameter="value",
                min_value=2.5,
                max_value=4.0,
                ctx=mock_context
            )


@pytest.mark.asyncio
async def test_length_restriction_exception(mock_context):
    """Test add_length_restriction handles exceptions."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Name",
        ctx=mock_context
    )

    with patch('ids_mcp_server.tools.restrictions.ids.Restriction', side_effect=RuntimeError("Restriction error")):
        with pytest.raises(ToolError, match="Failed to add length restriction"):
            await add_length_restriction(
                spec_id="S1",
                location="requirements",
                facet_index=0,
                parameter="value",
                min_length=1,
                max_length=100,
                ctx=mock_context
            )


# Validation Tool Edge Cases
@pytest.mark.asyncio
async def test_validate_ifc_model_json_parsing_error(mock_context):
    """Test validate_ifc_model handles JSON parsing errors."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create a minimal IFC file for testing
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        # Write minimal IFC header
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        # Patch JSON parsing to raise an exception
        with patch('json.loads', side_effect=ValueError("JSON parse error")):
            result = await validate_ifc_model(
                ifc_file_path=ifc_path,
                report_format="json",
                ctx=mock_context
            )

            # Should fall back to returning raw report
            assert result["status"] == "validation_complete"
            # Should have called warning about parsing error
            assert mock_context.warning.called
    finally:
        os.unlink(ifc_path)


@pytest.mark.asyncio
async def test_validate_ifc_model_html_format(mock_context):
    """Test validate_ifc_model with HTML format (line 242-250 coverage)."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create a minimal IFC file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        result = await validate_ifc_model(
            ifc_file_path=ifc_path,
            report_format="html",
            ctx=mock_context
        )

        # Should return HTML format
        assert result["format"] == "html"
        assert "html" in result
    finally:
        os.unlink(ifc_path)
