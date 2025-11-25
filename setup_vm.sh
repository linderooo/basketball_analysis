#!/bin/bash
# Basketball Analysis - VM Setup Script
# This script sets up a Python virtual environment and installs all dependencies
# Usage: ./setup_vm.sh [cpu|cuda]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to CPU if no argument provided
DEVICE="${1:-cpu}"

echo -e "${GREEN}🏀 Basketball Analysis - VM Setup${NC}"
echo "=================================="
echo ""

# Validate device argument
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo -e "${RED}Error: Invalid device. Use 'cpu' or 'cuda'${NC}"
    echo "Usage: ./setup_vm.sh [cpu|cuda]"
    exit 1
fi

echo -e "${YELLOW}Device:${NC} $DEVICE"
echo ""

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

# Check if python3-venv is installed (needed on Debian/Ubuntu)
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}⚠️  python3-venv not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-venv
fi

# Create virtual environment
echo ""
echo "🔨 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}   Virtual environment already exists. Removing...${NC}"
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}   ✓ Virtual environment created${NC}"

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}   ✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo -e "${GREEN}   ✓ pip upgraded${NC}"

# Install PyTorch based on device type
echo ""
if [ "$DEVICE" = "cuda" ]; then
    echo "🚀 Installing PyTorch with CUDA support..."
    echo "   This may take a few minutes..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    
    # Verify CUDA installation
    echo ""
    echo "🔍 Verifying CUDA installation..."
    python3 -c "import torch; print(f'   CUDA available: {torch.cuda.is_available()}')" || {
        echo -e "${RED}   ✗ CUDA verification failed${NC}"
        exit 1
    }
    
    if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)"; then
        GPU_NAME=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))")
        echo -e "${GREEN}   ✓ GPU detected: $GPU_NAME${NC}"
    else
        echo -e "${YELLOW}   ⚠️  CUDA installed but no GPU detected${NC}"
    fi
else
    echo "💻 Installing PyTorch (CPU version)..."
    pip install torch torchvision
fi

echo -e "${GREEN}   ✓ PyTorch installed${NC}"

# Install other dependencies
echo ""
echo "📚 Installing other dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}   ✓ All dependencies installed${NC}"

# Install system dependencies for video processing (if needed)
echo ""
echo "🎬 Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "   Installing OpenCV system dependencies..."
    sudo apt-get update -qq
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 2>/dev/null || {
        echo -e "${YELLOW}   ⚠️  Could not install system dependencies (may not be needed)${NC}"
    }
fi

# Create necessary directories
echo ""
echo "📁 Creating project directories..."
mkdir -p input_videos
mkdir -p output_videos
mkdir -p models
mkdir -p stubs
echo -e "${GREEN}   ✓ Directories created${NC}"

# Check if models exist
echo ""
echo "🤖 Checking for ML models..."
MODELS_EXIST=true
if [ ! -f "models/player_detector.pt" ]; then
    echo -e "${YELLOW}   ⚠️  models/player_detector.pt not found${NC}"
    MODELS_EXIST=false
fi
if [ ! -f "models/ball_detector_model.pt" ]; then
    echo -e "${YELLOW}   ⚠️  models/ball_detector_model.pt not found${NC}"
    MODELS_EXIST=false
fi
if [ ! -f "models/court_keypoint_detector.pt" ]; then
    echo -e "${YELLOW}   ⚠️  models/court_keypoint_detector.pt not found${NC}"
    MODELS_EXIST=false
fi

if [ "$MODELS_EXIST" = false ]; then
    echo ""
    echo -e "${YELLOW}   ℹ️  ML models are missing. You need to:${NC}"
    echo "      1. Download the models from your source"
    echo "      2. Place them in the models/ directory"
fi

# Final summary
echo ""
echo "=================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================="
echo ""
echo "To use the environment:"
echo "  1. Activate: ${GREEN}source venv/bin/activate${NC}"
echo "  2. Run: ${GREEN}python3 main.py --file input_videos/video.mp4${NC}"
echo ""
if [ "$DEVICE" = "cuda" ]; then
    echo "GPU mode: Add ${GREEN}--device cuda${NC} to use GPU acceleration"
    echo "Example: ${GREEN}python3 main.py --file video.mp4 --device cuda${NC}"
fi
echo ""
echo "To deactivate: ${GREEN}deactivate${NC}"
echo ""
