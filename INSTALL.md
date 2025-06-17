# Installation Guide for kindmesh

This guide provides instructions for installing and running the kindmesh application.

## Option 1: Install from PyPI (Recommended)

```bash
pip install kindmesh
```

## Option 2: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/patchmemory/kindmesh.git
   cd kindmesh
   ```

2. Install the package:
   ```bash
   pip install .
   ```

3. For development installation:
   ```bash
   pip install -e .
   ```

## Option 3: Using the Setup Scripts

For a complete local development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/patchmemory/kindmesh.git
   cd kindmesh
   ```

2. Run the setup script:
   ```bash
   ./local_setup.sh
   ```
   
   This script will:
   - Check for system dependencies
   - Create a virtual environment
   - Install all required dependencies
   - Install the kindmesh package in development mode

## Neo4j Database Setup

kindmesh requires a Neo4j database:

1. Install Neo4j Community Edition from https://neo4j.com/download/
2. Configure Neo4j to use the password 'kindmesh' (or update the environment variables)
3. Install APOC libraries for Neo4j
4. Run the initialization script in scripts/init-db.cypher

## Running the Application

After installation, you can run the application using:

```bash
# Start Neo4j database (required)
# See README.md for Neo4j setup instructions

# Run the application
kindmesh
```

Or run directly with Python:

```bash
python -m kindmesh.app
```

## Using the Local Start Script

If you used the setup script, you can start the application with:

```bash
./local_start.sh
```

## Environment Variables

The following environment variables can be set to configure the application:

- `NEO4J_URI`: URI for the Neo4j database (default: bolt://neo4j:7687)
- `NEO4J_USER`: Username for the Neo4j database (default: neo4j)
- `NEO4J_PASSWORD`: Password for the Neo4j database (default: kindmesh)

## Troubleshooting

If you encounter any issues:

1. Ensure Neo4j is running and accessible
2. Check that the Neo4j credentials are correct
3. For development installations, try reinstalling with:
   ```bash
   ./local_setup.sh --clean
   ```
4. Check the logs for specific error messages

For more detailed information, please refer to the README.md file.