import mcp.types as types
from rhinomcp.server import mcp
from pydantic import FileUrl


import os
from pathlib import Path

# Define path to static folder
STATIC_FOLDER = Path("./static")


@mcp.tool()
def get_rhinoscriptsyntax_resource(category: str) -> str:
    """
    Return the RhinoScriptsyntax for a specific category.

    Parameters:
    - category: The category of the RhinoScriptsyntax to get.

    The following categories are available:
    - application
    - block
    - compat
    - curve
    - dimension
    - document
    - geometry
    - grips
    - group
    - hatch
    - layer
    - light
    - line
    - linetype
    - material
    - mesh
    - object
    - plane
    - pointvector
    - selection
    - surface
    - toolbar
    - transformation
    - userdata
    - userinterface
    - utility
    - view
    """

    for file_path in STATIC_FOLDER.glob("*.py"):
        if file_path.name == f"{category}.py":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

                
