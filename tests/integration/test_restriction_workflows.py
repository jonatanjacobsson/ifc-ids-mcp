"""Integration tests for restriction workflows."""

import pytest
from ids_mcp_server.tools.document import create_ids, export_ids
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.facets import add_entity_facet, add_property_facet, add_attribute_facet
from ids_mcp_server.tools.restrictions import (
    add_enumeration_restriction,
    add_pattern_restriction,
    add_bounds_restriction,
    add_length_restriction
)
from ids_mcp_server.session.storage import get_session_storage
from ifctester import ids


@pytest.mark.asyncio
async def test_fire_safety_specification_workflow(mock_context):
    """
    Integration test: Fire safety wall specification with multiple restrictions.

    Scenario: Define requirements for fire-rated walls
    - Walls must be IFCWALL entities
    - FireRating must be REI30, REI60, or REI90 (enumeration)
    - Tag must match pattern EW-[0-9]{3}
    - Height must be between 2.4m and 3.5m (bounds)
    - Description must be 10-200 characters (length)
    """
    # Create IDS document
    await create_ids(
        title="Fire Safety Wall Requirements",
        ctx=mock_context,
        description="Requirements for fire-rated walls in commercial buildings"
    )

    # Add specification
    await add_specification(
        name="Fire-rated External Walls",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="FS-EW-001",
        description="External walls with fire rating requirements"
    )

    # Applicability: All walls
    await add_entity_facet(
        spec_id="FS-EW-001",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    # Requirement 1: FireRating property with enumeration restriction
    await add_property_facet(
        spec_id="FS-EW-001",
        location="requirements",
        property_name="FireRating",
        property_set="Pset_WallCommon",
        ctx=mock_context
    )

    await add_enumeration_restriction(
        spec_id="FS-EW-001",
        facet_index=0,  # First requirement
        parameter_name="value",
        base_type="xs:string",
        values=["REI30", "REI60", "REI90"],
        ctx=mock_context,
        location="requirements"
    )

    # Requirement 2: Tag attribute with pattern restriction
    await add_attribute_facet(
        spec_id="FS-EW-001",
        location="requirements",
        attribute_name="Tag",
        ctx=mock_context
    )

    await add_pattern_restriction(
        spec_id="FS-EW-001",
        facet_index=1,  # Second requirement
        parameter_name="value",
        base_type="xs:string",
        pattern="EW-[0-9]{3}",
        ctx=mock_context,
        location="requirements"
    )

    # Requirement 3: Height property with bounds restriction
    await add_property_facet(
        spec_id="FS-EW-001",
        location="requirements",
        property_name="Height",
        property_set="Pset_WallCommon",
        data_type="IFCREAL",
        ctx=mock_context
    )

    await add_bounds_restriction(
        spec_id="FS-EW-001",
        facet_index=2,  # Third requirement
        parameter_name="value",
        base_type="xs:double",
        min_inclusive=2.4,
        max_inclusive=3.5,
        ctx=mock_context,
        location="requirements"
    )

    # Requirement 4: Description attribute with length restriction
    await add_attribute_facet(
        spec_id="FS-EW-001",
        location="requirements",
        attribute_name="Description",
        ctx=mock_context
    )

    await add_length_restriction(
        spec_id="FS-EW-001",
        facet_index=3,  # Fourth requirement
        parameter_name="value",
        base_type="xs:string",
        min_length=10,
        max_length=200,
        ctx=mock_context,
        location="requirements"
    )

    # Verify IfcTester object structure
    storage = get_session_storage()
    session_data = storage.get(mock_context.session_id)
    ids_obj = session_data.ids_obj

    assert len(ids_obj.specifications) == 1
    spec = ids_obj.specifications[0]

    # Verify specification
    assert spec.name == "Fire-rated External Walls"
    assert len(spec.applicability) == 1
    assert len(spec.requirements) == 4

    # Verify enumeration restriction (FireRating)
    fire_rating = spec.requirements[0]
    assert isinstance(fire_rating, ids.Property)
    # IfcTester may store baseName as string or object
    base_name = fire_rating.baseName if isinstance(fire_rating.baseName, str) else fire_rating.baseName.simpleValue
    assert base_name == "FireRating"
    assert isinstance(fire_rating.value, ids.Restriction)
    assert fire_rating.value.base == "string"  # IfcTester normalizes

    # Verify pattern restriction (Tag)
    tag = spec.requirements[1]
    assert isinstance(tag, ids.Attribute)
    tag_name = tag.name if isinstance(tag.name, str) else tag.name.simpleValue
    assert tag_name == "Tag"
    assert isinstance(tag.value, ids.Restriction)

    # Verify bounds restriction (Height)
    height = spec.requirements[2]
    assert isinstance(height, ids.Property)
    height_name = height.baseName if isinstance(height.baseName, str) else height.baseName.simpleValue
    assert height_name == "Height"
    assert isinstance(height.value, ids.Restriction)
    assert height.value.base == "double"

    # Verify length restriction (Description)
    description = spec.requirements[3]
    assert isinstance(description, ids.Attribute)
    desc_name = description.name if isinstance(description.name, str) else description.name.simpleValue
    assert desc_name == "Description"
    assert isinstance(description.value, ids.Restriction)

    # Export to XML
    result = await export_ids(ctx=mock_context, validate=False)

    # Verify XML contains all restrictions
    xml = result["xml"]
    assert "<xs:enumeration" in xml
    assert 'value="REI30"' in xml
    assert 'value="REI60"' in xml
    assert 'value="REI90"' in xml
    assert "<xs:pattern" in xml
    assert 'value="EW-[0-9]{3}"' in xml
    assert "<xs:minInclusive" in xml or 'value="2.4"' in xml
    assert "<xs:maxInclusive" in xml or 'value="3.5"' in xml
    assert "<xs:minLength" in xml or 'value="10"' in xml
    assert "<xs:maxLength" in xml or 'value="200"' in xml

    # Verify IDS structure
    assert '<title>Fire Safety Wall Requirements</title>' in xml
    assert 'name="Fire-rated External Walls"' in xml


@pytest.mark.asyncio
async def test_multiple_specifications_with_restrictions(mock_context):
    """
    Integration test: Multiple specifications, each with different restrictions.

    Demonstrates managing complex IDS documents with multiple specs.
    """
    # Create IDS
    await create_ids(title="Building Standards", ctx=mock_context)

    # Specification 1: Wall heights
    await add_specification(
        name="Wall Heights",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="S1"
    )

    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="Height",
        property_set="Pset_WallCommon",  # Required for valid IDS
        ctx=mock_context
    )

    await add_bounds_restriction(
        spec_id="S1",
        facet_index=0,
        parameter_name="value",
        base_type="xs:double",
        min_inclusive=2.0,
        max_inclusive=4.0,
        ctx=mock_context,
        location="requirements"
    )

    # Specification 2: Door sizes
    await add_specification(
        name="Door Sizes",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="S2"
    )

    await add_entity_facet(
        spec_id="S2",
        location="applicability",
        entity_name="IFCDOOR",
        ctx=mock_context
    )

    await add_property_facet(
        spec_id="S2",
        location="requirements",
        property_name="Width",
        property_set="Pset_DoorCommon",  # Required for valid IDS
        ctx=mock_context
    )

    await add_enumeration_restriction(
        spec_id="S2",
        facet_index=0,
        parameter_name="value",
        base_type="xs:double",
        values=["0.8", "0.9", "1.0"],
        ctx=mock_context,
        location="requirements"
    )

    # Verify
    storage = get_session_storage()
    ids_obj = storage.get(mock_context.session_id).ids_obj

    assert len(ids_obj.specifications) == 2

    # Verify S1
    s1 = ids_obj.specifications[0]
    assert s1.name == "Wall Heights"
    assert len(s1.requirements) == 1
    assert isinstance(s1.requirements[0].value, ids.Restriction)

    # Verify S2
    s2 = ids_obj.specifications[1]
    assert s2.name == "Door Sizes"
    assert len(s2.requirements) == 1
    assert isinstance(s2.requirements[0].value, ids.Restriction)

    # Export
    result = await export_ids(ctx=mock_context, validate=False)
    assert result["status"] == "exported"
    assert "Wall Heights" in result["xml"]
    assert "Door Sizes" in result["xml"]


@pytest.mark.asyncio
async def test_restriction_on_different_parameters(mock_context):
    """
    Integration test: Apply restrictions to different facet parameters.

    Demonstrates that restrictions can be applied to various parameters,
    not just 'value'.
    """
    await create_ids(title="Advanced Restrictions", ctx=mock_context)

    await add_specification(
        name="Property Set Patterns",
        ifc_versions=["IFC4"],
        ctx=mock_context,
        identifier="ADV1"
    )

    await add_entity_facet(
        spec_id="ADV1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    # Add property with pattern restriction on propertySet parameter
    await add_property_facet(
        spec_id="ADV1",
        location="requirements",
        property_name=".*",  # Any property name
        ctx=mock_context,
        property_set="Pset_Common"
    )

    await add_pattern_restriction(
        spec_id="ADV1",
        facet_index=0,
        parameter_name="propertySet",  # Restrict the property set name, not value
        base_type="xs:string",
        pattern="Pset_.*",  # Only allow standard property sets
        ctx=mock_context,
        location="requirements"
    )

    # Verify restriction applied to propertySet parameter
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    assert isinstance(prop.propertySet, ids.Restriction)
    assert prop.propertySet.base == "string"

    # Verify baseName is still a simple value (not restricted)
    assert hasattr(prop.baseName, "simpleValue") or isinstance(prop.baseName, str)
