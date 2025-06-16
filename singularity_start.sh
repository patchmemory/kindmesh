#!/bin/bash

# kindmesh Singularity Container Starter
# This script starts the Neo4j Singularity container

echo "=== KindMesh Singularity Container Starter ==="

# Check if Singularity is installed
if ! command -v singularity &> /dev/null; then
    echo "Error: Singularity is not installed or not in PATH"
    echo "Please install Singularity from https://sylabs.io/guides/latest/user-guide/quick_start.html"
    exit 1
fi

# Check if the container exists
if [ ! -f "neo4j.sif" ]; then
    echo "Error: Neo4j Singularity container not found"
    echo "Please build the container first using: ./singularity_build.sh"
    exit 1
fi

# Create directories for data persistence if they don't exist
mkdir -p neo4j_data
mkdir -p neo4j_logs
mkdir -p neo4j_import
mkdir -p neo4j_plugins

# Start the container
echo "Starting Neo4j Singularity container..."
singularity instance start \
    --bind neo4j_data:/data \
    --bind neo4j_logs:/logs \
    --bind neo4j_import:/var/lib/neo4j/import \
    --bind neo4j_plugins:/plugins \
    neo4j.sif neo4j

if [ $? -ne 0 ]; then
    echo "Error: Failed to start the Singularity container"
    echo "Please check the error messages above and try again"
    exit 1
fi

echo ""
echo "=== Neo4j Singularity Container Started Successfully! ==="
echo ""
echo "Neo4j is now running and accessible at:"
echo "  - HTTP: http://localhost:7474"
echo "  - Bolt: bolt://localhost:7687"
echo ""
echo "Default credentials:"
echo "  - Username: neo4j"
echo "  - Password: kindmesh"
echo ""
echo "To stop the container, run: singularity instance stop neo4j"
echo ""

exit 0