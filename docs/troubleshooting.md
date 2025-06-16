# KindMesh Troubleshooting Guide

This guide provides solutions for common issues you might encounter when setting up and running KindMesh.

## Installation Issues

### Docker Installation

#### Docker or Docker Compose Not Found

**Symptoms:**
- Error message: `docker: command not found` or `docker-compose: command not found`
- The start.sh script fails with a message about Docker not being installed

**Solutions:**
1. Run the automated installation script:
   ```
   chmod +x install_docker.sh
   ./install_docker.sh
   ```

2. If the script fails, install Docker manually:
   - For Ubuntu/Debian:
     ```
     sudo apt update
     sudo apt install docker.io docker-compose
     sudo systemctl enable --now docker
     sudo usermod -aG docker $USER
     ```
   - For CentOS/RHEL:
     ```
     sudo yum install -y yum-utils
     sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
     sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin
     sudo systemctl enable --now docker
     sudo usermod -aG docker $USER
     ```
   - For macOS:
     - Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

3. After installation, log out and log back in for group changes to take effect

#### Permission Denied

**Symptoms:**
- Error message: `permission denied while trying to connect to the Docker daemon socket`

**Solutions:**
1. Add your user to the docker group:
   ```
   sudo usermod -aG docker $USER
   ```
2. Log out and log back in for the changes to take effect
3. If you're still having issues, try running the commands with sudo

### Local Installation

#### Python Version Issues

**Symptoms:**
- Error message about Python version being too old
- ImportError for modules that should be available

**Solutions:**
1. Check your Python version:
   ```
   python --version
   ```
2. If it's older than 3.12, install a newer version:
   - For Ubuntu/Debian:
     ```
     sudo apt update
     sudo apt install python3.12 python3.12-venv python3.12-dev
     ```
   - For macOS:
     ```
     brew install python@3.12
     ```
3. Make sure you're using the correct Python version when creating the virtual environment:
   ```
   python3.12 -m venv venv
   ```

#### Package Installation Failures

**Symptoms:**
- Error messages during pip install
- Dependency conflicts

**Solutions:**
1. Try the clean setup option:
   ```
   ./local_setup.sh --clean
   ```
2. If specific packages are failing, try installing them manually:
   ```
   source venv/bin/activate
   pip install --upgrade pip
   pip install package-name
   ```
3. Check for system dependencies that might be missing:
   - For Ubuntu/Debian:
     ```
     sudo apt install build-essential libssl-dev libffi-dev python3-dev
     ```

## Database Issues

### Neo4j Connection Problems

**Symptoms:**
- Error message: `Failed to connect to Neo4j`
- Application starts but shows database connection errors

**Solutions:**
1. Check if the Neo4j container is running:
   ```
   docker ps | grep neo4j
   ```
2. If it's not running, start it:
   ```
   docker-compose up -d neo4j
   ```
3. Check the Neo4j logs for errors:
   ```
   docker-compose logs neo4j
   ```
4. Verify the Neo4j connection settings in the application:
   - Check that the URI, username, and password match what's in the docker-compose.yml file
   - Default values are:
     - URI: bolt://neo4j:7687
     - Username: neo4j
     - Password: kindmesh

### Database Initialization Issues

**Symptoms:**
- Error message about missing constraints or initial user
- Unable to log in with the default Greeter account

**Solutions:**
1. Check if the database was initialized:
   ```
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh "MATCH (u:User) RETURN u.username, u.role"
   ```
2. If no users are found, manually initialize the database:
   ```
   cat scripts/init-db.cypher | docker exec -i kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh
   ```
3. If you need to reset the database:
   ```
   docker-compose down -v
   docker-compose up -d
   ```

## Application Issues

### Streamlit Interface Problems

**Symptoms:**
- Blank page when accessing the application
- Interface elements not loading properly
- JavaScript errors in the browser console

**Solutions:**
1. Clear your browser cache and reload the page
2. Try a different browser
3. Check if the Streamlit container is running:
   ```
   docker ps | grep streamlit
   ```
4. Restart the Streamlit container:
   ```
   docker-compose restart streamlit
   ```
5. Check the Streamlit logs for errors:
   ```
   docker-compose logs streamlit
   ```

### Login Issues

**Symptoms:**
- Unable to log in with correct credentials
- No error message when logging in fails

**Solutions:**
1. Verify the default Greeter account:
   - Username: `Hello`
   - Password: `World!`
2. Check if the user exists in the database:
   ```
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh "MATCH (u:User {username: 'Hello'}) RETURN u.username, u.role"
   ```
3. If the user doesn't exist, the database may need to be reinitialized
4. If you've forgotten a password, you can reset it using the Neo4j shell:
   ```
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh
   ```
   Then run:
   ```
   MATCH (u:User {username: 'username'})
   SET u.password_hash = '$2b$12$K9oSxMW18aXF8z1VnJyXR.9/iOZBkQtTB9mf0A5WV5/xzv8Oq7bui'
   RETURN u.username;
   ```
   This resets the password to 'password'. Change it immediately after logging in.

### Data Not Showing Up

**Symptoms:**
- Interactions are logged but don't appear in the data view
- Recipients are created but don't show up in dropdowns

**Solutions:**
1. Check if the data exists in the database:
   ```
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh "MATCH (i:Interaction) RETURN count(i)"
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh "MATCH (r:Recipient) RETURN count(r)"
   ```
2. Refresh the page to reload the data
3. Check if you have the correct permissions to view the data
4. Verify that the data was saved correctly by examining the database directly

## Performance Issues

### Slow Application

**Symptoms:**
- Pages take a long time to load
- Operations like logging interactions are slow

**Solutions:**
1. Check system resources (CPU, memory) on the host machine
2. Increase resources allocated to Docker if possible
3. Optimize database queries by adding appropriate indexes:
   ```
   docker exec -it kindmesh-neo4j-1 cypher-shell -u neo4j -p kindmesh "CREATE INDEX ON :Interaction(timestamp)"
   ```
4. If the database has grown large, consider archiving old data

### Memory Issues

**Symptoms:**
- Out of memory errors
- Docker containers crashing

**Solutions:**
1. Increase memory limits in docker-compose.yml:
   ```yaml
   services:
     neo4j:
       deploy:
         resources:
           limits:
             memory: 2G
   ```
2. Restart the containers with the new settings:
   ```
   docker-compose up -d
   ```
3. If running locally, close other applications to free up memory

## Getting Additional Help

If you're still experiencing issues after trying the solutions in this guide:

1. Check the application logs for more detailed error messages:
   ```
   docker-compose logs
   ```

2. Search for similar issues in the project's issue tracker

3. Contact the development team with:
   - A description of the issue
   - Steps to reproduce the problem
   - Error messages and logs
   - Your environment details (OS, Docker version, etc.)