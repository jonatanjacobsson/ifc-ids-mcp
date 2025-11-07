# Implementation Plan: Advanced Facets (Classification, Material, PartOf)

**Branch**: `claude/006-advanced-facets` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement MCP tools for the three advanced IDS facets: Classification (classification systems), Material (material assignments), and PartOf (spatial relationships). These facets enable complex requirements for classification codes, material specifications, and structural hierarchy validation.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tools
- `ifctester` - `ids.Classification`, `ids.Material`, `ids.PartOf` classes

**Performance Goals**: Facet creation <5ms
**Constraints**:
- PartOf requires nested entity specification
- Classification systems must support URIs
- Material supports both names and URIs

**Scale/Scope**: Support 20+ advanced facets per specification

## Project Structure

```text
specs/006-advanced-facets/
└── plan.md

src/ids_mcp_server/tools/
└── advanced_facets.py   # Classification, Material, PartOf tools

tests/
├── unit/tools/
│   └── test_advanced_facet_tools.py
└── integration/
    └── test_advanced_facet_workflow.py
```

## Phase 1: Design

### Tool Contracts

```python
@mcp.tool
async def add_classification_facet(
    spec_id: str,
    location: str,
    classification_value: str,
    ctx: Context,
    classification_system: str = None,
    cardinality: str = "required"
) -> dict:
    """
    Add classification facet.

    Args:
        classification_value: Classification code or URI
        classification_system: Optional system name or URI

    Contract:
        - MUST create ids.Classification object
        - MUST support both simple codes and URIs
    """

@mcp.tool
async def add_material_facet(
    spec_id: str,
    location: str,
    material_value: str,
    ctx: Context,
    cardinality: str = "required"
) -> dict:
    """
    Add material facet.

    Args:
        material_value: Material name or URI

    Contract:
        - MUST create ids.Material object
        - MUST support material URIs (e.g., from bSDD)
    """

@mcp.tool
async def add_partof_facet(
    spec_id: str,
    location: str,
    relation: str,
    parent_entity: str,
    ctx: Context,
    parent_predefined_type: str = None,
    cardinality: str = "required"
) -> dict:
    """
    Add partOf facet for spatial relationships.

    Args:
        relation: IFC relationship type (e.g., "IFCRELCONTAINEDINSPATIALSTRUCTURE")
        parent_entity: Parent entity name
        parent_predefined_type: Optional parent type

    Contract:
        - MUST create ids.Entity for parent
        - MUST create ids.PartOf with entity reference
        - MUST support common relations
    """
```

## Phase 2: Test-Driven Implementation

### Classification Facet Tests

```python
@pytest.mark.asyncio
async def test_add_classification_facet():
    """Test adding classification with system."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        await client.call_tool("add_classification_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "classification_value": "EF_25_10_25",
            "classification_system": "Uniclass 2015",
            "cardinality": "required"
        })

        # Validate with IfcTester
        session_data = _session_storage.get(client.session_id)
        classif = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(classif, ids.Classification)
        assert classif.value == "EF_25_10_25"
        assert classif.system == "Uniclass 2015"
```

### Material Facet Tests

```python
@pytest.mark.asyncio
async def test_add_material_facet():
    """Test adding material facet."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        await client.call_tool("add_material_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "material_value": "Concrete",
            "cardinality": "required"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        material = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(material, ids.Material)
        assert material.value == "Concrete"
```

### PartOf Facet Tests

```python
@pytest.mark.asyncio
async def test_add_partof_facet():
    """Test adding partOf facet for spatial containment."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_test_spec(client)

        await client.call_tool("add_partof_facet", {
            "spec_id": "S1",
            "location": "requirements",
            "relation": "IFCRELCONTAINEDINSPATIALSTRUCTURE",
            "parent_entity": "IFCSPACE",
            "cardinality": "required"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        partof = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(partof, ids.PartOf)
        assert partof.relation == "IFCRELCONTAINEDINSPATIALSTRUCTURE"
        assert partof.entity.name == "IFCSPACE"
```

## Success Metrics

- ✅ All three advanced facets implemented
- ✅ PartOf correctly creates nested entity
- ✅ Test coverage ≥ 95%

## Next Steps

After Phase 006:
1. Proceed to **007-restrictions** - Implement value restrictions (enumeration, pattern, bounds)
