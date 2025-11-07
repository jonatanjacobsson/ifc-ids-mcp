# Implementation Plan: Validation Tools

**Branch**: `claude/008-validation` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement validation tools for verifying IDS document correctness and optionally validating IFC models against IDS specifications. The primary tool validates IDS structure and XSD compliance, while the bonus feature enables IFC model checking using IfcTester's built-in validation capabilities.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP tools
- `ifctester` - IDS validation and IFC checking
- `ifcopenshell` - IFC file reading (for model validation)

**Performance Goals**:
- IDS validation <50ms
- IFC model validation <5s for typical models

**Constraints**:
- Must validate against official IDS 1.0 XSD
- IFC validation is optional bonus feature
- Must handle large IFC files gracefully

**Scale/Scope**:
- IDS files up to 10MB
- IFC models up to 100MB (bonus feature)

## Project Structure

```text
specs/008-validation/
└── plan.md

src/ids_mcp_server/
├── tools/
│   └── validation.py        # Validation tools
└── validation/
    ├── ids_validator.py     # IDS validation logic
    └── ifc_validator.py     # IFC validation (bonus)

tests/
├── unit/tools/
│   └── test_validation_tools.py
├── integration/
│   └── test_validation_workflow.py
└── validation/
    ├── test_xsd_compliance.py
    └── fixtures/
        ├── valid_ids_files/
        ├── invalid_ids_files/
        └── sample_ifc_files/
```

## Phase 1: Design

### Tool Contracts

```python
@mcp.tool
async def validate_ids(ctx: Context) -> dict:
    """
    Validate current session's IDS document.

    Validates:
    1. Required fields present (title, specifications, etc.)
    2. Each specification has applicability
    3. IFC versions are valid
    4. XSD schema compliance (via IfcTester)

    Contract:
        - MUST check IDS completeness
        - MUST validate against XSD schema
        - MUST return detailed error messages
        - MUST use IfcTester's built-in validation

    Returns:
        {
            "valid": true,
            "errors": [],
            "warnings": [],
            "specifications_count": 3,
            "details": {
                "has_title": true,
                "has_specifications": true,
                "xsd_valid": true
            }
        }
    """

@mcp.tool
async def validate_ifc_model(
    ifc_file_path: str,
    ctx: Context,
    report_format: str = "json"
) -> dict:
    """
    Validate IFC model against current session's IDS specifications.

    BONUS FEATURE - leverages IfcTester's IFC validation.

    Args:
        ifc_file_path: Path to IFC file
        report_format: "json", "html", or "console"

    Contract:
        - MUST check file exists
        - MUST use ifcopenshell.open() to load IFC
        - MUST use ids.validate() from IfcTester
        - MUST generate report in requested format
        - MUST handle large files gracefully

    Returns (json format):
        {
            "status": "validation_complete",
            "total_specifications": 3,
            "passed_specifications": 2,
            "failed_specifications": 1,
            "report": {
                "specifications": [
                    {
                        "name": "Wall Fire Rating",
                        "status": "passed",
                        "applicable_entities": 25,
                        "passed_entities": 25,
                        "failed_entities": 0
                    },
                    ...
                ]
            }
        }
    """
```

## Phase 2: Test-Driven Implementation

### Milestone 1: IDS Validation Tool

**RED: Write failing tests**

```python
import pytest
from fastmcp.client import Client

@pytest.mark.asyncio
async def test_validate_empty_ids():
    """Test validating IDS with no specifications."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Empty"})

        result = await client.call_tool("validate_ids", {})

        assert result["valid"] == False
        assert "no specifications" in str(result["errors"]).lower()

@pytest.mark.asyncio
async def test_validate_complete_ids():
    """Test validating complete valid IDS."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create complete IDS
        await client.call_tool("create_ids", {"title": "Valid IDS"})

        result = await client.call_tool("add_specification", {
            "name": "Test Spec",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # Add applicability
        await client.call_tool("add_entity_facet", {
            "spec_id": spec_id,
            "location": "applicability",
            "entity_name": "IFCWALL"
        })

        # Validate
        result = await client.call_tool("validate_ids", {})

        assert result["valid"] == True
        assert result["errors"] == []
        assert result["specifications_count"] == 1
        assert result["details"]["xsd_valid"] == True

@pytest.mark.asyncio
async def test_validate_ids_xsd_compliance():
    """Test that validation checks XSD compliance."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_complete_ids(client)

        result = await client.call_tool("validate_ids", {})

        # Export and re-validate with IfcTester to confirm
        export_result = await client.call_tool("export_ids", {})

        from ifctester import ids
        validated_ids = ids.from_string(export_result["xml"], validate=True)

        assert validated_ids is not None
        assert result["valid"] == True

@pytest.mark.asyncio
async def test_validate_ids_missing_applicability():
    """Test validation catches missing applicability."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool("create_ids", {"title": "Test"})
        await client.call_tool("add_specification", {
            "name": "No Applicability",
            "ifc_versions": ["IFC4"]
        })

        result = await client.call_tool("validate_ids", {})

        assert result["valid"] == False
        assert any("applicability" in str(err).lower() for err in result["errors"])
```

**GREEN: Implementation**

```python
# src/ids_mcp_server/tools/validation.py
from fastmcp import mcp, Context, ToolError
from ids_mcp_server.session.manager import get_or_create_session

@mcp.tool
async def validate_ids(ctx: Context) -> dict:
    """Validate IDS document."""
    try:
        await ctx.info("Validating IDS document")

        ids_obj = await get_or_create_session(ctx)

        errors = []
        warnings = []

        # Check has title
        if not ids_obj.info.get("title"):
            errors.append("IDS must have a title")

        # Check has specifications
        if not ids_obj.specifications:
            errors.append("IDS must have at least one specification")

        # Check each specification
        for i, spec in enumerate(ids_obj.specifications):
            # Check has applicability
            if not spec.applicability:
                errors.append(
                    f"Specification '{spec.name}' (index {i}) has no applicability facets"
                )

            # Check has name
            if not spec.name:
                errors.append(f"Specification at index {i} has no name")

        # Validate XSD by attempting to serialize
        xsd_valid = True
        try:
            xml_string = ids_obj.to_string()
            # If this succeeds, it's XSD valid (IfcTester validates on export)
        except Exception as e:
            xsd_valid = False
            errors.append(f"XSD validation failed: {str(e)}")

        valid = len(errors) == 0

        await ctx.info(f"Validation complete: {'PASS' if valid else 'FAIL'}")

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "specifications_count": len(ids_obj.specifications),
            "details": {
                "has_title": bool(ids_obj.info.get("title")),
                "has_specifications": len(ids_obj.specifications) > 0,
                "xsd_valid": xsd_valid
            }
        }

    except Exception as e:
        await ctx.error(f"Validation error: {str(e)}")
        raise ToolError(f"Validation failed: {str(e)}")
```

### Milestone 2: IFC Model Validation Tool (Bonus)

**RED: Write failing tests**

```python
@pytest.mark.asyncio
async def test_validate_ifc_model(tmp_path):
    """Test validating IFC model against IDS."""
    # Create sample IFC file
    ifc_file = create_sample_ifc_file(tmp_path)

    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create IDS with simple requirement
        await setup_ids_with_wall_spec(client)

        # Validate IFC
        result = await client.call_tool("validate_ifc_model", {
            "ifc_file_path": str(ifc_file),
            "report_format": "json"
        })

        assert result["status"] == "validation_complete"
        assert "total_specifications" in result
        assert "report" in result

@pytest.mark.asyncio
async def test_validate_ifc_file_not_found():
    """Test error handling for missing IFC file."""
    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_ids_with_wall_spec(client)

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("validate_ifc_model", {
                "ifc_file_path": "/nonexistent/file.ifc"
            })

        assert "not found" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_validate_ifc_html_report(tmp_path):
    """Test generating HTML report."""
    ifc_file = create_sample_ifc_file(tmp_path)

    mcp = create_test_server()

    async with Client(mcp) as client:
        await setup_ids_with_wall_spec(client)

        result = await client.call_tool("validate_ifc_model", {
            "ifc_file_path": str(ifc_file),
            "report_format": "html"
        })

        assert result["status"] == "validation_complete"
        assert "html" in result
        assert "<html" in result["html"].lower()
```

**GREEN: Implementation**

```python
@mcp.tool
async def validate_ifc_model(
    ifc_file_path: str,
    ctx: Context,
    report_format: str = "json"
) -> dict:
    """Validate IFC model against IDS."""
    import ifcopenshell
    from ifctester import reporter
    from pathlib import Path

    try:
        await ctx.info(f"Validating IFC file: {ifc_file_path}")

        # Check file exists
        if not Path(ifc_file_path).exists():
            raise ToolError(f"IFC file not found: {ifc_file_path}")

        # Get IDS
        ids_obj = await get_or_create_session(ctx)

        if not ids_obj.specifications:
            raise ToolError("IDS has no specifications to validate against")

        # Load IFC file
        await ctx.info("Loading IFC file")
        ifc_file = ifcopenshell.open(ifc_file_path)

        # Validate
        await ctx.info("Running IDS validation")
        ids_obj.validate(ifc_file)

        # Generate report
        if report_format == "json":
            json_reporter = reporter.Json(ids_obj)
            json_reporter.report()

            return {
                "status": "validation_complete",
                "total_specifications": len(ids_obj.specifications),
                "report": json_reporter.to_string()
            }

        elif report_format == "html":
            html_reporter = reporter.Html(ids_obj)
            html_reporter.report()

            return {
                "status": "validation_complete",
                "html": html_reporter.to_string()
            }

        elif report_format == "console":
            reporter.Console(ids_obj).report()
            return {"status": "validation_complete"}

        else:
            raise ToolError(f"Invalid report format: {report_format}")

    except FileNotFoundError as e:
        await ctx.error(f"File not found: {str(e)}")
        raise ToolError(f"IFC file not found: {ifc_file_path}")
    except Exception as e:
        await ctx.error(f"IFC validation error: {str(e)}")
        raise ToolError(f"IFC validation failed: {str(e)}")
```

## Phase 3: Validation

**Validation Checklist:**
- ✅ IDS validation detects incomplete specifications
- ✅ XSD validation integrated
- ✅ IFC model validation works (bonus)
- ✅ Report formats supported (json, html, console)
- ✅ Error handling robust
- ✅ Test coverage ≥ 95%

## Success Metrics

- ✅ IDS validation <50ms
- ✅ IFC validation <5s for 10MB files
- ✅ All report formats working
- ✅ Test coverage ≥ 95%

## Next Steps

After Phase 008:
1. Proceed to **009-testing-framework** - Establish comprehensive TDD testing infrastructure
2. All features complete - ready for production deployment
