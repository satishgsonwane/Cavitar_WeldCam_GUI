#!/usr/bin/env python3
"""
MvCam GUI Application
A simple GUI for controlling Hikvision industrial cameras using MvCamCtrlSDK
"""

import sys
import os
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                             QGroupBox, QTabWidget, QSplitter, QMessageBox,
                             QFileDialog, QProgressBar, QStatusBar, QSlider)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor, QFont
import cv2

# Import our SDK wrapper
try:
    from mvcam_sdk import MvCamSDK, TriggerMode, TriggerSource
    SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import MvCamSDK: {e}")
    SDK_AVAILABLE = False

class CameraThread(QThread):
    """Thread for camera operations to avoid blocking the GUI"""
    image_received = pyqtSignal(np.ndarray)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.sdk = None
        self.current_image = None
        
    def set_sdk(self, sdk):
        """Set the SDK instance"""
        self.sdk = sdk
        
    def run(self):
        """Main camera thread loop"""
        try:
            if not SDK_AVAILABLE:
                self.error_occurred.emit("MvCamSDK not available")
                return
                
            if not self.sdk:
                self.error_occurred.emit("No SDK instance provided")
                return
                
            self.status_update.emit("Camera thread started")
            
            while self.running:
                try:
                    # Get image from camera
                    if self.sdk and self.sdk.is_grabbing:
                        image = self.sdk.get_image(timeout_ms=100)
                        if image is not None:
                            self.current_image = image
                            self.image_received.emit(image)
                        else:
                            # If no image received, use the last one or create a placeholder
                            if self.current_image is None:
                                self.current_image = np.zeros((480, 640, 3), dtype=np.uint8)
                            self.image_received.emit(self.current_image)
                    else:
                        # Create a placeholder image when not grabbing
                        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(placeholder, "No Camera", (200, 240), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        self.image_received.emit(placeholder)
                
                except Exception as e:
                    self.error_occurred.emit(f"Image acquisition error: {str(e)}")
                    break
                
                self.msleep(50)  # 20 FPS
                
        except Exception as e:
            self.error_occurred.emit(f"Camera thread error: {str(e)}")
    
    def stop(self):
        """Stop the camera thread"""
        self.running = False
        self.wait()

class ImageViewer(QLabel):
    """Custom widget for displaying camera images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 8px;
                color: #cccccc;
            }
        """)
        self.setText("No Image")
        
    def set_image(self, image):
        """Display an OpenCV image"""
        if image is None:
            self.setText("No Image")
            return
            
        # Convert OpenCV BGR to RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
        # Convert to QImage
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to fit the widget while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled_pixmap)

class MvCamGUI(QMainWindow):
    """Main GUI window for MvCam camera control"""
    
    def __init__(self):
        super().__init__()
        self.camera_thread = None
        self.sdk = None
        self.settings = QSettings("MvCamGUI", "CameraControl")
        self.init_ui()
        self.load_settings()
        
        # Initialize SDK if available
        if SDK_AVAILABLE:
            try:
                self.sdk = MvCamSDK()
                self.camera_thread.set_sdk(self.sdk)
                # Check if any cameras are available
                devices = self.sdk.enum_devices()
                if devices:
                    self.status_label.setText(f"SDK initialized successfully - {len(devices)} camera(s) found")
                else:
                    self.status_label.setText("SDK initialized successfully - No cameras detected (simulation mode)")
            except Exception as e:
                QMessageBox.warning(self, "SDK Warning", f"Failed to initialize SDK: {str(e)}")
                self.status_label.setText("SDK initialization failed")
        else:
            QMessageBox.warning(self, "SDK Warning", "MvCamSDK not available. Running in simulation mode.")
            self.status_label.setText("Running in simulation mode")
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MvCam Camera Control GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d5aa0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create left panel (camera view)
        self.create_camera_panel(splitter)
        
        # Create right panel (controls)
        self.create_control_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([800, 400])
        
        # Create status bar
        self.create_status_bar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Setup camera thread
        self.camera_thread = CameraThread()
        self.camera_thread.image_received.connect(self.on_image_received)
        self.camera_thread.status_update.connect(self.on_status_update)
        self.camera_thread.error_occurred.connect(self.on_error_occurred)
        
    def create_camera_panel(self, parent):
        """Create the camera view panel"""
        camera_widget = QWidget()
        layout = QVBoxLayout(camera_widget)
        
        # Camera info label
        self.camera_info_label = QLabel("Camera: Not Connected")
        self.camera_info_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.camera_info_label)
        
        # Camera selection
        camera_select_layout = QHBoxLayout()
        camera_select_layout.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("No cameras found")
        self.refresh_cameras_button = QPushButton("Refresh")
        self.refresh_cameras_button.clicked.connect(self.refresh_cameras)
        camera_select_layout.addWidget(self.camera_combo)
        camera_select_layout.addWidget(self.refresh_cameras_button)
        layout.addLayout(camera_select_layout)
        
        # Image viewer
        self.image_viewer = ImageViewer()
        layout.addWidget(self.image_viewer)
        
        # Camera control buttons
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_camera)
        button_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_camera)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)
        
        self.start_button = QPushButton("Start Acquisition")
        self.start_button.clicked.connect(self.start_acquisition)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Acquisition")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        parent.addWidget(camera_widget)
        
    def create_control_panel(self, parent):
        """Create the control panel"""
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        
        # Create tab widget for different control sections
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Camera settings tab
        self.create_camera_settings_tab(tab_widget)
        
        # Image settings tab
        self.create_image_settings_tab(tab_widget)
        
        # Trigger settings tab
        self.create_trigger_settings_tab(tab_widget)
        
        parent.addWidget(control_widget)
        
    def create_camera_settings_tab(self, parent):
        """Create camera settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Exposure settings
        exposure_group = QGroupBox("Exposure Settings")
        exposure_layout = QGridLayout(exposure_group)
        
        self.auto_exposure_check = QCheckBox("Auto Exposure")
        self.auto_exposure_check.setChecked(True)
        self.auto_exposure_check.toggled.connect(self.on_exposure_changed)
        exposure_layout.addWidget(self.auto_exposure_check, 0, 0, 1, 2)
        
        exposure_layout.addWidget(QLabel("Exposure Time (μs):"), 1, 0)
        self.exposure_spinbox = QDoubleSpinBox()
        self.exposure_spinbox.setRange(1, 1000000)
        self.exposure_spinbox.setValue(10000)
        self.exposure_spinbox.setSuffix(" μs")
        self.exposure_spinbox.valueChanged.connect(self.on_exposure_changed)
        exposure_layout.addWidget(self.exposure_spinbox, 1, 1)
        
        layout.addWidget(exposure_group)
        
        # Gain settings
        gain_group = QGroupBox("Gain Settings")
        gain_layout = QGridLayout(gain_group)
        
        self.auto_gain_check = QCheckBox("Auto Gain")
        self.auto_gain_check.setChecked(True)
        self.auto_gain_check.toggled.connect(self.on_gain_changed)
        gain_layout.addWidget(self.auto_gain_check, 0, 0, 1, 2)
        
        gain_layout.addWidget(QLabel("Gain (dB):"), 1, 0)
        self.gain_spinbox = QDoubleSpinBox()
        self.gain_spinbox.setRange(0, 24)
        self.gain_spinbox.setValue(0)
        self.gain_spinbox.setSuffix(" dB")
        self.gain_spinbox.valueChanged.connect(self.on_gain_changed)
        gain_layout.addWidget(self.gain_spinbox, 1, 1)
        
        layout.addWidget(gain_group)
        
        # Frame rate settings
        framerate_group = QGroupBox("Frame Rate Settings")
        framerate_layout = QGridLayout(framerate_group)
        
        framerate_layout.addWidget(QLabel("Frame Rate (fps):"), 0, 0)
        self.framerate_spinbox = QDoubleSpinBox()
        self.framerate_spinbox.setRange(0.1, 1000)
        self.framerate_spinbox.setValue(30)
        self.framerate_spinbox.setSuffix(" fps")
        self.framerate_spinbox.valueChanged.connect(self.on_framerate_changed)
        framerate_layout.addWidget(self.framerate_spinbox, 0, 1)
        
        layout.addWidget(framerate_group)
        
        layout.addStretch()
        parent.addTab(settings_widget, "Camera Settings")
        
    def create_image_settings_tab(self, parent):
        """Create image settings tab"""
        image_widget = QWidget()
        layout = QVBoxLayout(image_widget)
        
        # Image format settings
        format_group = QGroupBox("Image Format")
        format_layout = QGridLayout(format_group)
        
        format_layout.addWidget(QLabel("Pixel Format:"), 0, 0)
        self.pixel_format_combo = QComboBox()
        self.pixel_format_combo.addItems(["Mono8", "RGB8", "BGR8", "YUV422"])
        format_layout.addWidget(self.pixel_format_combo, 0, 1)
        
        format_layout.addWidget(QLabel("Width:"), 1, 0)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 4096)
        self.width_spinbox.setValue(640)
        format_layout.addWidget(self.width_spinbox, 1, 1)
        
        format_layout.addWidget(QLabel("Height:"), 2, 0)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 4096)
        self.height_spinbox.setValue(480)
        format_layout.addWidget(self.height_spinbox, 2, 1)
        
        layout.addWidget(format_group)
        
        # Image processing settings
        processing_group = QGroupBox("Image Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        self.auto_white_balance_check = QCheckBox("Auto White Balance")
        self.auto_white_balance_check.setChecked(True)
        processing_layout.addWidget(self.auto_white_balance_check)
        
        self.noise_reduction_check = QCheckBox("Noise Reduction")
        processing_layout.addWidget(self.noise_reduction_check)
        
        self.edge_enhancement_check = QCheckBox("Edge Enhancement")
        processing_layout.addWidget(self.edge_enhancement_check)
        
        layout.addWidget(processing_group)
        
        layout.addStretch()
        parent.addTab(image_widget, "Image Settings")
        
    def create_trigger_settings_tab(self, parent):
        """Create trigger settings tab"""
        trigger_widget = QWidget()
        layout = QVBoxLayout(trigger_widget)
        
        # Trigger mode settings
        trigger_group = QGroupBox("Trigger Settings")
        trigger_layout = QGridLayout(trigger_group)
        
        trigger_layout.addWidget(QLabel("Trigger Mode:"), 0, 0)
        self.trigger_mode_combo = QComboBox()
        self.trigger_mode_combo.addItems(["Off", "Software", "Hardware"])
        self.trigger_mode_combo.currentTextChanged.connect(self.on_trigger_mode_changed)
        trigger_layout.addWidget(self.trigger_mode_combo, 0, 1)
        
        self.trigger_button = QPushButton("Software Trigger")
        self.trigger_button.clicked.connect(self.software_trigger)
        self.trigger_button.setEnabled(False)
        trigger_layout.addWidget(self.trigger_button, 1, 0, 1, 2)
        
        layout.addWidget(trigger_group)
        
        # Save settings
        save_group = QGroupBox("Save Settings")
        save_layout = QVBoxLayout(save_group)
        
        self.save_image_button = QPushButton("Save Current Image")
        self.save_image_button.clicked.connect(self.save_image)
        save_layout.addWidget(self.save_image_button)
        
        self.save_video_button = QPushButton("Start/Stop Video Recording")
        self.save_video_button.clicked.connect(self.toggle_video_recording)
        save_layout.addWidget(self.save_video_button)
        
        layout.addWidget(save_group)
        
        layout.addStretch()
        parent.addTab(trigger_widget, "Trigger & Save")
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        save_action = file_menu.addAction("Save Image")
        save_action.triggered.connect(self.save_image)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Camera menu
        camera_menu = menubar.addMenu("Camera")
        
        connect_action = camera_menu.addAction("Connect")
        connect_action.triggered.connect(self.connect_camera)
        
        disconnect_action = camera_menu.addAction("Disconnect")
        disconnect_action.triggered.connect(self.disconnect_camera)
        
        camera_menu.addSeparator()
        
        start_action = camera_menu.addAction("Start Acquisition")
        start_action.triggered.connect(self.start_acquisition)
        
        stop_action = camera_menu.addAction("Stop Acquisition")
        stop_action.triggered.connect(self.stop_acquisition)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
        
    def refresh_cameras(self):
        """Refresh the list of available cameras"""
        try:
            self.camera_combo.clear()
            
            if not SDK_AVAILABLE or not self.sdk:
                self.camera_combo.addItem("SDK not available")
                return
            
            devices = self.sdk.enum_devices()
            
            if not devices:
                self.camera_combo.addItem("No cameras found")
            else:
                for device in devices:
                    self.camera_combo.addItem(f"{device['name']} ({device['serial']})")
            
            self.status_label.setText(f"Found {len(devices)} camera(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "Refresh Error", f"Failed to refresh cameras: {str(e)}")
            self.camera_combo.addItem("Error refreshing cameras")
    
    def connect_camera(self):
        """Connect to camera"""
        try:
            if not SDK_AVAILABLE or not self.sdk:
                QMessageBox.warning(self, "SDK Error", "SDK not available")
                return
            
            if self.camera_combo.currentText() == "No cameras found" or "Error" in self.camera_combo.currentText():
                QMessageBox.warning(self, "Camera Error", "No valid camera selected")
                return
            
            self.status_label.setText("Connecting to camera...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Get selected camera index
            camera_index = self.camera_combo.currentIndex()
            
            # Connect to camera
            self.sdk.connect(camera_index)
            
            # Apply current settings
            self.apply_camera_settings()
            
            self.camera_info_label.setText(f"Camera: Connected ({self.camera_combo.currentText()})")
            self.camera_info_label.setStyleSheet("font-weight: bold; color: #27ae60;")
            
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.start_button.setEnabled(True)
            
            self.status_label.setText("Camera connected successfully")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to camera: {str(e)}")
            self.status_label.setText("Connection failed")
            self.progress_bar.setVisible(False)
            
    def disconnect_camera(self):
        """Disconnect from camera"""
        try:
            self.stop_acquisition()
            
            # Disconnect from camera
            if self.sdk:
                self.sdk.disconnect()
            
            self.camera_info_label.setText("Camera: Not Connected")
            self.camera_info_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            
            self.status_label.setText("Camera disconnected")
            
        except Exception as e:
            QMessageBox.critical(self, "Disconnection Error", f"Failed to disconnect from camera: {str(e)}")
            
    def start_acquisition(self):
        """Start image acquisition"""
        try:
            if not self.sdk or not self.sdk.is_connected:
                QMessageBox.warning(self, "Warning", "Please connect to a camera first")
                return
                
            # Start grabbing
            self.sdk.start_grabbing()
            
            # Start camera thread
            self.camera_thread.running = True
            self.camera_thread.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.trigger_button.setEnabled(True)
            
            self.status_label.setText("Acquisition started")
            
        except Exception as e:
            QMessageBox.critical(self, "Acquisition Error", f"Failed to start acquisition: {str(e)}")
            
    def stop_acquisition(self):
        """Stop image acquisition"""
        try:
            # Stop camera thread
            self.camera_thread.stop()
            
            # Stop grabbing
            if self.sdk:
                self.sdk.stop_grabbing()
            
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.trigger_button.setEnabled(False)
            
            self.status_label.setText("Acquisition stopped")
            
        except Exception as e:
            QMessageBox.critical(self, "Stop Error", f"Failed to stop acquisition: {str(e)}")
            
    def apply_camera_settings(self):
        """Apply current camera settings"""
        if not self.sdk or not self.sdk.is_connected:
            return
        
        try:
            # Apply exposure settings
            if self.auto_exposure_check.isChecked():
                self.sdk.set_auto_exposure(True)
            else:
                self.sdk.set_auto_exposure(False)
                self.sdk.set_exposure_time(self.exposure_spinbox.value())
            
            # Apply gain settings
            if self.auto_gain_check.isChecked():
                self.sdk.set_auto_gain(True)
            else:
                self.sdk.set_auto_gain(False)
                self.sdk.set_gain(self.gain_spinbox.value())
            
            # Apply frame rate
            self.sdk.set_frame_rate(self.framerate_spinbox.value())
            
            # Apply trigger settings
            trigger_mode = self.trigger_mode_combo.currentText()
            if trigger_mode == "Off":
                self.sdk.set_trigger_mode(TriggerMode.Off)
            elif trigger_mode == "Software":
                self.sdk.set_trigger_mode(TriggerMode.On)
                self.sdk.set_trigger_source(TriggerSource.Software)
            elif trigger_mode == "Hardware":
                self.sdk.set_trigger_mode(TriggerMode.On)
                self.sdk.set_trigger_source(TriggerSource.Line1)
            
            self.status_label.setText("Camera settings applied")
            
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Failed to apply some settings: {str(e)}")
    
    def software_trigger(self):
        """Send software trigger"""
        try:
            if not self.sdk or not self.sdk.is_connected:
                QMessageBox.warning(self, "Warning", "Camera not connected")
                return
            
            if self.sdk.send_software_trigger():
                self.status_label.setText("Software trigger sent")
            else:
                QMessageBox.warning(self, "Trigger Error", "Failed to send software trigger")
        except Exception as e:
            QMessageBox.critical(self, "Trigger Error", f"Failed to send trigger: {str(e)}")
            
    def save_image(self):
        """Save current image"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Image", "", "Images (*.png *.jpg *.bmp *.tiff)"
            )
            
            if file_path:
                # In real implementation, save the current image
                QMessageBox.information(self, "Save Image", f"Image saved to: {file_path}")
                self.status_label.setText(f"Image saved: {os.path.basename(file_path)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save image: {str(e)}")
            
    def toggle_video_recording(self):
        """Toggle video recording"""
        try:
            if self.save_video_button.text() == "Start/Stop Video Recording":
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Video", "", "Videos (*.avi *.mp4)"
                )
                
                if file_path:
                    self.save_video_button.setText("Stop Recording")
                    self.status_label.setText("Video recording started")
            else:
                self.save_video_button.setText("Start/Stop Video Recording")
                self.status_label.setText("Video recording stopped")
                
        except Exception as e:
            QMessageBox.critical(self, "Video Error", f"Failed to toggle video recording: {str(e)}")
            
    def on_image_received(self, image):
        """Handle received image from camera thread"""
        self.image_viewer.set_image(image)
        
    def on_status_update(self, status):
        """Handle status updates from camera thread"""
        self.status_label.setText(status)
        
    def on_error_occurred(self, error):
        """Handle errors from camera thread"""
        QMessageBox.critical(self, "Camera Error", error)
        self.status_label.setText("Error occurred")
    
    def on_exposure_changed(self):
        """Handle exposure setting changes"""
        if self.sdk and self.sdk.is_connected:
            try:
                if self.auto_exposure_check.isChecked():
                    self.sdk.set_auto_exposure(True)
                else:
                    self.sdk.set_auto_exposure(False)
                    self.sdk.set_exposure_time(self.exposure_spinbox.value())
            except Exception as e:
                print(f"Exposure change error: {e}")
    
    def on_gain_changed(self):
        """Handle gain setting changes"""
        if self.sdk and self.sdk.is_connected:
            try:
                if self.auto_gain_check.isChecked():
                    self.sdk.set_auto_gain(True)
                else:
                    self.sdk.set_auto_gain(False)
                    self.sdk.set_gain(self.gain_spinbox.value())
            except Exception as e:
                print(f"Gain change error: {e}")
    
    def on_framerate_changed(self):
        """Handle frame rate setting changes"""
        if self.sdk and self.sdk.is_connected:
            try:
                self.sdk.set_frame_rate(self.framerate_spinbox.value())
            except Exception as e:
                print(f"Frame rate change error: {e}")
    
    def on_trigger_mode_changed(self):
        """Handle trigger mode changes"""
        if self.sdk and self.sdk.is_connected:
            try:
                trigger_mode = self.trigger_mode_combo.currentText()
                if trigger_mode == "Off":
                    self.sdk.set_trigger_mode(TriggerMode.Off)
                elif trigger_mode == "Software":
                    self.sdk.set_trigger_mode(TriggerMode.On)
                    self.sdk.set_trigger_source(TriggerSource.Software)
                elif trigger_mode == "Hardware":
                    self.sdk.set_trigger_mode(TriggerMode.On)
                    self.sdk.set_trigger_source(TriggerSource.Line1)
            except Exception as e:
                print(f"Trigger mode change error: {e}")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About MvCam GUI", 
                         "MvCam Camera Control GUI\n\n"
                         "A simple GUI application for controlling Hikvision industrial cameras.\n"
                         "Version 1.0.0\n\n"
                         "This is a demonstration application.")
        
    def load_settings(self):
        """Load application settings"""
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
    def save_settings(self):
        """Save application settings"""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
    def closeEvent(self, event):
        """Handle application close event"""
        self.save_settings()
        
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
        
        if self.sdk:
            self.sdk.disconnect()
            
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("MvCam GUI")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = MvCamGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 