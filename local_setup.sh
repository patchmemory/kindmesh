#!/bin/bash

# kindmesh Local Setup
# This script sets up the kindmesh application for local development without Docker

# Check for cleanup flag
CLEANUP=false
if [ "$1" == "--clean" ] || [ "$1" == "-c" ]; then
    CLEANUP=true
fi

echo "=== KindMesh Local Setup ==="

# Check for system dependencies required for bcrypt
if [ "$CLEANUP" = true ]; then
    echo "Checking system dependencies for bcrypt..."
    if command -v apt-get &> /dev/null; then
        echo "Installing system dependencies using apt-get..."
        sudo apt-get update
        sudo apt-get install -y build-essential libffi-dev python3-dev
    elif command -v yum &> /dev/null; then
        echo "Installing system dependencies using yum..."
        sudo yum -y install gcc libffi-devel python3-devel
    elif command -v brew &> /dev/null; then
        echo "Installing system dependencies using brew..."
        brew install libffi
    else
        echo "Warning: Could not install system dependencies automatically."
        echo "You may need to manually install the following packages:"
        echo "  - build-essential/gcc"
        echo "  - libffi-dev/libffi-devel"
        echo "  - python3-dev/python3-devel"
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version (need 3.12 or later)
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ $(echo "$PYTHON_VERSION < 3.12" | bc) -eq 1 ]; then
    echo "Warning: Python version $PYTHON_VERSION detected, but KindMesh requires Python 3.12 or later"
    echo "Please upgrade your Python installation from https://www.python.org/downloads/"
    echo "Continuing anyway, but you may encounter compatibility issues..."
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed or not in PATH"
    echo "Please install pip for Python 3"
    exit 1
fi

# Check if virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    pip3 install virtualenv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install virtualenv"
        exit 1
    fi
fi

# Handle virtual environment creation or cleanup
if [ "$CLEANUP" = true ] && [ -d "venv" ]; then
    echo "Cleaning up existing virtual environment..."
    rm -rf venv
    echo "Creating new virtual environment..."
    virtualenv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
elif [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    virtualenv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
else
    echo "Virtual environment already exists, updating..."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Install kindmesh package in development mode
echo "Installing kindmesh package in development mode..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "Error: Failed to install kindmesh package"
    exit 1
fi

echo ""
echo "=== KindMesh Local Setup Completed Successfully! ==="
echo ""
echo "To start the application, run: ./local_start.sh"
echo ""
echo "If you encounter any issues with package compatibility, you can run:"
echo "./local_setup.sh --clean"
echo "This will remove the existing virtual environment and create a fresh one."
echo ""
echo "Note: This setup does not include Neo4j database. You will need to:"
echo "1. Install Neo4j Community Edition separately from https://neo4j.com/download/"
echo "2. Configure Neo4j to use the password 'kindmesh'"
echo "3. Install APOC libraries for Neo4j"
echo "4. Run the initialization script in scripts/init-db.cypher"
echo ""
echo "For detailed instructions, please refer to the README.md file."
echo ""

exit 0
