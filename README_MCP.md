# PlantUML MCP Server

This is a Model Context Protocol (MCP) server that exposes PlantUML diagram generation functionality through the MCP protocol. It allows AI assistants and other MCP clients to generate UML diagrams from text descriptions.

## Features

- Generate PlantUML diagrams in SVG or PNG format
- Validate PlantUML code with detailed error messages
- Access diagram templates for different UML diagram types
- View example diagrams
- Create diagrams from templates with customizations
- Convert text descriptions to PlantUML diagrams (basic implementation)

## Prerequisites

- Python 3.8+
- PlantUML server (local or remote)
- MCP client (like Claude Desktop)

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set the PlantUML server URL (optional):

```bash
export PLANTUML_SERVER="http://127.0.0.1:8000/plantuml/"
```

By default, it uses `http://127.0.0.1:8000/plantuml/` which is the local PlantUML server.

## Usage

### Starting the MCP Server

Run the server:

```bash
python plantuml_mcp_server.py
```

This will start the MCP server on port 8765 (default). You can change the port by setting the `PORT` environment variable:

```bash
PORT=9000 python plantuml_mcp_server.py
```

### Connecting to the MCP Server

You can connect to the MCP server using any MCP client, such as Claude Desktop:

1. Open Claude Desktop
2. Go to Settings > MCP Servers
3. Add a new server with the URL: `http://localhost:8765/sse`
4. Restart Claude Desktop

### Available MCP Resources

- `plantuml://info` - Information about the PlantUML server
- `plantuml://examples` - Examples of PlantUML diagrams
- `plantuml://templates/{diagram_type}` - Templates for specific diagram types (class, sequence, component, activity, usecase)

### Available MCP Tools

- `generate_diagram_base64(uml_code: str, format_type: str = "svg", timeout: int = 30) -> str` - Generate a diagram from PlantUML code and return it as a base64 encoded string
- `validate_plantuml(uml_code: str) -> Dict[str, Union[bool, str]]` - Validate PlantUML code and return validation result with error message if any
- `create_diagram_from_template(diagram_type: str, customizations: str) -> str` - Create a diagram from a template with customizations
- `convert_text_to_diagram(text_description: str, diagram_type: str = "class") -> Dict[str, str]` - Convert a text description to a PlantUML diagram

## Example Usage

Once connected to an MCP client like Claude, you can use the PlantUML server like this:

```
Can you create a class diagram for a simple blog system with User, Post, and Comment classes?
```

The AI assistant can then use the MCP server to generate the diagram and display it.

## License

This project is licensed under the same license as the main PlantUML web project.
