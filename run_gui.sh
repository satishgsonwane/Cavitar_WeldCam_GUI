#!/bin/bash

# MvCam GUI Launcher Script
# This script sets up the environment and launches the MvCam GUI application

echo "Starting MvCam Camera Control GUI..."

# Set up environment variables
export LD_LIBRARY_PATH=/opt/MVS/lib/64:$LD_LIBRARY_PATH
export MVCAM_SDK_PATH=/opt/MVS

# Check if SDK is installed
if [ ! -d "/opt/MVS" ]; then
    echo "Error: MvCamCtrlSDK not found at /opt/MVS"
    echo "Please install the SDK first."
    exit 1
fi

# Check if Python dependencies are installed
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Error: PyQt6 not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
echo "Launching GUI application..."
python3 mvcam_gui.py 