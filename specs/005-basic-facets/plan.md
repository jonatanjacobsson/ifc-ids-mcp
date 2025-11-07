# Implementation Plan: Basic Facets (Entity, Property, Attribute)

**Branch**: `claude/005-basic-facets` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement MCP tools for adding the three most common IDS facets: Entity (IFC types), Property (property sets), and Attribute (IFC attributes). These facets form the foundation of most IDS specifications and are used in both applicability and requirements sections.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tools and Context
- `ifctester` - `ids.Entity`, `ids.Property`, `ids.Attribute` classes
- `pydantic` - Parameter validation

**Storage**: Session-based via Context
**Testing**: pytest with TDD, IfcTester validation
**Target Platform**: Cross-platform Python
**Project Type**: Single project
**Performance Goals**: Facet creation <5ms
**Constraints**:
- Must support all facet parameters per IDS spec
- Must handle applicability vs requirements location
- Must support cardinality for requirements

**Scale/Scope**: Support 50+ facets per specification

## Constitution Check

**Required Checks:**
- ✅ IfcTester supports all three facet types
- ✅ Facets can be added to applicability/requirements lists
- ✅ Cardinality only applies to requirements
- ✅ Entity names validated against IFC schema

## Project Structure

```text
specs/005-basic-facets/
├── plan.md
├── research.md          # IfcTester facet classes research
├── data-model.md        # Facet parameter models
└── contracts/           # Tool contracts

src/ids_mcp_server/
├── tools/
│   └── facets.py        # Facet management tools
└── utils/
    └── facet_helpers.py # Common facet operations

tests/
├── unit/tools/
│   └── test_facet_tools.py
└── integration/
    └── test_facet_workflow.py
```

## Phase 0: Research

**Research Questions:**
- How to create Entity facets with predefinedType?
- How to create Property facets with all parameters?
- How to create Attribute facets?
- When does cardinality apply?
- How to find and update facets in specification?

**Deliverable**: `research.md` with IfcTester facet examples

## Phase 1: Design

### Tool Parameter Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class AddEntityFacetParams(BaseModel):
    """Parameters for add_entity_facet tool."""
    spec_id: str = Field(..., description="Specification identifier")
    location: str = Field(..., description="'applicability' or 'requirements'")
    entity_name: str = Field(..., description="IFC entity name (e.g., 'IFCWALL')")
    predefined_type: Optional[str] = Field(None, description="Predefined type")
    cardinality: str = Field("required", description="Cardinality (requirements only)")

    @validator('location')
    def validate_location(cls, v):
        if v not in ["applicability", "requirements"]:
            raise ValueError("location must be 'applicability' or 'requirements'")
        return v

    @validator('entity_name')
    def validate_entity_name(cls, v):
        """Ensure entity name is uppercase."""
        return v.upper()

class AddPropertyFacetParams(BaseModel):
    """Parameters for add_property_facet tool."""
    spec_id: str
    location: str
    property_name: str = Field(..., description="Property base name")
    property_set: Optional[str] = Field(None, description="Property set name")
    data_type: Optional[str] = Field(None, description="IFC data type")
    property_location: str = Field("any", description="'instance', 'type', or 'any'")
    cardinality: str = Field("required")

    @validator('property_location')
    def validate_property_location(cls, v):
        if v not in ["instance", "type", "any"]:
            raise ValueError("property_location must be 'instance', 'type', or 'any'")
        return v

class AddAttributeFacetParams(BaseModel):
    """Parameters for add_attribute_facet tool."""
    spec_id: str
    location: str
    attribute_name: str = Field(..., description="Attribute name (e.g., 'Name')")
    cardinality: str = Field("required")
```

### Tool Contracts

```python
@mcp.tool
async def add_entity_facet(
    spec_id: str,
    location: str,
    entity_name: str,
    ctx: Context,
    predefined_type: str = None,
    cardinality: str = "required"
) -> dict:
    """
    Add entity facet to specification.

    Contract:
        - MUST create ids.Entity object
        - MUST find specification by spec_id
        - MUST append to correct location (applicability/requirements)
        - MUST uppercase entity_name
        - MUST ignore cardinality in applicability

    Returns:
        {
            "status": "added",
            "facet_type": "entity",
            "spec_id": "S1",
            "location": "applicability"
        }
    """

@mcp.tool
async def add_property_facet(
    spec_id: str,
    location: str,
    property_name: str,
    ctx: Context,
    property_set: str = None,
    data_type: str = None,
    property_location: str = "any",
    cardinality: str = "required"
) -> dict:
    """
    Add property facet to specification.

    Contract:
        - MUST create ids.Property object
        - MUST support optional property_set
        - MUST support optional data_type
        - MUST handle property_location (instance/type/any)
        - MUST apply cardinality only to requirements
    """

@mcp.tool
async def add_attribute_facet(
    spec_id: str,
    location: str,
    attribute_name: str,
    ctx: Context,
    cardinality: str = "required"
) -> dict:
    """
    Add attribute facet to specification.

    Contract:
        - MUST create ids.Attribute object
        - MUST support common attributes (Name, Description, Tag, etc.)
    """
```

## Phase 2: Test-Driven Implementation

### Milestone 1: Entity Facet Tool

**RED: Write failing tests**

```python
import pytest
from fastmcp.client import Client
from ifctester import ids

@pytest.mark.asyncio
async def test_add_entity_facet_to_applicability():
    """Test adding entity facet to applicability."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})
        result = await client.call_tool("add_specification", {
            "name": "Wall Spec",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # Add entity facet
        result = await client.call_tool("add_entity_facet", {
            "spec_id": spec_id,
            "location": "applicability",
            "entity_name": "IFCWALL"
        })

        assert result["status"] == "added"
        assert result["facet_type"] == "entity"

        # Validate with IfcTester
        from ids_mcp_server.session.storage import _session_storage
        session_data = _session_storage.get(client.session_id)
        spec = session_data.ids_obj.specifications[0]

        assert len(spec.applicability) == 1
        entity = spec.applicability[0]
        assert isinstance(entity, ids.Entity)
        assert entity.name == "IFCWALL"

@pytest.mark.asyncio
async def test_add_entity_facet_with_predefined_type():
    """Test entity facet with predefined type."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        result = await client.call_tool("add_entity_facet", {
            "spec_id": "S1",
            "location": "applicability",
            "entity_name": "IFCWALL",
            "predefined_type": "SOLIDWALL"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        entity = session_data.ids_obj.specifications[0].applicability[0]

        assert entity.predefinedType == "SOLIDWALL"

@pytest.mark.asyncio
async def test_entity_name_uppercased():
    """Test that entity names are automatically uppercased."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        await client.call_tool("add_entity_facet", {
            "spec_id": "S1",
            "location": "applicability",
            "entity_name": "ifcwall"  # lowercase
        })

        # Should be uppercased
        session_data = _session_storage.get(client.session_id)
        entity = session_data.ids_obj.specifications[0].applicability[0]
        assert entity.name == "IFCWALL"
```

**GREEN: Implementation**
1. Create `tools/facets.py`
2. Implement `add_entity_facet`
3. Use IfcTester `ids.Entity()`
4. Run tests → PASS

### Milestone 2: Property Facet Tool

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_add_property_facet_minimal():
    """Test adding property facet with minimal parameters."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        result = await client.call_tool("add_property_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "property_name": "FireRating"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        prop = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(prop, ids.Property)
        assert prop.baseName == "FireRating"
        assert prop.cardinality == "required"

@pytest.mark.asyncio
async def test_add_property_facet_full():
    """Test property facet with all parameters."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        result = await client.call_tool("add_property_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "property_name": "FireRating",
            "property_set": "Pset_WallCommon",
            "data_type": "IFCLABEL",
            "property_location": "type",
            "cardinality": "optional"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        prop = session_data.ids_obj.specifications[0].requirements[0]

        assert prop.baseName == "FireRating"
        assert prop.propertySet == "Pset_WallCommon"
        assert prop.dataType == "IFCLABEL"
        assert prop.cardinality == "optional"

@pytest.mark.asyncio
async def test_property_facet_exports_correctly():
    """Test that property facet exports to valid XML."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        await client.call_tool("add_property_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "property_name": "LoadBearing",
            "property_set": "Pset_WallCommon",
            "cardinality": "required"
        })

        result = await client.call_tool("export_ids", {})

        # Validate with IfcTester
        validated_ids = ids.from_string(result["xml"], validate=True)
        prop = validated_ids.specifications[0].requirements[0]

        assert prop.baseName == "LoadBearing"
        assert prop.propertySet == "Pset_WallCommon"
```

**GREEN: Implementation**
1. Implement `add_property_facet`
2. Use IfcTester `ids.Property()`
3. Run tests → PASS

### Milestone 3: Attribute Facet Tool

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_add_attribute_facet():
    """Test adding attribute facet."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        result = await client.call_tool("add_attribute_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "attribute_name": "Name",
            "cardinality": "required"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        attr = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(attr, ids.Attribute)
        assert attr.name == "Name"
        assert attr.cardinality == "required"

@pytest.mark.asyncio
async def test_common_attributes():
    """Test common IFC attributes."""
    common_attrs = ["Name", "Description", "Tag", "ObjectType"]

    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        for attr_name in common_attrs:
            await client.call_tool("add_attribute_facet", {
                "spec_id": "S1",
                "location": "requirements",
                "attribute_name": attr_name
            })

        # Verify all added
        session_data = _session_storage.get(client.session_id)
        spec = session_data.ids_obj.specifications[0]
        assert len(spec.requirements) == 4
```

**GREEN: Implementation**
1. Implement `add_attribute_facet`
2. Use IfcTester `ids.Attribute()`
3. Run tests → PASS

### Milestone 4: Complete Workflow Test

```python
@pytest.mark.asyncio
async def test_complete_specification_with_facets():
    """
    Integration test: Create complete specification with all facet types.
    """
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create IDS
        await client.call_tool("create_ids", {
            "title": "Complete Test",
            "author": "test@example.com"
        })

        # Add specification
        result = await client.call_tool("add_specification", {
            "name": "Wall Requirements",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # Add entity to applicability
        await client.call_tool("add_entity_facet", {
            "spec_id": spec_id,
            "location": "applicability",
            "entity_name": "IFCWALL"
        })

        # Add property to requirements
        await client.call_tool("add_property_facet", {
            "spec_id": spec_id,
            "location": "requirements",
            "property_name": "FireRating",
            "property_set": "Pset_WallCommon",
            "cardinality": "required"
        })

        # Add attribute to requirements
        await client.call_tool("add_attribute_facet", {
            "spec_id": spec_id,
            "location": "requirements",
            "attribute_name": "Name",
            "cardinality": "required"
        })

        # Export and validate
        result = await client.call_tool("export_ids", {})

        # Critical: Validate with IfcTester
        validated_ids = ids.from_string(result["xml"], validate=True)

        spec = validated_ids.specifications[0]
        assert len(spec.applicability) == 1
        assert len(spec.requirements) == 2
        assert isinstance(spec.applicability[0], ids.Entity)
        assert isinstance(spec.requirements[0], ids.Property)
        assert isinstance(spec.requirements[1], ids.Attribute)
```

## Phase 3: Validation

**Validation Checklist:**
- ✅ All three facet types implemented
- ✅ Facets can be added to both applicability and requirements
- ✅ Cardinality handled correctly
- ✅ Exported XML validates against XSD
- ✅ Test coverage ≥ 95%

## Success Metrics

- ✅ All tools respond in <5ms
- ✅ 100% XSD compliance
- ✅ Complete workflow test passes
- ✅ Test coverage ≥ 95%

## Next Steps

After Phase 005:
1. Proceed to **006-advanced-facets** - Implement Classification, Material, PartOf facets
2. These build on the same patterns as basic facets
