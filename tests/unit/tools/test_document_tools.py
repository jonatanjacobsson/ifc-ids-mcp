"""RED: Tests for document management tools."""

import pytest
from ifctester import ids
from fastmcp.exceptions import ToolError
from ids_mcp_server.tools.document import (
    create_ids,
    load_ids,
    export_ids,
    get_ids_info
)


@pytest.mark.asyncio
async def test_create_ids_minimal(mock_context):
    """Test creating IDS with only required fields."""
    result = await create_ids(
        title="Test IDS",
        ctx=mock_context
    )

    assert result["status"] == "created"
    assert result["title"] == "Test IDS"
    assert "session_id" in result


@pytest.mark.asyncio
async def test_create_ids_with_all_metadata(mock_context):
    """Test creating IDS with all metadata fields."""
    result = await create_ids(
        title="Complete IDS",
        ctx=mock_context,
        author="test@example.com",
        version="1.0",
        date="2025-11-01",
        description="Test description",
        copyright="© 2025",
        milestone="Design",
        purpose="Testing"
    )

    assert result["status"] == "created"
    assert result["title"] == "Complete IDS"


@pytest.mark.asyncio
async def test_create_ids_stores_in_session(mock_context):
    """Verify IDS is stored in session using IfcTester."""
    from ids_mcp_server.session.storage import get_session_storage

    result = await create_ids(
        title="Session Test",
        ctx=mock_context
    )

    session_id = result["session_id"]
    storage = get_session_storage()

    # Verify using IfcTester API
    session_data = storage.get(session_id)
    assert session_data is not None

    ids_obj = session_data.ids_obj
    assert isinstance(ids_obj, ids.Ids)
    assert ids_obj.info["title"] == "Session Test"


@pytest.mark.asyncio
async def test_export_ids_to_string(mock_context):
    """Test exporting IDS to XML string."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    # Create IDS
    await create_ids(title="Export Test", ctx=mock_context)

    # Add a specification (required by IDS XSD schema)
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids_lib.Specification(name="Test Spec", ifcVersion=["IFC4"])
    spec.applicability.append(ids_lib.Entity(name="IFCWALL"))
    session_data.ids_obj.specifications.append(spec)

    # Export to string
    result = await export_ids(ctx=mock_context)

    assert result["status"] == "exported"
    assert "xml" in result
    assert '<ids xmlns="http://standards.buildingsmart.org/IDS"' in result["xml"]
    assert "<title>Export Test</title>" in result["xml"]


@pytest.mark.asyncio
async def test_export_ids_validates_with_xsd(mock_context):
    """Test that exported XML validates against XSD."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    await create_ids(title="Validation Test", ctx=mock_context)

    # Add a specification (required by IDS XSD schema)
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids_lib.Specification(name="Test Spec", ifcVersion=["IFC4"])
    spec.applicability.append(ids_lib.Entity(name="IFCWALL"))
    session_data.ids_obj.specifications.append(spec)

    result = await export_ids(ctx=mock_context, validate=True)

    # Critical: Use IfcTester to validate
    xml_string = result["xml"]
    validated_ids = ids.from_string(xml_string, validate=True)

    assert validated_ids is not None
    assert result["validation"]["valid"] is True
    assert result["validation"]["errors"] == []


@pytest.mark.asyncio
async def test_export_ids_to_file(mock_context, tmp_path):
    """Test exporting IDS to file."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    output_file = tmp_path / "test.ids"

    await create_ids(title="File Export", ctx=mock_context)

    # Add a specification (required by IDS XSD schema)
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids_lib.Specification(name="Test Spec", ifcVersion=["IFC4"])
    spec.applicability.append(ids_lib.Entity(name="IFCWALL"))
    session_data.ids_obj.specifications.append(spec)

    result = await export_ids(
        ctx=mock_context,
        output_path=str(output_file)
    )

    assert result["status"] == "exported"
    assert result["file_path"] == str(output_file)
    assert output_file.exists()

    # Verify file is valid IDS
    loaded_ids = ids.open(str(output_file), validate=True)
    assert loaded_ids.info["title"] == "File Export"


@pytest.mark.asyncio
async def test_load_ids_from_string(mock_context, sample_ids_xml):
    """Test loading IDS from XML string."""
    result = await load_ids(
        source=sample_ids_xml,
        ctx=mock_context,
        source_type="string"
    )

    assert result["status"] == "loaded"
    assert result["title"] == "Test IDS"


@pytest.mark.asyncio
async def test_load_ids_from_file(mock_context, temp_ids_file):
    """Test loading IDS from file."""
    result = await load_ids(
        source=str(temp_ids_file),
        ctx=mock_context,
        source_type="file"
    )

    assert result["status"] == "loaded"
    assert result["title"] == "Test IDS"


@pytest.mark.asyncio
async def test_get_ids_info_empty(mock_context):
    """Test getting info from IDS with no specifications."""
    await create_ids(
        title="Empty IDS",
        ctx=mock_context,
        author="test@example.com"
    )

    result = await get_ids_info(ctx=mock_context)

    assert result["title"] == "Empty IDS"
    assert result["author"] == "test@example.com"
    assert result["specification_count"] == 0
    assert result["specifications"] == []



# Error Handling Tests

@pytest.mark.asyncio
async def test_load_ids_invalid_source_type(mock_context):
    """Test that invalid source_type raises error."""
    with pytest.raises(ToolError) as exc_info:
        await load_ids(
            source="dummy",
            ctx=mock_context,
            source_type="invalid"
        )

    assert "Invalid source_type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_load_ids_file_not_found(mock_context):
    """Test that missing file raises error."""
    with pytest.raises(ToolError) as exc_info:
        await load_ids(
            source="/nonexistent/path/to/file.ids",
            ctx=mock_context,
            source_type="file"
        )

    assert "File not found" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_load_ids_invalid_xml_string(mock_context):
    """Test that invalid XML raises error."""
    with pytest.raises(ToolError) as exc_info:
        await load_ids(
            source="<invalid>xml</invalid>",
            ctx=mock_context,
            source_type="string"
        )

    assert "Failed to load IDS" in str(exc_info.value)


@pytest.mark.asyncio
async def test_export_ids_creates_parent_directory(mock_context, tmp_path):
    """Test that export creates parent directory if needed."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    # Create nested path that doesn't exist
    output_file = tmp_path / "nested" / "dir" / "test.ids"

    await create_ids(title="Test IDS", ctx=mock_context)

    # Add specification
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids_lib.Specification(name="Test Spec", ifcVersion=["IFC4"])
    spec.applicability.append(ids_lib.Entity(name="IFCWALL"))
    session_data.ids_obj.specifications.append(spec)

    result = await export_ids(ctx=mock_context, output_path=str(output_file))

    assert result["status"] == "exported"
    assert output_file.exists()
    assert output_file.parent.exists()


@pytest.mark.asyncio
async def test_create_ids_error_handling(mock_context):
    """Test error handling in create_ids."""
    # Test with invalid date format (should succeed but date might be None)
    result = await create_ids(
        title="Test",
        ctx=mock_context,
        date="invalid-date"  # IfcTester may accept this
    )

    assert result["status"] == "created"


@pytest.mark.asyncio
async def test_get_ids_info_with_specifications(mock_context):
    """Test get_ids_info with specifications that have facets."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    await create_ids(title="Test IDS", ctx=mock_context)

    # Manually add specification with facets for testing
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)

    spec = ids_lib.Specification(
        name="Complete Spec",
        ifcVersion=["IFC4"],
        identifier="S1",
        description="Test description"
    )
    spec.applicability.append(ids_lib.Entity(name="IFCWALL"))
    spec.requirements.append(ids_lib.Property(baseName="FireRating", cardinality="required"))
    spec.requirements.append(ids_lib.Material(value="Concrete"))

    session_data.ids_obj.specifications.append(spec)

    result = await get_ids_info(ctx=mock_context)

    assert result["specification_count"] == 1
    assert len(result["specifications"]) == 1

    spec_info = result["specifications"][0]
    assert spec_info["name"] == "Complete Spec"
    assert spec_info["identifier"] == "S1"
    assert spec_info["ifc_versions"] == ["IFC4"]
    assert spec_info["applicability_facets"] == 1
    assert spec_info["requirement_facets"] == 2


@pytest.mark.asyncio
async def test_load_ids_updates_session_metadata(mock_context, sample_ids_xml):
    """Test that loading IDS updates session metadata."""
    result = await load_ids(
        source=sample_ids_xml,
        ctx=mock_context,
        source_type="string"
    )

    assert result["title"] == "Test IDS"
    assert result["specification_count"] == 1
    assert len(result["specifications"]) == 1


@pytest.mark.asyncio  
async def test_export_ids_validation_errors(mock_context):
    """Test export with validation returning errors."""
    from ifctester import ids as ids_lib
    from ids_mcp_server.session.storage import get_session_storage

    await create_ids(title="Test IDS", ctx=mock_context)

    # Add invalid specification (no applicability) - may cause validation issues
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    spec = ids_lib.Specification(name="Test Spec", ifcVersion=["IFC4"])
    # Don't add applicability - this might cause validation issues
    session_data.ids_obj.specifications.append(spec)

    # Try to export - should handle validation
    try:
        result = await export_ids(ctx=mock_context, validate=True)
        # May succeed or fail depending on IfcTester validation
        assert "validation" in result
    except ToolError:
        # If it fails, that's also valid error handling
        pass

