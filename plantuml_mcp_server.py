#!/usr/bin/env python3
"""
PlantUML MCP Server

This server provides PlantUML diagram generation functionality through MCP protocol.
It allows AI assistants and other MCP clients to generate UML diagrams from text descriptions.
"""

from mcp.server.fastmcp import FastMCP, Context
import uvicorn
import os
import base64
import zlib
import string
import httpx
import io
import json
import asyncio
from typing import Literal, Optional, Dict, List, Union, Any

# Import the PlantUML encoding/decoding functions from main.py
maketrans = bytes.maketrans
plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))
plantuml_to_b64 = maketrans(plantuml_alphabet.encode('utf-8'), base64_alphabet.encode('utf-8'))

# PlantUML server URL
PLANTUML_SERVER = os.environ.get("PLANTUML_SERVER", "http://127.0.0.1:8000/plantuml/")

# Instantiate an MCP server with description
mcp = FastMCP(
    "PlantUML MCP Server",
    description="A server that provides PlantUML diagram generation functionality through MCP protocol."
)

# Helper functions
def plantuml_encode(plantuml_text):
    """zlib compress the plantuml text and encode it for the plantuml server"""
    zlibbed_str = zlib.compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

def plantuml_decode(plantuml_url):
    """decode plantuml encoded url back to plantuml text"""
    data = base64.b64decode(plantuml_url.translate(plantuml_to_b64).encode("utf-8"))
    dec = zlib.decompressobj() # without check the crc.
    header = b'x\x9c'
    return dec.decompress(header + data).decode("utf-8")

async def generate_diagram(uml_code: str, format_type: str = "svg", timeout: int = 30):
    """Generate a diagram from PlantUML code"""
    try:
        # Add @startuml and @enduml if not present
        if "@startuml" not in uml_code:
            uml_code = "@startuml\n" + uml_code
        if "@enduml" not in uml_code:
            uml_code = uml_code + "\n@enduml"
            
        # Encode the PlantUML code
        uml_encoded = plantuml_encode(uml_code)
        
        # Construct the URL
        img_src = PLANTUML_SERVER
        img_src += 'svg/' if format_type.lower() == 'svg' else 'png/'
        url = img_src + uml_encoded
        
        # Fetch the diagram with timeout
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.content
            else:
                error_msg = f"Request failed, status code: {response.status_code}"
                if response.content:
                    error_msg += f", response: {response.content.decode('utf-8', errors='ignore')}"
                raise Exception(error_msg)
    except httpx.TimeoutException:
        raise Exception(f"Request timed out after {timeout} seconds")
    except Exception as e:
        raise Exception(f"Error generating diagram: {str(e)}")

# DEFINE TOOLS

@mcp.tool()
async def generate_diagram_base64(
    uml_code: str, 
    format_type: Literal["svg", "png"] = "svg",
    timeout: int = 30
) -> str:
    """
    Generate a diagram from PlantUML code and return it as a base64 encoded string.
    
    Args:
        uml_code: The PlantUML code to generate a diagram from
        format_type: The format of the diagram (svg or png)
        timeout: Timeout in seconds for the request
        
    Returns:
        A base64 encoded string of the diagram that can be displayed in HTML with an img tag
    """
    diagram_data = await generate_diagram(uml_code, format_type, timeout)
    base64_prefix = 'data:image/svg+xml;base64,' if format_type == 'svg' else 'data:image/png;base64,'
    image_base64 = base64.b64encode(diagram_data).decode("utf-8")
    return base64_prefix + image_base64

@mcp.tool()
async def validate_plantuml(uml_code: str) -> Dict[str, Union[bool, str]]:
    """
    Validate PlantUML code by attempting to generate a diagram.
    
    Args:
        uml_code: The PlantUML code to validate
        
    Returns:
        A dictionary with validation result and error message if any
    """
    try:
        await generate_diagram(uml_code)
        return {"valid": True, "error": None}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# Run the server with SSE transport
if __name__ == "__main__":
    # Default to port 8765 if not specified
    port = int(os.environ.get("PORT", 8765))
    
    # Create a FastAPI app with SSE transport
    app = mcp.sse_app()
    
    print(f"Starting PlantUML MCP Server with SSE transport on port {port}")
    print(f"Available at http://localhost:{port}/sse")
    print(f"Using PlantUML server at: {PLANTUML_SERVER}")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)
