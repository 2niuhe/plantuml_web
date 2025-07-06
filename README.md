# plantuml_web
Using nicegui as a PlantUML frontend, you can deploy PlantUML on an intranet.

It's a nicegui demo project with an added MCP (Model Context Protocol) server that exposes PlantUML functionality to AI assistants.

Plantuml jar version: plantuml-1.2025.3.jar

![demo](https://github.com/2niuhe/plantuml_web/blob/main/demo_img/demo.png)

## Features

### Web Interface
- Interactive PlantUML editor with live preview
- Save and load diagrams
- Responsive UI with resizable panels

### MCP Server
- Generate PlantUML diagrams in SVG or PNG format
- Validate PlantUML code with detailed error messages

## Usage:

### With Docker

```shell
docker build -t plantuml_web_mcp .

# or pull from dockerhub
# docker pull  2niuhe/plantuml_web_mcp:latest

docker run -d -p 8080:8080 -p 8765:8765 plantuml_web_mcp:latest
```

Then you can access:
- Web interface: http://127.0.0.1:8080
- MCP server: http://127.0.0.1:8765/sse

### Without Docker

```shell
pip install -r requirements.txt
sh start.sh
```

The start script will launch:
1. PlantUML server on port 8000
2. Web interface on port 8080
3. MCP server on port 8765

## Connecting to the MCP Server

You can connect to the MCP server using any MCP client, such as Claude Desktop:

1. Open Claude Desktop
2. Go to Settings > MCP Servers
3. Add a new server with the URL: `http://localhost:8765/sse`
4. Restart Claude Desktop

## Testing the MCP Server

A test client is provided to verify the MCP server functionality:

```shell
python test_plantuml_mcp.py http://localhost:8765/sse
```



## Available MCP Tools

- `generate_plantuml_image`: Generate a diagram image from PlantUML code
- `validate_plantuml_syntax`: Validate PlantUML code and return validation result


### ref

[Home · zauberzeug/nicegui Wiki](https://github.com/zauberzeug/nicegui/wiki)

[How to use nicegui for beginners？ · zauberzeug/nicegui · Discussion #1486](https://github.com/zauberzeug/nicegui/discussions/1486)

[Nicegui example and suggestions · zauberzeug/nicegui · Discussion #1778](https://github.com/zauberzeug/nicegui/discussions/1778)

[NiceGUI](https://nicegui.io/documentation)

[syejing/nicegui-reference-cn: NiceGUI 中文版本文档](https://github.com/syejing/nicegui-reference-cn?tab=readme-ov-file)

[(1) Use NiceGUI to watch images and do it from the COMMAND LINE! - YouTube](https://www.youtube.com/watch?v=eq0k642zQQ8)
