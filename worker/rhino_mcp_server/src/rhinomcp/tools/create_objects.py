from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict


@mcp.tool()
def create_objects(
    ctx: Context,
    objects: List[Dict[str, Any]]
) -> str:
    """
    Create multiple objects at once in the Rhino document.
    
    Parameters:
    - objects: A list of dictionaries, each containing the parameters for a single object

    Each object should have the following values:
    - type: Object type ("POINT", "LINE", "POLYLINE", "BOX", "SPHERE", etc.)
    - name: Optional name for the object
    - color: Optional [r, g, b] color values (0-255) for the object
    - params: Type-specific parameters dictionary (see documentation for each type in create_object() function)
    - translation: Optional [x, y, z] translation vector
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale factors

    Returns:
    A message indicating the created objects.
    
    Examples of params:
    [
        {
            "type": "POINT",
            "name": "Point 1",
            "params": {"x": 0, "y": 0, "z": 0}
        },
        {
            "type": "LINE",
            "name": "Line 1",
            "params": {"start": [0, 0, 0], "end": [1, 1, 1]}
        },
        {
            "type": "POLYLINE",
            "name": "Polyline 1",
            "params": {"points": [[0, 0, 0], [1, 1, 1], [2, 2, 2]]}
        },
        {
            "type": "CURVE",
            "name": "Curve 1",
            "params": {"points": [[0, 0, 0], [1, 1, 1], [2, 2, 2]], "degree": 3}
        },
        {
            "type": "BOX",
            "name": "Box 1",
            "color": [255, 0, 0],
            "params": {"width": 1.0, "length": 1.0, "height": 1.0},
            "translation": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1]
        },
        {
            "type": "SPHERE",
            "name": "Sphere 1",
            "color": [0, 255, 0],
            "params": {"radius": 1.0},
            "translation": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1]
        }
    ]
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()
        command_params = {}
        for obj in objects:
            command_params[obj["name"]] = obj
        result = rhino.send_command("create_objects", command_params)
  
        
        return f"Created {len(result)} objects"
    except Exception as e:
        logger.error(f"Error creating object: {str(e)}")
        return f"Error creating object: {str(e)}"

