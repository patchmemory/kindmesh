#!/bin/bash

# KindMesh Docker Installer
# This script installs Docker and Docker Compose if they are not already installed

echo "=== KindMesh Docker Installer ==="

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    echo "Detected OS: $OS $VER"
}

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "Docker is already installed."
else
    echo "Docker is not installed. Installing..."
    
    detect_os
    
    # Install Docker based on OS
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Update package index
        sudo apt-get update
        
        # Install prerequisites
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        
        # Set up the stable repository
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        
        # Update package index again
        sudo apt-get update
        
        # Install Docker CE
        sudo apt-get install -y docker-ce
        
        # Add current user to docker group
        sudo usermod -aG docker $USER
        
        echo "Docker installed successfully. You may need to log out and back in for group changes to take effect."
    
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        # Install prerequisites
        sudo yum install -y yum-utils device-mapper-persistent-data lvm2
        
        # Add Docker repository
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        
        # Install Docker CE
        sudo yum install -y docker-ce
        
        # Start and enable Docker service
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # Add current user to docker group
        sudo usermod -aG docker $USER
        
        echo "Docker installed successfully. You may need to log out and back in for group changes to take effect."
    
    elif [[ "$OS" == *"Darwin"* ]]; then
        echo "For macOS, please install Docker Desktop from https://www.docker.com/products/docker-desktop"
        exit 1
    else
        echo "Unsupported OS: $OS"
        echo "Please install Docker manually from https://docs.docker.com/get-docker/"
        exit 1
    fi
fi

# Check if Docker Compose is already installed
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose is already installed."
else
    echo "Docker Compose is not installed. Installing..."
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo "Docker Compose installed successfully."
fi

# Verify installations
echo "Verifying installations..."
docker --version
docker-compose --version

echo ""
echo "=== Docker and Docker Compose installed successfully! ==="
echo ""
echo "You can now run the application using: ./start.sh"
echo ""

# Ask if user wants to start the application now
read -p "Do you want to start the application now? (y/n): " START_APP
if [[ "$START_APP" == "y" ]] || [[ "$START_APP" == "Y" ]]; then
    ./start.sh
fi

exit 0