#!/bin/bash

# kindmesh Local Starter
# This script starts the kindmesh application locally without Docker

echo "=== KindMesh Local Starter ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./local_setup.sh first to set up the environment"
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set environment variables for Neo4j connection
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="kindmesh"

# Start the Streamlit application
echo "Starting KindMesh application..."
echo "The application will be available at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app/app.py

# Deactivate the virtual environment when done
deactivate

exit 0