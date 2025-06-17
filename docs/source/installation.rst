Installation
============

This guide provides instructions for installing and running the kindmesh application.

From PyPI
---------

The recommended way to install kindmesh is from PyPI:

.. code-block:: bash

    pip install kindmesh

From Source
-----------

You can also install kindmesh from source:

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/patchmemory/kindmesh.git
       cd kindmesh

2. Install the package:

   .. code-block:: bash

       pip install .

   For development installation:

   .. code-block:: bash

       pip install -e .

Using the Setup Scripts
----------------------

For a complete local development environment:

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/patchmemory/kindmesh.git
       cd kindmesh

2. Run the setup script:

   .. code-block:: bash

       ./local_setup.sh

   This script will:
   
   - Check for system dependencies
   - Create a virtual environment
   - Install all required dependencies
   - Install the kindmesh package in development mode

Neo4j Database Setup
-------------------

kindmesh requires a Neo4j database:

1. Install Neo4j Community Edition from https://neo4j.com/download/
2. Configure Neo4j to use the password 'kindmesh' (or update the environment variables)
3. Install APOC libraries for Neo4j
4. Run the initialization script in scripts/init-db.cypher

Environment Variables
--------------------

The following environment variables can be set to configure the application:

- ``NEO4J_URI``: URI for the Neo4j database (default: bolt://neo4j:7687)
- ``NEO4J_USER``: Username for the Neo4j database (default: neo4j)
- ``NEO4J_PASSWORD``: Password for the Neo4j database (default: kindmesh)