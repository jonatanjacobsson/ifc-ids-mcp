# Implementation Plan: Document Management Tools

**Branch**: `claude/003-document-management` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement MCP tools for creating, loading, exporting, and inspecting IDS documents using IfcTester library. These tools provide the foundation for AI agents to perform CRUD operations on IDS files with automatic session management via FastMCP Context.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tool decorators and Context
- `ifctester` - IDS document creation, loading, and export
- `pydantic` - Tool parameter validation

**Storage**: Session-based (from 002-session-management)
**Testing**: pytest with TDD, IfcTester validation
**Target Platform**: Cross-platform Python
**Project Type**: Single project
**Performance Goals**:
- Document creation <10ms
- File export <100ms for typical IDS
- File loading <200ms

**Constraints**:
- Must produce 100% IDS 1.0 compliant XML
- All exports must validate against XSD schema
- Tools must use Context for automatic session management

**Scale/Scope**:
- Support IDS files up to 10MB
- Handle 100+ specifications per IDS
- Export to file or return XML string

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks:**

- ✅ IfcTester supports IDS creation via `ids.Ids()`
- ✅ IfcTester can export via `to_xml()` and `to_string()`
- ✅ IfcTester can load via `ids.open()` and `ids.from_string()`
- ✅ All exports validate against official XSD schema
- ✅ Tools integrate with session management

**Post-Design Checks:**

- ✅ All 4 core tools implemented (create, load, export, info)
- ✅ Generated XML validates against IDS 1.0 XSD
- ✅ Round-trip test passes (create → export → load → export)

## Project Structure

### Documentation (this feature)

```text
specs/003-document-management/
├── plan.md              # This file
├── research.md          # IfcTester IDS API research
├── data-model.md        # Tool parameter models
├── quickstart.md        # Usage examples
├── contracts/           # Tool contracts
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/ids_mcp_server/
├── tools/
│   ├── __init__.py
│   └── document.py          # Document management tools
├── validation/
│   ├── __init__.py
│   └── xsd.py               # XSD schema validation

tests/
├── unit/
│   └── tools/
│       └── test_document_tools.py
├── integration/
│   └── test_document_workflow.py
└── validation/
    ├── test_xsd_compliance.py
    └── fixtures/
        └── sample_ids_files/
```

**Structure Decision**: Created `tools/` module for all MCP tools, starting with document tools. Separate `validation/` module for XSD validation logic.

---

## Phase 0: Research

**Objectives:**
1. Verify IfcTester IDS creation API
2. Test IDS export methods (to_xml, to_string)
3. Test IDS loading methods (open, from_string)
4. Verify XSD validation capabilities
5. Test info metadata extraction

**Research Questions:**
- What are required fields for `ids.Ids()` constructor?
- How to set IDS info metadata (title, author, etc.)?
- Does IfcTester validate automatically on export?
- Can we validate without exporting to file?
- How to extract IDS structure for introspection tool?

**Deliverable**: `research.md` with IfcTester API examples

---

## Phase 1: Design

**Objectives:**
1. Design tool parameter schemas (Pydantic models)
2. Define tool response formats
3. Design XSD validation integration
4. Create tool contracts
5. Define error handling patterns

**Design Artifacts:**

### 1. Tool Parameter Models (`data-model.md`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

class CreateIDSParams(BaseModel):
    """Parameters for create_ids tool."""
    title: str = Field(..., description="IDS document title")
    author: Optional[str] = Field(None, description="Author email or name")
    version: Optional[str] = Field(None, description="Version identifier")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    description: Optional[str] = Field(None, description="Document description")
    copyright: Optional[str] = Field(None, description="Copyright notice")
    milestone: Optional[str] = Field(None, description="Project milestone")
    purpose: Optional[str] = Field(None, description="Purpose of IDS")

    @validator('date')
    def validate_date_format(cls, v):
        """Validate date is YYYY-MM-DD format."""
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class LoadIDSParams(BaseModel):
    """Parameters for load_ids tool."""
    source: str = Field(..., description="File path or XML string")
    source_type: str = Field("file", description="'file' or 'string'")

    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in ["file", "string"]:
            raise ValueError("source_type must be 'file' or 'string'")
        return v

class ExportIDSParams(BaseModel):
    """Parameters for export_ids tool."""
    output_path: Optional[str] = Field(None, description="File path (optional)")
    validate: bool = Field(True, description="Validate against XSD")
```

### 2. Tool Contracts (`contracts/`)

**create_ids Contract:**

```python
@mcp.tool
async def create_ids(
    title: str,
    ctx: Context,
    author: str = None,
    version: str = None,
    date: str = None,
    description: str = None,
    copyright: str = None,
    milestone: str = None,
    purpose: str = None
) -> dict:
    """
    Create a new IDS document for this session.

    Contract:
        - MUST create ids.Ids object with provided metadata
        - MUST store in session via ctx.session_id
        - MUST replace any existing IDS in session
        - MUST log creation via ctx.info()
        - MUST return session_id and title

    Returns:
        {
            "status": "created",
            "session_id": "auto-generated",
            "title": "..."
        }
    """
```

**load_ids Contract:**

```python
@mcp.tool
async def load_ids(
    source: str,
    ctx: Context,
    source_type: str = "file"
) -> dict:
    """
    Load existing IDS file into session.

    Contract:
        - MUST use ids.open() for files
        - MUST use ids.from_string() for XML strings
        - MUST validate file exists before loading
        - MUST handle XML parsing errors
        - MUST replace existing session IDS
        - MUST return IDS metadata

    Returns:
        {
            "status": "loaded",
            "title": "...",
            "specification_count": 3,
            "specifications": [
                {"name": "...", "identifier": "..."},
                ...
            ]
        }
    """
```

**export_ids Contract:**

```python
@mcp.tool
async def export_ids(
    ctx: Context,
    output_path: str = None,
    validate: bool = True
) -> dict:
    """
    Export IDS document to XML.

    Contract:
        - MUST use to_xml(path) if output_path provided
        - MUST use to_string() if no output_path
        - MUST validate against XSD if validate=True
        - MUST handle write permission errors
        - MUST return XML string or file path

    Returns (with output_path):
        {
            "status": "exported",
            "file_path": "...",
            "validation": {"valid": true, "errors": []}
        }

    Returns (without output_path):
        {
            "status": "exported",
            "xml": "...",
            "validation": {"valid": true, "errors": []}
        }
    """
```

**get_ids_info Contract:**

```python
@mcp.tool
async def get_ids_info(ctx: Context) -> dict:
    """
    Get IDS document structure.

    Contract:
        - MUST return IDS metadata
        - MUST return specification summary
        - MUST handle empty IDS gracefully

    Returns:
        {
            "title": "...",
            "author": "...",
            "specification_count": 3,
            "specifications": [
                {
                    "identifier": "S1",
                    "name": "Wall Fire Rating",
                    "ifc_versions": ["IFC4"],
                    "applicability_facets": 1,
                    "requirement_facets": 2
                },
                ...
            ]
        }
    """
```

---

## Phase 2: Test-Driven Implementation

**TDD Workflow**: Red → Green → Refactor for each tool

### Milestone 1: create_ids Tool

**RED: Write failing tests**

```python
# tests/unit/tools/test_document_tools.py
import pytest
from fastmcp import FastMCP
from fastmcp.client import Client
from ifctester import ids

@pytest.mark.asyncio
async def test_create_ids_minimal():
    """Test creating IDS with only required fields."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool("create_ids", {
            "title": "Test IDS"
        })

        assert result["status"] == "created"
        assert result["title"] == "Test IDS"
        assert "session_id" in result

@pytest.mark.asyncio
async def test_create_ids_with_all_metadata():
    """Test creating IDS with all metadata fields."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool("create_ids", {
            "title": "Complete IDS",
            "author": "test@example.com",
            "version": "1.0",
            "date": "2025-11-01",
            "description": "Test description",
            "copyright": "© 2025",
            "milestone": "Design",
            "purpose": "Testing"
        })

        assert result["status"] == "created"
        assert result["title"] == "Complete IDS"

@pytest.mark.asyncio
async def test_create_ids_stores_in_session():
    """Verify IDS is stored in session using IfcTester."""
    from ids_mcp_server.session.storage import _session_storage

    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool("create_ids", {
            "title": "Session Test"
        })

        session_id = result["session_id"]

        # Verify using IfcTester API
        session_data = _session_storage.get(session_id)
        assert session_data is not None

        ids_obj = session_data.ids_obj
        assert isinstance(ids_obj, ids.Ids)
        assert ids_obj.info["title"] == "Session Test"
```

**GREEN: Implementation**
1. Create `tools/document.py`
2. Implement `create_ids` tool
3. Integrate with session manager
4. Run tests → PASS

**REFACTOR**: Extract common patterns

### Milestone 2: export_ids Tool

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_export_ids_to_string():
    """Test exporting IDS to XML string."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create IDS
        await client.call_tool("create_ids", {"title": "Export Test"})

        # Export to string
        result = await client.call_tool("export_ids", {})

        assert result["status"] == "exported"
        assert "xml" in result
        assert '<?xml version="1.0"' in result["xml"]
        assert "<ids:title>Export Test</ids:title>" in result["xml"]

@pytest.mark.asyncio
async def test_export_ids_validates_with_xsd():
    """Test that exported XML validates against XSD."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Validation Test"})

        result = await client.call_tool("export_ids", {
            "validate": True
        })

        # Critical: Use IfcTester to validate
        from ifctester import ids
        xml_string = result["xml"]
        validated_ids = ids.from_string(xml_string, validate=True)

        assert validated_ids is not None
        assert result["validation"]["valid"] == True
        assert result["validation"]["errors"] == []

@pytest.mark.asyncio
async def test_export_ids_to_file(tmp_path):
    """Test exporting IDS to file."""
    mcp = create_test_server()
    output_file = tmp_path / "test.ids"

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "File Export"})

        result = await client.call_tool("export_ids", {
            "output_path": str(output_file)
        })

        assert result["status"] == "exported"
        assert result["file_path"] == str(output_file)
        assert output_file.exists()

        # Verify file is valid IDS
        from ifctester import ids
        loaded_ids = ids.open(str(output_file), validate=True)
        assert loaded_ids.info["title"] == "File Export"
```

**GREEN: Implementation**
1. Implement `export_ids` tool
2. Add XSD validation
3. Handle file writing
4. Run tests → PASS

### Milestone 3: load_ids Tool

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_load_ids_from_string():
    """Test loading IDS from XML string."""
    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://standards.buildingsmart.org/IDS
                                 http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
        <ids:info>
            <ids:title>Loaded IDS</ids:title>
        </ids:info>
        <ids:specifications></ids:specifications>
    </ids:ids>"""

    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool("load_ids", {
            "source": xml_string,
            "source_type": "string"
        })

        assert result["status"] == "loaded"
        assert result["title"] == "Loaded IDS"

@pytest.mark.asyncio
async def test_load_ids_from_file(tmp_path):
    """Test loading IDS from file."""
    # Create test IDS file
    from ifctester import ids

    test_ids = ids.Ids(title="Test File IDS")
    test_file = tmp_path / "test.ids"
    test_ids.to_xml(str(test_file))

    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool("load_ids", {
            "source": str(test_file),
            "source_type": "file"
        })

        assert result["status"] == "loaded"
        assert result["title"] == "Test File IDS"

@pytest.mark.asyncio
async def test_load_ids_replaces_existing():
    """Test that loading replaces existing IDS in session."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create initial IDS
        await client.call_tool("create_ids", {"title": "Original"})

        # Load new IDS
        xml_string = """<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS">
            <ids:info><ids:title>Replacement</ids:title></ids:info>
            <ids:specifications></ids:specifications>
        </ids:ids>"""

        await client.call_tool("load_ids", {
            "source": xml_string,
            "source_type": "string"
        })

        # Verify replaced
        result = await client.call_tool("get_ids_info", {})
        assert result["title"] == "Replacement"
```

**GREEN: Implementation**
1. Implement `load_ids` tool
2. Use IfcTester's `open()` and `from_string()`
3. Handle errors
4. Run tests → PASS

### Milestone 4: get_ids_info Tool

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_get_ids_info_empty():
    """Test getting info from IDS with no specifications."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {
            "title": "Empty IDS",
            "author": "test@example.com"
        })

        result = await client.call_tool("get_ids_info", {})

        assert result["title"] == "Empty IDS"
        assert result["author"] == "test@example.com"
        assert result["specification_count"] == 0
        assert result["specifications"] == []

@pytest.mark.asyncio
async def test_get_ids_info_with_specifications():
    """Test getting info from IDS with specifications."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test IDS"})

        # Add specification (will be implemented in 004)
        # For now, manually add to session for testing
        from ids_mcp_server.session.storage import _session_storage
        from ifctester import ids

        session_data = _session_storage.get(client.session_id)
        spec = ids.Specification(
            name="Test Spec",
            ifcVersion=["IFC4"],
            identifier="S1"
        )
        session_data.ids_obj.specifications.append(spec)

        # Get info
        result = await client.call_tool("get_ids_info", {})

        assert result["specification_count"] == 1
        assert len(result["specifications"]) == 1
        assert result["specifications"][0]["name"] == "Test Spec"
        assert result["specifications"][0]["identifier"] == "S1"
```

**GREEN: Implementation**
1. Implement `get_ids_info` tool
2. Extract specification summary
3. Run tests → PASS

---

## Phase 3: Validation

**Validation Checklist:**

- ✅ All 4 tools implemented and tested
- ✅ All exports validate against IDS 1.0 XSD
- ✅ Round-trip test passes (create → export → load → export)
- ✅ Tools integrate with session management
- ✅ Test coverage ≥ 95%
- ✅ All IfcTester validations pass

**Round-Trip Validation Test:**

```python
@pytest.mark.asyncio
async def test_complete_round_trip():
    """
    Critical validation: Create → Export → Load → Export
    Ensures no data loss and 100% XML compliance.
    """
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create IDS
        await client.call_tool("create_ids", {
            "title": "Round Trip Test",
            "author": "test@example.com",
            "version": "1.0",
            "description": "Testing round-trip"
        })

        # Export to XML string
        export1 = await client.call_tool("export_ids", {})
        xml1 = export1["xml"]

        # Load back
        await client.call_tool("load_ids", {
            "source": xml1,
            "source_type": "string"
        })

        # Export again
        export2 = await client.call_tool("export_ids", {})
        xml2 = export2["xml"]

        # Verify using IfcTester
        from ifctester import ids

        ids1 = ids.from_string(xml1, validate=True)
        ids2 = ids.from_string(xml2, validate=True)

        assert ids1.info["title"] == ids2.info["title"]
        assert ids1.info["author"] == ids2.info["author"]
```

---

## Dependencies

**Depends on:**
- 001-project-setup (infrastructure)
- 002-session-management (Context integration)

**Provides for:**
- All subsequent features (003+) depend on these tools

---

## Success Metrics

- ✅ All tools respond in <100ms
- ✅ 100% XSD validation success rate
- ✅ Round-trip test passes
- ✅ Test coverage ≥ 95%
- ✅ No memory leaks during export

---

## Next Steps

After Phase 003 completion:
1. Proceed to **004-specification-management** - Add specification management tools
2. All specification tools will build on document management foundation
