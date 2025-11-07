"""FastMCP server initialization and tool registration."""

from fastmcp import FastMCP, Context
from ids_mcp_server.config import IDSMCPConfig
from ids_mcp_server.tools import document, specification, facets, validation, restrictions


def create_server(config: IDSMCPConfig) -> FastMCP:
    """
    Create and configure FastMCP server instance.

    Args:
        config: Server configuration

    Returns:
        Configured FastMCP instance
    """
    mcp_server = FastMCP(
        name=config.server.name,
        # mask_error_details=config.server.mask_error_details  # Will enable when needed
    )

    # Register document management tools
    mcp_server.tool(document.create_ids)
    mcp_server.tool(document.load_ids)
    mcp_server.tool(document.export_ids)
    mcp_server.tool(document.get_ids_info)

    # Register specification management tools
    mcp_server.tool(specification.add_specification)

    # Register facet management tools
    mcp_server.tool(facets.add_entity_facet)
    mcp_server.tool(facets.add_property_facet)
    mcp_server.tool(facets.add_attribute_facet)
    mcp_server.tool(facets.add_classification_facet)
    mcp_server.tool(facets.add_material_facet)
    mcp_server.tool(facets.add_partof_facet)

    # Register validation tools
    mcp_server.tool(validation.validate_ids)
    mcp_server.tool(validation.validate_ifc_model)

    # Register restriction management tools
    mcp_server.tool(restrictions.add_enumeration_restriction)
    mcp_server.tool(restrictions.add_pattern_restriction)
    mcp_server.tool(restrictions.add_bounds_restriction)
    mcp_server.tool(restrictions.add_length_restriction)

    return mcp_server


# Create default server instance
from ids_mcp_server.config import load_config_from_env
config = load_config_from_env()
mcp = create_server(config)
