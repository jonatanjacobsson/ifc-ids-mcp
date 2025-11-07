"""Quick tests to cover the last few uncovered lines for 95%+ coverage.

These tests target specific uncovered lines to push coverage over 95%.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ids_mcp_server.tools.document import create_ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.facets import add_property_facet, add_attribute_facet
from ids_mcp_server.session.storage import get_session_storage


@pytest.fixture
def mock_context():
    """Provide mock FastMCP Context for testing."""
    ctx = MagicMock()
    ctx.session_id = "test-coverage-booster"
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


# Facets.py lines 113, 171 - add to applicability instead of requirements
@pytest.mark.asyncio
async def test_property_facet_in_applicability(mock_context):
    """Test add_property_facet to applicability (line 113)."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add property to APPLICABILITY (not requirements)
    result = await add_property_facet(
        spec_id="S1",
        location="applicability",  # This covers line 113
        property_name="FireRating",
        property_set="Pset_WallCommon",
        ctx=mock_context
    )

    assert result["status"] == "added"

    # Verify it's in applicability
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.applicability) == 1


# Validation.py line 50 - missing title error
@pytest.mark.asyncio
async def test_validate_ids_no_title_error(mock_context):
    """Test validate_ids errors when IDS has no title (line 50)."""
    from ifctester import ids

    # Create IDS without title
    ids_obj = ids.Ids()
    ids_obj.info = {}  # No title

    storage = get_session_storage()
    from ids_mcp_server.session.models import SessionData
    storage.set(mock_context.session_id, SessionData(ids_obj=ids_obj))

    from ids_mcp_server.tools.validation import validate_ids
    result = await validate_ids(ctx=mock_context)

    # Should error about missing title (line 50)
    assert result["valid"] is False
    assert "title" in str(result["errors"]).lower()
    assert result["details"]["has_title"] is False


# Validation.py lines 175-176 - console format
@pytest.mark.asyncio
async def test_validate_ifc_model_console_format_path(mock_context):
    """Test validate_ifc_model with console format (lines 175-176)."""
    import tempfile
    import os

    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create minimal IFC file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        from ids_mcp_server.tools.validation import validate_ifc_model
        result = await validate_ifc_model(
            ifc_file_path=ifc_path,
            report_format="console",  # Covers lines 175-176
            ctx=mock_context
        )

        assert result["format"] == "console"
        assert result["status"] == "validation_complete"
    finally:
        os.unlink(ifc_path)


# Validation.py line 253 - invalid report format
@pytest.mark.asyncio
async def test_validate_ifc_model_truly_invalid_format(mock_context):
    """Test validate_ifc_model with invalid format (line 253)."""
    import tempfile
    import os
    from fastmcp.exceptions import ToolError

    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create minimal IFC file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        from ids_mcp_server.tools.validation import validate_ifc_model
        with pytest.raises(ToolError, match="Invalid report format"):
            await validate_ifc_model(
                ifc_file_path=ifc_path,
                report_format="xml",  # Invalid format - covers line 253
                ctx=mock_context
            )
    finally:
        os.unlink(ifc_path)


@pytest.mark.asyncio
async def test_attribute_facet_in_applicability(mock_context):
    """Test add_attribute_facet to applicability (line 171)."""
    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add attribute to APPLICABILITY (not requirements)
    result = await add_attribute_facet(
        spec_id="S1",
        location="applicability",  # This covers line 171
        attribute_name="Name",
        ctx=mock_context
    )

    assert result["status"] == "added"

    # Verify it's in applicability
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.applicability) == 1


# Validation.py line 50 - missing title error
@pytest.mark.asyncio
async def test_validate_ids_no_title_error(mock_context):
    """Test validate_ids errors when IDS has no title (line 50)."""
    from ifctester import ids

    # Create IDS without title
    ids_obj = ids.Ids()
    ids_obj.info = {}  # No title

    storage = get_session_storage()
    from ids_mcp_server.session.models import SessionData
    storage.set(mock_context.session_id, SessionData(ids_obj=ids_obj))

    from ids_mcp_server.tools.validation import validate_ids
    result = await validate_ids(ctx=mock_context)

    # Should error about missing title (line 50)
    assert result["valid"] is False
    assert "title" in str(result["errors"]).lower()
    assert result["details"]["has_title"] is False


# Validation.py lines 175-176 - console format
@pytest.mark.asyncio
async def test_validate_ifc_model_console_format_path(mock_context):
    """Test validate_ifc_model with console format (lines 175-176)."""
    import tempfile
    import os

    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create minimal IFC file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        from ids_mcp_server.tools.validation import validate_ifc_model
        result = await validate_ifc_model(
            ifc_file_path=ifc_path,
            report_format="console",  # Covers lines 175-176
            ctx=mock_context
        )

        assert result["format"] == "console"
        assert result["status"] == "validation_complete"
    finally:
        os.unlink(ifc_path)


# Validation.py line 253 - invalid report format
@pytest.mark.asyncio
async def test_validate_ifc_model_truly_invalid_format(mock_context):
    """Test validate_ifc_model with invalid format (line 253)."""
    import tempfile
    import os
    from fastmcp.exceptions import ToolError

    await create_ids(title="Test", ctx=mock_context)
    await add_specification(name="Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Create minimal IFC file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''), '2;1');\nFILE_NAME('', '', (''), (''), '', '', '');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        ifc_path = f.name

    try:
        from ids_mcp_server.tools.validation import validate_ifc_model
        with pytest.raises(ToolError, match="Invalid report format"):
            await validate_ifc_model(
                ifc_file_path=ifc_path,
                report_format="xml",  # Invalid format - covers line 253
                ctx=mock_context
            )
    finally:
        os.unlink(ifc_path)
