from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict


@mcp.tool()
def modify_objects(
    ctx: Context,
    objects: List[Dict[str, Any]],
    all: bool = None
) -> str:
    """
    Create multiple objects at once in the Rhino document.
    
    Parameters:
    - objects: A List of objects, each containing the parameters for a single object modification 
    - all: Optional boolean to modify all objects, if true, only one object is required in the objects dictionary

    Each object can have the following parameters:
    - id: The id of the object to modify
    - new_color: Optional [r, g, b] color values (0-255) for the object
    - translation: Optional [x, y, z] translation vector
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale factors
    - visible: Optional boolean to set visibility

    Returns:
    A message indicating the modified objects.
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()
        command_params = {}
        command_params["objects"] = objects
        if all:
            command_params["all"] = all
        result = rhino.send_command("modify_objects", command_params)
  
        
        return f"Modified {result['modified']} objects"
    except Exception as e:
        logger.error(f"Error modifying objects: {str(e)}")
        return f"Error modifying objects: {str(e)}"

