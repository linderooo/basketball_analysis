# Quick Start - New VM Setup

## 1. Clone Repository

```bash
git clone https://github.com/linderooo/basketball_analysis.git
cd basketball_analysis
```

## 2. Run Setup Script

**For CPU-only systems:**
```bash
chmod +x setup_vm.sh
./setup_vm.sh cpu
```

**For GPU systems (GCE, AWS, etc.):**
```bash
chmod +x setup_vm.sh
./setup_vm.sh cuda
```

The script will:
- Create Python virtual environment (`venv/`)
- Install PyTorch (CPU or CUDA version)
- Install all dependencies
- Create necessary directories
- Verify installation

## 3. Add ML Models

Download the 3 required models and place them in `models/`:
- `models/player_detector.pt`
- `models/ball_detector_model.pt`
- `models/court_keypoint_detector.pt`

## 4. Run Analysis

```bash
# Activate environment
source venv/bin/activate

# CPU mode
python3 main.py --file input_videos/video.mp4

# GPU mode (if available)
python3 main.py --file input_videos/video.mp4 --device cuda
```

## Manual Setup (Alternative)

If the script doesn't work, follow [`GPU_INSTALL.md`](GPU_INSTALL.md) for manual installation.
