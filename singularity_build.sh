#!/bin/bash

# kindmesh Singularity Container Builder
# This script builds a Singularity container for Neo4j

echo "=== KindMesh Singularity Container Builder ==="

# Check if Singularity is installed
if ! command -v singularity &> /dev/null; then
    echo "Error: Singularity is not installed or not in PATH"
    echo "Please install Singularity from https://sylabs.io/guides/latest/user-guide/quick_start.html"
    exit 1
fi

# Build the Singularity container
echo "Building Singularity container for Neo4j..."
singularity build --fakeroot neo4j.sif neo4j.def

if [ $? -ne 0 ]; then
    echo "Error: Failed to build the Singularity container"
    echo "Please check the error messages above and try again"
    exit 1
fi

echo ""
echo "=== Singularity Container Built Successfully! ==="
echo ""
echo "To start the Neo4j container, run: ./singularity_start.sh"
echo ""

exit 0