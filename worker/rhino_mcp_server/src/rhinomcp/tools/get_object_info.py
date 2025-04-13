from mcp.server.fastmcp import Context
import json
from rhinomcp import get_rhino_connection, mcp, logger

@mcp.tool()
def get_object_info(ctx: Context, id: str = None, name: str = None) -> str:
    """
    Get detailed information about a specific object in the Rhino document.
    You can either provide the id or the object_name of the object to get information about.
    If both are provided, the id will be used.
    
    Parameters:
    - id: The id of the object to get information about
    - name: The name of the object to get information about
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("get_object_info", {"id": id, "name": name})
        
        # Just return the JSON representation of what Rhino sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info from Rhino: {str(e)}")
        return f"Error getting object info: {str(e)}"
