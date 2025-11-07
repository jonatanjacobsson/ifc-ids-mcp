"""Restriction management MCP tools."""

from typing import Optional, Dict, Any, List
from fastmcp import Context
from fastmcp.exceptions import ToolError
from ifctester import ids

from ids_mcp_server.session.manager import get_or_create_session
from ids_mcp_server.tools.specification import _find_specification


def _normalize_base_type(base_type: str) -> str:
    """
    Normalize XML Schema base type for IfcTester.

    IfcTester adds 'xs:' prefix automatically, so we need to remove it if present.

    Args:
        base_type: Base type (e.g., "xs:string" or "string")

    Returns:
        Normalized base type without 'xs:' prefix (e.g., "string")
    """
    if base_type.startswith("xs:"):
        return base_type[3:]  # Remove 'xs:' prefix
    return base_type


def _get_facet_from_spec(
    spec: ids.Specification,
    location: str,
    facet_index: int
) -> Any:
    """
    Get facet from specification by location and index.

    Args:
        spec: Specification object
        location: "applicability" or "requirements"
        facet_index: Index of facet in location (0-based)

    Returns:
        Facet object

    Raises:
        ToolError: If location invalid or index out of range
    """
    if location == "applicability":
        facets = spec.applicability
    elif location == "requirements":
        facets = spec.requirements
    else:
        raise ToolError(f"Invalid location: {location}. Must be 'applicability' or 'requirements'")

    if facet_index < 0 or facet_index >= len(facets):
        raise ToolError(
            f"Facet index {facet_index} out of range. "
            f"Location '{location}' has {len(facets)} facet(s)"
        )

    return facets[facet_index]


def _apply_restriction_to_facet(
    facet: Any,
    parameter_name: str,
    restriction: ids.Restriction
) -> None:
    """
    Apply restriction to a facet parameter.

    Args:
        facet: Facet object (Entity, Property, Attribute, etc.)
        parameter_name: Parameter to restrict (e.g., "value", "propertySet", "baseName")
        restriction: Restriction object to apply

    Raises:
        ToolError: If parameter doesn't exist on facet
    """
    # Check if parameter exists
    if not hasattr(facet, parameter_name):
        raise ToolError(
            f"Parameter '{parameter_name}' not found on facet type {type(facet).__name__}"
        )

    # Set the restriction on the parameter
    setattr(facet, parameter_name, restriction)


async def add_enumeration_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    values: List[str],
    ctx: Context,
    location: str = "requirements"
) -> Dict[str, Any]:
    """
    Add enumeration restriction (list of allowed values).

    Args:
        spec_id: Specification identifier or name
        facet_index: Index of facet in location (0-based)
        parameter_name: Which parameter to restrict (e.g., "value", "propertySet")
        base_type: XSD base type (e.g., "xs:string", "xs:integer")
        values: List of allowed values
        ctx: FastMCP Context (auto-injected)
        location: "applicability" or "requirements" (default: "requirements")

    Returns:
        {"status": "added", "restriction_type": "enumeration", "spec_id": "S1"}

    Example:
        Add enumeration to property value: FireRating must be "REI30", "REI60", or "REI90"
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding enumeration restriction to {spec_id}, facet {facet_index}")

        # Get the facet
        facet = _get_facet_from_spec(spec, location, facet_index)

        # Create enumeration restriction using IfcTester
        # Normalize base type (remove 'xs:' prefix if present)
        normalized_base = _normalize_base_type(base_type)
        restriction = ids.Restriction(
            base=normalized_base,
            options={"enumeration": values}
        )

        # Apply restriction to the parameter
        _apply_restriction_to_facet(facet, parameter_name, restriction)

        await ctx.info(f"Enumeration restriction added with {len(values)} values")

        return {
            "status": "added",
            "restriction_type": "enumeration",
            "spec_id": spec_id,
            "facet_index": facet_index,
            "parameter": parameter_name,
            "value_count": len(values)
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add enumeration restriction: {str(e)}")
        raise ToolError(f"Failed to add enumeration restriction: {str(e)}")


async def add_pattern_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    pattern: str,
    ctx: Context,
    location: str = "requirements"
) -> Dict[str, Any]:
    """
    Add pattern restriction (regex matching).

    Args:
        spec_id: Specification identifier or name
        facet_index: Index of facet in location (0-based)
        parameter_name: Which parameter to restrict (e.g., "value")
        base_type: XSD base type (e.g., "xs:string")
        pattern: Regular expression pattern
        ctx: FastMCP Context (auto-injected)
        location: "applicability" or "requirements" (default: "requirements")

    Returns:
        {"status": "added", "restriction_type": "pattern", "spec_id": "S1"}

    Example:
        Add pattern to attribute value: Name must match "EW-[0-9]{3}"
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding pattern restriction to {spec_id}, facet {facet_index}")

        # Get the facet
        facet = _get_facet_from_spec(spec, location, facet_index)

        # Create pattern restriction using IfcTester
        # Normalize base type (remove 'xs:' prefix if present)
        normalized_base = _normalize_base_type(base_type)
        restriction = ids.Restriction(
            base=normalized_base,
            options={"pattern": pattern}
        )

        # Apply restriction to the parameter
        _apply_restriction_to_facet(facet, parameter_name, restriction)

        await ctx.info(f"Pattern restriction added: {pattern}")

        return {
            "status": "added",
            "restriction_type": "pattern",
            "spec_id": spec_id,
            "facet_index": facet_index,
            "parameter": parameter_name,
            "pattern": pattern
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add pattern restriction: {str(e)}")
        raise ToolError(f"Failed to add pattern restriction: {str(e)}")


async def add_bounds_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    ctx: Context,
    location: str = "requirements",
    min_inclusive: Optional[float] = None,
    max_inclusive: Optional[float] = None,
    min_exclusive: Optional[float] = None,
    max_exclusive: Optional[float] = None
) -> Dict[str, Any]:
    """
    Add numeric bounds restriction.

    Args:
        spec_id: Specification identifier or name
        facet_index: Index of facet in location (0-based)
        parameter_name: Which parameter to restrict (e.g., "value")
        base_type: XSD base type (e.g., "xs:double", "xs:integer")
        ctx: FastMCP Context (auto-injected)
        location: "applicability" or "requirements" (default: "requirements")
        min_inclusive: Minimum value (inclusive)
        max_inclusive: Maximum value (inclusive)
        min_exclusive: Minimum value (exclusive)
        max_exclusive: Maximum value (exclusive)

    Returns:
        {"status": "added", "restriction_type": "bounds", "spec_id": "S1"}

    Example:
        Add bounds to property value: Height must be between 2.4 and 3.0 meters
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding bounds restriction to {spec_id}, facet {facet_index}")

        # Get the facet
        facet = _get_facet_from_spec(spec, location, facet_index)

        # Build bounds parameters
        bounds_params = {}
        if min_inclusive is not None:
            bounds_params["minInclusive"] = min_inclusive
        if max_inclusive is not None:
            bounds_params["maxInclusive"] = max_inclusive
        if min_exclusive is not None:
            bounds_params["minExclusive"] = min_exclusive
        if max_exclusive is not None:
            bounds_params["maxExclusive"] = max_exclusive

        # Create bounds restriction using IfcTester
        # Normalize base type (remove 'xs:' prefix if present)
        normalized_base = _normalize_base_type(base_type)
        restriction = ids.Restriction(
            base=normalized_base,
            options=bounds_params
        )

        # Apply restriction to the parameter
        _apply_restriction_to_facet(facet, parameter_name, restriction)

        await ctx.info(f"Bounds restriction added: {bounds_params}")

        return {
            "status": "added",
            "restriction_type": "bounds",
            "spec_id": spec_id,
            "facet_index": facet_index,
            "parameter": parameter_name,
            "bounds": bounds_params
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add bounds restriction: {str(e)}")
        raise ToolError(f"Failed to add bounds restriction: {str(e)}")


async def add_length_restriction(
    spec_id: str,
    facet_index: int,
    parameter_name: str,
    base_type: str,
    ctx: Context,
    location: str = "requirements",
    length: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add string length restriction.

    Args:
        spec_id: Specification identifier or name
        facet_index: Index of facet in location (0-based)
        parameter_name: Which parameter to restrict (e.g., "value")
        base_type: XSD base type (e.g., "xs:string")
        ctx: FastMCP Context (auto-injected)
        location: "applicability" or "requirements" (default: "requirements")
        length: Exact length
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        {"status": "added", "restriction_type": "length", "spec_id": "S1"}

    Example:
        Add length restriction to attribute value: Tag must be between 5 and 50 characters
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding length restriction to {spec_id}, facet {facet_index}")

        # Get the facet
        facet = _get_facet_from_spec(spec, location, facet_index)

        # Build length parameters
        length_params = {}
        if length is not None:
            length_params["length"] = length
        if min_length is not None:
            length_params["minLength"] = min_length
        if max_length is not None:
            length_params["maxLength"] = max_length

        # Create length restriction using IfcTester
        # Normalize base type (remove 'xs:' prefix if present)
        normalized_base = _normalize_base_type(base_type)
        restriction = ids.Restriction(
            base=normalized_base,
            options=length_params
        )

        # Apply restriction to the parameter
        _apply_restriction_to_facet(facet, parameter_name, restriction)

        await ctx.info(f"Length restriction added: {length_params}")

        return {
            "status": "added",
            "restriction_type": "length",
            "spec_id": spec_id,
            "facet_index": facet_index,
            "parameter": parameter_name,
            "constraints": length_params
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add length restriction: {str(e)}")
        raise ToolError(f"Failed to add length restriction: {str(e)}")
