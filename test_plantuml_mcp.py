#!/usr/bin/env python3
"""
PlantUML MCP Client Tester

This script tests the PlantUML MCP server by connecting to it and calling its tools.
"""

import asyncio
import os
import sys
import traceback
from typing import Dict, Any, List, Optional
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
import base64
from pathlib import Path

# Test parameters for PlantUML MCP server tools
PLANTUML_TOOL_TESTS = {
    "generate_diagram_base64": {
        "uml_code": """
@startuml
Alice -> Bob: Hello
Bob --> Alice: Hi there
@enduml
""",
        "format_type": "svg"
    },
    "validate_plantuml": {
        "uml_code": """
@startuml
class User {
  +name: String
  +email: String
}
@enduml
"""
    },
    "create_diagram_from_template": {
        "diagram_type": "class",
        "customizations": """
class CustomClass {
  +customMethod()
  -privateField: int
}
"""
    },
    "convert_text_to_diagram": {
        "text_description": "A User can create many Posts, and each Post can have many Comments",
        "diagram_type": "class"
    }
}

# Resource URIs to test
PLANTUML_RESOURCE_TESTS = [
    "plantuml://info",
    "plantuml://examples",
    "plantuml://templates/class",
    "plantuml://templates/sequence",
    "plantuml://templates/component"
]

class PlantUMLMCPClient:
    def __init__(self):
        self.session = None
        self.available_tools = []
        self.available_resources = []
        self.output_dir = Path("./test_output")
        self.output_dir.mkdir(exist_ok=True)

    async def connect(self, server_url: str):
        print(f"Connecting to PlantUML MCP server at {server_url}")

        try:
            print("Creating SSE Client...")
            # Store the context managers but don't enter them yet
            self._streams_context = sse_client(url=server_url)
            streams = await self._streams_context.__aenter__()

            print("Creating MCP Session...")
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()

            print("Initializing Session...")
            await self.session.initialize()
            
            print("Getting Tool List...")
            response = await self.session.list_tools()
            self.available_tools = response.tools

            print("Getting Resource List...")
            response = await self.session.list_resources()
            self.available_resources = response.resources

            tool_names = [tool.name for tool in self.available_tools]
            resource_uris = [resource.uri for resource in self.available_resources]
            
            print(f'Connection Successful!')
            print(f'Available Tools: {tool_names}')
            print(f'Available Resources: {resource_uris}')

            return True
        except Exception as e:
            # If an error occurs during connection, clean up any partially initialized resources
            print(f'Connection Failed: {e}')
            print(traceback.format_exc())
            
            # Clean up any resources that might have been created
            await self.cleanup()
            return False
        
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if not self.session:
            print('Error: Not connected to MCP server')
            return "Not connected to MCP server"
        
        try:
            print(f'Calling Tool: {tool_name}')
            print(f'Parameters: {parameters}')

            result = await self.session.call_tool(tool_name, parameters)
            
            # Handle different result types
            if hasattr(result, 'content'):
                content_str = ""
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_str += item.text
                return content_str
            else:
                return result
        except Exception as e:
            error_msg = f"Tool execution failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            return error_msg
    
    async def read_resource(self, uri: str) -> str:
        if not self.session:
            print('Error: Not connected to MCP server')
            return "Not connected to MCP server"
        
        try:
            print(f'Reading Resource: {uri}')
            result = await self.session.read_resource(uri)
            
            if hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
        except Exception as e:
            error_msg = f"Resource read failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            return error_msg
    
    async def save_diagram(self, base64_data: str, filename: str):
        """Save a base64 encoded diagram to a file"""
        try:
            # Extract the actual base64 data after the prefix
            if "," in base64_data:
                _, data = base64_data.split(",", 1)
            else:
                data = base64_data
                
            # Determine file extension based on data prefix
            if "data:image/svg+xml;base64" in base64_data:
                ext = ".svg"
            else:
                ext = ".png"
                
            # Save to file
            output_path = self.output_dir / f"{filename}{ext}"
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(data))
            
            print(f"Saved diagram to {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"Error saving diagram: {e}")
            return None
    
    async def test_tools(self):
        if not self.session or not self.available_tools:
            print("Error: Not connected to MCP server or no tools available")
            return False
        
        print("\n===== Testing PlantUML MCP Tools =====\n")

        available_tool_names = {tool.name for tool in self.available_tools}
        results = []

        for tool_name, test_params in PLANTUML_TOOL_TESTS.items():
            if tool_name in available_tool_names:
                print(f"\nTesting Tool: {tool_name}")
                result = await self.call_tool(tool_name, test_params)
                
                # For diagram tools, save the output
                if tool_name == "generate_diagram_base64" or tool_name == "create_diagram_from_template":
                    if isinstance(result, str) and "base64" in result:
                        file_path = await self.save_diagram(result, f"test_{tool_name}")
                        success = "Success" if file_path else "Failed"
                        results.append({"tool": tool_name, "result": f"Saved to {file_path}", "status": success})
                    else:
                        results.append({"tool": tool_name, "result": "Invalid diagram data", "status": "Failed"})
                elif tool_name == "convert_text_to_diagram":
                    if isinstance(result, dict) and "diagram" in result:
                        file_path = await self.save_diagram(result["diagram"], f"test_{tool_name}")
                        success = "Success" if file_path else "Failed"
                        results.append({
                            "tool": tool_name, 
                            "result": f"Code: {result.get('plantuml_code', 'N/A')[:50]}..., Saved to {file_path}", 
                            "status": success
                        })
                    else:
                        results.append({"tool": tool_name, "result": str(result)[:100], "status": "Failed"})
                else:
                    success = "Success" if result and not isinstance(result, str) else "Failed"
                    results.append({"tool": tool_name, "result": str(result)[:100], "status": success})
            else:
                print(f"Skipping test for unavailable tool: {tool_name}")
        
        print("\n===== Tool Test Summary =====")
        for result in results:
            print(f"{result['tool']} {result['status']}: {result['result']}")
        
        all_success = all([r['status'] == "Success" for r in results])
        print(f"\nAll Tool Tests: {'Success' if all_success else 'Failed'}")

        return all_success
    
    async def test_resources(self):
        if not self.session:
            print("Error: Not connected to MCP server")
            return False
        
        print("\n===== Testing PlantUML MCP Resources =====\n")
        
        results = []
        
        for uri in PLANTUML_RESOURCE_TESTS:
            print(f"\nTesting Resource: {uri}")
            content = await self.read_resource(uri)
            
            if content and not content.startswith("Resource read failed"):
                # Truncate long content for display
                display_content = content[:100] + "..." if len(content) > 100 else content
                results.append({"uri": uri, "content": display_content, "status": "Success"})
            else:
                results.append({"uri": uri, "content": content, "status": "Failed"})
        
        print("\n===== Resource Test Summary =====")
        for result in results:
            print(f"{result['uri']} {result['status']}: {result['content']}")
        
        all_success = all([r['status'] == "Success" for r in results])
        print(f"\nAll Resource Tests: {'Success' if all_success else 'Failed'}")
        
        return all_success

    async def cleanup(self):
        try:
            if hasattr(self, '_session_context') and self._session_context:
                await self._session_context.__aexit__(None, None, None)
                self._session_context = None
                self.session = None
            
            if hasattr(self, '_streams_context') and self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
                self._streams_context = None
            
            print("Cleanup completed successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            print(traceback.format_exc())


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_plantuml_mcp.py <MCP Server URL>")
        print("Example: python test_plantuml_mcp.py http://localhost:8765/sse")
        sys.exit(1)
    
    server_url = sys.argv[1]
    client = PlantUMLMCPClient()

    try:
        if await client.connect(server_url):
            print('Connection successful')

            # Test tools
            await client.test_tools()
            
            # Test resources
            await client.test_resources()
            
            print("\nAll tests completed")
        else:
            print("Connection failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
    except asyncio.CancelledError:
        print("\nTask cancelled, shutting down...")
    except Exception as e:
        print('Execution failed')
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        print("\nCleaning up resources...")
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
