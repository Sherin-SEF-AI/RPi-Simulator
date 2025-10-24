"""
Main Window for PiStudio Desktop GUI
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QTextEdit, QPushButton,
    QLabel, QStatusBar, QMenuBar, QToolBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from .breadboard_widget import BreadboardWidget
from .pin_inspector import PinInspectorWidget
from .device_panel import DevicePanelWidget
from .console_widget import ConsoleWidget
from .logic_analyzer_widget import LogicAnalyzerWidget
from .project_wizard import ProjectWizardDialog
from .environment_widget import EnvironmentWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PiStudio - Raspberry Pi Simulator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize UI components
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        
        # Simulation state
        self.simulation_running = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_simulation)
        
    def _setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._show_project_wizard)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("Simulation")
        
        self.run_action = QAction("Run", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self._toggle_simulation)
        sim_menu.addAction(self.run_action)
        
        pause_action = QAction("Pause", self)
        pause_action.setShortcut("F6")
        sim_menu.addAction(pause_action)
        
        stop_action = QAction("Stop", self)
        stop_action.setShortcut("F7")
        sim_menu.addAction(stop_action)
        
        sim_menu.addSeparator()
        
        record_action = QAction("Start Recording", self)
        sim_menu.addAction(record_action)
        
    def _setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Simulation controls
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self._toggle_simulation)
        toolbar.addWidget(self.run_button)
        
        self.pause_button = QPushButton("Pause")
        toolbar.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop")
        toolbar.addWidget(self.stop_button)
        
        toolbar.addSeparator()
        
        # Recording controls
        self.record_button = QPushButton("Record")
        toolbar.addWidget(self.record_button)
        
        self.replay_button = QPushButton("Replay")
        toolbar.addWidget(self.replay_button)
        
    def _setup_central_widget(self):
        """Setup central widget layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Breadboard and devices
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Breadboard widget
        self.breadboard = BreadboardWidget()
        left_layout.addWidget(self.breadboard)
        
        # Device panel
        self.device_panel = DevicePanelWidget()
        left_layout.addWidget(self.device_panel)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel - Inspector and console
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tab widget for different views
        tab_widget = QTabWidget()
        
        # Pin Inspector tab
        self.pin_inspector = PinInspectorWidget()
        tab_widget.addTab(self.pin_inspector, "Pin Inspector")
        
        # Logic Analyzer tab
        self.logic_analyzer = LogicAnalyzerWidget()
        tab_widget.addTab(self.logic_analyzer, "Logic Analyzer")
        
        # Environment tab
        self.environment = EnvironmentWidget()
        tab_widget.addTab(self.environment, "Environment")
        
        right_layout.addWidget(tab_widget)
        
        # Console widget
        self.console = ConsoleWidget()
        right_layout.addWidget(self.console)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([800, 600])
        
        layout = QVBoxLayout(central_widget)
        layout.addWidget(main_splitter)
        
    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Simulation status
        self.sim_status_label = QLabel("Simulation: Stopped")
        self.status_bar.addWidget(self.sim_status_label)
        
        self.status_bar.addPermanentWidget(QLabel("PiStudio v0.1.0"))
        
    def _toggle_simulation(self):
        """Toggle simulation run/stop"""
        if self.simulation_running:
            self._stop_simulation()
        else:
            self._start_simulation()
            
    def _start_simulation(self):
        """Start simulation"""
        self.simulation_running = True
        self.run_button.setText("Stop")
        self.sim_status_label.setText("Simulation: Running")
        self.update_timer.start(50)  # 20 FPS update
        
        self.console.append_text("Simulation started\n")
        
    def _stop_simulation(self):
        """Stop simulation"""
        self.simulation_running = False
        self.run_button.setText("Run")
        self.sim_status_label.setText("Simulation: Stopped")
        self.update_timer.stop()
        
        self.console.append_text("Simulation stopped\n")
        
    def _update_simulation(self):
        """Update simulation (called by timer)"""
        # Update UI components
        self.breadboard.update_display()
        self.pin_inspector.update_display()
        self.device_panel.update_display()
        
    def _show_project_wizard(self):
        """Show project creation wizard"""
        wizard = ProjectWizardDialog(self)
        wizard.project_created.connect(self._on_project_created)
        wizard.exec()
        
    def _on_project_created(self, project):
        """Handle new project creation"""
        # Load the new project
        self.current_project = project
        self.setWindowTitle(f"PiStudio - {project.config['name']}")
        
        # Update UI with project data
        self._load_project_devices()
        
    def _open_project(self):
        """Open existing project"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PiStudio Project", "", 
            "PiStudio Projects (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from pistudio import Project
                from pathlib import Path
                
                project = Project.load(Path(file_path).parent)
                self._on_project_created(project)
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to open project:\\n{str(e)}")
                
    def _save_project(self):
        """Save current project"""
        if hasattr(self, 'current_project'):
            try:
                self.current_project.save()
                self.statusBar().showMessage("Project saved", 2000)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to save project:\\n{str(e)}")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Project", "No project is currently open")
            
    def _load_project_devices(self):
        """Load project devices into UI"""
        if not hasattr(self, 'current_project'):
            return
            
        # Clear existing devices
        self.device_panel.clear_devices()
        
        # Add project devices
        for device in self.current_project.devices:
            self.device_panel.add_device_from_config(device)
            
        # Update breadboard connections
        self.breadboard.load_connections(self.current_project.connections)