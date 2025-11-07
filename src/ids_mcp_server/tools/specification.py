"""Specification management MCP tools."""

from typing import Optional, Dict, Any, List, Union
from fastmcp import Context
from fastmcp.exceptions import ToolError
from ifctester import ids

from ids_mcp_server.session.manager import get_or_create_session


def _find_specification(ids_obj: ids.Ids, spec_id: str) -> ids.Specification:
    """
    Find specification by identifier or name.

    Args:
        ids_obj: IDS object
        spec_id: Specification identifier or name

    Returns:
        Specification object

    Raises:
        ToolError: If specification not found
    """
    for spec in ids_obj.specifications:
        if getattr(spec, 'identifier', None) == spec_id or spec.name == spec_id:
            return spec
    raise ToolError(f"Specification not found: {spec_id}")


async def add_specification(
    name: str,
    ifc_versions: List[str],
    ctx: Context,
    identifier: Optional[str] = None,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    min_occurs: int = 0,
    max_occurs: Union[int, str] = "unbounded"
) -> Dict[str, Any]:
    """
    Add a specification to the current session's IDS document.

    Args:
        name: Specification name
        ifc_versions: List of IFC versions (e.g., ["IFC4", "IFC4X3"])
        ctx: FastMCP Context (auto-injected)
        identifier: Optional unique identifier
        description: Why this information is required
        instructions: How to fulfill requirements
        min_occurs: Minimum occurrences (0 = optional)
        max_occurs: Maximum occurrences (int or "unbounded")

    Returns:
        {
            "status": "added",
            "spec_id": "S1",
            "ifc_versions": ["IFC4"]
        }
    """
    try:
        # Get IDS from session
        ids_obj = await get_or_create_session(ctx)

        await ctx.info(f"Adding specification: {name}")

        # Validate IFC versions and normalize
        valid_versions = {"IFC2X3", "IFC4", "IFC4X3_ADD2"}
        version_mapping = {
            "IFC4X3": "IFC4X3_ADD2",  # Normalize IFC4X3 to IFC4X3_ADD2
        }
        normalized_versions = []
        for version in ifc_versions:
            version_upper = version.upper()
            # Apply mapping if exists
            version_upper = version_mapping.get(version_upper, version_upper)
            if version_upper not in valid_versions:
                raise ToolError(
                    f"Invalid IFC version: {version}. Valid versions: {', '.join(valid_versions)}"
                )
            normalized_versions.append(version_upper)

        # Create specification using IfcTester
        spec = ids.Specification(
            name=name,
            ifcVersion=normalized_versions,
            identifier=identifier,
            description=description,
            instructions=instructions,
            minOccurs=min_occurs,
            maxOccurs=max_occurs if isinstance(max_occurs, str) else int(max_occurs)
        )

        # Add to IDS
        ids_obj.specifications.append(spec)

        spec_id = identifier if identifier else name

        await ctx.info(f"Specification added: {spec_id}")

        return {
            "status": "added",
            "spec_id": spec_id,
            "ifc_versions": normalized_versions
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add specification: {str(e)}")
        raise ToolError(f"Failed to add specification: {str(e)}")
