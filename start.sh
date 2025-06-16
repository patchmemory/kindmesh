#!/bin/bash

# kindmesh Application Launcher
# This script launches the kindmesh application using Docker Compose

echo "=== KindMesh Application Launcher ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed or not in PATH"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if the application is already running
if [ "$(docker ps -q -f name=kindmesh-app)" ]; then
    echo "KindMesh application is already running!"
    echo "You can access it at: http://localhost:8501"
    echo ""
    echo "To stop the application, run: ./stop.sh"
    exit 0
fi

# Start the containers in detached mode
echo "Starting KindMesh application..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "Error: Failed to start the application"
    echo "Please check the error messages above and try again"
    exit 1
fi

echo "Waiting for services to be ready..."
sleep 5

# Check if containers are running
if ! [ "$(docker ps -q -f name=kindmesh-neo4j)" ] || ! [ "$(docker ps -q -f name=kindmesh-app)" ]; then
    echo "Error: One or more containers failed to start"
    docker-compose logs
    echo "Stopping containers..."
    docker-compose down
    exit 1
fi

echo ""
echo "=== KindMesh Application Started Successfully! ==="
echo ""
echo "The application is now running at: http://localhost:8501"
echo ""
echo "Default login credentials:"
echo "  Username: Hello"
echo "  Password: World!"
echo ""
echo "After logging in, you can create your first user who will become an Admin."
echo ""
echo "To stop the application, run: ./stop.sh"
echo ""

exit 0