"""
Environment Simulation Widget - Control environmental parameters
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSlider,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QComboBox,
    QCheckBox, QTabWidget, QTextEdit, QProgressBar, QDial,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class EnvironmentPlot(FigureCanvas):
    """Plot widget for environmental data"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 4), facecolor='#2b2b2b')
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Configure for dark theme
        plt.style.use('dark_background')
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.grid(True, alpha=0.3)
        
        # Data storage
        self.time_data = []
        self.temp_data = []
        self.humidity_data = []
        self.light_data = []
        self.max_points = 1000
        
        self.setup_plot()
        
    def setup_plot(self):
        """Setup plot appearance"""
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.set_ylabel('Value', color='white')
        self.ax.tick_params(colors='white')
        self.ax.set_title('Environmental Parameters', color='white')
        
        # Create empty lines
        self.temp_line, = self.ax.plot([], [], 'r-', label='Temperature (°C)', linewidth=2)
        self.humidity_line, = self.ax.plot([], [], 'b-', label='Humidity (%)', linewidth=2)
        self.light_line, = self.ax.plot([], [], 'y-', label='Light Level (%)', linewidth=2)
        
        self.ax.legend(loc='upper right')
        self.figure.tight_layout()
        
    def update_data(self, sim_time: float, temperature: float, 
                   humidity: float, light_level: float):
        """Update plot with new data"""
        self.time_data.append(sim_time)
        self.temp_data.append(temperature)
        self.humidity_data.append(humidity)
        self.light_data.append(light_level)
        
        # Limit data points
        if len(self.time_data) > self.max_points:
            self.time_data.pop(0)
            self.temp_data.pop(0)
            self.humidity_data.pop(0)
            self.light_data.pop(0)
            
        # Update plot lines
        self.temp_line.set_data(self.time_data, self.temp_data)
        self.humidity_line.set_data(self.time_data, self.humidity_data)
        self.light_line.set_data(self.time_data, self.light_data)
        
        # Auto-scale axes
        if self.time_data:
            self.ax.set_xlim(min(self.time_data), max(self.time_data))
            
            all_values = self.temp_data + self.humidity_data + self.light_data
            if all_values:
                margin = (max(all_values) - min(all_values)) * 0.1
                self.ax.set_ylim(min(all_values) - margin, max(all_values) + margin)
                
        self.draw()
        
    def clear_data(self):
        """Clear all data"""
        self.time_data.clear()
        self.temp_data.clear()
        self.humidity_data.clear()
        self.light_data.clear()
        
        self.temp_line.set_data([], [])
        self.humidity_line.set_data([], [])
        self.light_line.set_data([], [])
        
        self.draw()


class CompassWidget(QWidget):
    """Compass widget for orientation display"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 120)
        self.heading = 0.0  # degrees
        
    def set_heading(self, heading: float):
        """Set compass heading"""
        self.heading = heading % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint compass"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center and radius
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 10
        
        # Draw compass circle
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawEllipse(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2)
        
        # Draw cardinal directions
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(255, 255, 255)))
        
        directions = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
        for text, angle in directions:
            angle_rad = math.radians(angle - 90)  # Adjust for Qt coordinate system
            text_x = center_x + (radius - 15) * math.cos(angle_rad)
            text_y = center_y + (radius - 15) * math.sin(angle_rad)
            
            painter.drawText(int(text_x - 5), int(text_y + 5), text)
            
        # Draw heading needle
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        
        # North needle (red)
        angle_rad = math.radians(self.heading - 90)
        end_x = center_x + (radius - 20) * math.cos(angle_rad)
        end_y = center_y + (radius - 20) * math.sin(angle_rad)
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))
        
        # South needle (white)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        angle_rad = math.radians(self.heading + 90)
        end_x = center_x + (radius - 30) * math.cos(angle_rad)
        end_y = center_y + (radius - 30) * math.sin(angle_rad)
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))
        
        # Center dot
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)


class EnvironmentWidget(QWidget):
    """Environment simulation control widget"""
    
    # Signals
    environment_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Environment state
        self.temperature = 25.0
        self.humidity = 50.0
        self.pressure = 1013.25
        self.light_level = 100.0
        self.wind_speed = 0.0
        self.wind_direction = 0.0
        
        # Motion simulation
        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        self.acceleration_z = 9.81  # Gravity
        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0
        
        # GPS simulation
        self.latitude = 37.7749   # San Francisco
        self.longitude = -122.4194
        self.altitude = 0.0
        self.gps_speed = 0.0
        self.gps_heading = 0.0
        
        # Animation
        self.animation_enabled = False
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_time = 0.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Tab widget for different environment categories
        tab_widget = QTabWidget()
        
        # Basic environment tab
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "🌡️ Basic")
        
        # Motion/IMU tab
        motion_tab = self.create_motion_tab()
        tab_widget.addTab(motion_tab, "📱 Motion")
        
        # GPS/Location tab
        gps_tab = self.create_gps_tab()
        tab_widget.addTab(gps_tab, "🗺️ GPS")
        
        # Scenarios tab
        scenarios_tab = self.create_scenarios_tab()
        tab_widget.addTab(scenarios_tab, "🎬 Scenarios")
        
        layout.addWidget(tab_widget)
        
        # Environment plot
        self.env_plot = EnvironmentPlot()
        layout.addWidget(self.env_plot)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_environment)
        self.update_timer.start(100)  # 10 FPS
        
    def create_basic_tab(self) -> QWidget:
        """Create basic environment controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Temperature control
        temp_group = QGroupBox("Temperature")
        temp_layout = QVBoxLayout(temp_group)
        
        temp_controls = QHBoxLayout()
        temp_controls.addWidget(QLabel("Temperature:"))
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(-40, 80)
        self.temp_slider.setValue(25)
        self.temp_slider.valueChanged.connect(self.update_temperature)
        temp_controls.addWidget(self.temp_slider)
        
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(-40, 80)
        self.temp_spinbox.setValue(25.0)
        self.temp_spinbox.setSuffix(" °C")
        self.temp_spinbox.valueChanged.connect(self.set_temperature)
        temp_controls.addWidget(self.temp_spinbox)
        
        temp_layout.addLayout(temp_controls)
        
        # Temperature presets
        temp_presets = QHBoxLayout()
        presets = [("Freezing", -10), ("Cold", 5), ("Room", 22), ("Warm", 30), ("Hot", 40)]
        for name, temp in presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=temp: self.set_temperature(t))
            temp_presets.addWidget(btn)
        temp_layout.addLayout(temp_presets)
        
        layout.addWidget(temp_group)
        
        # Humidity control
        humidity_group = QGroupBox("Humidity")
        humidity_layout = QVBoxLayout(humidity_group)
        
        humidity_controls = QHBoxLayout()
        humidity_controls.addWidget(QLabel("Humidity:"))
        
        self.humidity_slider = QSlider(Qt.Orientation.Horizontal)
        self.humidity_slider.setRange(0, 100)
        self.humidity_slider.setValue(50)
        self.humidity_slider.valueChanged.connect(self.update_humidity)
        humidity_controls.addWidget(self.humidity_slider)
        
        self.humidity_spinbox = QDoubleSpinBox()
        self.humidity_spinbox.setRange(0, 100)
        self.humidity_spinbox.setValue(50.0)
        self.humidity_spinbox.setSuffix(" %RH")
        self.humidity_spinbox.valueChanged.connect(self.set_humidity)
        humidity_controls.addWidget(self.humidity_spinbox)
        
        humidity_layout.addLayout(humidity_controls)
        layout.addWidget(humidity_group)
        
        # Light level control
        light_group = QGroupBox("Light Level")
        light_layout = QVBoxLayout(light_group)
        
        light_controls = QHBoxLayout()
        light_controls.addWidget(QLabel("Light:"))
        
        self.light_slider = QSlider(Qt.Orientation.Horizontal)
        self.light_slider.setRange(0, 100)
        self.light_slider.setValue(100)
        self.light_slider.valueChanged.connect(self.update_light)
        light_controls.addWidget(self.light_slider)
        
        self.light_spinbox = QDoubleSpinBox()
        self.light_spinbox.setRange(0, 100)
        self.light_spinbox.setValue(100.0)
        self.light_spinbox.setSuffix(" %")
        self.light_spinbox.valueChanged.connect(self.set_light)
        light_controls.addWidget(self.light_spinbox)
        
        light_layout.addLayout(light_controls)
        
        # Light presets
        light_presets = QHBoxLayout()
        presets = [("Dark", 0), ("Dim", 20), ("Indoor", 50), ("Bright", 80), ("Sunny", 100)]
        for name, level in presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, l=level: self.set_light(l))
            light_presets.addWidget(btn)
        light_layout.addLayout(light_presets)
        
        layout.addWidget(light_group)
        
        return widget
        
    def create_motion_tab(self) -> QWidget:
        """Create motion/IMU controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Accelerometer
        accel_group = QGroupBox("Accelerometer")
        accel_layout = QGridLayout(accel_group)
        
        # X axis
        accel_layout.addWidget(QLabel("X:"), 0, 0)
        self.accel_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.accel_x_slider.setRange(-20, 20)
        self.accel_x_slider.setValue(0)
        self.accel_x_slider.valueChanged.connect(self.update_accel_x)
        accel_layout.addWidget(self.accel_x_slider, 0, 1)
        
        self.accel_x_label = QLabel("0.0 g")
        accel_layout.addWidget(self.accel_x_label, 0, 2)
        
        # Y axis
        accel_layout.addWidget(QLabel("Y:"), 1, 0)
        self.accel_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.accel_y_slider.setRange(-20, 20)
        self.accel_y_slider.setValue(0)
        self.accel_y_slider.valueChanged.connect(self.update_accel_y)
        accel_layout.addWidget(self.accel_y_slider, 1, 1)
        
        self.accel_y_label = QLabel("0.0 g")
        accel_layout.addWidget(self.accel_y_label, 1, 2)
        
        # Z axis
        accel_layout.addWidget(QLabel("Z:"), 2, 0)
        self.accel_z_slider = QSlider(Qt.Orientation.Horizontal)
        self.accel_z_slider.setRange(-20, 20)
        self.accel_z_slider.setValue(10)  # 1g = 9.81 m/s²
        self.accel_z_slider.valueChanged.connect(self.update_accel_z)
        accel_layout.addWidget(self.accel_z_slider, 2, 1)
        
        self.accel_z_label = QLabel("9.8 g")
        accel_layout.addWidget(self.accel_z_label, 2, 2)
        
        layout.addWidget(accel_group)
        
        # Gyroscope
        gyro_group = QGroupBox("Gyroscope")
        gyro_layout = QGridLayout(gyro_group)
        
        # Rotation controls
        axes = [("X (Roll):", "gyro_x"), ("Y (Pitch):", "gyro_y"), ("Z (Yaw):", "gyro_z")]
        
        for i, (label, attr) in enumerate(axes):
            gyro_layout.addWidget(QLabel(label), i, 0)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-360, 360)
            slider.setValue(0)
            slider.valueChanged.connect(lambda v, a=attr: self.update_gyro(a, v))
            gyro_layout.addWidget(slider, i, 1)
            
            value_label = QLabel("0.0 °/s")
            gyro_layout.addWidget(value_label, i, 2)
            
            setattr(self, f"{attr}_slider", slider)
            setattr(self, f"{attr}_label", value_label)
            
        layout.addWidget(gyro_group)
        
        # Motion presets
        preset_group = QGroupBox("Motion Presets")
        preset_layout = QHBoxLayout(preset_group)
        
        presets = [
            ("Still", self.preset_still),
            ("Vibration", self.preset_vibration),
            ("Tilt Left", self.preset_tilt_left),
            ("Tilt Right", self.preset_tilt_right),
            ("Shake", self.preset_shake)
        ]
        
        for name, func in presets:
            btn = QPushButton(name)
            btn.clicked.connect(func)
            preset_layout.addWidget(btn)
            
        layout.addWidget(preset_group)
        
        return widget
        
    def create_gps_tab(self) -> QWidget:
        """Create GPS/location controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current position
        pos_group = QGroupBox("Current Position")
        pos_layout = QGridLayout(pos_group)
        
        # Latitude
        pos_layout.addWidget(QLabel("Latitude:"), 0, 0)
        self.lat_spinbox = QDoubleSpinBox()
        self.lat_spinbox.setRange(-90, 90)
        self.lat_spinbox.setDecimals(6)
        self.lat_spinbox.setValue(37.7749)
        self.lat_spinbox.valueChanged.connect(self.update_latitude)
        pos_layout.addWidget(self.lat_spinbox, 0, 1)
        
        # Longitude
        pos_layout.addWidget(QLabel("Longitude:"), 1, 0)
        self.lon_spinbox = QDoubleSpinBox()
        self.lon_spinbox.setRange(-180, 180)
        self.lon_spinbox.setDecimals(6)
        self.lon_spinbox.setValue(-122.4194)
        self.lon_spinbox.valueChanged.connect(self.update_longitude)
        pos_layout.addWidget(self.lon_spinbox, 1, 1)
        
        # Altitude
        pos_layout.addWidget(QLabel("Altitude:"), 2, 0)
        self.alt_spinbox = QDoubleSpinBox()
        self.alt_spinbox.setRange(-1000, 10000)
        self.alt_spinbox.setValue(0)
        self.alt_spinbox.setSuffix(" m")
        self.alt_spinbox.valueChanged.connect(self.update_altitude)
        pos_layout.addWidget(self.alt_spinbox, 2, 1)
        
        layout.addWidget(pos_group)
        
        # Movement
        movement_group = QGroupBox("Movement")
        movement_layout = QGridLayout(movement_group)
        
        # Speed
        movement_layout.addWidget(QLabel("Speed:"), 0, 0)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(0, 200)  # 0-200 km/h
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self.update_speed)
        movement_layout.addWidget(self.speed_slider, 0, 1)
        
        self.speed_label = QLabel("0 km/h")
        movement_layout.addWidget(self.speed_label, 0, 2)
        
        # Heading with compass
        movement_layout.addWidget(QLabel("Heading:"), 1, 0)
        
        heading_widget = QWidget()
        heading_layout = QHBoxLayout(heading_widget)
        
        self.compass = CompassWidget()
        heading_layout.addWidget(self.compass)
        
        heading_controls = QVBoxLayout()
        
        self.heading_dial = QDial()
        self.heading_dial.setRange(0, 359)
        self.heading_dial.setValue(0)
        self.heading_dial.valueChanged.connect(self.update_heading)
        heading_controls.addWidget(self.heading_dial)
        
        self.heading_label = QLabel("0°")
        self.heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_controls.addWidget(self.heading_label)
        
        heading_layout.addLayout(heading_controls)
        movement_layout.addWidget(heading_widget, 1, 1, 1, 2)
        
        layout.addWidget(movement_group)
        
        # Location presets
        preset_group = QGroupBox("Location Presets")
        preset_layout = QGridLayout(preset_group)
        
        locations = [
            ("San Francisco", 37.7749, -122.4194),
            ("New York", 40.7128, -74.0060),
            ("London", 51.5074, -0.1278),
            ("Tokyo", 35.6762, 139.6503),
            ("Sydney", -33.8688, 151.2093)
        ]
        
        for i, (name, lat, lon) in enumerate(locations):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, la=lat, lo=lon: self.set_location(la, lo))
            preset_layout.addWidget(btn, i // 3, i % 3)
            
        layout.addWidget(preset_group)
        
        return widget
        
    def create_scenarios_tab(self) -> QWidget:
        """Create environment scenarios"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Animation controls
        anim_group = QGroupBox("Animation")
        anim_layout = QHBoxLayout(anim_group)
        
        self.anim_checkbox = QCheckBox("Enable Animation")
        self.anim_checkbox.toggled.connect(self.toggle_animation)
        anim_layout.addWidget(self.anim_checkbox)
        
        anim_layout.addWidget(QLabel("Speed:"))
        self.anim_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.anim_speed_slider.setRange(1, 10)
        self.anim_speed_slider.setValue(5)
        anim_layout.addWidget(self.anim_speed_slider)
        
        layout.addWidget(anim_group)
        
        # Scenario presets
        scenario_group = QGroupBox("Environment Scenarios")
        scenario_layout = QVBoxLayout(scenario_group)
        
        scenarios = [
            ("🌅 Sunrise", "Gradual temperature and light increase", self.scenario_sunrise),
            ("🌙 Night", "Low light, cool temperature", self.scenario_night),
            ("🌧️ Rainy Day", "High humidity, low light", self.scenario_rainy),
            ("🏜️ Desert", "High temperature, low humidity", self.scenario_desert),
            ("❄️ Winter", "Low temperature, variable conditions", self.scenario_winter),
            ("🏃 Jogging", "Motion simulation with GPS track", self.scenario_jogging),
            ("🚗 Driving", "Vehicle motion simulation", self.scenario_driving),
            ("📱 Phone Usage", "Typical phone orientations", self.scenario_phone)
        ]
        
        for name, description, func in scenarios:
            scenario_frame = QFrame()
            scenario_frame.setFrameStyle(QFrame.Shape.Box)
            frame_layout = QVBoxLayout(scenario_frame)
            
            title_layout = QHBoxLayout()
            title_label = QLabel(name)
            title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            title_layout.addWidget(title_label)
            
            run_btn = QPushButton("Run")
            run_btn.clicked.connect(func)
            title_layout.addWidget(run_btn)
            
            frame_layout.addLayout(title_layout)
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #888888; font-size: 9px;")
            frame_layout.addWidget(desc_label)
            
            scenario_layout.addWidget(scenario_frame)
            
        layout.addWidget(scenario_group)
        
        return widget
        
    # Update methods
    def update_temperature(self, value: int):
        """Update temperature from slider"""
        self.temperature = float(value)
        self.temp_spinbox.setValue(self.temperature)
        self.emit_environment_change()
        
    def set_temperature(self, value: float):
        """Set temperature from spinbox"""
        self.temperature = value
        self.temp_slider.setValue(int(value))
        self.emit_environment_change()
        
    def update_humidity(self, value: int):
        """Update humidity from slider"""
        self.humidity = float(value)
        self.humidity_spinbox.setValue(self.humidity)
        self.emit_environment_change()
        
    def set_humidity(self, value: float):
        """Set humidity from spinbox"""
        self.humidity = value
        self.humidity_slider.setValue(int(value))
        self.emit_environment_change()
        
    def update_light(self, value: int):
        """Update light level from slider"""
        self.light_level = float(value)
        self.light_spinbox.setValue(self.light_level)
        self.emit_environment_change()
        
    def set_light(self, value: float):
        """Set light level from spinbox"""
        self.light_level = value
        self.light_slider.setValue(int(value))
        self.emit_environment_change()
        
    def update_accel_x(self, value: int):
        """Update X acceleration"""
        self.acceleration_x = value / 10.0  # Convert to g
        self.accel_x_label.setText(f"{self.acceleration_x:.1f} g")
        self.emit_environment_change()
        
    def update_accel_y(self, value: int):
        """Update Y acceleration"""
        self.acceleration_y = value / 10.0
        self.accel_y_label.setText(f"{self.acceleration_y:.1f} g")
        self.emit_environment_change()
        
    def update_accel_z(self, value: int):
        """Update Z acceleration"""
        self.acceleration_z = value / 10.0
        self.accel_z_label.setText(f"{self.acceleration_z:.1f} g")
        self.emit_environment_change()
        
    def update_gyro(self, axis: str, value: int):
        """Update gyroscope value"""
        gyro_value = value / 10.0  # Convert to degrees/second
        setattr(self, axis, gyro_value)
        
        label = getattr(self, f"{axis}_label")
        label.setText(f"{gyro_value:.1f} °/s")
        
        self.emit_environment_change()
        
    def update_latitude(self, value: float):
        """Update GPS latitude"""
        self.latitude = value
        self.emit_environment_change()
        
    def update_longitude(self, value: float):
        """Update GPS longitude"""
        self.longitude = value
        self.emit_environment_change()
        
    def update_altitude(self, value: float):
        """Update GPS altitude"""
        self.altitude = value
        self.emit_environment_change()
        
    def update_speed(self, value: int):
        """Update GPS speed"""
        self.gps_speed = float(value)
        self.speed_label.setText(f"{value} km/h")
        self.emit_environment_change()
        
    def update_heading(self, value: int):
        """Update GPS heading"""
        self.gps_heading = float(value)
        self.heading_label.setText(f"{value}°")
        self.compass.set_heading(value)
        self.emit_environment_change()
        
    def set_location(self, lat: float, lon: float):
        """Set GPS location"""
        self.lat_spinbox.setValue(lat)
        self.lon_spinbox.setValue(lon)
        
    def toggle_animation(self, enabled: bool):
        """Toggle environment animation"""
        self.animation_enabled = enabled
        if enabled:
            self.animation_timer.start(100)  # 10 FPS
        else:
            self.animation_timer.stop()
            
    def update_animation(self):
        """Update animated environment parameters"""
        if not self.animation_enabled:
            return
            
        self.animation_time += 0.1 * self.anim_speed_slider.value()
        
        # Animate temperature with daily cycle
        base_temp = 20.0
        temp_variation = 10.0 * math.sin(self.animation_time * 0.1)
        self.set_temperature(base_temp + temp_variation)
        
        # Animate light with day/night cycle
        base_light = 50.0
        light_variation = 50.0 * (math.sin(self.animation_time * 0.05) + 1) / 2
        self.set_light(base_light + light_variation)
        
    def update_environment(self):
        """Update environment plot"""
        import time
        current_time = time.time()
        
        self.env_plot.update_data(
            current_time, self.temperature, 
            self.humidity, self.light_level
        )
        
    def emit_environment_change(self):
        """Emit environment change signal"""
        env_data = {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "light_level": self.light_level,
            "acceleration": {
                "x": self.acceleration_x,
                "y": self.acceleration_y,
                "z": self.acceleration_z
            },
            "gyroscope": {
                "x": self.gyro_x,
                "y": self.gyro_y,
                "z": self.gyro_z
            },
            "gps": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "altitude": self.altitude,
                "speed": self.gps_speed,
                "heading": self.gps_heading
            }
        }
        
        self.environment_changed.emit(env_data)
        
    # Scenario methods
    def scenario_sunrise(self):
        """Sunrise scenario"""
        self.set_temperature(15.0)
        self.set_humidity(80.0)
        self.set_light(10.0)
        
    def scenario_night(self):
        """Night scenario"""
        self.set_temperature(12.0)
        self.set_humidity(70.0)
        self.set_light(0.0)
        
    def scenario_rainy(self):
        """Rainy day scenario"""
        self.set_temperature(18.0)
        self.set_humidity(95.0)
        self.set_light(30.0)
        
    def scenario_desert(self):
        """Desert scenario"""
        self.set_temperature(45.0)
        self.set_humidity(10.0)
        self.set_light(100.0)
        
    def scenario_winter(self):
        """Winter scenario"""
        self.set_temperature(-5.0)
        self.set_humidity(60.0)
        self.set_light(40.0)
        
    def scenario_jogging(self):
        """Jogging motion scenario"""
        # Simulate jogging motion
        self.accel_x_slider.setValue(2)  # Side-to-side motion
        self.accel_y_slider.setValue(5)  # Forward motion
        self.accel_z_slider.setValue(12) # Vertical bounce
        
    def scenario_driving(self):
        """Driving scenario"""
        # Simulate car motion
        self.accel_y_slider.setValue(3)  # Forward acceleration
        self.update_speed(60)  # 60 km/h
        
    def scenario_phone(self):
        """Phone usage scenario"""
        # Typical phone orientation
        self.accel_x_slider.setValue(0)
        self.accel_y_slider.setValue(0)
        self.accel_z_slider.setValue(10)  # Upright
        
    # Motion presets
    def preset_still(self):
        """Still motion preset"""
        self.accel_x_slider.setValue(0)
        self.accel_y_slider.setValue(0)
        self.accel_z_slider.setValue(10)  # 1g gravity
        
    def preset_vibration(self):
        """Vibration preset"""
        # Small random vibrations would be implemented with animation
        pass
        
    def preset_tilt_left(self):
        """Tilt left preset"""
        self.accel_x_slider.setValue(-7)  # -0.7g
        self.accel_z_slider.setValue(7)   # 0.7g
        
    def preset_tilt_right(self):
        """Tilt right preset"""
        self.accel_x_slider.setValue(7)   # 0.7g
        self.accel_z_slider.setValue(7)   # 0.7g
        
    def preset_shake(self):
        """Shake preset"""
        # Would implement with animation
        pass