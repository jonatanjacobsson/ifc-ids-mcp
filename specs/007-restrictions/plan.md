# Implementation Plan: Restriction Management

**Branch**: `claude/007-restrictions` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement MCP tools for adding value restrictions to facet parameters using XML Schema constraints. Restrictions enable precise value validation including enumerations (allowed values), patterns (regex), numeric bounds, and length constraints.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tools
- `ifctester` - `ids.Restriction` class

**Performance Goals**: Restriction creation <5ms
**Constraints**:
- Must support all XSD restriction types
- Must validate base types (xs:string, xs:integer, xs:double, etc.)
- Restrictions apply to facet values

**Scale/Scope**: Support multiple restrictions per facet parameter

## Project Structure

```text
specs/007-restrictions/
└── plan.md

src/ids_mcp_server/
├── tools/
│   └── restrictions.py      # Restriction tools
└── utils/
    └── restriction_helpers.py # Restriction builders

tests/
├── unit/tools/
│   └── test_restriction_tools.py
└── integration/
    └── test_restriction_workflow.py
```

## Phase 1: Design

### Tool Contracts

```python
@mcp.tool
async def add_enumeration_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    values: list[str],
    ctx: Context,
    location: str = "requirements"
) -> dict:
    """
    Add enumeration restriction (list of allowed values).

    Example: FireRating must be one of ["REI30", "REI60", "REI90"]

    Args:
        facet_index: Index of facet in location (0-based)
        parameter_name: Which parameter to restrict (e.g., "value")
        base_type: XSD base type (e.g., "xs:string")
        values: List of allowed values

    Contract:
        - MUST create ids.Restriction with enumeration
        - MUST apply to specified facet parameter
    """

@mcp.tool
async def add_pattern_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    pattern: str,
    ctx: Context,
    location: str = "requirements"
) -> dict:
    """
    Add pattern restriction (regex matching).

    Example: Name must match "EW-[0-9]{3}"

    Args:
        pattern: Regular expression pattern
    """

@mcp.tool
async def add_bounds_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    ctx: Context,
    location: str = "requirements",
    min_inclusive: float = None,
    max_inclusive: float = None,
    min_exclusive: float = None,
    max_exclusive: float = None
) -> dict:
    """
    Add numeric bounds restriction.

    Example: Height must be between 2.4 and 3.0 meters

    Args:
        min_inclusive: Minimum value (inclusive)
        max_inclusive: Maximum value (inclusive)
        min_exclusive: Minimum value (exclusive)
        max_exclusive: Maximum value (exclusive)
    """

@mcp.tool
async def add_length_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    ctx: Context,
    location: str = "requirements",
    length: int = None,
    min_length: int = None,
    max_length: int = None
) -> dict:
    """
    Add string length restriction.

    Example: Tag must be between 5 and 50 characters

    Args:
        length: Exact length
        min_length: Minimum length
        max_length: Maximum length
    """
```

## Phase 2: Test-Driven Implementation

### Enumeration Restriction Tests

```python
@pytest.mark.asyncio
async def test_add_enumeration_restriction():
    """Test adding enumeration restriction to property value."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Setup: Create spec with property facet
        await setup_spec_with_property_facet(client)

        # Add enumeration restriction to property value
        await client.call_tool("add_enumeration_restriction", {
            "spec_id": "S1",
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:string",
            "values": ["REI30", "REI60", "REI90"],
            "location": "requirements"
        })

        # Validate with IfcTester
        session_data = _session_storage.get(client.session_id)
        prop = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(prop.value, ids.Restriction)
        assert prop.value.base == "xs:string"
        assert "enumeration" in prop.value.options
        assert set(prop.value.options["enumeration"]) == {"REI30", "REI60", "REI90"}

@pytest.mark.asyncio
async def test_enumeration_exports_correctly():
    """Test that enumeration restriction exports to valid XML."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_spec_with_property_facet(client)

        await client.call_tool("add_enumeration_restriction", {
            "spec_id": "S1",
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:string",
            "values": ["Option1", "Option2"]
        })

        result = await client.call_tool("export_ids", {})

        # Validate XML
        validated_ids = ids.from_string(result["xml"], validate=True)
        prop = validated_ids.specifications[0].requirements[0]

        assert prop.value.options["enumeration"] == ["Option1", "Option2"]
```

### Pattern Restriction Tests

```python
@pytest.mark.asyncio
async def test_add_pattern_restriction():
    """Test adding regex pattern restriction."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_spec_with_attribute_facet(client)

        await client.call_tool("add_pattern_restriction", {
            "spec_id": "S1",
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:string",
            "pattern": "EW-[0-9]{3}"
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        attr = session_data.ids_obj.specifications[0].requirements[0]

        assert isinstance(attr.value, ids.Restriction)
        assert attr.value.options["pattern"] == "EW-[0-9]{3}"
```

### Bounds Restriction Tests

```python
@pytest.mark.asyncio
async def test_add_bounds_restriction():
    """Test adding numeric bounds restriction."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_spec_with_property_facet(client)

        await client.call_tool("add_bounds_restriction", {
            "spec_id": "S1",
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:double",
            "min_inclusive": 2.4,
            "max_inclusive": 3.0
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        prop = session_data.ids_obj.specifications[0].requirements[0]

        assert prop.value.base == "xs:double"
        assert prop.value.options["minInclusive"] == 2.4
        assert prop.value.options["maxInclusive"] == 3.0
```

### Length Restriction Tests

```python
@pytest.mark.asyncio
async def test_add_length_restriction():
    """Test adding string length restriction."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_spec_with_attribute_facet(client)

        await client.call_tool("add_length_restriction", {
            "spec_id": "S1",
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:string",
            "min_length": 5,
            "max_length": 50
        })

        # Validate
        session_data = _session_storage.get(client.session_id)
        attr = session_data.ids_obj.specifications[0].requirements[0]

        assert attr.value.options["minLength"] == 5
        assert attr.value.options["maxLength"] == 50
```

### Complete Workflow Test

```python
@pytest.mark.asyncio
async def test_complete_specification_with_restrictions():
    """
    Integration test: Complete specification with facets and restrictions.
    """
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create IDS and specification
        await client.call_tool("create_ids", {"title": "Restrictions Test"})
        result = await client.call_tool("add_specification", {
            "name": "Wall Fire Rating",
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
            "property_set": "Pset_WallCommon"
        })

        # Add enumeration restriction to property
        await client.call_tool("add_enumeration_restriction", {
            "spec_id": spec_id,
            "facet_index": 0,
            "parameter_name": "value",
            "base_type": "xs:string",
            "values": ["REI30", "REI60", "REI90", "REI120"]
        })

        # Export and validate
        result = await client.call_tool("export_ids", {})

        # Critical validation with IfcTester
        validated_ids = ids.from_string(result["xml"], validate=True)

        spec = validated_ids.specifications[0]
        prop = spec.requirements[0]

        assert isinstance(prop, ids.Property)
        assert prop.baseName == "FireRating"
        assert isinstance(prop.value, ids.Restriction)
        assert "enumeration" in prop.value.options
        assert "REI30" in prop.value.options["enumeration"]
```

## Success Metrics

- ✅ All restriction types implemented
- ✅ Restrictions apply to correct facet parameters
- ✅ Exported XML validates against XSD
- ✅ Test coverage ≥ 95%

## Next Steps

After Phase 007:
1. Proceed to **008-validation** - Implement IDS validation and IFC model validation tools
