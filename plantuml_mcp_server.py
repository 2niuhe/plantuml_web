#!/usr/bin/env python3
"""
PlantUML MCP Server

This server provides PlantUML diagram generation functionality through MCP protocol.
It allows AI assistants and other MCP clients to generate UML diagrams from text descriptions.
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
import uvicorn
import os
import base64
import zlib
import string
import httpx
from typing import Literal, Dict, Union

# Import the PlantUML encoding/decoding functions from main.py
maketrans = bytes.maketrans
plantuml_alphabet = (
    string.digits + string.ascii_uppercase + string.ascii_lowercase + "-_"
)
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
b64_to_plantuml = maketrans(
    base64_alphabet.encode("utf-8"), plantuml_alphabet.encode("utf-8")
)
plantuml_to_b64 = maketrans(
    plantuml_alphabet.encode("utf-8"), base64_alphabet.encode("utf-8")
)

# PlantUML server URL
PLANTUML_SERVER = os.environ.get("PLANTUML_SERVER", "http://127.0.0.1:8000/plantuml/")

# Instantiate an MCP server with description
mcp = FastMCP(
    "PlantUML MCP Server",
    description="A server that provides PlantUML diagram generation functionality through MCP protocol.",
)


# Helper functions
def plantuml_encode(plantuml_text):
    """zlib compress the plantuml text and encode it for the plantuml server"""
    zlibbed_str = zlib.compress(plantuml_text.encode("utf-8"))
    compressed_string = zlibbed_str[2:-4]
    return (
        base64.b64encode(compressed_string).translate(b64_to_plantuml).decode("utf-8")
    )


def plantuml_decode(plantuml_url):
    """decode plantuml encoded url back to plantuml text"""
    data = base64.b64decode(plantuml_url.translate(plantuml_to_b64).encode("utf-8"))
    dec = zlib.decompressobj()  # without check the crc.
    header = b"x\x9c"
    return dec.decompress(header + data).decode("utf-8")


async def generate_diagram(uml_code: str, format_type: str = "svg", timeout: int = 30):
    """Generate a diagram from PlantUML code with optimized quality for PNG"""
    try:
        # Add @startuml and @enduml if not present
        if "@startuml" not in uml_code:
            uml_code = "@startuml\n" + uml_code
        if "@enduml" not in uml_code:
            uml_code = uml_code + "\n@enduml"

        # Apply high-quality settings for PNG format
        if format_type.lower() == "png":
            # Insert high-quality directives after @startuml
            lines = uml_code.split("\n")
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("@startuml"):
                    start_idx = i + 1
                    break

            # Insert quality improvement directives
            quality_directives = ["skinparam dpi 300",]

            for directive in quality_directives:
                lines.insert(start_idx, directive)
                start_idx += 1

            uml_code = "\n".join(lines)

        # Encode the PlantUML code
        uml_encoded = plantuml_encode(uml_code)

        # Construct the URL
        img_src = PLANTUML_SERVER
        img_src += "svg/" if format_type.lower() == "svg" else "png/"
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
async def generate_plantuml_image(
    uml_code: str, format_type: Literal["svg", "png"] = "png", timeout: int = 30
) -> ImageContent:
    """
    Generate high-quality UML diagrams(生成plantuml图) from PlantUML code and return as ImageContent.

    This tool converts PlantUML text descriptions into visual diagrams. It supports various
    UML diagram types including sequence diagrams, class diagrams, use case diagrams,
    activity diagrams, component diagrams, and more. The generated diagrams are optimized
    for clarity and can be used directly in documentation, presentations, or web content.

    WHEN TO USE THIS TOOL:
    - Create visual representations of system architecture or design
    - Generate sequence diagrams to show interaction flows
    - Draw class diagrams to illustrate object relationships
    - Create flowcharts and activity diagrams for process documentation
    - Visualize database schemas or component relationships
    - Convert textual descriptions into professional UML diagrams

    SUPPORTED DIAGRAM TYPES:
    - Sequence diagrams (@startuml -> @enduml)
    - Class diagrams (class definitions and relationships)
    - Use case diagrams (actors and use cases)
    - Activity diagrams (workflows and processes)
    - Component diagrams (system components)
    - State diagrams (state machines)
    - Object diagrams, deployment diagrams, and more

    Args:
        uml_code (str): The PlantUML code describing the diagram. Can include or omit
                       @startuml/@enduml tags (they will be added automatically if missing).

                       EXAMPLES:
                       - Simple sequence: "Alice -> Bob: Hello\\nBob -> Alice: Hi!"
                       - Class diagram: "class User {\\n  +name: string\\n  +email: string\\n}"
                       - Use case: "actor User\\nUser -> (Login)\\nUser -> (Register)"
                       - Activity: "start\\n:Process data;\\nif (valid?) then (yes)\\n  :Save;\\nelse (no)\\n  :Error;\\nendif\\nstop"

        format_type (str, optional): Output format for the diagram.
                                   - 'png': High-quality bitmap image (recommended for most uses)
                                   - 'svg': Scalable vector graphics (best for web integration and zooming)
                                   Defaults to 'png' for optimal quality.

        timeout (int, optional): Defaults to 30 seconds.

    Returns:
        ImageContent: An MCP ImageContent object containing the generated diagram.
                     The returned object has base64-encoded image data and proper MIME type.
                     Can be directly embedded in HTML, markdown, or other content formats.

    Raises:
        Exception: If diagram generation fails or times out
    """
    diagram_data = await generate_diagram(uml_code, format_type, timeout)
    image_base64 = base64.b64encode(diagram_data).decode("utf-8")
    mime_type = "image/svg+xml" if format_type == "svg" else "image/png"
    return ImageContent(type="image", data=image_base64, mimeType=mime_type)


@mcp.tool()
async def validate_plantuml_syntax(uml_code: str) -> Dict[str, Union[bool, str, None]]:
    """
    Validate PlantUML code by attempting to generate a diagram.

    Use this tool to check if PlantUML code is syntactically correct before
    generating a full diagram. This is useful for catching syntax errors early.

    Args:
        uml_code (str): The PlantUML code to validate.
                      Example: "@startuml\nAlice -> Bob: Hello\n@enduml"

    Returns:
        Dict[str, Union[bool, str, None]]: A dictionary containing:
            - valid (bool): True if the code is valid, False otherwise
            - error (str): Error message if validation fails, None if successful

    Example return value for valid code:
        {"valid": True, "error": None}

    Example return value for invalid code:
        {"valid": False, "error": "Syntax error at line 2"}
    """
    try:
        await generate_diagram(uml_code, "svg", 30)
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
