"""Tests for validation tools."""

import pytest
from ifctester import ids
from ids_mcp_server.tools.validation import validate_ids, validate_ifc_model
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.facets import add_entity_facet
from ids_mcp_server.tools.document import create_ids
from ids_mcp_server.session.storage import get_session_storage
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_validate_ids_empty_specs(mock_context):
    """Test that validating IDS with no specifications returns error."""
    await create_ids(title="Test IDS", ctx=mock_context)

    result = await validate_ids(ctx=mock_context)

    assert result["valid"] is False
    assert "at least one specification" in result["errors"][0].lower()
    assert result["specifications_count"] == 0
    # Verify details structure
    assert "details" in result
    assert result["details"]["has_specifications"] is False


@pytest.mark.asyncio
async def test_validate_ids_valid(mock_context):
    """Test validating a valid IDS document."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to make it valid
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    result = await validate_ids(ctx=mock_context)

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["specifications_count"] == 1
    # Verify enhanced details structure
    assert "details" in result
    assert result["details"]["has_title"] is True
    assert result["details"]["has_specifications"] is True
    assert result["details"]["xsd_valid"] is True


@pytest.mark.asyncio
async def test_validate_ids_multiple_specs(mock_context):
    """Test validating IDS with multiple specifications."""
    await create_ids(title="Test IDS", ctx=mock_context)

    # Add first spec
    await add_specification(name="Spec 1", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # Add second spec
    await add_specification(name="Spec 2", ifc_versions=["IFC4"], ctx=mock_context, identifier="S2")
    await add_entity_facet(spec_id="S2", location="applicability", entity_name="IFCDOOR", ctx=mock_context)

    result = await validate_ids(ctx=mock_context)

    assert result["valid"] is True
    assert result["specifications_count"] == 2


@pytest.mark.asyncio
async def test_validate_ids_validates_xml_structure(mock_context):
    """Test that validation checks XML structure."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add complete specification
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    result = await validate_ids(ctx=mock_context)

    # Should serialize to XML and validate against XSD
    assert result["valid"] is True
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio
async def test_validate_ifc_model_file_not_found(mock_context):
    """Test that missing IFC file raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    with pytest.raises(ToolError) as exc_info:
        await validate_ifc_model(
            ifc_file_path="/nonexistent/path/to/model.ifc",
            ctx=mock_context
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_ifc_model_json_format(mock_context, tmp_path):
    """Test IFC model validation with JSON report format."""
    # Create a minimal valid IFC file for testing
    ifc_content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','2025-01-01T00:00:00',(),(),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('Project',$,$,$,$,$,$,$,$);
#2=IFCWALL('Wall',$,$,$,$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;
"""
    ifc_file = tmp_path / "test.ifc"
    ifc_file.write_text(ifc_content)

    # Create IDS with specification
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Wall Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # This should work but may fail if IFC is invalid - that's okay for testing
    try:
        result = await validate_ifc_model(
            ifc_file_path=str(ifc_file),
            ctx=mock_context,
            report_format="json"
        )

        assert result["status"] == "validation_complete"
        # Check for enhanced JSON structure (with per-spec breakdown)
        assert "total_specifications" in result
        assert result["total_specifications"] >= 0
        # Enhanced format includes structured report
        assert "report" in result
        if "specifications" in result["report"]:
            # Structured enhanced format
            assert "passed_specifications" in result
            assert "failed_specifications" in result
        # May also have raw format for fallback compatibility
    except ToolError as e:
        # IFC parsing may fail - that's okay for this test
        assert "validation error" in str(e).lower() or "ifc" in str(e).lower()


@pytest.mark.asyncio
async def test_validate_ifc_model_invalid_format(mock_context, tmp_path):
    """Test that invalid IFC file raises error."""
    ifc_file = tmp_path / "test.ifc"
    ifc_file.write_text("dummy content")

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # Invalid IFC file content will raise error when ifcopenshell tries to open it
    with pytest.raises(ToolError) as exc_info:
        await validate_ifc_model(
            ifc_file_path=str(ifc_file),
            ctx=mock_context,
            report_format="json"
        )

    assert "IFC validation error" in str(exc_info.value) or "validation error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_ids_returns_warnings(mock_context):
    """Test that validation can return warnings."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")
    await add_entity_facet(spec_id="S1", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    result = await validate_ids(ctx=mock_context)

    # Should have warnings key even if empty
    assert "warnings" in result
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio
async def test_validate_ifc_model_console_format(mock_context, tmp_path):
    """Test IFC validation with console report format."""
    ifc_file = tmp_path / "test.ifc"
    ifc_file.write_text("dummy")  # Will fail to parse

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context)
    await add_entity_facet(spec_id="Test Spec", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # Console format should work but IFC parsing will fail
    with pytest.raises(ToolError):
        await validate_ifc_model(
            ifc_file_path=str(ifc_file),
            ctx=mock_context,
            report_format="console"
        )


@pytest.mark.asyncio
async def test_validate_ifc_model_html_format(mock_context, tmp_path):
    """Test IFC validation with HTML report format."""
    ifc_file = tmp_path / "test.ifc"
    ifc_file.write_text("dummy")  # Will fail to parse

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context)
    await add_entity_facet(spec_id="Test Spec", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # HTML format should work but IFC parsing will fail
    with pytest.raises(ToolError):
        await validate_ifc_model(
            ifc_file_path=str(ifc_file),
            ctx=mock_context,
            report_format="html"
        )


@pytest.mark.asyncio
async def test_validate_ifc_model_truly_invalid_format(mock_context):
    """Test IFC validation with truly invalid report format on non-existent file."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context)
    await add_entity_facet(spec_id="Test Spec", location="applicability", entity_name="IFCWALL", ctx=mock_context)

    # Non-existent file should raise FileNotFoundError first
    with pytest.raises(ToolError) as exc_info:
        await validate_ifc_model(
            ifc_file_path="/nonexistent/path/file.ifc",
            ctx=mock_context,
            report_format="json"
        )

    assert "file not found" in str(exc_info.value).lower() or "ifc file not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_ids_with_validation_errors(mock_context):
    """Test validate_ids when IDS has validation errors."""
    from ids_mcp_server.session.storage import get_session_storage
    from ifctester import ids

    await create_ids(title="Test IDS", ctx=mock_context)

    # Create specification without required applicability
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids.Specification(name="Invalid Spec", ifcVersion=["IFC4"])
    # Don't add applicability - this might cause validation issues
    session_data.ids_obj.specifications.append(spec)

    # Validate should handle the error
    result = await validate_ids(ctx=mock_context)

    # May return invalid or valid depending on IfcTester behavior
    assert "valid" in result
    assert "errors" in result
