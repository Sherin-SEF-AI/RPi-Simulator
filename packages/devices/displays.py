"""
Display Device Implementations
"""

import time
from typing import List, Tuple, Optional, Dict, Any
from peripherals import I2cDevice, SpiDevice
from .base import VirtualDevice, DeviceParameter


class LCD1602(I2cDevice, VirtualDevice):
    """16x2 Character LCD Display (I2C)"""
    
    def __init__(self, address: int = 0x27, name: str = "LCD1602"):
        I2cDevice.__init__(self, address, name)
        VirtualDevice.__init__(self, name, "display")
        
        # Display parameters
        self.parameters = {
            "backlight": DeviceParameter("Backlight", True, description="LCD backlight on/off"),
            "contrast": DeviceParameter("Contrast", 50, 0, 100, "%", "Display contrast"),
            "cursor": DeviceParameter("Cursor", False, description="Show cursor"),
            "blink": DeviceParameter("Blink", False, description="Cursor blink")
        }
        
        # Display state
        self.display_buffer = [[' ' for _ in range(16)] for _ in range(2)]
        self.cursor_pos = (0, 0)
        self.display_on = True
        
        # Command history for debugging
        self.command_history: List[Tuple[float, str, List[int]]] = []
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update display state"""
        self.last_update = sim_time
        
    def write(self, data: List[int]) -> bool:
        """Handle I2C write commands"""
        if not data:
            return True
            
        timestamp = time.time()
        
        # Parse LCD commands (simplified I2C-to-parallel converter)
        for byte in data:
            if byte & 0x08:  # Enable bit set
                if byte & 0x01:  # RS bit - data
                    char = chr((byte & 0xF0) | ((byte >> 4) & 0x0F))
                    self._write_char(char)
                else:  # Command
                    self._process_command(byte & 0xF0)
                    
        self.command_history.append((timestamp, "write", data))
        return True
        
    def _write_char(self, char: str) -> None:
        """Write character to current cursor position"""
        row, col = self.cursor_pos
        if 0 <= row < 2 and 0 <= col < 16:
            self.display_buffer[row][col] = char
            
            # Advance cursor
            col += 1
            if col >= 16:
                col = 0
                row = (row + 1) % 2
            self.cursor_pos = (row, col)
            
    def _process_command(self, cmd: int) -> None:
        """Process LCD command"""
        if cmd == 0x01:  # Clear display
            self.clear()
        elif cmd == 0x02:  # Return home
            self.cursor_pos = (0, 0)
        elif cmd & 0x80:  # Set DDRAM address
            addr = cmd & 0x7F
            if addr < 0x40:
                self.cursor_pos = (0, addr)
            else:
                self.cursor_pos = (1, addr - 0x40)
                
    def clear(self) -> None:
        """Clear display"""
        self.display_buffer = [[' ' for _ in range(16)] for _ in range(2)]
        self.cursor_pos = (0, 0)
        
    def set_cursor(self, row: int, col: int) -> None:
        """Set cursor position"""
        if 0 <= row < 2 and 0 <= col < 16:
            self.cursor_pos = (row, col)
            
    def print_text(self, text: str, row: int = 0, col: int = 0) -> None:
        """Print text at specified position"""
        self.set_cursor(row, col)
        for char in text:
            if char == '\n':
                self.cursor_pos = (1, 0)
            else:
                self._write_char(char)
                
    def get_display_text(self) -> List[str]:
        """Get current display content as strings"""
        return [''.join(row) for row in self.display_buffer]
        
    def reset(self) -> None:
        """Reset display"""
        self.clear()
        self.display_on = True
        self.command_history.clear()


class SSD1306(I2cDevice, VirtualDevice):
    """128x64 OLED Display (I2C)"""
    
    def __init__(self, address: int = 0x3C, name: str = "SSD1306"):
        I2cDevice.__init__(self, address, name)
        VirtualDevice.__init__(self, name, "display")
        
        # Display parameters
        self.parameters = {
            "brightness": DeviceParameter("Brightness", 255, 0, 255, "", "Display brightness"),
            "invert": DeviceParameter("Invert", False, description="Invert display colors"),
            "rotation": DeviceParameter("Rotation", 0, 0, 3, "", "Display rotation (0-3)")
        }
        
        # Display buffer (128x64 pixels, 1 bit per pixel)
        self.width = 128
        self.height = 64
        self.pages = 8  # 64 / 8 = 8 pages
        self.buffer = bytearray(self.width * self.pages)
        
        # State
        self.display_on = False
        self.column_start = 0
        self.column_end = 127
        self.page_start = 0
        self.page_end = 7
        self.current_page = 0
        self.current_column = 0
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update display state"""
        self.last_update = sim_time
        
    def write(self, data: List[int]) -> bool:
        """Handle I2C write"""
        if not data:
            return True
            
        i = 0
        while i < len(data):
            if data[i] == 0x00:  # Command mode
                i += 1
                if i < len(data):
                    self._process_command(data[i])
            elif data[i] == 0x40:  # Data mode
                i += 1
                while i < len(data):
                    self._write_data(data[i])
                    i += 1
                break
            i += 1
            
        return True
        
    def _process_command(self, cmd: int) -> None:
        """Process OLED command"""
        if cmd == 0xAE:  # Display off
            self.display_on = False
        elif cmd == 0xAF:  # Display on
            self.display_on = True
        elif cmd & 0xF0 == 0xB0:  # Set page address
            self.current_page = cmd & 0x0F
        elif cmd & 0xF0 == 0x00:  # Set lower column address
            self.current_column = (self.current_column & 0xF0) | (cmd & 0x0F)
        elif cmd & 0xF0 == 0x10:  # Set higher column address
            self.current_column = (self.current_column & 0x0F) | ((cmd & 0x0F) << 4)
            
    def _write_data(self, data: int) -> None:
        """Write data to display buffer"""
        if (0 <= self.current_page < self.pages and 
            0 <= self.current_column < self.width):
            
            addr = self.current_page * self.width + self.current_column
            self.buffer[addr] = data
            
            self.current_column += 1
            if self.current_column >= self.width:
                self.current_column = 0
                
    def clear(self) -> None:
        """Clear display"""
        self.buffer = bytearray(self.width * self.pages)
        
    def set_pixel(self, x: int, y: int, color: bool = True) -> None:
        """Set individual pixel"""
        if 0 <= x < self.width and 0 <= y < self.height:
            page = y // 8
            bit = y % 8
            addr = page * self.width + x
            
            if color:
                self.buffer[addr] |= (1 << bit)
            else:
                self.buffer[addr] &= ~(1 << bit)
                
    def get_pixel(self, x: int, y: int) -> bool:
        """Get pixel state"""
        if 0 <= x < self.width and 0 <= y < self.height:
            page = y // 8
            bit = y % 8
            addr = page * self.width + x
            return bool(self.buffer[addr] & (1 << bit))
        return False
        
    def draw_text(self, text: str, x: int, y: int, font_size: int = 8) -> None:
        """Draw text (simplified 8x8 font)"""
        # Simple 8x8 bitmap font (would be expanded in real implementation)
        char_width = font_size
        
        for i, char in enumerate(text):
            char_x = x + i * char_width
            if char_x >= self.width:
                break
                
            # Draw simple character representation
            ascii_val = ord(char)
            for py in range(font_size):
                for px in range(char_width):
                    # Simple pattern based on ASCII value
                    if (ascii_val + px + py) % 3 == 0:
                        self.set_pixel(char_x + px, y + py, True)
                        
    def get_display_data(self) -> bytes:
        """Get display buffer for visualization"""
        return bytes(self.buffer)
        
    def reset(self) -> None:
        """Reset display"""
        self.clear()
        self.display_on = False
        self.current_page = 0
        self.current_column = 0


class SevenSegment(VirtualDevice):
    """7-Segment Display"""
    
    def __init__(self, name: str = "7Segment", pins: List[int] = None):
        super().__init__(name, "display")
        
        # Default pins: [a, b, c, d, e, f, g, dp]
        self.pins = pins or [2, 3, 4, 5, 6, 7, 8, 9]
        
        # Parameters
        self.parameters = {
            "brightness": DeviceParameter("Brightness", 100, 0, 100, "%"),
            "common_cathode": DeviceParameter("Common Cathode", True, description="Common cathode (vs anode)")
        }
        
        # Segment states (a, b, c, d, e, f, g, dp)
        self.segments = [False] * 8
        
        # Digit patterns (0-9, A-F)
        self.digit_patterns = {
            0: [True, True, True, True, True, True, False, False],    # 0
            1: [False, True, True, False, False, False, False, False], # 1
            2: [True, True, False, True, True, False, True, False],   # 2
            3: [True, True, True, True, False, False, True, False],   # 3
            4: [False, True, True, False, False, True, True, False],  # 4
            5: [True, False, True, True, False, True, True, False],   # 5
            6: [True, False, True, True, True, True, True, False],    # 6
            7: [True, True, True, False, False, False, False, False], # 7
            8: [True, True, True, True, True, True, True, False],     # 8
            9: [True, True, True, True, False, True, True, False],    # 9
            10: [True, True, True, False, True, True, True, False],   # A
            11: [False, False, True, True, True, True, True, False],  # b
            12: [True, False, False, True, True, True, False, False], # C
            13: [False, True, True, True, True, False, True, False],  # d
            14: [True, False, False, True, True, True, True, False],  # E
            15: [True, False, False, False, True, True, True, False], # F
        }
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update display state"""
        self.last_update = sim_time
        
    def set_segments(self, segments: List[bool]) -> None:
        """Set individual segment states"""
        if len(segments) >= 7:
            self.segments[:7] = segments[:7]
            
    def set_digit(self, digit: int, decimal_point: bool = False) -> None:
        """Display a digit (0-15)"""
        if digit in self.digit_patterns:
            self.segments = self.digit_patterns[digit].copy()
            self.segments[7] = decimal_point  # Decimal point
            
    def set_character(self, char: str, decimal_point: bool = False) -> None:
        """Display a character"""
        char = char.upper()
        if char.isdigit():
            self.set_digit(int(char), decimal_point)
        elif char in 'ABCDEF':
            self.set_digit(ord(char) - ord('A') + 10, decimal_point)
        elif char == '-':
            self.segments = [False, False, False, False, False, False, True, decimal_point]
        elif char == ' ':
            self.segments = [False] * 8
            
    def get_segments(self) -> List[bool]:
        """Get current segment states"""
        return self.segments.copy()
        
    def get_pin_states(self) -> Dict[int, bool]:
        """Get pin states for GPIO simulation"""
        common_cathode = self.get_parameter("common_cathode")
        pin_states = {}
        
        for i, pin in enumerate(self.pins):
            if i < len(self.segments):
                # Invert for common anode
                state = self.segments[i] if common_cathode else not self.segments[i]
                pin_states[pin] = state
                
        return pin_states
        
    def reset(self) -> None:
        """Reset display"""
        self.segments = [False] * 8


class NeoPixelStrip(VirtualDevice):
    """WS2812B NeoPixel LED Strip"""
    
    def __init__(self, name: str = "NeoPixel", data_pin: int = 18, num_pixels: int = 8):
        super().__init__(name, "display")
        
        self.data_pin = data_pin
        self.num_pixels = num_pixels
        
        # Parameters
        self.parameters = {
            "num_pixels": DeviceParameter("Pixel Count", num_pixels, 1, 1000, "", "Number of LEDs"),
            "brightness": DeviceParameter("Brightness", 255, 0, 255, "", "Global brightness"),
            "color_order": DeviceParameter("Color Order", "GRB", description="Color byte order")
        }
        
        # Pixel data: [(R, G, B), ...]
        self.pixels: List[Tuple[int, int, int]] = [(0, 0, 0)] * num_pixels
        
        # Animation state
        self.animation_mode = "static"
        self.animation_speed = 1.0
        self.animation_time = 0.0
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update animation"""
        self.last_update = sim_time
        self.animation_time += dt
        
        if self.animation_mode == "rainbow":
            self._update_rainbow()
        elif self.animation_mode == "chase":
            self._update_chase()
        elif self.animation_mode == "breathe":
            self._update_breathe()
            
    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """Set individual pixel color"""
        if 0 <= index < len(self.pixels):
            self.pixels[index] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            )
            
    def set_all(self, r: int, g: int, b: int) -> None:
        """Set all pixels to same color"""
        color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        self.pixels = [color] * len(self.pixels)
        
    def clear(self) -> None:
        """Turn off all pixels"""
        self.pixels = [(0, 0, 0)] * len(self.pixels)
        
    def fill_range(self, start: int, end: int, r: int, g: int, b: int) -> None:
        """Fill range of pixels"""
        for i in range(max(0, start), min(len(self.pixels), end + 1)):
            self.set_pixel(i, r, g, b)
            
    def set_animation(self, mode: str, speed: float = 1.0) -> None:
        """Set animation mode"""
        self.animation_mode = mode
        self.animation_speed = speed
        self.animation_time = 0.0
        
    def _update_rainbow(self) -> None:
        """Rainbow animation"""
        import math
        
        for i in range(len(self.pixels)):
            hue = (self.animation_time * self.animation_speed + i * 0.1) % 1.0
            r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
            self.pixels[i] = (int(r * 255), int(g * 255), int(b * 255))
            
    def _update_chase(self) -> None:
        """Chase animation"""
        pos = int(self.animation_time * self.animation_speed * 10) % len(self.pixels)
        self.clear()
        self.set_pixel(pos, 255, 255, 255)
        
    def _update_breathe(self) -> None:
        """Breathing animation"""
        import math
        
        brightness = (math.sin(self.animation_time * self.animation_speed * 2) + 1) / 2
        intensity = int(brightness * 255)
        self.set_all(intensity, intensity, intensity)
        
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV to RGB"""
        import math
        
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        i = i % 6
        if i == 0:
            return v, t, p
        elif i == 1:
            return q, v, p
        elif i == 2:
            return p, v, t
        elif i == 3:
            return p, q, v
        elif i == 4:
            return t, p, v
        else:
            return v, p, q
            
    def get_pixel_data(self) -> List[Tuple[int, int, int]]:
        """Get current pixel colors"""
        brightness = self.get_parameter("brightness") / 255.0
        return [(int(r * brightness), int(g * brightness), int(b * brightness)) 
                for r, g, b in self.pixels]
                
    def reset(self) -> None:
        """Reset strip"""
        self.clear()
        self.animation_mode = "static"
        self.animation_time = 0.0