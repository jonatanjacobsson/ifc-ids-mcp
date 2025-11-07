"""Facet management MCP tools."""

from typing import Optional, Dict, Any
from fastmcp import Context
from fastmcp.exceptions import ToolError
from ifctester import ids

from ids_mcp_server.session.manager import get_or_create_session
from ids_mcp_server.tools.specification import _find_specification
from ids_mcp_server.tools.validators import (
    validate_single_entity_in_applicability,
    validate_property_set_required
)


async def add_entity_facet(
    spec_id: str,
    location: str,
    entity_name: str,
    ctx: Context,
    predefined_type: Optional[str] = None,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add an entity facet to a specification.

    IMPORTANT: IDS 1.0 allows only ONE entity facet per applicability section.
    If you need multiple entity types, create separate specifications.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        entity_name: IFC entity name (e.g., "IFCWALL")
        ctx: FastMCP Context (auto-injected)
        predefined_type: Optional predefined type
        cardinality: "required", "optional", or "prohibited" (requirements only)

    Returns:
        {"status": "added", "facet_type": "entity", "spec_id": "S1"}

    Raises:
        ToolError: If trying to add second entity to applicability section
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        # EARLY VALIDATION: Check IDS 1.0 constraint
        validate_single_entity_in_applicability(spec, location)

        await ctx.info(f"Adding entity facet: {entity_name} to {spec_id}")

        # Create entity facet using IfcTester
        entity = ids.Entity(
            name=entity_name.upper(),
            predefinedType=predefined_type
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(entity)
        elif location == "requirements":
            # Note: Entity facets in requirements don't have cardinality in IDS
            spec.requirements.append(entity)
        else:
            raise ToolError(f"Invalid location: {location}. Must be 'applicability' or 'requirements'")

        await ctx.info(f"Entity facet added: {entity_name}")

        return {
            "status": "added",
            "facet_type": "entity",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add entity facet: {str(e)}")
        raise ToolError(f"Failed to add entity facet: {str(e)}")


async def add_property_facet(
    spec_id: str,
    location: str,
    property_name: str,
    ctx: Context,
    property_set: Optional[str] = None,
    data_type: Optional[str] = None,
    value: Optional[str] = None,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add a property facet to a specification.

    IMPORTANT: The property_set parameter is REQUIRED for valid IDS export.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        property_name: Property name (e.g., "FireRating")
        ctx: FastMCP Context (auto-injected)
        property_set: Property set name (e.g., "Pset_WallCommon") - REQUIRED
        data_type: IFC data type (e.g., "IFCLABEL")
        value: Required value or pattern
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {"status": "added", "facet_type": "property", "spec_id": "S1"}

    Raises:
        ToolError: If property_set is None or empty
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        # EARLY VALIDATION: Check property_set required
        validate_property_set_required(property_set, property_name)

        await ctx.info(f"Adding property facet: {property_name} to {spec_id}")

        # Create property facet using IfcTester
        prop = ids.Property(
            baseName=property_name,
            propertySet=property_set,
            dataType=data_type.upper() if data_type else None,
            value=value,
            cardinality=cardinality if location == "requirements" else None
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(prop)
        elif location == "requirements":
            spec.requirements.append(prop)
        else:
            raise ToolError(f"Invalid location: {location}")

        await ctx.info(f"Property facet added: {property_name}")

        return {
            "status": "added",
            "facet_type": "property",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add property facet: {str(e)}")
        raise ToolError(f"Failed to add property facet: {str(e)}")


async def add_attribute_facet(
    spec_id: str,
    location: str,
    attribute_name: str,
    ctx: Context,
    value: Optional[str] = None,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add an attribute facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        attribute_name: Attribute name (e.g., "Name", "Description")
        ctx: FastMCP Context (auto-injected)
        value: Required value or pattern
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {"status": "added", "facet_type": "attribute", "spec_id": "S1"}
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding attribute facet: {attribute_name} to {spec_id}")

        # Create attribute facet using IfcTester
        attr = ids.Attribute(
            name=attribute_name,
            value=value,
            cardinality=cardinality if location == "requirements" else None
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(attr)
        elif location == "requirements":
            spec.requirements.append(attr)
        else:
            raise ToolError(f"Invalid location: {location}")

        await ctx.info(f"Attribute facet added: {attribute_name}")

        return {
            "status": "added",
            "facet_type": "attribute",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add attribute facet: {str(e)}")
        raise ToolError(f"Failed to add attribute facet: {str(e)}")


async def add_classification_facet(
    spec_id: str,
    location: str,
    classification_value: str,
    ctx: Context,
    classification_system: Optional[str] = None,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add a classification facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        classification_value: Classification code or pattern
        ctx: FastMCP Context (auto-injected)
        classification_system: Classification system name or URI
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {"status": "added", "facet_type": "classification", "spec_id": "S1"}
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding classification facet: {classification_value} to {spec_id}")

        # Create classification facet using IfcTester
        classification = ids.Classification(
            value=classification_value,
            system=classification_system,
            cardinality=cardinality if location == "requirements" else None
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(classification)
        elif location == "requirements":
            spec.requirements.append(classification)
        else:
            raise ToolError(f"Invalid location: {location}")

        await ctx.info(f"Classification facet added: {classification_value}")

        return {
            "status": "added",
            "facet_type": "classification",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add classification facet: {str(e)}")
        raise ToolError(f"Failed to add classification facet: {str(e)}")


async def add_material_facet(
    spec_id: str,
    location: str,
    material_value: str,
    ctx: Context,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add a material facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        material_value: Material name, category, or URI
        ctx: FastMCP Context (auto-injected)
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {"status": "added", "facet_type": "material", "spec_id": "S1"}
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding material facet: {material_value} to {spec_id}")

        # Create material facet using IfcTester
        material = ids.Material(
            value=material_value,
            cardinality=cardinality if location == "requirements" else None
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(material)
        elif location == "requirements":
            spec.requirements.append(material)
        else:
            raise ToolError(f"Invalid location: {location}")

        await ctx.info(f"Material facet added: {material_value}")

        return {
            "status": "added",
            "facet_type": "material",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add material facet: {str(e)}")
        raise ToolError(f"Failed to add material facet: {str(e)}")


async def add_partof_facet(
    spec_id: str,
    location: str,
    relation: str,
    parent_entity: str,
    ctx: Context,
    parent_predefined_type: Optional[str] = None,
    cardinality: str = "required"
) -> Dict[str, Any]:
    """
    Add a partOf facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        relation: Relationship type (e.g., "IFCRELCONTAINEDINSPATIALSTRUCTURE")
        parent_entity: Parent entity name (e.g., "IFCSPACE")
        ctx: FastMCP Context (auto-injected)
        parent_predefined_type: Optional predefined type for parent
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {"status": "added", "facet_type": "partof", "spec_id": "S1"}
    """
    try:
        ids_obj = await get_or_create_session(ctx)
        spec = _find_specification(ids_obj, spec_id)

        await ctx.info(f"Adding partOf facet: {relation} to {spec_id}")

        # Create partOf facet using IfcTester
        # PartOf takes name directly, not an entity object
        part_of = ids.PartOf(
            name=parent_entity.upper(),
            predefinedType=parent_predefined_type,
            relation=relation.upper(),
            cardinality=cardinality if location == "requirements" else None
        )

        # Add to appropriate section
        if location == "applicability":
            spec.applicability.append(part_of)
        elif location == "requirements":
            spec.requirements.append(part_of)
        else:
            raise ToolError(f"Invalid location: {location}")

        await ctx.info(f"PartOf facet added: {relation}")

        return {
            "status": "added",
            "facet_type": "partof",
            "spec_id": spec_id
        }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Failed to add partOf facet: {str(e)}")
        raise ToolError(f"Failed to add partOf facet: {str(e)}")
