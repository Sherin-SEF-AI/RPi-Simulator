"""
Logic Analyzer Widget - Interactive signal analysis interface
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QLabel, QGroupBox, QCheckBox, QColorDialog, QTabWidget, QTextEdit,
    QSlider, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    from logic_tools import LogicAnalyzer, ChannelConfig, TriggerType
    from logic_tools.protocol_decoder import I2CDecoder, SPIDecoder, UARTDecoder
except ImportError:
    # Create dummy classes for demo
    class LogicAnalyzer:
        def __init__(self, event_bus=None, max_channels=16):
            self.channels = {}
            self.acquiring = False
            
        def get_waveform_data(self, channel_id):
            return [], []
            
        def measure_frequency(self, channel_id):
            return None
            
        def measure_duty_cycle(self, channel_id):
            return None
            
    class ChannelConfig:
        pass
        
    class TriggerType:
        pass
        
    class I2CDecoder:
        pass
        
    class SPIDecoder:
        pass
        
    class UARTDecoder:
        pass


class WaveformCanvas(FigureCanvas):
    """Custom matplotlib canvas for waveform display"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#2b2b2b')
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Configure matplotlib for dark theme
        plt.style.use('dark_background')
        
        # Create subplots for channels
        self.axes = []
        self.max_channels = 8
        
        # Time cursor
        self.cursor_time = 0.0
        self.cursor_lines = []
        
        # Zoom and pan
        self.time_range = [0, 1e-3]  # 1ms default
        self.voltage_range = [-0.5, 3.5]
        
        self.setup_plots()
        
    def setup_plots(self):
        """Setup subplot layout"""
        self.figure.clear()
        
        # Create subplots for each channel
        for i in range(self.max_channels):
            if i == 0:
                ax = self.figure.add_subplot(self.max_channels, 1, i + 1)
            else:
                ax = self.figure.add_subplot(self.max_channels, 1, i + 1, sharex=self.axes[0])
                
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, alpha=0.3)
            ax.set_ylabel(f'CH{i}', color='white')
            ax.tick_params(colors='white')
            
            # Hide x-axis labels except for bottom plot
            if i < self.max_channels - 1:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel('Time (s)', color='white')
                
            self.axes.append(ax)
            
        self.figure.tight_layout()
        
    def update_waveforms(self, analyzer: LogicAnalyzer):
        """Update waveform display"""
        # Clear all plots
        for ax in self.axes:
            ax.clear()
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(self.voltage_range)
            ax.set_xlim(self.time_range)
            
        # Plot each channel
        channel_idx = 0
        for channel_id, config in analyzer.channels.items():
            if channel_idx >= len(self.axes) or not config.enabled:
                continue
                
            ax = self.axes[channel_idx]
            
            # Get waveform data
            time_data, signal_data = analyzer.get_waveform_data(channel_id)
            
            if len(time_data) > 0:
                # Convert boolean to voltage levels
                voltage_data = signal_data.astype(float) * 3.3
                
                # Plot digital waveform
                color = config.color
                ax.plot(time_data, voltage_data, color=color, linewidth=1.5, 
                       label=config.name)
                ax.fill_between(time_data, 0, voltage_data, alpha=0.3, color=color)
                
                # Add channel label
                ax.text(0.02, 0.8, config.name, transform=ax.transAxes, 
                       color='white', fontweight='bold')
                       
                # Show measurements
                frequency = analyzer.measure_frequency(channel_id)
                duty_cycle = analyzer.measure_duty_cycle(channel_id)
                
                measurements = []
                if frequency:
                    measurements.append(f"Freq: {frequency:.1f} Hz")
                if duty_cycle:
                    measurements.append(f"Duty: {duty_cycle:.1f}%")
                    
                if measurements:
                    ax.text(0.02, 0.6, " | ".join(measurements), 
                           transform=ax.transAxes, color='yellow', fontsize=8)
                           
            ax.set_ylabel(f'CH{channel_id}', color='white')
            ax.tick_params(colors='white')
            
            channel_idx += 1
            
        # Hide unused channels
        for i in range(channel_idx, len(self.axes)):
            self.axes[i].set_visible(False)
            
        # Show cursor
        self.update_cursor()
        
        self.draw()
        
    def update_cursor(self):
        """Update time cursor"""
        # Remove old cursor lines
        for line in self.cursor_lines:
            line.remove()
        self.cursor_lines.clear()
        
        # Add new cursor line to each visible axis
        for ax in self.axes:
            if ax.get_visible():
                line = ax.axvline(x=self.cursor_time, color='red', 
                                linestyle='--', alpha=0.7)
                self.cursor_lines.append(line)
                
    def set_cursor_time(self, time: float):
        """Set cursor time position"""
        self.cursor_time = time
        self.update_cursor()
        self.draw()
        
    def set_time_range(self, start: float, end: float):
        """Set time axis range"""
        self.time_range = [start, end]
        for ax in self.axes:
            ax.set_xlim(self.time_range)
        self.draw()


class LogicAnalyzerWidget(QWidget):
    """Logic Analyzer control and display widget"""
    
    # Signals
    acquisition_started = pyqtSignal()
    acquisition_stopped = pyqtSignal()
    
    def __init__(self, analyzer: LogicAnalyzer = None):
        super().__init__()
        self.analyzer = analyzer
        self.decoders = {
            "I2C": I2CDecoder(),
            "SPI": SPIDecoder(), 
            "UART": UARTDecoder()
        }
        
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # 10 FPS
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - waveform display
        waveform_widget = QWidget()
        waveform_layout = QVBoxLayout(waveform_widget)
        
        # Waveform canvas
        self.waveform_canvas = WaveformCanvas()
        waveform_layout.addWidget(self.waveform_canvas)
        
        # Time controls
        time_controls = self.create_time_controls()
        waveform_layout.addWidget(time_controls)
        
        main_splitter.addWidget(waveform_widget)
        
        # Right side - channel config and protocol decode
        right_panel = QTabWidget()
        
        # Channel configuration tab
        channel_tab = self.create_channel_tab()
        right_panel.addTab(channel_tab, "Channels")
        
        # Trigger configuration tab
        trigger_tab = self.create_trigger_tab()
        right_panel.addTab(trigger_tab, "Trigger")
        
        # Protocol decoder tab
        protocol_tab = self.create_protocol_tab()
        right_panel.addTab(protocol_tab, "Protocol")
        
        # Measurements tab
        measurements_tab = self.create_measurements_tab()
        right_panel.addTab(measurements_tab, "Measurements")
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([800, 400])
        
        layout.addWidget(main_splitter)
        
    def create_control_panel(self) -> QWidget:
        """Create main control panel"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Acquisition controls
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.toggle_acquisition)
        layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        layout.addWidget(self.stop_button)
        
        self.single_button = QPushButton("Single")
        self.single_button.clicked.connect(self.single_acquisition)
        layout.addWidget(self.single_button)
        
        layout.addWidget(QLabel("|"))
        
        # Sample rate
        layout.addWidget(QLabel("Sample Rate:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems([
            "1 MHz", "2 MHz", "5 MHz", "10 MHz", "25 MHz", "50 MHz", "100 MHz"
        ])
        self.sample_rate_combo.setCurrentText("1 MHz")
        self.sample_rate_combo.currentTextChanged.connect(self.update_sample_rate)
        layout.addWidget(self.sample_rate_combo)
        
        # Memory depth
        layout.addWidget(QLabel("Memory:"))
        self.memory_combo = QComboBox()
        self.memory_combo.addItems([
            "1K", "2K", "5K", "10K", "25K", "50K", "100K"
        ])
        self.memory_combo.setCurrentText("10K")
        self.memory_combo.currentTextChanged.connect(self.update_memory_depth)
        layout.addWidget(self.memory_combo)
        
        layout.addStretch()
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
        
    def create_time_controls(self) -> QWidget:
        """Create time axis controls"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Time base
        layout.addWidget(QLabel("Time/Div:"))
        self.timebase_combo = QComboBox()
        self.timebase_combo.addItems([
            "1 ns", "2 ns", "5 ns", "10 ns", "20 ns", "50 ns",
            "100 ns", "200 ns", "500 ns", "1 µs", "2 µs", "5 µs",
            "10 µs", "20 µs", "50 µs", "100 µs", "200 µs", "500 µs",
            "1 ms", "2 ms", "5 ms", "10 ms"
        ])
        self.timebase_combo.setCurrentText("100 µs")
        self.timebase_combo.currentTextChanged.connect(self.update_timebase)
        layout.addWidget(self.timebase_combo)
        
        # Horizontal position
        layout.addWidget(QLabel("H-Pos:"))
        self.h_pos_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_pos_slider.setRange(-100, 100)
        self.h_pos_slider.setValue(0)
        self.h_pos_slider.valueChanged.connect(self.update_h_position)
        layout.addWidget(self.h_pos_slider)
        
        # Cursor controls
        layout.addWidget(QLabel("|"))
        layout.addWidget(QLabel("Cursor:"))
        self.cursor_spinbox = QDoubleSpinBox()
        self.cursor_spinbox.setRange(0, 1)
        self.cursor_spinbox.setDecimals(6)
        self.cursor_spinbox.setSuffix(" s")
        self.cursor_spinbox.valueChanged.connect(self.update_cursor)
        layout.addWidget(self.cursor_spinbox)
        
        layout.addStretch()
        
        return panel
        
    def create_channel_tab(self) -> QWidget:
        """Create channel configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Channel table
        self.channel_table = QTableWidget()
        self.channel_table.setColumnCount(5)
        self.channel_table.setHorizontalHeaderLabels([
            "Enable", "Name", "Color", "Threshold", "Invert"
        ])
        
        # Populate with default channels
        self.channel_table.setRowCount(8)
        for i in range(8):
            # Enable checkbox
            enable_cb = QCheckBox()
            enable_cb.setChecked(i < 4)  # Enable first 4 channels
            self.channel_table.setCellWidget(i, 0, enable_cb)
            
            # Name
            name_item = QTableWidgetItem(f"CH{i}")
            self.channel_table.setItem(i, 1, name_item)
            
            # Color button
            color_btn = QPushButton()
            colors = ["#00FF00", "#FF0000", "#0000FF", "#FFFF00", 
                     "#FF00FF", "#00FFFF", "#FFA500", "#800080"]
            color_btn.setStyleSheet(f"background-color: {colors[i % len(colors)]}")
            color_btn.clicked.connect(lambda checked, row=i: self.choose_color(row))
            self.channel_table.setCellWidget(i, 2, color_btn)
            
            # Threshold
            threshold_spin = QDoubleSpinBox()
            threshold_spin.setRange(0.1, 5.0)
            threshold_spin.setValue(1.65)
            threshold_spin.setSuffix(" V")
            self.channel_table.setCellWidget(i, 3, threshold_spin)
            
            # Invert
            invert_cb = QCheckBox()
            self.channel_table.setCellWidget(i, 4, invert_cb)
            
        layout.addWidget(self.channel_table)
        
        # Channel controls
        controls = QHBoxLayout()
        
        add_btn = QPushButton("Add Channel")
        add_btn.clicked.connect(self.add_channel)
        controls.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Channel")
        remove_btn.clicked.connect(self.remove_channel)
        controls.addWidget(remove_btn)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        return widget
        
    def create_trigger_tab(self) -> QWidget:
        """Create trigger configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Trigger settings group
        trigger_group = QGroupBox("Trigger Settings")
        trigger_layout = QVBoxLayout(trigger_group)
        
        # Trigger source
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.trigger_source_combo = QComboBox()
        self.trigger_source_combo.addItems([f"CH{i}" for i in range(8)])
        source_layout.addWidget(self.trigger_source_combo)
        source_layout.addStretch()
        trigger_layout.addLayout(source_layout)
        
        # Trigger type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.trigger_type_combo = QComboBox()
        self.trigger_type_combo.addItems([
            "Rising Edge", "Falling Edge", "Both Edges", "High Level", "Low Level"
        ])
        type_layout.addWidget(self.trigger_type_combo)
        type_layout.addStretch()
        trigger_layout.addLayout(type_layout)
        
        # Auto trigger
        self.auto_trigger_cb = QCheckBox("Auto Trigger")
        self.auto_trigger_cb.setChecked(True)
        trigger_layout.addWidget(self.auto_trigger_cb)
        
        # Trigger position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.trigger_pos_slider = QSlider(Qt.Orientation.Horizontal)
        self.trigger_pos_slider.setRange(0, 100)
        self.trigger_pos_slider.setValue(10)  # 10% pre-trigger
        pos_layout.addWidget(self.trigger_pos_slider)
        self.trigger_pos_label = QLabel("10%")
        pos_layout.addWidget(self.trigger_pos_label)
        trigger_layout.addLayout(pos_layout)
        
        layout.addWidget(trigger_group)
        
        # Force trigger button
        force_btn = QPushButton("Force Trigger")
        force_btn.clicked.connect(self.force_trigger)
        layout.addWidget(force_btn)
        
        layout.addStretch()
        
        return widget
        
    def create_protocol_tab(self) -> QWidget:
        """Create protocol decoder tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Protocol selection
        protocol_layout = QHBoxLayout()
        protocol_layout.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["None", "I2C", "SPI", "UART"])
        self.protocol_combo.currentTextChanged.connect(self.update_protocol_decoder)
        protocol_layout.addWidget(self.protocol_combo)
        protocol_layout.addStretch()
        layout.addLayout(protocol_layout)
        
        # Protocol-specific settings
        self.protocol_settings = QGroupBox("Protocol Settings")
        self.protocol_settings_layout = QVBoxLayout(self.protocol_settings)
        layout.addWidget(self.protocol_settings)
        
        # Decoded data table
        self.protocol_table = QTableWidget()
        self.protocol_table.setColumnCount(4)
        self.protocol_table.setHorizontalHeaderLabels([
            "Time", "Type", "Data", "Description"
        ])
        layout.addWidget(self.protocol_table)
        
        return widget
        
    def create_measurements_tab(self) -> QWidget:
        """Create measurements tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Measurement controls
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("Channel:"))
        self.measure_channel_combo = QComboBox()
        self.measure_channel_combo.addItems([f"CH{i}" for i in range(8)])
        controls.addWidget(self.measure_channel_combo)
        
        measure_btn = QPushButton("Measure")
        measure_btn.clicked.connect(self.perform_measurements)
        controls.addWidget(measure_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Measurements display
        self.measurements_text = QTextEdit()
        self.measurements_text.setReadOnly(True)
        self.measurements_text.setMaximumHeight(200)
        layout.addWidget(self.measurements_text)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        return widget
        
    def toggle_acquisition(self):
        """Toggle acquisition on/off"""
        if self.analyzer and not self.analyzer.acquiring:
            self.start_acquisition()
        else:
            self.stop_acquisition()
            
    def start_acquisition(self):
        """Start logic analyzer acquisition"""
        if self.analyzer:
            self.analyzer.start_acquisition()
            self.run_button.setText("Stop")
            self.status_label.setText("Acquiring...")
            self.progress_bar.setVisible(True)
            self.acquisition_started.emit()
            
    def stop_acquisition(self):
        """Stop logic analyzer acquisition"""
        if self.analyzer:
            self.analyzer.stop_acquisition()
            self.run_button.setText("Run")
            self.status_label.setText("Stopped")
            self.progress_bar.setVisible(False)
            self.acquisition_stopped.emit()
            
    def single_acquisition(self):
        """Perform single acquisition"""
        if self.analyzer:
            self.analyzer.auto_trigger = False
            self.start_acquisition()
            
    def update_display(self):
        """Update waveform display"""
        if self.analyzer and self.analyzer.acquiring:
            self.waveform_canvas.update_waveforms(self.analyzer)
            
    def update_sample_rate(self, rate_text: str):
        """Update sample rate"""
        if self.analyzer:
            rate_map = {
                "1 MHz": 1_000_000,
                "2 MHz": 2_000_000,
                "5 MHz": 5_000_000,
                "10 MHz": 10_000_000,
                "25 MHz": 25_000_000,
                "50 MHz": 50_000_000,
                "100 MHz": 100_000_000
            }
            self.analyzer.sample_rate = rate_map.get(rate_text, 1_000_000)
            
    def update_memory_depth(self, memory_text: str):
        """Update memory depth"""
        if self.analyzer:
            memory_map = {
                "1K": 1024,
                "2K": 2048,
                "5K": 5120,
                "10K": 10240,
                "25K": 25600,
                "50K": 51200,
                "100K": 102400
            }
            self.analyzer.memory_depth = memory_map.get(memory_text, 10240)
            
    def update_timebase(self, timebase_text: str):
        """Update time base"""
        # Parse timebase and update display range
        timebase_map = {
            "1 ns": 1e-9, "2 ns": 2e-9, "5 ns": 5e-9,
            "10 ns": 10e-9, "20 ns": 20e-9, "50 ns": 50e-9,
            "100 ns": 100e-9, "200 ns": 200e-9, "500 ns": 500e-9,
            "1 µs": 1e-6, "2 µs": 2e-6, "5 µs": 5e-6,
            "10 µs": 10e-6, "20 µs": 20e-6, "50 µs": 50e-6,
            "100 µs": 100e-6, "200 µs": 200e-6, "500 µs": 500e-6,
            "1 ms": 1e-3, "2 ms": 2e-3, "5 ms": 5e-3, "10 ms": 10e-3
        }
        
        time_per_div = timebase_map.get(timebase_text, 100e-6)
        total_time = time_per_div * 10  # 10 divisions
        
        self.waveform_canvas.set_time_range(0, total_time)
        
    def update_h_position(self, value: int):
        """Update horizontal position"""
        # Shift time range based on slider value
        current_range = self.waveform_canvas.time_range
        range_width = current_range[1] - current_range[0]
        
        # Convert slider value (-100 to 100) to time offset
        offset = (value / 100.0) * range_width * 0.5
        
        new_start = offset
        new_end = offset + range_width
        
        self.waveform_canvas.set_time_range(new_start, new_end)
        
    def update_cursor(self, time: float):
        """Update cursor position"""
        self.waveform_canvas.set_cursor_time(time)
        
    def choose_color(self, row: int):
        """Choose color for channel"""
        color = QColorDialog.getColor()
        if color.isValid():
            button = self.channel_table.cellWidget(row, 2)
            button.setStyleSheet(f"background-color: {color.name()}")
            
    def add_channel(self):
        """Add new channel"""
        row_count = self.channel_table.rowCount()
        if row_count < 16:  # Maximum 16 channels
            self.channel_table.insertRow(row_count)
            # Add widgets for new row
            # ... (similar to setup in create_channel_tab)
            
    def remove_channel(self):
        """Remove selected channel"""
        current_row = self.channel_table.currentRow()
        if current_row >= 0:
            self.channel_table.removeRow(current_row)
            
    def update_protocol_decoder(self, protocol: str):
        """Update protocol decoder settings"""
        # Clear existing settings
        for i in reversed(range(self.protocol_settings_layout.count())):
            self.protocol_settings_layout.itemAt(i).widget().setParent(None)
            
        if protocol == "I2C":
            # I2C settings
            layout = QHBoxLayout()
            layout.addWidget(QLabel("SCL:"))
            scl_combo = QComboBox()
            scl_combo.addItems([f"CH{i}" for i in range(8)])
            layout.addWidget(scl_combo)
            
            layout.addWidget(QLabel("SDA:"))
            sda_combo = QComboBox()
            sda_combo.addItems([f"CH{i}" for i in range(8)])
            sda_combo.setCurrentIndex(1)
            layout.addWidget(sda_combo)
            
            self.protocol_settings_layout.addLayout(layout)
            
        elif protocol == "SPI":
            # SPI settings
            layout = QVBoxLayout()
            
            row1 = QHBoxLayout()
            row1.addWidget(QLabel("SCLK:"))
            sclk_combo = QComboBox()
            sclk_combo.addItems([f"CH{i}" for i in range(8)])
            row1.addWidget(sclk_combo)
            
            row1.addWidget(QLabel("MOSI:"))
            mosi_combo = QComboBox()
            mosi_combo.addItems([f"CH{i}" for i in range(8)])
            mosi_combo.setCurrentIndex(1)
            row1.addWidget(mosi_combo)
            
            layout.addLayout(row1)
            
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("MISO:"))
            miso_combo = QComboBox()
            miso_combo.addItems([f"CH{i}" for i in range(8)])
            miso_combo.setCurrentIndex(2)
            row2.addWidget(miso_combo)
            
            row2.addWidget(QLabel("CS:"))
            cs_combo = QComboBox()
            cs_combo.addItems([f"CH{i}" for i in range(8)])
            cs_combo.setCurrentIndex(3)
            row2.addWidget(cs_combo)
            
            layout.addLayout(row2)
            
            self.protocol_settings_layout.addLayout(layout)
            
        elif protocol == "UART":
            # UART settings
            layout = QVBoxLayout()
            
            row1 = QHBoxLayout()
            row1.addWidget(QLabel("TX:"))
            tx_combo = QComboBox()
            tx_combo.addItems([f"CH{i}" for i in range(8)])
            row1.addWidget(tx_combo)
            
            row1.addWidget(QLabel("RX:"))
            rx_combo = QComboBox()
            rx_combo.addItems([f"CH{i}" for i in range(8)])
            rx_combo.setCurrentIndex(1)
            row1.addWidget(rx_combo)
            
            layout.addLayout(row1)
            
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("Baud Rate:"))
            baud_combo = QComboBox()
            baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
            row2.addWidget(baud_combo)
            
            layout.addLayout(row2)
            
            self.protocol_settings_layout.addLayout(layout)
            
    def force_trigger(self):
        """Force trigger event"""
        if self.analyzer:
            # Manually trigger acquisition
            pass
            
    def perform_measurements(self):
        """Perform measurements on selected channel"""
        if not self.analyzer:
            return
            
        channel_id = self.measure_channel_combo.currentIndex()
        
        # Get measurements
        frequency = self.analyzer.measure_frequency(channel_id)
        duty_cycle = self.analyzer.measure_duty_cycle(channel_id)
        edges = self.analyzer.find_edges(channel_id)
        
        # Display results
        results = []
        if frequency:
            results.append(f"Frequency: {frequency:.2f} Hz")
            results.append(f"Period: {1/frequency*1000:.3f} ms")
            
        if duty_cycle:
            results.append(f"Duty Cycle: {duty_cycle:.1f}%")
            
        results.append(f"Edge Count: {len(edges)}")
        
        self.measurements_text.setText("\\n".join(results))
        
        # Update statistics
        if self.analyzer:
            stats = self.analyzer.get_statistics()
            stats_text = []
            for key, value in stats.items():
                stats_text.append(f"{key}: {value}")
            self.stats_text.setText("\\n".join(stats_text))