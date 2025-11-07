"""Validation MCP tools."""

import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from fastmcp import Context
from fastmcp.exceptions import ToolError
from ifctester import ids, reporter
import ifcopenshell

from ids_mcp_server.session.manager import get_or_create_session
from ids_mcp_server.config import load_config_from_env
from ids_mcp_server.tools.ids_audit_tool import run_audit_tool


async def validate_ids(ctx: Context) -> Dict[str, Any]:
    """
    Validate current session's IDS document.

    Validates using both IfcTester and buildingSMART IDS-Audit-tool:
    1. Required fields present (title, specifications, etc.)
    2. Each specification has applicability
    3. IFC versions are valid
    4. XSD schema compliance (via IfcTester)
    5. IDS-Audit-tool validation (if enabled)

    Args:
        ctx: FastMCP Context (auto-injected)

    Returns:
        {
            "valid": true,  # Both validators must pass
            "errors": [],  # Combined from both
            "warnings": [],  # Combined from both
            "specifications_count": 3,
            "details": {
                "has_title": true,
                "has_specifications": true,
                "xsd_valid": true  # From IfcTester
            },
            "audit_tool": {  # New section
                "valid": true,
                "exit_code": 0,
                "output": "...",
                "errors": [],
                "warnings": []
            }
        }
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        config = load_config_from_env()

        await ctx.info("Validating IDS document")

        errors = []
        warnings = []

        # Check has title
        has_title = bool(ids_obj.info.get("title"))
        if not has_title:
            errors.append("IDS must have a title")

        # Check has specifications
        has_specifications = len(ids_obj.specifications) > 0
        if not has_specifications:
            errors.append("IDS must have at least one specification")

        # Valid IFC versions (from IDS 1.0 spec)
        valid_ifc_versions = {"IFC2X3", "IFC4", "IFC4X3", "IFC4X3_ADD2"}

        # Check each specification
        for i, spec in enumerate(ids_obj.specifications):
            spec_name = spec.name if spec.name else f"Specification {i}"

            # Check has name
            if not spec.name:
                warnings.append(f"Specification at index {i} has no name")

            # Check has applicability facets
            if not spec.applicability or len(spec.applicability) == 0:
                errors.append(
                    f"Specification '{spec_name}' (index {i}) has no applicability facets. "
                    "At least one applicability facet is required."
                )

            # Check IFC versions are valid
            if hasattr(spec, 'ifcVersion'):
                ifc_versions = spec.ifcVersion if isinstance(spec.ifcVersion, list) else [spec.ifcVersion]
                for version in ifc_versions:
                    if version not in valid_ifc_versions:
                        warnings.append(
                            f"Specification '{spec_name}' uses non-standard IFC version: {version}"
                        )

        # Validate XSD compliance by attempting to serialize and re-parse
        xsd_valid = True
        try:
            xml_string = ids_obj.to_string()
            # Try to parse it back with XSD validation
            validated_ids = ids.from_string(xml_string, validate=True)
        except Exception as e:
            xsd_valid = False
            errors.append(f"XSD validation failed: {str(e)}")

        # Track IfcTester validation result before audit tool
        ifc_tester_valid = len(errors) == 0 and xsd_valid

        # Run IDS-Audit-tool validation if enabled
        audit_tool_result = None
        if config.audit_tool.enabled:
            try:
                await ctx.info("Running IDS-Audit-tool validation...")
                # Export IDS to temporary file for audit tool
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ids', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    ids_obj.to_xml(tmp_path)

                try:
                    # Run audit tool with config
                    audit_tool_result = run_audit_tool(tmp_path, config.audit_tool)

                    # Merge errors and warnings from audit tool
                    if audit_tool_result.get("errors"):
                        errors.extend([f"Audit tool: {e}" for e in audit_tool_result["errors"]])
                    if audit_tool_result.get("warnings"):
                        warnings.extend([f"Audit tool: {w}" for w in audit_tool_result["warnings"]])

                finally:
                    # Clean up temporary file
                    try:
                        Path(tmp_path).unlink()
                    except Exception:
                        pass  # Ignore cleanup errors

            except Exception as e:
                await ctx.warning(f"IDS-Audit-tool validation failed: {str(e)}")
                audit_tool_result = {
                    "valid": False,
                    "exit_code": -1,
                    "output": f"Error running audit tool: {str(e)}",
                    "errors": [f"Error running audit tool: {str(e)}"],
                    "warnings": []
                }
                # Add to errors list
                errors.append(f"Audit tool: Error running audit tool: {str(e)}")
        else:
            await ctx.info("IDS-Audit-tool validation disabled")

        # Overall validation: both IfcTester and audit tool must pass
        audit_tool_valid = audit_tool_result is None or audit_tool_result.get("valid", False)
        valid = ifc_tester_valid and audit_tool_valid

        await ctx.info(f"Validation complete: {'PASS' if valid else 'FAIL'}")

        result = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "specifications_count": len(ids_obj.specifications),
            "details": {
                "has_title": has_title,
                "has_specifications": has_specifications,
                "xsd_valid": xsd_valid
            }
        }

        # Add audit tool results if available
        if audit_tool_result is not None:
            result["audit_tool"] = audit_tool_result
        elif config.audit_tool.enabled:
            # Tool was enabled but result is None (shouldn't happen, but handle gracefully)
            result["audit_tool"] = {
                "valid": False,
                "exit_code": -1,
                "output": "Audit tool validation was attempted but no result was returned",
                "errors": ["Audit tool validation failed"],
                "warnings": []
            }

        return result

    except Exception as e:
        await ctx.error(f"Validation error: {str(e)}")
        raise ToolError(f"Validation error: {str(e)}")


async def validate_ifc_model(
    ifc_file_path: str,
    ctx: Context,
    report_format: str = "json"
) -> Dict[str, Any]:
    """
    Validate an IFC model against the current session's IDS specifications.

    This bonus feature leverages IfcTester's IFC validation capabilities.

    Args:
        ifc_file_path: Path to IFC file
        ctx: FastMCP Context (auto-injected)
        report_format: "console", "json", or "html"

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
    import json as json_lib

    try:
        ids_obj = await get_or_create_session(ctx)

        await ctx.info(f"Validating IFC model: {ifc_file_path}")

        # Validate file exists
        if not Path(ifc_file_path).exists():
            raise ToolError(f"IFC file not found: {ifc_file_path}")

        # Check has specifications
        if not ids_obj.specifications:
            raise ToolError("IDS has no specifications to validate against")

        # Load IFC file
        await ctx.info("Loading IFC file...")
        ifc_file = ifcopenshell.open(ifc_file_path)

        # Validate
        await ctx.info("Running validation...")
        ids_obj.validate(ifc_file)

        # Generate report
        if report_format == "console":
            reporter.Console(ids_obj).report()
            return {"status": "validation_complete", "format": "console"}

        elif report_format == "json":
            json_reporter = reporter.Json(ids_obj)
            json_reporter.report()
            raw_report = json_reporter.to_string()

            # Parse the JSON report to extract structured data
            try:
                report_data = json_lib.loads(raw_report)

                # Extract specification-level summary
                specifications_summary = []
                passed_count = 0
                failed_count = 0

                for spec in ids_obj.specifications:
                    # Count applicable, passed, and failed entities for this spec
                    applicable = 0
                    passed = 0
                    failed = 0

                    # IfcTester stores results in spec after validation
                    if hasattr(spec, 'requirements'):
                        for req in spec.requirements:
                            if hasattr(req, 'failed_entities'):
                                failed += len(req.failed_entities) if req.failed_entities else 0
                            if hasattr(req, 'passed_entities'):
                                passed += len(req.passed_entities) if req.passed_entities else 0

                    applicable = passed + failed
                    spec_status = "passed" if failed == 0 and applicable > 0 else "failed" if failed > 0 else "no_applicable_entities"

                    if spec_status == "passed":
                        passed_count += 1
                    elif spec_status == "failed":
                        failed_count += 1

                    specifications_summary.append({
                        "name": spec.name if spec.name else f"Specification {len(specifications_summary)}",
                        "status": spec_status,
                        "applicable_entities": applicable,
                        "passed_entities": passed,
                        "failed_entities": failed
                    })

                return {
                    "status": "validation_complete",
                    "total_specifications": len(ids_obj.specifications),
                    "passed_specifications": passed_count,
                    "failed_specifications": failed_count,
                    "report": {
                        "specifications": specifications_summary,
                        "raw_json": report_data  # Include original report
                    }
                }
            except Exception as parse_error:
                # Fallback if parsing fails - return raw report
                await ctx.warning(f"Could not parse report structure: {parse_error}")
                return {
                    "status": "validation_complete",
                    "total_specifications": len(ids_obj.specifications),
                    "format": "json",
                    "report": raw_report
                }

        elif report_format == "html":
            html_reporter = reporter.Html(ids_obj)
            html_reporter.report()
            return {
                "status": "validation_complete",
                "total_specifications": len(ids_obj.specifications),
                "format": "html",
                "html": html_reporter.to_string()
            }

        else:
            raise ToolError(f"Invalid report format: {report_format}. Must be 'console', 'json', or 'html'")

    except FileNotFoundError as e:
        await ctx.error(f"File not found: {str(e)}")
        raise ToolError(f"File not found: {str(e)}")
    except Exception as e:
        await ctx.error(f"IFC validation error: {str(e)}")
        raise ToolError(f"IFC validation error: {str(e)}")
