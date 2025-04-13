from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict


@mcp.tool()
def select_objects(
    ctx: Context,
    filters: Dict[str, Any] = {},
    filters_type: str = "and",
) -> str:
    """
    Select objects in the Rhino document.
    
    Parameters:
    - filters: A dictionary containing the filters. The filters parameter is necessary, unless it's empty, in which case all objects will be selected.
    - filters_type: The type of the filters, it's "and" or "or", default is "and"

    The filters dictionary can contain the following keys:
    - name: The name of the object
    - color: The color of the object, for example [255, 0, 0]

    Additionaly, rhino allows to have user custom attributes, which can be used to filters the objects.
    For example, if the object has a user custom attribute called "category", the filters dictionary can contain:
    - category: custom_attribute_value

    Example:
    filters = {
        "name": "object_name",
        "category": "custom_attribute_value"
    },
    filters_type = "or"
    

    Returns:
    A number indicating the number of objects that have been selected.
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()
        command_params = {
            "filters": filters,
            "filters_type": filters_type
        }

        result = rhino.send_command("select_objects", command_params)
          
        return f"Selected {result['count']} objects"
    except Exception as e:
        logger.error(f"Error selecting objects: {str(e)}")
        return f"Error selecting objects: {str(e)}"

