#!/bin/bash

# kindmesh Singularity Installer
# This script installs Singularity if it is not already installed

echo "=== KindMesh Singularity Installer ==="

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

# Check if Singularity is already installed
if command -v singularity &> /dev/null; then
    echo "Singularity is already installed."
else
    echo "Singularity is not installed. Installing..."
    
    detect_os
    
    # Install Singularity based on OS
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Install dependencies
        sudo apt-get update
        sudo apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev wget pkg-config git cryptsetup-bin
        
        # Install Go (required for Singularity)
        export VERSION=1.17.3 OS=linux ARCH=amd64
        wget -O /tmp/go${VERSION}.${OS}-${ARCH}.tar.gz https://dl.google.com/go/go${VERSION}.${OS}-${ARCH}.tar.gz
        sudo tar -C /usr/local -xzf /tmp/go${VERSION}.${OS}-${ARCH}.tar.gz
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        source ~/.bashrc
        
        # Download Singularity
        export VERSION=3.8.4
        wget -O /tmp/singularity-${VERSION}.tar.gz https://github.com/hpcng/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz
        tar -xzf /tmp/singularity-${VERSION}.tar.gz -C /tmp
        cd /tmp/singularity-${VERSION}
        
        # Build and install Singularity
        ./mconfig
        make -C builddir
        sudo make -C builddir install
        
        echo "Singularity installed successfully."
    
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        # Install dependencies
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y openssl-devel libuuid-devel libseccomp-devel wget squashfs-tools cryptsetup
        
        # Install Go (required for Singularity)
        export VERSION=1.17.3 OS=linux ARCH=amd64
        wget -O /tmp/go${VERSION}.${OS}-${ARCH}.tar.gz https://dl.google.com/go/go${VERSION}.${OS}-${ARCH}.tar.gz
        sudo tar -C /usr/local -xzf /tmp/go${VERSION}.${OS}-${ARCH}.tar.gz
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        source ~/.bashrc
        
        # Download Singularity
        export VERSION=3.8.4
        wget -O /tmp/singularity-${VERSION}.tar.gz https://github.com/hpcng/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz
        tar -xzf /tmp/singularity-${VERSION}.tar.gz -C /tmp
        cd /tmp/singularity-${VERSION}
        
        # Build and install Singularity
        ./mconfig
        make -C builddir
        sudo make -C builddir install
        
        echo "Singularity installed successfully."
    
    else
        echo "Unsupported OS: $OS"
        echo "Please install Singularity manually from https://sylabs.io/guides/latest/user-guide/quick_start.html"
        exit 1
    fi
fi

# Verify installation
echo "Verifying installation..."
singularity --version

echo ""
echo "=== Singularity installed successfully! ==="
echo ""
echo "You can now build and start the Neo4j container using:"
echo "  ./singularity_build.sh"
echo "  ./singularity_start.sh"
echo ""

# Ask if user wants to build and start the container now
read -p "Do you want to build and start the Neo4j container now? (y/n): " START_CONTAINER
if [[ "$START_CONTAINER" == "y" ]] || [[ "$START_CONTAINER" == "Y" ]]; then
    ./singularity_build.sh
    ./singularity_start.sh
fi

exit 0