#!/bin/bash

# Test script for kindmesh application setup
# This script verifies that the Docker containers can be built and started

echo "=== KindMesh Setup Test ==="
echo "Testing Docker Compose configuration..."

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

# Validate docker-compose.yml
echo "Validating docker-compose.yml..."
docker-compose config > /dev/null
if [ $? -ne 0 ]; then
    echo "Error: docker-compose.yml is invalid"
    exit 1
else
    echo "docker-compose.yml is valid"
fi

# Test building the containers
echo "Building containers (this may take a few minutes)..."
docker-compose build --no-cache
if [ $? -ne 0 ]; then
    echo "Error: Failed to build containers"
    exit 1
else
    echo "Containers built successfully"
fi

# Start the containers in detached mode
echo "Starting containers..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "Error: Failed to start containers"
    exit 1
else
    echo "Containers started successfully"
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if Neo4j is running
echo "Checking Neo4j container..."
if [ "$(docker ps -q -f name=kindmesh-neo4j)" ]; then
    echo "Neo4j container is running"
else
    echo "Error: Neo4j container is not running"
    docker-compose logs neo4j
    docker-compose down
    exit 1
fi

# Check if app is running
echo "Checking app container..."
if [ "$(docker ps -q -f name=kindmesh-app)" ]; then
    echo "App container is running"
else
    echo "Error: App container is not running"
    docker-compose logs app
    docker-compose down
    exit 1
fi

# Check if Streamlit is accessible
echo "Checking if Streamlit is accessible..."
if command -v curl &> /dev/null; then
    curl -s --head http://localhost:8501 | grep "200 OK" > /dev/null
    if [ $? -eq 0 ]; then
        echo "Streamlit is accessible at http://localhost:8501"
    else
        echo "Warning: Streamlit may not be accessible yet. Check http://localhost:8501 manually."
    fi
else
    echo "Warning: curl not found, can't check if Streamlit is accessible. Check http://localhost:8501 manually."
fi

echo "=== Setup Test Complete ==="
echo "The application should be running at http://localhost:8501"
echo "Default login: Username 'Hello', Password 'World!'"
echo ""
echo "To stop the application, run: docker-compose down"

exit 0