"""
Pin Inspector Widget - Real-time GPIO pin monitoring
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class PinInspectorWidget(QWidget):
    """Widget for monitoring GPIO pin states and signals"""
    
    def __init__(self):
        super().__init__()
        
        # Pin data
        self.pin_data = {}
        self._init_pin_data()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Pin mode selector
        controls_layout.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["All Pins", "GPIO Only", "Active Only"])
        controls_layout.addWidget(self.view_combo)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        controls_layout.addWidget(self.refresh_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Pin table
        self.pin_table = QTableWidget()
        self.pin_table.setColumnCount(6)
        self.pin_table.setHorizontalHeaderLabels([
            "Pin", "BCM", "Mode", "Value", "Function", "State"
        ])
        
        # Set column widths
        header = self.pin_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.pin_table)
        
        # Update table
        self._update_table()
        
    def _init_pin_data(self):
        """Initialize pin data structure"""
        # GPIO pin definitions (simplified)
        gpio_pins = [
            (1, None, "3V3", "Power"),
            (2, None, "5V", "Power"),
            (3, 2, "GPIO2", "I2C SDA"),
            (4, None, "5V", "Power"),
            (5, 3, "GPIO3", "I2C SCL"),
            (6, None, "GND", "Ground"),
            (7, 4, "GPIO4", "GPIO"),
            (8, 14, "GPIO14", "UART TX"),
            (9, None, "GND", "Ground"),
            (10, 15, "GPIO15", "UART RX"),
            (11, 17, "GPIO17", "GPIO"),
            (12, 18, "GPIO18", "PWM"),
            (13, 27, "GPIO27", "GPIO"),
            (14, None, "GND", "Ground"),
            (15, 22, "GPIO22", "GPIO"),
            (16, 23, "GPIO23", "GPIO"),
            (17, None, "3V3", "Power"),
            (18, 24, "GPIO24", "GPIO"),
            (19, 10, "GPIO10", "SPI MOSI"),
            (20, None, "GND", "Ground"),
        ]
        
        for board_pin, bcm_pin, name, function in gpio_pins:
            self.pin_data[board_pin] = {
                "board": board_pin,
                "bcm": bcm_pin,
                "name": name,
                "function": function,
                "mode": "INPUT" if bcm_pin else "N/A",
                "value": 0,
                "state": "LOW" if bcm_pin else "N/A"
            }
            
    def _update_table(self):
        """Update pin table display"""
        # Filter pins based on view selection
        view_mode = self.view_combo.currentText()
        
        if view_mode == "GPIO Only":
            pins = {k: v for k, v in self.pin_data.items() if v["bcm"] is not None}
        elif view_mode == "Active Only":
            pins = {k: v for k, v in self.pin_data.items() 
                   if v["bcm"] is not None and v["mode"] != "INPUT"}
        else:
            pins = self.pin_data
            
        # Set table size
        self.pin_table.setRowCount(len(pins))
        
        # Populate table
        for row, (pin_num, pin_info) in enumerate(pins.items()):
            # Pin number
            self.pin_table.setItem(row, 0, QTableWidgetItem(str(pin_info["board"])))
            
            # BCM number
            bcm_text = str(pin_info["bcm"]) if pin_info["bcm"] is not None else "-"
            self.pin_table.setItem(row, 1, QTableWidgetItem(bcm_text))
            
            # Mode
            mode_item = QTableWidgetItem(pin_info["mode"])
            if pin_info["mode"] == "OUTPUT":
                mode_item.setBackground(QColor(100, 200, 100))
            elif pin_info["mode"] == "INPUT":
                mode_item.setBackground(QColor(200, 200, 100))
            self.pin_table.setItem(row, 2, mode_item)
            
            # Value
            value_item = QTableWidgetItem(str(pin_info["value"]))
            if pin_info["value"] == 1:
                value_item.setBackground(QColor(200, 100, 100))
            self.pin_table.setItem(row, 3, value_item)
            
            # Function
            self.pin_table.setItem(row, 4, QTableWidgetItem(pin_info["function"]))
            
            # State
            state_item = QTableWidgetItem(pin_info["state"])
            if pin_info["state"] == "HIGH":
                state_item.setBackground(QColor(255, 100, 100))
            elif pin_info["state"] == "LOW":
                state_item.setBackground(QColor(100, 100, 255))
            self.pin_table.setItem(row, 5, state_item)
            
    def update_pin_state(self, bcm_pin, mode, value):
        """Update pin state from simulation"""
        for pin_info in self.pin_data.values():
            if pin_info["bcm"] == bcm_pin:
                pin_info["mode"] = mode
                pin_info["value"] = value
                pin_info["state"] = "HIGH" if value else "LOW"
                break
                
        self._update_table()
        
    def update_display(self):
        """Update display (called from main window)"""
        # This would be called periodically to refresh the display
        # For now, just refresh the table
        pass