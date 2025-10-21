#!/bin/bash
# Setup script for discovery tools using hybrid approach
# This script sets up both local and Docker-based tools

set -e

echo "🔧 Setting up Discovery Tools (Hybrid Approach)"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker availability..."
    if docker --version > /dev/null 2>&1; then
        print_success "Docker is available"
        return 0
    else
        print_error "Docker is not available"
        return 1
    fi
}

# Check local tool availability
check_local_tools() {
    print_status "Checking local tool availability..."
    
    local tools=("subfinder" "nuclei" "feroxbuster" "waybackurls")
    local available_tools=()
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            available_tools+=("$tool")
            print_success "$tool is available locally"
        else
            missing_tools+=("$tool")
            print_warning "$tool is not available locally"
        fi
    done
    
    echo ""
    print_status "Local tools available: ${#available_tools[@]}/${#tools[@]}"
    print_status "Available: ${available_tools[*]}"
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_warning "Missing: ${missing_tools[*]}"
    fi
}

# Setup Docker-based tools
setup_docker_tools() {
    print_status "Setting up Docker-based discovery tools..."
    
    # Start discovery-tools container if not running
    if ! docker ps | grep -q "discovery-tools"; then
        print_status "Starting discovery-tools container..."
        cd "$(dirname "$0")"
        docker-compose up -d discovery-tools
    else
        print_success "Discovery-tools container is already running"
    fi
    
    # Test Docker tools
    print_status "Testing Docker-based tools..."
    
    local docker_tools=("httpx" "katana" "gospider")
    for tool in "${docker_tools[@]}"; do
        if docker exec discovery-tools_1 "$tool" --version > /dev/null 2>&1; then
            print_success "$tool is available in Docker"
        else
            print_warning "$tool test failed in Docker"
        fi
    done
}

# Create wrapper scripts for local use
create_wrapper_scripts() {
    print_status "Creating wrapper scripts for local use..."
    
    local script_dir="$(dirname "$0")/scripts"
    local local_bin="$HOME/.local/bin"
    
    # Create local bin directory if it doesn't exist
    mkdir -p "$local_bin"
    
    # Copy wrapper scripts to local bin
    cp "$script_dir"/*-docker "$local_bin/"
    chmod +x "$local_bin"/*-docker
    
    # Create symlinks for easier access
    ln -sf "$local_bin/httpx-docker" "$local_bin/httpx" 2>/dev/null || true
    ln -sf "$local_bin/katana-docker" "$local_bin/katana" 2>/dev/null || true
    ln -sf "$local_bin/gospider-docker" "$local_bin/gospider" 2>/dev/null || true
    
    print_success "Wrapper scripts created in $local_bin"
}

# Test the hybrid setup
test_hybrid_setup() {
    print_status "Testing hybrid setup..."
    
    # Test local tools
    local local_tools=("subfinder" "nuclei" "feroxbuster" "waybackurls")
    for tool in "${local_tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            print_success "$tool (local) - OK"
        else
            print_warning "$tool (local) - Not available"
        fi
    done
    
    # Test Docker tools
    local docker_tools=("httpx" "katana" "gospider")
    for tool in "${docker_tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            print_success "$tool (Docker wrapper) - OK"
        else
            print_warning "$tool (Docker wrapper) - Not available"
        fi
    done
}

# Main execution
main() {
    echo ""
    print_status "Starting discovery tools setup..."
    echo ""
    
    # Check prerequisites
    if ! check_docker; then
        print_error "Docker is required for the hybrid approach"
        exit 1
    fi
    
    # Check local tools
    check_local_tools
    echo ""
    
    # Setup Docker tools
    setup_docker_tools
    echo ""
    
    # Create wrapper scripts
    create_wrapper_scripts
    echo ""
    
    # Test the setup
    test_hybrid_setup
    echo ""
    
    print_success "Discovery tools setup completed!"
    print_status "You can now use both local and Docker-based tools seamlessly"
    print_status "Local tools: subfinder, nuclei, feroxbuster, waybackurls"
    print_status "Docker tools: httpx, katana, gospider"
}

# Run main function
main "$@"

