#!/bin/bash

# kindmesh Application Stopper
# This script stops the kindmesh application running in Docker Compose

echo "=== KindMesh Application Stopper ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check if the application is running
if ! [ "$(docker ps -q -f name=kindmesh-app)" ] && ! [ "$(docker ps -q -f name=kindmesh-neo4j)" ]; then
    echo "KindMesh application is not running!"
    exit 0
fi

# Stop the containers
echo "Stopping KindMesh application..."
docker-compose down

if [ $? -ne 0 ]; then
    echo "Error: Failed to stop the application"
    echo "Please check the error messages above and try again"
    exit 1
fi

echo ""
echo "=== KindMesh Application Stopped Successfully! ==="
echo ""
echo "To start the application again, run: ./start.sh"
echo ""

exit 0