"""Document management MCP tools."""

from typing import Optional, Dict, Any, List
from pathlib import Path
from fastmcp import Context
from fastmcp.exceptions import ToolError
from ifctester import ids

from ids_mcp_server.session.manager import (
    get_or_create_session,
    create_session_from_file,
    create_session_from_string
)
from ids_mcp_server.session.storage import get_session_storage


async def create_ids(
    title: str,
    ctx: Context,
    author: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    description: Optional[str] = None,
    copyright: Optional[str] = None,
    milestone: Optional[str] = None,
    purpose: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new IDS document for this session.

    Session is automatically tracked by FastMCP - no session_id parameter needed!

    Args:
        title: Document title (required)
        ctx: FastMCP Context (auto-injected)
        author: Author email or name
        version: Version string
        date: Date in YYYY-MM-DD format
        description: Document description
        copyright: Copyright notice
        milestone: Project milestone
        purpose: Purpose of this IDS

    Returns:
        {
            "status": "created",
            "session_id": "auto-generated-by-fastmcp",
            "title": "..."
        }
    """
    try:
        await ctx.info(f"Creating IDS: {title}")

        # Create new IDS using IfcTester
        ids_obj = ids.Ids(
            title=title,
            author=author,
            version=version,
            date=date,
            description=description,
            copyright=copyright,
            milestone=milestone,
            purpose=purpose
        )

        # Store in session
        storage = get_session_storage()
        session_id = ctx.session_id

        from ids_mcp_server.session.models import SessionData
        session_data = SessionData(session_id=session_id)
        session_data.ids_obj = ids_obj
        session_data.set_ids_title(title)
        storage.set(session_id, session_data)

        await ctx.info(f"IDS created successfully for session {session_id}")

        return {
            "status": "created",
            "session_id": session_id,
            "title": title
        }

    except Exception as e:
        await ctx.error(f"Failed to create IDS: {str(e)}")
        raise ToolError(f"Failed to create IDS: {str(e)}")


async def load_ids(
    source: str,
    ctx: Context,
    source_type: str = "file"
) -> Dict[str, Any]:
    """
    Load an existing IDS file into the current session.

    Replaces any existing IDS in this session.

    Args:
        source: File path or XML string
        ctx: FastMCP Context (auto-injected)
        source_type: "file" or "string"

    Returns:
        {
            "status": "loaded",
            "title": "...",
            "specification_count": 3,
            "specifications": [...]
        }
    """
    try:
        if source_type == "file":
            ids_obj = await create_session_from_file(ctx, source)
        elif source_type == "string":
            ids_obj = await create_session_from_string(ctx, source)
        else:
            raise ToolError(f"Invalid source_type: {source_type}. Must be 'file' or 'string'")

        # Build specification summary
        spec_list = []
        for spec in ids_obj.specifications:
            spec_list.append({
                "name": spec.name,
                "identifier": getattr(spec, 'identifier', None),
                "ifc_versions": spec.ifcVersion if hasattr(spec, 'ifcVersion') else []
            })

        return {
            "status": "loaded",
            "title": ids_obj.info.get("title", "Untitled"),
            "author": ids_obj.info.get("author"),
            "specification_count": len(ids_obj.specifications),
            "specifications": spec_list
        }

    except FileNotFoundError as e:
        await ctx.error(f"File not found: {str(e)}")
        raise ToolError(f"File not found: {str(e)}")
    except Exception as e:
        await ctx.error(f"Failed to load IDS: {str(e)}")
        raise ToolError(f"Failed to load IDS: {str(e)}")


async def export_ids(
    ctx: Context,
    output_path: Optional[str] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Export IDS document to XML file using IfcTester.

    Uses current session automatically - no session_id parameter needed!

    Args:
        ctx: FastMCP Context (auto-injected)
        output_path: File path (optional, returns XML string if not provided)
        validate: Whether to validate against XSD (default: True)

    Returns:
        {
            "status": "exported",
            "xml": "...",  # If no output_path
            "file_path": "...",  # If output_path provided
            "validation": {"valid": true, "errors": []}
        }
    """
    try:
        # Get IDS from session
        ids_obj = await get_or_create_session(ctx)

        validation_result = {"valid": True, "errors": []}

        # Export based on whether path is provided
        if output_path:
            await ctx.info(f"Exporting IDS to file: {output_path}")
            # Create parent directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            ids_obj.to_xml(output_path)

            # Validate if requested
            if validate:
                try:
                    validated_ids = ids.open(output_path, validate=True)
                    validation_result["valid"] = True
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"] = [str(e)]

            await ctx.info(f"IDS exported successfully to {output_path}")

            return {
                "status": "exported",
                "file_path": output_path,
                "validation": validation_result
            }
        else:
            await ctx.info("Exporting IDS to XML string")
            xml_string = ids_obj.to_string()

            # Validate if requested
            if validate:
                try:
                    validated_ids = ids.from_string(xml_string, validate=True)
                    validation_result["valid"] = True
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"] = [str(e)]

            await ctx.info("IDS exported successfully to XML string")

            return {
                "status": "exported",
                "xml": xml_string,
                "validation": validation_result
            }

    except Exception as e:
        await ctx.error(f"Failed to export IDS: {str(e)}")
        raise ToolError(f"Failed to export IDS: {str(e)}")


async def get_ids_info(ctx: Context) -> Dict[str, Any]:
    """
    Get current session's IDS document structure.

    Uses current session automatically - no session_id parameter needed!

    Args:
        ctx: FastMCP Context (auto-injected)

    Returns:
        {
            "title": "...",
            "author": "...",
            "specification_count": 3,
            "specifications": [...]
        }
    """
    try:
        # Get IDS from session
        ids_obj = await get_or_create_session(ctx)

        # Build specification summary
        spec_list = []
        for spec in ids_obj.specifications:
            spec_list.append({
                "identifier": getattr(spec, 'identifier', None),
                "name": spec.name,
                "ifc_versions": spec.ifcVersion if hasattr(spec, 'ifcVersion') else [],
                "applicability_facets": len(spec.applicability) if hasattr(spec, 'applicability') else 0,
                "requirement_facets": len(spec.requirements) if hasattr(spec, 'requirements') else 0
            })

        return {
            "title": ids_obj.info.get("title"),
            "author": ids_obj.info.get("author"),
            "version": ids_obj.info.get("version"),
            "description": ids_obj.info.get("description"),
            "specification_count": len(ids_obj.specifications),
            "specifications": spec_list
        }

    except Exception as e:
        await ctx.error(f"Failed to get IDS info: {str(e)}")
        raise ToolError(f"Failed to get IDS info: {str(e)}")
