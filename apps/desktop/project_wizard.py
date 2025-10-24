"""
Project Wizard Dialog - Interactive project creation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QListWidget, QListWidgetItem,
    QGroupBox, QRadioButton, QCheckBox, QSpinBox, QTabWidget,
    QWidget, QScrollArea, QGridLayout, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QFont, QIcon

try:
    from pistudio.project_builder import ProjectBuilder
except ImportError:
    # Create dummy class for demo
    class ProjectBuilder:
        def list_templates(self):
            return []
        def get_template_info(self, template_id):
            return None


class ProjectCreationThread(QThread):
    """Background thread for project creation"""
    
    progress_updated = pyqtSignal(int, str)
    project_created = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, builder: ProjectBuilder, project_data: dict):
        super().__init__()
        self.builder = builder
        self.project_data = project_data
        
    def run(self):
        """Create project in background"""
        try:
            self.progress_updated.emit(10, "Initializing project...")
            
            if self.project_data["use_template"]:
                self.progress_updated.emit(30, "Loading template...")
                project = self.builder.create_from_template(
                    self.project_data["template_id"],
                    self.project_data["name"]
                )
            else:
                self.progress_updated.emit(30, "Creating custom project...")
                # Custom project creation would go here
                project = None
                
            self.progress_updated.emit(70, "Setting up files...")
            # Additional setup steps
            
            self.progress_updated.emit(100, "Project created successfully!")
            self.project_created.emit(project)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class TemplateCard(QWidget):
    """Template selection card widget"""
    
    selected = pyqtSignal(str)
    
    def __init__(self, template_info: dict):
        super().__init__()
        self.template_id = template_info["id"]
        self.template_info = template_info
        self.is_selected = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Template name
        name_label = QLabel(self.template_info["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(self.template_info["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888;")
        layout.addWidget(desc_label)
        
        # Difficulty badge
        difficulty = self.template_info["difficulty"]
        difficulty_label = QLabel(difficulty.title())
        
        if difficulty == "beginner":
            color = "#4CAF50"
        elif difficulty == "intermediate":
            color = "#FF9800"
        else:
            color = "#F44336"
            
        difficulty_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
        """)
        difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        difficulty_label.setMaximumWidth(80)
        layout.addWidget(difficulty_label)
        
        # Stats
        stats_text = f"Devices: {self.template_info['device_count']} | Connections: {self.template_info['connection_count']}"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 10px; color: #666666;")
        layout.addWidget(stats_label)
        
        # Set card style
        self.setStyleSheet("""
            TemplateCard {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #3a3a3a;
            }
            TemplateCard:hover {
                border-color: #777777;
                background-color: #404040;
            }
        """)
        
        self.setFixedSize(250, 120)
        
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.select()
            
    def select(self):
        """Select this template"""
        self.is_selected = True
        self.setStyleSheet("""
            TemplateCard {
                border: 2px solid #0078d4;
                border-radius: 8px;
                background-color: #404040;
            }
        """)
        self.selected.emit(self.template_id)
        
    def deselect(self):
        """Deselect this template"""
        self.is_selected = False
        self.setStyleSheet("""
            TemplateCard {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #3a3a3a;
            }
        """)


class ProjectWizardDialog(QDialog):
    """Project creation wizard dialog"""
    
    project_created = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PiStudio Project Wizard")
        self.setModal(True)
        self.resize(800, 600)
        
        self.builder = ProjectBuilder()
        self.selected_template = None
        self.template_cards = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup wizard UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Tab widget for different creation methods
        self.tab_widget = QTabWidget()
        
        # Template tab
        template_tab = self.create_template_tab()
        self.tab_widget.addTab(template_tab, "📋 Use Template")
        
        # Custom tab
        custom_tab = self.create_custom_tab()
        self.tab_widget.addTab(custom_tab, "🔧 Custom Project")
        
        # Import tab
        import_tab = self.create_import_tab()
        self.tab_widget.addTab(import_tab, "📁 Import Project")
        
        layout.addWidget(self.tab_widget)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_button)
        
        self.create_button = QPushButton("Create Project")
        self.create_button.clicked.connect(self.create_project)
        self.create_button.setVisible(False)
        button_layout.addWidget(self.create_button)
        
        layout.addLayout(button_layout)
        
    def create_header(self) -> QWidget:
        """Create wizard header"""
        header = QWidget()
        header.setStyleSheet("background-color: #2d2d2d; padding: 20px;")
        layout = QVBoxLayout(header)
        
        title = QLabel("🚀 Create New PiStudio Project")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        subtitle = QLabel("Choose how you'd like to create your Raspberry Pi project")
        subtitle.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(subtitle)
        
        return header
        
    def create_template_tab(self) -> QWidget:
        """Create template selection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Project name input
        name_group = QGroupBox("Project Information")
        name_layout = QVBoxLayout(name_group)
        
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Project Name:"))
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("my-awesome-project")
        name_row.addWidget(self.project_name_edit)
        name_layout.addLayout(name_row)
        
        board_row = QHBoxLayout()
        board_row.addWidget(QLabel("Target Board:"))
        self.board_combo = QComboBox()
        self.board_combo.addItems([
            "Raspberry Pi 4 Model B",
            "Raspberry Pi 3 Model B+", 
            "Raspberry Pi Zero 2 W"
        ])
        board_row.addWidget(self.board_combo)
        board_row.addStretch()
        name_layout.addLayout(board_row)
        
        layout.addWidget(name_group)
        
        # Template selection
        template_group = QGroupBox("Choose Template")
        template_layout = QVBoxLayout(template_group)
        
        # Difficulty filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Difficulty:"))
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["All", "Beginner", "Intermediate", "Advanced"])
        self.difficulty_combo.currentTextChanged.connect(self.filter_templates)
        filter_layout.addWidget(self.difficulty_combo)
        
        filter_layout.addStretch()
        template_layout.addLayout(filter_layout)
        
        # Template cards in scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.template_grid = QGridLayout(scroll_widget)
        
        # Load and display templates
        self.load_templates()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        template_layout.addWidget(scroll_area)
        
        # Template preview
        self.template_preview = QTextEdit()
        self.template_preview.setReadOnly(True)
        self.template_preview.setMaximumHeight(100)
        self.template_preview.setPlaceholderText("Select a template to see preview...")
        template_layout.addWidget(self.template_preview)
        
        layout.addWidget(template_group)
        
        return widget
        
    def create_custom_tab(self) -> QWidget:
        """Create custom project tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Project info
        info_group = QGroupBox("Project Information")
        info_layout = QVBoxLayout(info_group)
        
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Project Name:"))
        self.custom_name_edit = QLineEdit()
        name_row.addWidget(self.custom_name_edit)
        info_layout.addLayout(name_row)
        
        desc_row = QVBoxLayout()
        desc_row.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        desc_row.addWidget(self.description_edit)
        info_layout.addLayout(desc_row)
        
        layout.addWidget(info_group)
        
        # Device selection
        device_group = QGroupBox("Add Devices")
        device_layout = QVBoxLayout(device_group)
        
        # Device categories
        categories = {
            "Basic": ["LED", "RGB LED", "Button", "Switch"],
            "Motors": ["Servo", "Stepper Motor", "DC Motor"],
            "Sensors": ["DHT22", "BME280", "HC-SR04", "MPU6050", "PIR"],
            "Displays": ["LCD 16x2", "OLED 128x64", "7-Segment", "NeoPixel"],
            "Communication": ["Buzzer", "Relay", "ESP-01"]
        }
        
        self.device_checkboxes = {}
        
        for category, devices in categories.items():
            cat_label = QLabel(f"{category}:")
            cat_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            device_layout.addWidget(cat_label)
            
            device_row = QHBoxLayout()
            for device in devices:
                cb = QCheckBox(device)
                self.device_checkboxes[device] = cb
                device_row.addWidget(cb)
            device_row.addStretch()
            device_layout.addLayout(device_row)
            
        layout.addWidget(device_group)
        
        return widget
        
    def create_import_tab(self) -> QWidget:
        """Create import project tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Import options
        import_group = QGroupBox("Import Source")
        import_layout = QVBoxLayout(import_group)
        
        # File import
        self.file_radio = QRadioButton("Import from file")
        self.file_radio.setChecked(True)
        import_layout.addWidget(self.file_radio)
        
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("    File:"))
        self.file_path_edit = QLineEdit()
        file_row.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        file_row.addWidget(browse_button)
        import_layout.addLayout(file_row)
        
        # Git import
        self.git_radio = QRadioButton("Import from Git repository")
        import_layout.addWidget(self.git_radio)
        
        git_row = QHBoxLayout()
        git_row.addWidget(QLabel("    URL:"))
        self.git_url_edit = QLineEdit()
        self.git_url_edit.setPlaceholderText("https://github.com/user/repo.git")
        git_row.addWidget(self.git_url_edit)
        import_layout.addLayout(git_row)
        
        # Example import
        self.example_radio = QRadioButton("Import from examples")
        import_layout.addWidget(self.example_radio)
        
        layout.addWidget(import_group)
        
        # Import preview
        preview_group = QGroupBox("Import Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.import_preview = QTextEdit()
        self.import_preview.setReadOnly(True)
        self.import_preview.setPlaceholderText("Select import source to see preview...")
        preview_layout.addWidget(self.import_preview)
        
        layout.addWidget(preview_group)
        
        return widget
        
    def load_templates(self):
        """Load and display template cards"""
        templates = self.builder.list_templates()
        
        row = 0
        col = 0
        max_cols = 3
        
        for template_info in templates:
            card = TemplateCard(template_info)
            card.selected.connect(self.select_template)
            
            self.template_cards[template_info["id"]] = card
            self.template_grid.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def filter_templates(self, difficulty: str):
        """Filter templates by difficulty"""
        for template_id, card in self.template_cards.items():
            if difficulty == "All":
                card.setVisible(True)
            else:
                card.setVisible(card.template_info["difficulty"] == difficulty.lower())
                
    def select_template(self, template_id: str):
        """Select a template"""
        # Deselect all other cards
        for card in self.template_cards.values():
            if card.template_id != template_id:
                card.deselect()
                
        self.selected_template = template_id
        
        # Show template preview
        template_info = self.builder.get_template_info(template_id)
        if template_info:
            preview_text = f"""
Template: {template_info['name']}
Difficulty: {template_info['difficulty'].title()}

Description:
{template_info['description']}

Code Preview:
{template_info['code_preview']}
"""
            self.template_preview.setText(preview_text)
            
        # Enable next button
        self.next_button.setEnabled(True)
        
    def browse_file(self):
        """Browse for import file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Project File", "", 
            "PiStudio Projects (*.pistudio);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
    def go_back(self):
        """Go to previous step"""
        # Implementation depends on wizard flow
        pass
        
    def go_next(self):
        """Go to next step"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Template tab
            if self.selected_template and self.project_name_edit.text().strip():
                self.show_creation_summary()
            else:
                QMessageBox.warning(self, "Incomplete", 
                                  "Please select a template and enter a project name.")
        elif current_tab == 1:  # Custom tab
            if self.custom_name_edit.text().strip():
                self.show_creation_summary()
            else:
                QMessageBox.warning(self, "Incomplete", 
                                  "Please enter a project name.")
                                  
    def show_creation_summary(self):
        """Show project creation summary"""
        self.next_button.setVisible(False)
        self.create_button.setVisible(True)
        
    def create_project(self):
        """Create the project"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Template
            project_data = {
                "use_template": True,
                "template_id": self.selected_template,
                "name": self.project_name_edit.text().strip(),
                "board": self.board_combo.currentText()
            }
        elif current_tab == 1:  # Custom
            selected_devices = []
            for device, checkbox in self.device_checkboxes.items():
                if checkbox.isChecked():
                    selected_devices.append(device)
                    
            project_data = {
                "use_template": False,
                "name": self.custom_name_edit.text().strip(),
                "description": self.description_edit.toPlainText(),
                "devices": selected_devices
            }
        else:
            return
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.create_button.setEnabled(False)
        
        # Create project in background thread
        self.creation_thread = ProjectCreationThread(self.builder, project_data)
        self.creation_thread.progress_updated.connect(self.update_progress)
        self.creation_thread.project_created.connect(self.on_project_created)
        self.creation_thread.error_occurred.connect(self.on_error)
        self.creation_thread.start()
        
    def update_progress(self, value: int, message: str):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def on_project_created(self, project):
        """Handle successful project creation"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        QMessageBox.information(self, "Success", 
                              f"Project '{project.config['name']}' created successfully!")
        
        self.project_created.emit(project)
        self.accept()
        
    def on_error(self, error_message: str):
        """Handle project creation error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.create_button.setEnabled(True)
        
        QMessageBox.critical(self, "Error", f"Failed to create project:\\n{error_message}")