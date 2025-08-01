# MvCam Camera Control GUI

A modern Python GUI application for controlling Hikvision industrial cameras using the MvCamCtrlSDK.

## Features

- 🎥 **Real Camera Control**: Connect, disconnect, start/stop acquisition with actual Hikvision cameras
- 📊 **Real-time Display**: Live camera feed with adjustable settings
- ⚙️ **Camera Settings**: Exposure, gain, frame rate, pixel format
- 🎯 **Trigger Control**: Software and hardware trigger support
- 💾 **Image/Video Capture**: Save images and record video
- 🎨 **Modern UI**: Clean, responsive interface with dark theme support
- 🔧 **Multi-threaded**: Non-blocking camera operations
- 🔌 **SDK Integration**: Full MvCamCtrlSDK integration for real camera control

## Screenshots

The application features a split-panel interface with:
- **Left Panel**: Camera view and basic controls
- **Right Panel**: Advanced settings organized in tabs
- **Status Bar**: Real-time status updates and progress indicators

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- MvCamCtrlSDK Runtime (already installed)

### Python Dependencies
- PyQt6 (GUI framework)
- OpenCV (image processing)
- NumPy (numerical operations)
- Pillow (image handling)

## Installation

### 1. Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install PyQt6 opencv-python numpy Pillow
```

### 2. Verify SDK Installation

The MvCamCtrlSDK should already be installed at `/opt/MVS/`. Verify with:

```bash
ls -la /opt/MVS/lib/64/
```

You should see files like `libMvCameraControl.so`, `libMvCameraControlWrapper.so`, etc.

### 3. Set Environment Variables

```bash
# Add SDK library path to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/opt/MVS/lib/64:$LD_LIBRARY_PATH

# For permanent setup, add to ~/.bashrc
echo 'export LD_LIBRARY_PATH=/opt/MVS/lib/64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Running the Application

```bash
python3 mvcam_gui.py
```

### Basic Workflow

1. **Connect to Camera**
   - Click "Connect" button
   - Wait for connection confirmation

2. **Start Acquisition**
   - Click "Start Acquisition" to begin live feed
   - Adjust camera settings as needed

3. **Adjust Settings**
   - Use the tabs on the right panel:
     - **Camera Settings**: Exposure, gain, frame rate
     - **Image Settings**: Pixel format, resolution, processing
     - **Trigger & Save**: Trigger modes, save options

4. **Capture Images/Video**
   - Use "Save Current Image" for single captures
   - Use "Start/Stop Video Recording" for video

5. **Disconnect**
   - Stop acquisition first
   - Click "Disconnect" to close camera connection

## Camera Settings

### Exposure Settings
- **Auto Exposure**: Enable automatic exposure control
- **Exposure Time**: Manual exposure time in microseconds (1-1,000,000 μs)

### Gain Settings
- **Auto Gain**: Enable automatic gain control
- **Gain**: Manual gain in decibels (0-24 dB)

### Frame Rate
- **Frame Rate**: Set acquisition frame rate (0.1-1000 fps)

### Image Format
- **Pixel Format**: Choose from Mono8, RGB8, BGR8, YUV422
- **Resolution**: Set image width and height (1-4096 pixels)

### Trigger Settings
- **Trigger Mode**: Off, Software, or Hardware
- **Software Trigger**: Manual trigger button

## Development

### Project Structure
```
MvCamGUI/
├── mvcam_gui.py          # Main application
├── mvcam_sdk.py          # MvCamCtrlSDK wrapper
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .vscode/             # VS Code settings (if using)
```

### Architecture

The application uses a multi-threaded architecture:

- **Main Thread**: GUI and user interaction
- **Camera Thread**: Camera operations and image acquisition
- **Signal/Slot**: Qt's mechanism for thread communication

### Key Classes

- `MvCamGUI`: Main application window
- `CameraThread`: Background camera operations
- `ImageViewer`: Custom image display widget
- `MvCamSDK`: SDK wrapper for real camera operations

### Real Camera Integration

The application now includes full real camera support:

1. **SDK Wrapper** (`mvcam_sdk.py`)
   - Complete MvCamCtrlSDK integration
   - Camera enumeration and connection
   - Parameter setting and getting
   - Image acquisition and format conversion

2. **Real Camera Operations**
   - Automatic camera detection
   - Live image streaming
   - Real-time parameter adjustment
   - Trigger control (software and hardware)

3. **Error Handling**
   - SDK error code translation
   - Connection timeout handling
   - Resource cleanup

## Troubleshooting

### Common Issues

1. **"SDK library not found"**
   - Verify SDK installation: `ls /opt/MVS/lib/64/`
   - Check LD_LIBRARY_PATH: `echo $LD_LIBRARY_PATH`

2. **"No module named 'PyQt6'"**
   - Install PyQt6: `pip install PyQt6`

3. **Camera not detected**
   - Check USB permissions: `lsusb`
   - Verify udev rules: `ls /etc/udev/rules.d/ | grep mvcam`

4. **Permission denied**
   - Run with sudo for first-time setup
   - Check udev rules installation

### Debug Mode

Run with verbose output:
```bash
python3 -u mvcam_gui.py 2>&1 | tee debug.log
```

## SDK Integration

This application is designed to work with the MvCamCtrlSDK. For full camera functionality:

1. **Download Development Package**
   - Get headers and examples from Hikvision
   - Install development package

2. **Implement SDK Functions**
   - Camera enumeration
   - Device connection
   - Image acquisition
   - Parameter setting

3. **Add Error Handling**
   - SDK error codes
   - Connection timeouts
   - Resource cleanup

## License

This project is provided as-is for educational and development purposes. The MvCamCtrlSDK is proprietary software from Hikvision.

## Support

For issues related to:
- **This GUI Application**: Check troubleshooting section
- **MvCamCtrlSDK**: Contact Hikvision support
- **Camera Hardware**: Refer to camera documentation

## Version History

- **v1.0.0**: Initial release with simulated camera operations
- **v1.1.0**: Added real camera support with MvCamCtrlSDK integration

---

**Note**: This application now supports real Hikvision cameras through the MvCamCtrlSDK. The SDK must be installed at `/opt/MVS/` for full functionality. 