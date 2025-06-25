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

# DEFINE RESOURCES

@mcp.resource("plantuml://info")
def get_plantuml_info() -> str:
    """Get information about the PlantUML server"""
    return """
    This is a PlantUML MCP server that provides diagram generation functionality.
    
    PlantUML is an open-source tool that allows users to create UML diagrams from a plain text language.
    This server exposes PlantUML functionality through the Model Context Protocol (MCP).
    
    Available diagram types:
    - Class diagrams
    - Sequence diagrams
    - Use case diagrams
    - Activity diagrams
    - Component diagrams
    - State diagrams
    - Object diagrams
    - Deployment diagrams
    - Timing diagrams
    - Entity-Relationship diagrams
    """

@mcp.resource("plantuml://examples")
def get_examples() -> str:
    """Get examples of PlantUML diagrams"""
    examples = {
        "class": """@startuml
class User {
  +id: int
  +username: string
  +password: string
  +login()
  +logout()
}

class Post {
  +id: int
  +title: string
  +content: text
  +created_at: datetime
  +publish()
}

User "1" -- "*" Post : creates >
@enduml""",
        
        "sequence": """@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml""",
        
        "usecase": """@startuml
left to right direction
actor Customer
actor Clerk
rectangle Checkout {
  Customer -- (Checkout)
  (Checkout) .> (Payment) : include
  (Help) .> (Checkout) : extends
  (Checkout) -- Clerk
}
@enduml"""
    }
    
    result = "# PlantUML Examples\n\n"
    for diagram_type, example in examples.items():
        result += f"## {diagram_type.capitalize()} Diagram\n```\n{example}\n```\n\n"
    
    return result

@mcp.resource("plantuml://templates/{diagram_type}")
def get_template(diagram_type: str) -> str:
    """Get a template for a specific diagram type"""
    templates = {
        "class": """@startuml
' Class Diagram Template
class ClassName {
  +attribute: type
  -privateAttribute: type
  #protectedAttribute: type
  ~packageAttribute: type
  +method()
  -privateMethod()
}

class AnotherClass {
  +attribute: type
  +method()
}

ClassName -- AnotherClass: association
@enduml""",
        
        "sequence": """@startuml
' Sequence Diagram Template
actor Actor
participant "First Participant" as A
participant "Second Participant" as B
participant "Last Participant" as C

Actor -> A: Request
activate A
A -> B: Request
activate B
B -> C: Request
activate C
C --> B: Response
destroy C
B --> A: Response
deactivate B
A --> Actor: Response
deactivate A
@enduml""",
        
        "component": """@startuml
' Component Diagram Template
package "Package" {
  [Component 1]
  [Component 2]
}

node "Node" {
  database "Database" {
    [Component 3]
  }
}

[Component 1] --> [Component 2]
[Component 2] --> [Component 3]
@enduml""",
        
        "activity": """@startuml
' Activity Diagram Template
start
:Step 1;
if (Condition?) then (yes)
  :Step 2a;
else (no)
  :Step 2b;
endif
:Step 3;
stop
@enduml""",
        
        "usecase": """@startuml
' Use Case Diagram Template
left to right direction
actor User
rectangle System {
  User -- (Use Case 1)
  User -- (Use Case 2)
  (Use Case 1) ..> (Use Case 3) : includes
  (Use Case 4) .> (Use Case 2) : extends
}
@enduml"""
    }
    
    if diagram_type.lower() in templates:
        return templates[diagram_type.lower()]
    else:
        available_types = ", ".join(templates.keys())
        return f"Template not found. Available diagram types: {available_types}"

@mcp.tool()
async def create_diagram_from_template(
    diagram_type: Literal["class", "sequence", "component", "activity", "usecase"],
    customizations: str
) -> str:
    """
    Create a diagram from a template with customizations.
    
    Args:
        diagram_type: The type of diagram to create
        customizations: Custom PlantUML code to add to the template
        
    Returns:
        A base64 encoded string of the generated diagram
    """
    # Get the template
    template = get_template(diagram_type)
    
    # Replace the closing @enduml tag with the customizations and a new closing tag
    if "@enduml" in template:
        modified_template = template.replace("@enduml", f"{customizations}\n@enduml")
    else:
        modified_template = f"{template}\n{customizations}"
    
    # Generate the diagram
    return await generate_diagram_base64(modified_template)

@mcp.tool()
async def convert_text_to_diagram(
    text_description: str,
    diagram_type: Literal["class", "sequence", "component", "activity", "usecase"] = "class"
) -> Dict[str, str]:
    """
    Convert a text description to a PlantUML diagram. This is a best-effort conversion
    that tries to interpret the text description and generate appropriate PlantUML code.
    
    Args:
        text_description: A text description of what the diagram should contain
        diagram_type: The type of diagram to create
        
    Returns:
        A dictionary with the generated PlantUML code and base64 encoded diagram
    """
    # This is a simplified implementation - in a real-world scenario,
    # you might use an LLM to convert text to PlantUML code
    
    # Get the template as a starting point
    template = get_template(diagram_type)
    
    # For demonstration purposes, just add the text description as a comment
    # and return the template
    plantuml_code = f"@startuml\n' Generated from description: {text_description}\n\n"
    
    # Add some basic elements based on the diagram type and description
    if diagram_type == "class":
        # Extract potential class names from the description
        words = text_description.replace(',', ' ').replace('.', ' ').split()
        potential_classes = [w for w in words if w[0].isupper() and len(w) > 2]
        
        # Add unique class names (up to 3)
        classes = list(set(potential_classes))[:3]
        if not classes:
            classes = ["Class1", "Class2"]
            
        for cls in classes:
            plantuml_code += f"class {cls} {{\n  +attribute: type\n  +method()\n}}\n\n"
            
        # Add relationships
        if len(classes) > 1:
            plantuml_code += f"{classes[0]} -- {classes[1]}: relates to >\n"
    
    elif diagram_type == "sequence":
        # Extract potential actor names
        words = text_description.replace(',', ' ').replace('.', ' ').split()
        potential_actors = [w for w in words if w[0].isupper() and len(w) > 2][:2]
        
        if not potential_actors or len(potential_actors) < 2:
            potential_actors = ["Alice", "Bob"]
            
        plantuml_code += f"actor {potential_actors[0]}\nparticipant {potential_actors[1]}\n\n"
        plantuml_code += f"{potential_actors[0]} -> {potential_actors[1]}: Request\n"
        plantuml_code += f"{potential_actors[1]} --> {potential_actors[0]}: Response\n"
    
    # Add closing tag
    plantuml_code += "@enduml"
    
    # Generate the diagram
    diagram_base64 = await generate_diagram_base64(plantuml_code)
    
    return {
        "plantuml_code": plantuml_code,
        "diagram": diagram_base64
    }

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
