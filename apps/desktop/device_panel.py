"""
Device Panel Widget - Control panel for virtual devices
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QSpinBox, QGroupBox,
    QScrollArea, QDoubleSpinBox
)
from PyQt6.QtCore import Qt


class DeviceControlWidget(QWidget):
    """Control widget for a single device"""
    
    def __init__(self, device_name, device_type):
        super().__init__()
        self.device_name = device_name
        self.device_type = device_type
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup device-specific controls"""
        layout = QVBoxLayout(self)
        
        # Device header
        header = QLabel(f"{self.device_name} ({self.device_type})")
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)
        
        # Device-specific controls
        if self.device_type == "LED":
            self._setup_led_controls(layout)
        elif self.device_type == "Servo":
            self._setup_servo_controls(layout)
        elif self.device_type == "BME280":
            self._setup_bme280_controls(layout)
        elif self.device_type == "DHT22":
            self._setup_dht22_controls(layout)
        else:
            layout.addWidget(QLabel("No controls available"))
            
    def _setup_led_controls(self, layout):
        """Setup LED controls"""
        # Brightness slider
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        brightness_layout.addWidget(self.brightness_label)
        
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_label.setText(f"{v}%")
        )
        
        layout.addLayout(brightness_layout)
        
        # On/Off button
        self.led_button = QPushButton("Turn ON")
        self.led_button.setCheckable(True)
        self.led_button.clicked.connect(self._toggle_led)
        layout.addWidget(self.led_button)
        
    def _toggle_led(self):
        """Toggle LED state"""
        if self.led_button.isChecked():
            self.led_button.setText("Turn OFF")
            self.led_button.setStyleSheet("background-color: #ff4444;")
        else:
            self.led_button.setText("Turn ON")
            self.led_button.setStyleSheet("")
            
    def _setup_servo_controls(self, layout):
        """Setup servo controls"""
        # Position slider
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 180)
        self.position_slider.setValue(90)
        position_layout.addWidget(self.position_slider)
        
        self.position_label = QLabel("90°")
        position_layout.addWidget(self.position_label)
        
        self.position_slider.valueChanged.connect(
            lambda v: self.position_label.setText(f"{v}°")
        )
        
        layout.addLayout(position_layout)
        
        # Preset positions
        preset_layout = QHBoxLayout()
        
        btn_0 = QPushButton("0°")
        btn_0.clicked.connect(lambda: self.position_slider.setValue(0))
        preset_layout.addWidget(btn_0)
        
        btn_90 = QPushButton("90°")
        btn_90.clicked.connect(lambda: self.position_slider.setValue(90))
        preset_layout.addWidget(btn_90)
        
        btn_180 = QPushButton("180°")
        btn_180.clicked.connect(lambda: self.position_slider.setValue(180))
        preset_layout.addWidget(btn_180)
        
        layout.addLayout(preset_layout)
        
    def _setup_bme280_controls(self, layout):
        """Setup BME280 environmental controls"""
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(-40, 85)
        self.temp_spinbox.setValue(25.0)
        self.temp_spinbox.setSuffix(" °C")
        temp_layout.addWidget(self.temp_spinbox)
        
        layout.addLayout(temp_layout)
        
        # Pressure
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Pressure:"))
        
        self.pressure_spinbox = QDoubleSpinBox()
        self.pressure_spinbox.setRange(300, 1100)
        self.pressure_spinbox.setValue(1013.25)
        self.pressure_spinbox.setSuffix(" hPa")
        pressure_layout.addWidget(self.pressure_spinbox)
        
        layout.addLayout(pressure_layout)
        
        # Humidity
        humidity_layout = QHBoxLayout()
        humidity_layout.addWidget(QLabel("Humidity:"))
        
        self.humidity_spinbox = QDoubleSpinBox()
        self.humidity_spinbox.setRange(0, 100)
        self.humidity_spinbox.setValue(50.0)
        self.humidity_spinbox.setSuffix(" %RH")
        humidity_layout.addWidget(self.humidity_spinbox)
        
        layout.addLayout(humidity_layout)
        
    def _setup_dht22_controls(self, layout):
        """Setup DHT22 controls"""
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(-40, 80)
        self.temp_spinbox.setValue(25.0)
        self.temp_spinbox.setSuffix(" °C")
        temp_layout.addWidget(self.temp_spinbox)
        
        layout.addLayout(temp_layout)
        
        # Humidity
        humidity_layout = QHBoxLayout()
        humidity_layout.addWidget(QLabel("Humidity:"))
        
        self.humidity_spinbox = QDoubleSpinBox()
        self.humidity_spinbox.setRange(0, 100)
        self.humidity_spinbox.setValue(50.0)
        self.humidity_spinbox.setSuffix(" %RH")
        humidity_layout.addWidget(self.humidity_spinbox)
        
        layout.addLayout(humidity_layout)


class DevicePanelWidget(QWidget):
    """Panel containing all device controls"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
        # Device controls
        self.device_controls = []
        
        # Add some example devices
        self._add_example_devices()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Device Controls")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Scroll area for device controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        
        scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(scroll_area)
        
        # Add device button
        add_button = QPushButton("Add Device")
        add_button.clicked.connect(self._add_device_dialog)
        layout.addWidget(add_button)
        
    def _add_example_devices(self):
        """Add some example devices for demonstration"""
        self.add_device("LED1", "LED")
        self.add_device("Servo1", "Servo")
        self.add_device("BME280", "BME280")
        
    def add_device(self, name, device_type):
        """Add a device control"""
        device_control = DeviceControlWidget(name, device_type)
        
        # Wrap in group box
        group_box = QGroupBox()
        group_layout = QVBoxLayout(group_box)
        group_layout.addWidget(device_control)
        
        self.scroll_layout.addWidget(group_box)
        self.device_controls.append(device_control)
        
    def _add_device_dialog(self):
        """Show add device dialog (placeholder)"""
        # This would show a dialog to add new devices
        pass
        
    def update_display(self):
        """Update display (called from main window)"""
        # Update device states if needed
        pass
        
    def clear_devices(self):
        """Clear all devices"""
        # Clear the scroll layout
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        self.device_controls.clear()
        
    def add_device_from_config(self, device_config):
        """Add device from configuration"""
        self.add_device(device_config.name, device_config.type)