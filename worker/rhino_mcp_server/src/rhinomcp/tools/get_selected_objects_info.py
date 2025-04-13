from mcp.server.fastmcp import Context
import json
from rhinomcp import get_rhino_connection, mcp, logger

@mcp.tool()
def get_selected_objects_info(ctx: Context) -> str:
    """Get detailed information about the currently selected objects in Rhino"""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("get_selected_objects_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting selected objects from Rhino: {str(e)}")
        return f"Error getting selected objects: {str(e)}"

