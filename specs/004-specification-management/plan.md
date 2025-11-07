# Implementation Plan: Specification Management

**Branch**: `claude/004-specification-management` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement MCP tool for adding and managing IDS specifications within IDS documents. Specifications define individual requirements with applicability and requirement sections, supporting all IFC versions and cardinality constraints.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tools and Context
- `ifctester` - `ids.Specification` class
- `pydantic` - Parameter validation

**Storage**: Session-based via Context
**Testing**: pytest with TDD, IfcTester validation
**Target Platform**: Cross-platform Python
**Project Type**: Single project
**Performance Goals**: Specification creation <10ms
**Constraints**:
- Must support all IFC versions (IFC2X3, IFC4, IFC4X3)
- Must validate IFC version strings
- Must support cardinality (minOccurs, maxOccurs)

**Scale/Scope**: Support 100+ specifications per IDS document

## Constitution Check

**Required Checks:**
- ✅ IfcTester `ids.Specification` supports all required fields
- ✅ Specifications can be added to `ids.Ids.specifications` list
- ✅ IFC version validation is implemented
- ✅ Cardinality attributes supported

## Project Structure

```text
specs/004-specification-management/
├── plan.md
├── research.md          # IfcTester Specification API
├── data-model.md        # Specification parameter models
└── contracts/           # Tool contracts

src/ids_mcp_server/tools/
└── specification.py     # Specification management tool

tests/
├── unit/tools/
│   └── test_specification_tools.py
└── integration/
    └── test_specification_workflow.py
```

## Phase 0: Research

**Research Questions:**
- What are required vs optional fields for `ids.Specification()`?
- How to validate IFC version strings?
- How does IfcTester handle minOccurs/maxOccurs?
- How to find specifications by identifier?

## Phase 1: Design

### Tool Parameter Model

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union

class AddSpecificationParams(BaseModel):
    """Parameters for add_specification tool."""
    name: str = Field(..., description="Specification name")
    ifc_versions: List[str] = Field(..., description="IFC versions (e.g., ['IFC4'])")
    identifier: Optional[str] = Field(None, description="Unique identifier")
    description: Optional[str] = Field(None, description="Why this is required")
    instructions: Optional[str] = Field(None, description="How to fulfill")
    min_occurs: int = Field(0, description="Minimum occurrences")
    max_occurs: Union[int, str] = Field("unbounded", description="Maximum occurrences")

    @validator('ifc_versions')
    def validate_ifc_versions(cls, v):
        """Validate IFC versions."""
        valid = {"IFC2X3", "IFC4", "IFC4X3"}
        for version in v:
            if version.upper() not in valid:
                raise ValueError(f"Invalid IFC version: {version}")
        return [version.upper() for version in v]

    @validator('min_occurs')
    def validate_min_occurs(cls, v):
        if v < 0:
            raise ValueError("min_occurs must be >= 0")
        return v
```

### Tool Contract

```python
@mcp.tool
async def add_specification(
    name: str,
    ifc_versions: list[str],
    ctx: Context,
    identifier: str = None,
    description: str = None,
    instructions: str = None,
    min_occurs: int = 0,
    max_occurs: int | str = "unbounded"
) -> dict:
    """
    Add specification to IDS document.

    Contract:
        - MUST create ids.Specification object
        - MUST validate IFC versions
        - MUST append to session IDS
        - MUST generate identifier if not provided
        - MUST return spec_id for subsequent operations

    Returns:
        {
            "status": "added",
            "spec_id": "S1" or provided identifier,
            "ifc_versions": ["IFC4"]
        }
    """
```

## Phase 2: Test-Driven Implementation

### RED: Write Failing Tests

```python
import pytest
from fastmcp.client import Client

@pytest.mark.asyncio
async def test_add_specification_minimal():
    """Test adding specification with minimal parameters."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})

        result = await client.call_tool("add_specification", {
            "name": "Wall Requirements",
            "ifc_versions": ["IFC4"]
        })

        assert result["status"] == "added"
        assert "spec_id" in result
        assert result["ifc_versions"] == ["IFC4"]

        # Validate using IfcTester
        from ids_mcp_server.session.storage import _session_storage
        from ifctester import ids

        session_data = _session_storage.get(client.session_id)
        ids_obj = session_data.ids_obj

        assert len(ids_obj.specifications) == 1
        spec = ids_obj.specifications[0]
        assert isinstance(spec, ids.Specification)
        assert spec.name == "Wall Requirements"
        assert spec.ifcVersion == ["IFC4"]

@pytest.mark.asyncio
async def test_add_specification_full():
    """Test adding specification with all parameters."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})

        result = await client.call_tool("add_specification", {
            "name": "Fire Rating",
            "ifc_versions": ["IFC4", "IFC4X3"],
            "identifier": "FR-001",
            "description": "All walls must have fire rating",
            "instructions": "Set Pset_WallCommon.FireRating",
            "min_occurs": 1,
            "max_occurs": "unbounded"
        })

        # Validate using IfcTester
        from ids_mcp_server.session.storage import _session_storage
        from ifctester import ids

        session_data = _session_storage.get(client.session_id)
        spec = session_data.ids_obj.specifications[0]

        assert spec.name == "Fire Rating"
        assert set(spec.ifcVersion) == {"IFC4", "IFC4X3"}
        assert spec.identifier == "FR-001"
        assert spec.description == "All walls must have fire rating"

@pytest.mark.asyncio
async def test_invalid_ifc_version():
    """Test that invalid IFC version raises error."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("add_specification", {
                "name": "Test",
                "ifc_versions": ["IFC99"]
            })

        assert "Invalid IFC version" in str(exc_info.value)

@pytest.mark.asyncio
async def test_multiple_specifications():
    """Test adding multiple specifications to same IDS."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})

        # Add 3 specifications
        await client.call_tool("add_specification", {
            "name": "Spec 1",
            "ifc_versions": ["IFC4"]
        })
        await client.call_tool("add_specification", {
            "name": "Spec 2",
            "ifc_versions": ["IFC4"]
        })
        await client.call_tool("add_specification", {
            "name": "Spec 3",
            "ifc_versions": ["IFC4X3"]
        })

        # Verify
        result = await client.call_tool("get_ids_info", {})
        assert result["specification_count"] == 3
```

### GREEN: Implementation

1. Create `tools/specification.py`
2. Implement `add_specification` tool
3. Use IfcTester `ids.Specification()`
4. Integrate with session management
5. Run tests → PASS

### REFACTOR

Extract specification finder helper:

```python
def find_specification(ids_obj: ids.Ids, spec_id: str) -> ids.Specification:
    """Find specification by identifier or name."""
    for spec in ids_obj.specifications:
        if getattr(spec, 'identifier', None) == spec_id:
            return spec
        if spec.name == spec_id:
            return spec
    raise ValueError(f"Specification not found: {spec_id}")
```

## Phase 3: Validation

**Validation Checklist:**
- ✅ Specifications created correctly
- ✅ IFC versions validated
- ✅ Multiple specifications supported
- ✅ Specifications persist in session
- ✅ Exported XML includes specifications
- ✅ Test coverage ≥ 95%

**XML Validation Test:**

```python
@pytest.mark.asyncio
async def test_specification_exports_correctly():
    """Test that specification exports to valid XML."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})
        await client.call_tool("add_specification", {
            "name": "Test Spec",
            "ifc_versions": ["IFC4"],
            "identifier": "TS-1"
        })

        result = await client.call_tool("export_ids", {})

        # Validate with IfcTester
        from ifctester import ids
        validated_ids = ids.from_string(result["xml"], validate=True)

        assert len(validated_ids.specifications) == 1
        assert validated_ids.specifications[0].name == "Test Spec"
```

## Success Metrics

- ✅ Tool responds in <10ms
- ✅ All IFC versions supported
- ✅ 100% XSD compliance
- ✅ Test coverage ≥ 95%

## Next Steps

After Phase 004:
1. Proceed to **005-basic-facets** - Implement Entity, Property, Attribute facets
2. Facets will be added to specifications created by this tool
