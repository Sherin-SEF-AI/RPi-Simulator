"""
Console Widget - Code execution and logging
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QTabWidget, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont, QTextCursor


class ConsoleWidget(QWidget):
    """Console widget for code execution and logging"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
        # Process for running user code
        self.process = None
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Tab widget for different console views
        self.tab_widget = QTabWidget()
        
        # Output tab
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """)
        self.tab_widget.addTab(self.output_text, "Output")
        
        # Logs tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #555555;
            }
        """)
        self.tab_widget.addTab(self.log_text, "Simulation Log")
        
        # Code editor tab
        self.code_editor = QPlainTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """)
        
        # Default Python code
        default_code = '''#!/usr/bin/env python3
"""
PiStudio Example - LED Blink
"""

import RPiSim.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    print("Starting LED blink...")
    for i in range(10):
        GPIO.output(LED_PIN, GPIO.HIGH)
        print(f"LED ON - {i+1}")
        time.sleep(0.5)
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"LED OFF - {i+1}")
        time.sleep(0.5)
        
    print("Blink complete!")
    
except KeyboardInterrupt:
    print("Interrupted by user")
    
finally:
    GPIO.cleanup()
    print("GPIO cleanup complete")
'''
        self.code_editor.setPlainText(default_code)
        self.tab_widget.addTab(self.code_editor, "Code Editor")
        
        layout.addWidget(self.tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Code")
        self.run_button.clicked.connect(self._run_code)
        button_layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_code)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self._clear_output)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
        
    def _run_code(self):
        """Run the code in the editor"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.append_text("Process already running. Stop it first.\n")
            return
            
        # Get code from editor
        code = self.code_editor.toPlainText()
        
        # Save code to temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
            
        # Start process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._process_finished)
        
        self.process.start("python3", [temp_file])
        
        if self.process.waitForStarted():
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Running...")
            self.append_text("=== Code Execution Started ===\n")
        else:
            self.append_text("Failed to start process\n")
            os.unlink(temp_file)
            
    def _stop_code(self):
        """Stop running code"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.append_text("\n=== Process Terminated ===\n")
            
    def _clear_output(self):
        """Clear output text"""
        self.output_text.clear()
        
    def _handle_stdout(self):
        """Handle stdout from process"""
        if self.process:
            data = self.process.readAllStandardOutput()
            text = bytes(data).decode('utf-8')
            self.append_text(text)
            
    def _handle_stderr(self):
        """Handle stderr from process"""
        if self.process:
            data = self.process.readAllStandardError()
            text = bytes(data).decode('utf-8')
            self.append_text(text, error=True)
            
    def _process_finished(self):
        """Handle process completion"""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Ready")
        
        if self.process:
            exit_code = self.process.exitCode()
            self.append_text(f"\n=== Process Finished (Exit Code: {exit_code}) ===\n")
            
        # Clean up temp file
        # Note: In a real implementation, we'd track the temp file name
        
    def append_text(self, text, error=False):
        """Append text to output"""
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if error:
            # Red text for errors
            self.output_text.setTextColor(Qt.GlobalColor.red)
        else:
            # White text for normal output
            self.output_text.setTextColor(Qt.GlobalColor.white)
            
        cursor.insertText(text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
        
    def append_log(self, text):
        """Append text to simulation log"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()