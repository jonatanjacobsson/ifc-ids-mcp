"""Validation helpers for IDS facets and specifications.

This module provides early validation functions to catch IDS 1.0 schema violations
and IfcTester requirements before export time.
"""

from typing import List, Optional
from fastmcp.exceptions import ToolError
from ifctester import ids


def validate_single_entity_in_applicability(
    spec: ids.Specification,
    location: str
) -> None:
    """
    Validate that applicability section has at most one entity facet.

    IDS 1.0 XSD constraint: Only ONE entity facet allowed per applicability.
    This constraint does not apply to requirements sections.

    Args:
        spec: Specification to validate
        location: "applicability" or "requirements"

    Raises:
        ToolError: If trying to add second entity facet to applicability

    Example:
        >>> spec = ids.Specification(name="Test", ifcVersion=["IFC4"])
        >>> validate_single_entity_in_applicability(spec, "applicability")
        >>> # First call succeeds
        >>> spec.applicability.append(ids.Entity(name="IFCWALL"))
        >>> validate_single_entity_in_applicability(spec, "applicability")
        >>> # Second call raises ToolError
    """
    if location != "applicability":
        return  # Constraint only applies to applicability

    # Count existing entity facets
    entity_count = sum(
        1 for facet in spec.applicability
        if isinstance(facet, ids.Entity)
    )

    if entity_count >= 1:
        raise ToolError(
            "IDS 1.0 XSD constraint violation: Only ONE entity facet is allowed "
            "per specification's applicability section.\n\n"
            "WORKAROUND: Create a separate specification for each entity type.\n"
            "Example:\n"
            "  - Specification 1: Applicability = IFCWALL\n"
            "  - Specification 2: Applicability = IFCDOOR\n\n"
            f"Current specification '{spec.name}' already has an entity facet.\n\n"
            "See CLAUDE.md for more details on this IDS 1.0 limitation."
        )


def validate_property_set_required(
    property_set: Optional[str],
    property_name: str
) -> None:
    """
    Validate that property_set is provided for property facets.

    IfcTester requirement: property_set must be specified for valid XML export.
    While the IDS schema technically allows property_set to be optional,
    IfcTester's XML generation requires it for successful validation.

    Args:
        property_set: Property set name (can be None)
        property_name: Property name (for error message)

    Raises:
        ToolError: If property_set is None or empty

    Example:
        >>> validate_property_set_required("Pset_WallCommon", "FireRating")
        >>> # Succeeds
        >>> validate_property_set_required(None, "FireRating")
        >>> # Raises ToolError
    """
    if not property_set or property_set.strip() == "":
        raise ToolError(
            f"Property facet validation error: 'property_set' parameter is required.\n\n"
            f"Property '{property_name}' must belong to a property set for valid IDS export.\n\n"
            "COMMON PROPERTY SETS:\n"
            "  - Pset_WallCommon (for walls)\n"
            "  - Pset_DoorCommon (for doors)\n"
            "  - Pset_WindowCommon (for windows)\n"
            "  - Pset_SpaceCommon (for spaces)\n"
            "  - Pset_SlabCommon (for slabs)\n"
            "  - Pset_BeamCommon (for beams)\n"
            "  - Pset_ColumnCommon (for columns)\n\n"
            "CUSTOM PROPERTY SETS:\n"
            "  - Pset_Common (generic custom properties)\n"
            "  - Pset_CustomProperties (organization-specific)\n\n"
            "This requirement ensures valid XML export via IfcTester.\n"
            "See CLAUDE.md for more details on this IfcTester requirement."
        )


def count_facets_by_type(
    facets: List,
    facet_type: type
) -> int:
    """
    Count facets of a specific type in a list.

    Utility function for validation and inspection of facets in
    applicability or requirements sections.

    Args:
        facets: List of facets (applicability or requirements)
        facet_type: IfcTester facet class (e.g., ids.Entity, ids.Property)

    Returns:
        Count of facets matching the type

    Example:
        >>> from ifctester import ids
        >>> facets = [
        ...     ids.Entity(name="IFCWALL"),
        ...     ids.Property(baseName="FireRating", propertySet="Pset_WallCommon"),
        ...     ids.Attribute(name="Name")
        ... ]
        >>> count_facets_by_type(facets, ids.Entity)
        1
        >>> count_facets_by_type(facets, ids.Property)
        1
        >>> count_facets_by_type(facets, ids.Classification)
        0
    """
    return sum(1 for facet in facets if isinstance(facet, facet_type))
