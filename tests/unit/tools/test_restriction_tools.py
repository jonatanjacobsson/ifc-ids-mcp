"""RED: Tests for restriction management tools."""

import pytest
from ifctester import ids
from ids_mcp_server.tools.restrictions import (
    add_enumeration_restriction,
    add_pattern_restriction,
    add_bounds_restriction,
    add_length_restriction
)
from ids_mcp_server.tools.document import create_ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.facets import add_property_facet, add_attribute_facet, add_entity_facet
from ids_mcp_server.session.storage import get_session_storage
from fastmcp.exceptions import ToolError


# Enumeration Restriction Tests
@pytest.mark.asyncio
async def test_add_enumeration_restriction_to_property(mock_context):
    """Test adding enumeration restriction to property facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add property facet to requirements
    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="FireRating",
        ctx=mock_context,
        property_set="Pset_WallCommon"
    )

    # Add enumeration restriction to property value
    result = await add_enumeration_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        values=["REI30", "REI60", "REI90"],
        ctx=mock_context,
        location="requirements"
    )

    assert result["status"] == "added"
    assert result["restriction_type"] == "enumeration"

    # Verify restriction with IfcTester
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    assert isinstance(prop.value, ids.Restriction)
    # IfcTester stores base without 'xs:' prefix internally
    assert prop.value.base == "string"
    # Check enumeration values are stored
    assert hasattr(prop.value, "enumeration") or "enumeration" in getattr(prop.value, "options", {})


@pytest.mark.asyncio
async def test_enumeration_restriction_exports_to_xml(mock_context):
    """Test that enumeration restriction exports to valid XML."""
    from ids_mcp_server.tools.document import export_ids

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to applicability (required by IDS XSD)
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="LoadBearing",
        ctx=mock_context,
        property_set="Pset_WallCommon"
    )

    await add_enumeration_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        values=["TRUE", "FALSE"],
        ctx=mock_context
    )

    # Export to XML (skip XSD validation due to IfcTester namespace bug)
    result = await export_ids(ctx=mock_context, validate=False)

    # Verify XML contains restriction elements
    assert result["status"] == "exported"
    assert "<xs:restriction" in result["xml"]
    assert "<xs:enumeration" in result["xml"]
    assert 'value="TRUE"' in result["xml"]
    assert 'value="FALSE"' in result["xml"]


@pytest.mark.asyncio
async def test_enumeration_restriction_invalid_facet_index(mock_context):
    """Test that invalid facet index raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Don't add any facets

    with pytest.raises(ToolError) as exc_info:
        await add_enumeration_restriction(
            spec_id="S1",
            facet_index=0,
            parameter_name="value",
            base_type="xs:string",
            values=["A", "B"],
            ctx=mock_context
        )

    assert "facet index" in str(exc_info.value).lower() or "out of range" in str(exc_info.value).lower()


# Pattern Restriction Tests
@pytest.mark.asyncio
async def test_add_pattern_restriction_to_attribute(mock_context):
    """Test adding pattern restriction to attribute facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Name",
        ctx=mock_context
    )

    result = await add_pattern_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        pattern="EW-[0-9]{3}",
        ctx=mock_context
    )

    assert result["status"] == "added"
    assert result["restriction_type"] == "pattern"

    # Verify with IfcTester
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    attr = spec.requirements[0]

    assert isinstance(attr.value, ids.Restriction)
    # IfcTester stores base without 'xs:' prefix internally
    assert attr.value.base == "string"
    # Check pattern is stored
    assert hasattr(attr.value, "pattern") or "pattern" in getattr(attr.value, "options", {})


@pytest.mark.asyncio
async def test_pattern_restriction_exports_to_xml(mock_context):
    """Test that pattern restriction exports to valid XML."""
    from ids_mcp_server.tools.document import export_ids

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to applicability (required by IDS XSD)
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Tag",
        ctx=mock_context
    )

    await add_pattern_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        pattern="[A-Z]{2}-[0-9]{4}",
        ctx=mock_context
    )

    # Export to XML (skip XSD validation due to IfcTester namespace bug)
    result = await export_ids(ctx=mock_context, validate=False)

    # Verify XML contains restriction elements
    assert result["status"] == "exported"
    assert "<xs:restriction" in result["xml"]
    assert "<xs:pattern" in result["xml"]
    assert 'value="[A-Z]{2}-[0-9]{4}"' in result["xml"]


# Bounds Restriction Tests
@pytest.mark.asyncio
async def test_add_bounds_restriction_min_max_inclusive(mock_context):
    """Test adding bounds restriction with min/max inclusive."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="Height",
        ctx=mock_context,
        property_set="Pset_WallCommon",
        data_type="IFCREAL"
    )

    result = await add_bounds_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:double",
        ctx=mock_context,
        min_inclusive=2.4,
        max_inclusive=3.0
    )

    assert result["status"] == "added"
    assert result["restriction_type"] == "bounds"

    # Verify with IfcTester
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    assert isinstance(prop.value, ids.Restriction)
    # IfcTester stores base without 'xs:' prefix internally
    assert prop.value.base == "double"
    # Check bounds are stored
    options = getattr(prop.value, "options", {})
    assert "minInclusive" in options or hasattr(prop.value, "minInclusive")
    assert "maxInclusive" in options or hasattr(prop.value, "maxInclusive")


@pytest.mark.asyncio
async def test_add_bounds_restriction_exclusive(mock_context):
    """Test adding bounds restriction with exclusive bounds."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="Temperature",
        ctx=mock_context,
        property_set="Pset_Common",
        data_type="IFCREAL"
    )

    result = await add_bounds_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:double",
        ctx=mock_context,
        min_exclusive=0.0,
        max_exclusive=100.0
    )

    assert result["status"] == "added"

    # Verify with IfcTester
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    assert isinstance(prop.value, ids.Restriction)


@pytest.mark.asyncio
async def test_bounds_restriction_exports_to_xml(mock_context):
    """Test that bounds restriction exports to valid XML."""
    from ids_mcp_server.tools.document import export_ids

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to applicability (required by IDS XSD)
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="Width",
        ctx=mock_context,
        property_set="Pset_WallCommon",
        data_type="IFCREAL"
    )

    await add_bounds_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:double",
        ctx=mock_context,
        min_inclusive=0.1,
        max_inclusive=0.5
    )

    # Export to XML (skip XSD validation due to IfcTester namespace bug)
    result = await export_ids(ctx=mock_context, validate=False)

    # Verify XML contains restriction elements
    assert result["status"] == "exported"
    assert "<xs:restriction" in result["xml"]
    assert "<xs:minInclusive" in result["xml"] or "<xs:maxInclusive" in result["xml"]


# Length Restriction Tests
@pytest.mark.asyncio
async def test_add_length_restriction_min_max(mock_context):
    """Test adding length restriction with min/max."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Description",
        ctx=mock_context
    )

    result = await add_length_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        ctx=mock_context,
        min_length=5,
        max_length=50
    )

    assert result["status"] == "added"
    assert result["restriction_type"] == "length"

    # Verify with IfcTester
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    attr = spec.requirements[0]

    assert isinstance(attr.value, ids.Restriction)
    # IfcTester stores base without 'xs:' prefix internally
    assert attr.value.base == "string"


@pytest.mark.asyncio
async def test_add_length_restriction_exact(mock_context):
    """Test adding exact length restriction."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Tag",
        ctx=mock_context
    )

    result = await add_length_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        ctx=mock_context,
        length=10
    )

    assert result["status"] == "added"


@pytest.mark.asyncio
async def test_length_restriction_exports_to_xml(mock_context):
    """Test that length restriction exports to valid XML."""
    from ids_mcp_server.tools.document import export_ids

    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to applicability (required by IDS XSD)
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Name",
        ctx=mock_context
    )

    await add_length_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:string",
        ctx=mock_context,
        min_length=1,
        max_length=100
    )

    # Export to XML (skip XSD validation due to IfcTester namespace bug)
    result = await export_ids(ctx=mock_context, validate=False)

    # Verify XML contains restriction elements
    assert result["status"] == "exported"
    assert "<xs:restriction" in result["xml"]
    assert "<xs:minLength" in result["xml"] or "<xs:maxLength" in result["xml"]


# Error Handling Tests
@pytest.mark.asyncio
async def test_restriction_spec_not_found(mock_context):
    """Test that missing specification raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)

    with pytest.raises(ToolError) as exc_info:
        await add_enumeration_restriction(
            spec_id="NonExistent",
            facet_index=0,
            parameter_name="value",
            base_type="xs:string",
            values=["A"],
            ctx=mock_context
        )

    assert "Specification not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_restriction_invalid_location(mock_context):
    """Test that invalid location raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_pattern_restriction(
            spec_id="S1",
            facet_index=0,
            parameter_name="value",
            base_type="xs:string",
            pattern=".*",
            ctx=mock_context,
            location="invalid"
        )

    assert "Invalid location" in str(exc_info.value)


# Test applying restrictions to different parameters
@pytest.mark.asyncio
async def test_restriction_on_property_set_parameter(mock_context):
    """Test adding restriction to propertySet parameter."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name=".*",
        ctx=mock_context,
        property_set="Pset_Common"
    )

    # Restrict property set name
    result = await add_pattern_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="propertySet",
        base_type="xs:string",
        pattern="Pset_.*",
        ctx=mock_context
    )

    assert result["status"] == "added"

    # Verify restriction applied to propertySet, not value
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    # The restriction should be on propertySet parameter
    assert hasattr(prop, "propertySet") and isinstance(prop.propertySet, ids.Restriction)
