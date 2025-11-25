# GPU Installation Guide

This guide explains how to install the project on GPU-enabled systems without breaking CUDA support.

## Problem

Installing `requirements.txt` directly can install CPU-only PyTorch, which removes CUDA drivers.

## Solution: Two-Step Installation

### Step 1: Install PyTorch with CUDA Support

**For CUDA 11.8 (most common):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**For CUDA 12.1:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Verify CUDA is working:**
```bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### Step 2: Install Other Dependencies

```bash
pip install -r requirements.txt
```

This will skip PyTorch (already installed) and install everything else.

## Complete Installation Script for GCE/GPU Systems

```bash
#!/bin/bash
# Install on GPU-enabled Debian/Ubuntu system

# Update system
sudo apt-get update
sudo apt-get install -y python3-pip

# Install PyTorch with CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements.txt

# Verify
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## GCE Deep Learning VM

If using Google Cloud's Deep Learning VM, PyTorch with CUDA is already pre-installed. Just run:

```bash
pip install -r requirements.txt
```

The pre-installed PyTorch won't be overwritten.

## Troubleshooting

**If CUDA was removed:**
1. Uninstall CPU PyTorch:
   ```bash
   pip uninstall torch torchvision
   ```

2. Reinstall with CUDA:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. Verify:
   ```bash
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```
