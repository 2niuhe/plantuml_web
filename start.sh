#!/bin/bash

# Start the PlantUML server
echo "Starting PlantUML server..."
java -DPLANTUML_LIMIT_SIZE=8192 -jar plantuml.jar -picoweb:8000 &
PLANTUML_SERVER_PID=$!

# Wait for the PlantUML server to start
echo "Waiting for PlantUML server to start..."
sleep 3

# Start the PlantUML web interface
echo "Starting PlantUML web interface..."
python main.py &
WEB_PID=$!

# Wait for the web interface to start
echo "Waiting for web interface to start..."
sleep 3

# Start the MCP server
echo "Starting PlantUML MCP server..."
python plantuml_mcp_server.py &
MCP_PID=$!

echo "All services started!"
echo "- PlantUML server: http://localhost:8000"
echo "- Web interface: http://localhost:8080"
echo "- MCP server: http://localhost:8765/sse"

# Handle termination signals
cleanup() {
    echo "Shutting down services..."
    kill $MCP_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    kill $PLANTUML_SERVER_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep the script running
while true; do
    sleep 10
done
