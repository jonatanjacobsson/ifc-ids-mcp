"""Tests for facet management tools."""

import pytest
from ifctester import ids
from ids_mcp_server.tools.facets import (
    add_entity_facet,
    add_property_facet,
    add_attribute_facet,
    add_classification_facet,
    add_material_facet,
    add_partof_facet
)
from ids_mcp_server.tools.specification import add_specification
from ids_mcp_server.tools.document import create_ids
from ids_mcp_server.session.storage import get_session_storage
from fastmcp.exceptions import ToolError


# Entity Facet Tests
@pytest.mark.asyncio
async def test_add_entity_facet_to_applicability(mock_context):
    """Test adding entity facet to applicability."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "entity"

    # Verify facet added
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.applicability) == 1
    assert isinstance(spec.applicability[0], ids.Entity)
    assert spec.applicability[0].name == "IFCWALL"


@pytest.mark.asyncio
async def test_add_entity_facet_with_predefined_type(mock_context):
    """Test adding entity facet with predefined type."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context,
        predefined_type="SOLIDWALL"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    entity = spec.applicability[0]
    assert entity.predefinedType == "SOLIDWALL"


@pytest.mark.asyncio
async def test_add_entity_facet_to_requirements(mock_context):
    """Test adding entity facet to requirements."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_entity_facet(
        spec_id="S1",
        location="requirements",
        entity_name="IFCDOOR",
        ctx=mock_context
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 1


@pytest.mark.asyncio
async def test_add_entity_facet_invalid_location(mock_context):
    """Test that invalid location raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_entity_facet(
            spec_id="S1",
            location="invalid",
            entity_name="IFCWALL",
            ctx=mock_context
        )

    assert "Invalid location" in str(exc_info.value)


# Property Facet Tests
@pytest.mark.asyncio
async def test_add_property_facet_minimal(mock_context):
    """Test adding property facet with minimal fields."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="FireRating",
        ctx=mock_context,
        property_set="Pset_WallCommon"
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "property"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 1
    assert isinstance(spec.requirements[0], ids.Property)
    assert spec.requirements[0].baseName == "FireRating"


@pytest.mark.asyncio
async def test_add_property_facet_complete(mock_context):
    """Test adding property facet with all fields."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="LoadBearing",
        ctx=mock_context,
        property_set="Pset_WallCommon",
        data_type="IFCBOOLEAN",
        value="TRUE",
        cardinality="required"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]

    assert prop.baseName == "LoadBearing"
    assert prop.propertySet == "Pset_WallCommon"
    assert prop.dataType == "IFCBOOLEAN"
    assert prop.value == "TRUE"
    assert prop.cardinality == "required"


# Attribute Facet Tests
@pytest.mark.asyncio
async def test_add_attribute_facet(mock_context):
    """Test adding attribute facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Name",
        ctx=mock_context,
        value="External Wall"
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "attribute"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 1
    assert isinstance(spec.requirements[0], ids.Attribute)
    assert spec.requirements[0].name == "Name"
    assert spec.requirements[0].value == "External Wall"


@pytest.mark.asyncio
async def test_add_attribute_facet_with_cardinality(mock_context):
    """Test adding attribute facet with cardinality."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_attribute_facet(
        spec_id="S1",
        location="requirements",
        attribute_name="Description",
        ctx=mock_context,
        cardinality="optional"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    attr = spec.requirements[0]
    assert attr.cardinality == "optional"


# Classification Facet Tests
@pytest.mark.asyncio
async def test_add_classification_facet(mock_context):
    """Test adding classification facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_classification_facet(
        spec_id="S1",
        location="requirements",
        classification_value="Ss_25_10_20",
        ctx=mock_context,
        classification_system="Uniclass"
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "classification"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 1
    assert isinstance(spec.requirements[0], ids.Classification)
    assert spec.requirements[0].value == "Ss_25_10_20"
    assert spec.requirements[0].system == "Uniclass"


@pytest.mark.asyncio
async def test_add_classification_facet_with_uri(mock_context):
    """Test adding classification with URI system."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_classification_facet(
        spec_id="S1",
        location="applicability",
        classification_value="23.30.10",
        ctx=mock_context,
        classification_system="https://identifier.buildingsmart.org/uri/buildingsmart/ifc-4.3/class/IfcWall"
    )

    assert result["status"] == "added"


# Material Facet Tests
@pytest.mark.asyncio
async def test_add_material_facet(mock_context):
    """Test adding material facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_material_facet(
        spec_id="S1",
        location="requirements",
        material_value="Concrete",
        ctx=mock_context
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "material"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 1
    assert isinstance(spec.requirements[0], ids.Material)
    assert spec.requirements[0].value == "Concrete"


@pytest.mark.asyncio
async def test_add_material_facet_with_cardinality(mock_context):
    """Test adding material facet with cardinality."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_material_facet(
        spec_id="S1",
        location="requirements",
        material_value="Steel",
        ctx=mock_context,
        cardinality="prohibited"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    material = spec.requirements[0]
    assert material.cardinality == "prohibited"


# PartOf Facet Tests
@pytest.mark.asyncio
async def test_add_partof_facet(mock_context):
    """Test adding partOf facet."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_partof_facet(
        spec_id="S1",
        location="applicability",
        relation="IFCRELCONTAINEDINSPATIALSTRUCTURE",
        parent_entity="IFCSPACE",
        ctx=mock_context
    )

    assert result["status"] == "added"
    assert result["facet_type"] == "partof"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.applicability) == 1
    assert isinstance(spec.applicability[0], ids.PartOf)
    assert spec.applicability[0].relation == "IFCRELCONTAINEDINSPATIALSTRUCTURE"


@pytest.mark.asyncio
async def test_add_partof_facet_with_predefined_type(mock_context):
    """Test adding partOf facet with parent predefined type."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    result = await add_partof_facet(
        spec_id="S1",
        location="requirements",
        relation="IFCRELAGGREGATES",
        parent_entity="IFCBUILDING",
        ctx=mock_context,
        parent_predefined_type="RESIDENTIAL",
        cardinality="required"
    )

    assert result["status"] == "added"

    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    part_of = spec.requirements[0]
    assert isinstance(part_of, ids.PartOf)
    assert part_of.predefinedType == "RESIDENTIAL"
    assert part_of.cardinality == "required"


# Test finding specification by name
@pytest.mark.asyncio
async def test_facet_finds_spec_by_name(mock_context):
    """Test that facets can find specification by name."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="My Specification", ifc_versions=["IFC4"], ctx=mock_context)

    # Should find by name
    result = await add_entity_facet(
        spec_id="My Specification",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    assert result["status"] == "added"


@pytest.mark.asyncio
async def test_facet_spec_not_found(mock_context):
    """Test that missing specification raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Spec 1", ifc_versions=["IFC4"], ctx=mock_context)

    with pytest.raises(ToolError) as exc_info:
        await add_entity_facet(
            spec_id="NonExistent",
            location="applicability",
            entity_name="IFCWALL",
            ctx=mock_context
        )

    assert "Specification not found" in str(exc_info.value)


# Test combining multiple facets
@pytest.mark.asyncio
async def test_multiple_facets_same_specification(mock_context):
    """Test adding multiple different facets to same specification."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add entity to applicability
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    # Add property to requirements
    await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="FireRating",
        ctx=mock_context,
        property_set="Pset_WallCommon"
    )

    # Add material to requirements
    await add_material_facet(
        spec_id="S1",
        location="requirements",
        material_value="Concrete",
        ctx=mock_context
    )

    # Verify all facets added
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]

    assert len(spec.applicability) == 1
    assert len(spec.requirements) == 2
    assert isinstance(spec.applicability[0], ids.Entity)
    assert isinstance(spec.requirements[0], ids.Property)
    assert isinstance(spec.requirements[1], ids.Material)


# Error handling tests for facets
@pytest.mark.asyncio
async def test_entity_facet_generic_error(mock_context):
    """Test entity facet handles generic errors."""
    await create_ids(title="Test IDS", ctx=mock_context)

    # Try to add facet to non-existent spec
    with pytest.raises(ToolError) as exc_info:
        await add_entity_facet(
            spec_id="NonExistent",
            location="applicability",
            entity_name="IFCWALL",
            ctx=mock_context
        )

    assert "Specification not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_property_facet_invalid_location_error(mock_context):
    """Test property facet with invalid location."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_property_facet(
            spec_id="S1",
            location="invalid_location",
            property_name="FireRating",
            ctx=mock_context,
            property_set="Pset_WallCommon"
        )

    assert "Invalid location" in str(exc_info.value)


@pytest.mark.asyncio
async def test_attribute_facet_invalid_location_error(mock_context):
    """Test attribute facet with invalid location."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_attribute_facet(
            spec_id="S1",
            location="wrong",
            attribute_name="Name",
            ctx=mock_context
        )

    assert "Invalid location" in str(exc_info.value)


@pytest.mark.asyncio
async def test_classification_facet_invalid_location_error(mock_context):
    """Test classification facet with invalid location."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_classification_facet(
            spec_id="S1",
            location="other",
            classification_value="Test",
            ctx=mock_context
        )

    assert "Invalid location" in str(exc_info.value)


@pytest.mark.asyncio
async def test_material_facet_invalid_location_error(mock_context):
    """Test material facet with invalid location."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    with pytest.raises(ToolError) as exc_info:
        await add_material_facet(
            spec_id="S1",
            location="somewhere",
            material_value="Concrete",
            ctx=mock_context
        )

    assert "Invalid location" in str(exc_info.value)


# Validation Error Tests (IDS 1.0 Constraints)
@pytest.mark.asyncio
async def test_add_second_entity_facet_to_applicability_raises_error(mock_context):
    """Test that adding second entity facet to applicability raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # First entity - should succeed
    await add_entity_facet(
        spec_id="S1",
        location="applicability",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    # Second entity - should fail with clear error
    with pytest.raises(ToolError) as exc_info:
        await add_entity_facet(
            spec_id="S1",
            location="applicability",
            entity_name="IFCDOOR",
            ctx=mock_context
        )

    error_msg = str(exc_info.value)
    assert "IDS 1.0 XSD constraint violation" in error_msg
    assert "Only ONE entity facet" in error_msg
    assert "WORKAROUND" in error_msg
    assert "separate specification" in error_msg


@pytest.mark.asyncio
async def test_add_multiple_entity_facets_to_requirements_allowed(mock_context):
    """Test that multiple entity facets in requirements is allowed."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Multiple entity facets in requirements - should succeed
    await add_entity_facet(
        spec_id="S1",
        location="requirements",
        entity_name="IFCWALL",
        ctx=mock_context
    )

    await add_entity_facet(
        spec_id="S1",
        location="requirements",
        entity_name="IFCDOOR",
        ctx=mock_context
    )

    # Verify both added
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    assert len(spec.requirements) == 2
    assert isinstance(spec.requirements[0], ids.Entity)
    assert isinstance(spec.requirements[1], ids.Entity)


@pytest.mark.asyncio
async def test_add_property_facet_without_property_set_raises_error(mock_context):
    """Test that property facet without property_set raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Try to add property without property_set
    with pytest.raises(ToolError) as exc_info:
        await add_property_facet(
            spec_id="S1",
            location="requirements",
            property_name="FireRating",
            ctx=mock_context,
            property_set=None  # Missing!
        )

    error_msg = str(exc_info.value)
    assert "property_set" in error_msg.lower()
    assert "required" in error_msg.lower()
    assert "COMMON PROPERTY SETS" in error_msg
    assert "Pset_WallCommon" in error_msg


@pytest.mark.asyncio
async def test_add_property_facet_with_empty_property_set_raises_error(mock_context):
    """Test that property facet with empty property_set raises error."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Try to add property with empty property_set
    with pytest.raises(ToolError) as exc_info:
        await add_property_facet(
            spec_id="S1",
            location="requirements",
            property_name="FireRating",
            ctx=mock_context,
            property_set=""  # Empty!
        )

    assert "property_set" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_property_facet_with_property_set_succeeds(mock_context):
    """Test that property facet with property_set succeeds."""
    await create_ids(title="Test IDS", ctx=mock_context)
    await add_specification(name="Test Spec", ifc_versions=["IFC4"], ctx=mock_context, identifier="S1")

    # Add property with proper property_set
    result = await add_property_facet(
        spec_id="S1",
        location="requirements",
        property_name="FireRating",
        ctx=mock_context,
        property_set="Pset_WallCommon"  # Provided!
    )

    assert result["status"] == "added"

    # Verify in session
    storage = get_session_storage()
    spec = storage.get(mock_context.session_id).ids_obj.specifications[0]
    prop = spec.requirements[0]
    assert prop.baseName == "FireRating"
    assert prop.propertySet == "Pset_WallCommon"
