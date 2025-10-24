"""
Breadboard Widget - Visual breadboard with drag-and-drop wiring
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont


class BreadboardWidget(QWidget):
    """Visual breadboard for component placement and wiring"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        
        # Breadboard state
        self.components = []
        self.wires = []
        self.pi_header_rect = QRect(50, 50, 200, 300)
        
        # Drawing parameters
        self.pin_size = 8
        self.pin_spacing = 15
        
    def paintEvent(self, event):
        """Paint the breadboard"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        # Draw Pi header
        self._draw_pi_header(painter)
        
        # Draw components
        self._draw_components(painter)
        
        # Draw wires
        self._draw_wires(painter)
        
    def _draw_pi_header(self, painter):
        """Draw Raspberry Pi GPIO header"""
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRect(self.pi_header_rect)
        
        # Draw header label
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(self.pi_header_rect.x() + 5, self.pi_header_rect.y() - 5, "GPIO Header")
        
        # Draw pins (40-pin header, 2 columns)
        pin_colors = {
            "power": QColor(255, 0, 0),    # Red for power
            "ground": QColor(0, 0, 0),     # Black for ground
            "gpio": QColor(0, 255, 0),     # Green for GPIO
            "special": QColor(0, 0, 255)   # Blue for special functions
        }
        
        # Pin definitions (simplified)
        pin_types = [
            "power", "power",     # 3V3, 5V
            "special", "power",   # I2C SDA, 5V
            "special", "ground",  # I2C SCL, GND
            "gpio", "special",    # GPIO4, UART TX
            "ground", "special",  # GND, UART RX
            "gpio", "gpio",       # GPIO17, GPIO18
            "gpio", "ground",     # GPIO27, GND
            "gpio", "gpio",       # GPIO22, GPIO23
            "power", "gpio",      # 3V3, GPIO24
            "gpio", "gpio",       # GPIO10, GPIO25
            "gpio", "ground",     # GPIO9, GND
            "gpio", "gpio",       # GPIO11, GPIO8
            "ground", "gpio",     # GND, GPIO7
            "gpio", "gpio",       # GPIO0, GPIO1
            "gpio", "ground",     # GPIO5, GND
            "gpio", "gpio",       # GPIO6, GPIO12
            "gpio", "gpio",       # GPIO13, GND
            "gpio", "gpio",       # GPIO19, GPIO16
            "gpio", "gpio",       # GPIO26, GPIO20
            "ground", "gpio"      # GND, GPIO21
        ]
        
        for i in range(40):
            row = i // 2
            col = i % 2
            
            x = self.pi_header_rect.x() + 20 + col * 160
            y = self.pi_header_rect.y() + 20 + row * 14
            
            pin_type = pin_types[i] if i < len(pin_types) else "gpio"
            color = pin_colors.get(pin_type, pin_colors["gpio"])
            
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - self.pin_size//2, y - self.pin_size//2, 
                              self.pin_size, self.pin_size)
            
            # Pin number
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 6))
            painter.drawText(x + 10, y + 3, str(i + 1))
            
    def _draw_components(self, painter):
        """Draw placed components"""
        for component in self.components:
            # Draw component representation
            painter.setPen(QPen(QColor(200, 200, 200), 2))
            painter.setBrush(QBrush(QColor(80, 80, 80)))
            painter.drawRect(component["rect"])
            
            # Component label
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(component["rect"], Qt.AlignmentFlag.AlignCenter, component["name"])
            
    def _draw_wires(self, painter):
        """Draw wire connections"""
        for wire in self.wires:
            color = QColor(wire.get("color", "red"))
            painter.setPen(QPen(color, 3))
            painter.drawLine(wire["start"], wire["end"])
            
    def add_component(self, component_type, name, position):
        """Add component to breadboard"""
        component = {
            "type": component_type,
            "name": name,
            "rect": QRect(position.x(), position.y(), 60, 30),
            "pins": []
        }
        self.components.append(component)
        self.update()
        
    def add_wire(self, start_point, end_point, color="red"):
        """Add wire connection"""
        wire = {
            "start": start_point,
            "end": end_point,
            "color": color
        }
        self.wires.append(wire)
        self.update()
        
    def update_display(self):
        """Update display (called from main window)"""
        self.update()  # Trigger repaint
        
    def load_connections(self, connections):
        """Load connections from project"""
        self.wires.clear()
        for conn in connections:
            # Convert connection to wire representation
            # This is simplified - real implementation would parse pin locations
            start_point = QPoint(100, 100)  # Dummy positions
            end_point = QPoint(200, 200)
            self.add_wire(start_point, end_point, conn.wire_color)