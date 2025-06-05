"""
Global Manager Dialog for Lupine Engine
Provides UI for managing singletons and global variables
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QComboBox,
    QTextEdit, QLabel, QCheckBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QColorDialog,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from pathlib import Path
from typing import Any

from core.project import LupineProject
from core.globals.singleton_manager import SingletonManager, SingletonDefinition
from core.globals.variables_manager import VariablesManager, GlobalVariable, VariableType


class SingletonManagerWidget(QWidget):
    """Widget for managing singletons"""
    
    def __init__(self, project: LupineProject, singleton_manager: SingletonManager):
        super().__init__()
        self.project = project
        self.singleton_manager = singleton_manager
        self.setup_ui()
        self.load_singletons()
    
    def setup_ui(self):
        """Setup the singleton manager UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Singleton")
        self.add_btn.clicked.connect(self.add_singleton)
        toolbar_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_singleton)
        self.remove_btn.setEnabled(False)
        toolbar_layout.addWidget(self.remove_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_singleton)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Singletons list
        self.singletons_tree = QTreeWidget()
        self.singletons_tree.setHeaderLabels(["Name", "Script Path", "Enabled"])
        self.singletons_tree.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.singletons_tree)
        
        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Singleton details form
        details_group = QGroupBox("Singleton Details")
        form_layout = QFormLayout(details_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_details_changed)
        form_layout.addRow("Name:", self.name_edit)
        
        script_layout = QHBoxLayout()
        self.script_edit = QLineEdit()
        self.script_edit.textChanged.connect(self.on_details_changed)
        script_layout.addWidget(self.script_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_script)
        script_layout.addWidget(self.browse_btn)
        form_layout.addRow("Script Path:", script_layout)
        
        self.enabled_check = QCheckBox()
        self.enabled_check.stateChanged.connect(self.on_details_changed)
        form_layout.addRow("Enabled:", self.enabled_check)
        
        details_layout.addWidget(details_group)
        
        # Save/Cancel buttons
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)
        
        buttons_layout.addStretch()
        details_layout.addLayout(buttons_layout)
        
        details_layout.addStretch()
        splitter.addWidget(details_widget)
        
        layout.addWidget(splitter)
        
        # Set splitter proportions
        splitter.setSizes([300, 400])
        
        self.current_singleton = None
        self.editing = False
    
    def load_singletons(self):
        """Load singletons into the tree"""
        self.singletons_tree.clear()
        
        for singleton in self.singleton_manager.get_all_singletons():
            item = QTreeWidgetItem([
                singleton.name,
                singleton.script_path,
                "Yes" if singleton.enabled else "No"
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, singleton)
            self.singletons_tree.addTopLevelItem(item)
    
    def on_selection_changed(self):
        """Handle selection change in singletons tree"""
        items = self.singletons_tree.selectedItems()
        if items:
            singleton = items[0].data(0, Qt.ItemDataRole.UserRole)
            self.load_singleton_details(singleton)
            self.remove_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
        else:
            self.clear_details()
            self.remove_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
    
    def load_singleton_details(self, singleton: SingletonDefinition):
        """Load singleton details into the form"""
        self.current_singleton = singleton
        self.editing = False
        
        self.name_edit.setText(singleton.name)
        self.script_edit.setText(singleton.script_path)
        self.enabled_check.setChecked(singleton.enabled)
        
        # Disable editing initially
        self.name_edit.setEnabled(False)
        self.script_edit.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.enabled_check.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
    
    def clear_details(self):
        """Clear the details form"""
        self.current_singleton = None
        self.editing = False
        
        self.name_edit.clear()
        self.script_edit.clear()
        self.enabled_check.setChecked(False)
        
        self.name_edit.setEnabled(False)
        self.script_edit.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.enabled_check.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
    
    def add_singleton(self):
        """Add a new singleton"""
        self.current_singleton = None
        self.editing = True
        
        self.name_edit.clear()
        self.script_edit.clear()
        self.enabled_check.setChecked(True)
        
        self.name_edit.setEnabled(True)
        self.script_edit.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.enabled_check.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        self.name_edit.setFocus()
    
    def edit_singleton(self):
        """Edit the selected singleton"""
        if not self.current_singleton:
            return
        
        self.editing = True
        
        self.name_edit.setEnabled(True)
        self.script_edit.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.enabled_check.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
    
    def remove_singleton(self):
        """Remove the selected singleton"""
        if not self.current_singleton:
            return
        
        reply = QMessageBox.question(
            self, "Remove Singleton",
            f"Are you sure you want to remove singleton '{self.current_singleton.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.singleton_manager.remove_singleton(self.current_singleton.name):
                self.singleton_manager.save_singletons()
                self.load_singletons()
                self.clear_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove singleton.")
    
    def browse_script(self):
        """Browse for script file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Script File",
            str(self.project.project_path),
            "Python Files (*.py);;All Files (*)"
        )
        
        if file_path:
            # Make path relative to project
            try:
                rel_path = str(Path(file_path).relative_to(self.project.project_path))
                self.script_edit.setText(rel_path)
            except ValueError:
                # If can't make relative, use absolute
                self.script_edit.setText(file_path)
    
    def on_details_changed(self):
        """Handle changes in details form"""
        if self.editing:
            self.save_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
    
    def save_changes(self):
        """Save changes to singleton"""
        name = self.name_edit.text().strip()
        script_path = self.script_edit.text().strip()
        enabled = self.enabled_check.isChecked()
        
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return
        
        if not script_path:
            QMessageBox.warning(self, "Error", "Script path cannot be empty.")
            return
        
        success = False
        
        if self.current_singleton is None:
            # Adding new singleton
            success = self.singleton_manager.add_singleton(name, script_path, enabled)
            if not success:
                QMessageBox.warning(self, "Error", "Failed to add singleton. Name may already exist or script file not found.")
        else:
            # Updating existing singleton
            success = self.singleton_manager.update_singleton(
                self.current_singleton.name, script_path, enabled
            )
            if not success:
                QMessageBox.warning(self, "Error", "Failed to update singleton.")
        
        if success:
            self.singleton_manager.save_singletons()
            self.load_singletons()
            self.editing = False
            
            # Find and select the updated/new item
            for i in range(self.singletons_tree.topLevelItemCount()):
                item = self.singletons_tree.topLevelItem(i)
                if item.text(0) == name:
                    self.singletons_tree.setCurrentItem(item)
                    break
    
    def cancel_changes(self):
        """Cancel changes and revert form"""
        if self.current_singleton:
            self.load_singleton_details(self.current_singleton)
        else:
            self.clear_details()
        
        self.editing = False


class VariablesManagerWidget(QWidget):
    """Widget for managing global variables"""

    def __init__(self, project: LupineProject, variables_manager: VariablesManager):
        super().__init__()
        self.project = project
        self.variables_manager = variables_manager
        self.setup_ui()
        self.load_variables()

    def setup_ui(self):
        """Setup the variables manager UI"""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Variable")
        self.add_btn.clicked.connect(self.add_variable)
        toolbar_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_variable)
        self.remove_btn.setEnabled(False)
        toolbar_layout.addWidget(self.remove_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_variable)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)

        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_all_variables)
        toolbar_layout.addWidget(self.reset_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Variables list
        self.variables_tree = QTreeWidget()
        self.variables_tree.setHeaderLabels(["Name", "Type", "Value"])
        self.variables_tree.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.variables_tree)

        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # Variable details form
        details_group = QGroupBox("Variable Details")
        form_layout = QFormLayout(details_group)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_details_changed)
        form_layout.addRow("Name:", self.name_edit)

        self.type_combo = QComboBox()
        for var_type in VariableType:
            self.type_combo.addItem(var_type.value.title(), var_type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Type:", self.type_combo)

        # Value editor (will be dynamically created based on type)
        self.value_widget = QWidget()
        self.value_layout = QVBoxLayout(self.value_widget)
        form_layout.addRow("Value:", self.value_widget)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self.on_details_changed)
        form_layout.addRow("Description:", self.description_edit)

        details_layout.addWidget(details_group)

        # Save/Cancel buttons
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)

        buttons_layout.addStretch()
        details_layout.addLayout(buttons_layout)

        details_layout.addStretch()
        splitter.addWidget(details_widget)

        layout.addWidget(splitter)

        # Set splitter proportions
        splitter.setSizes([300, 400])

        self.current_variable = None
        self.editing = False
        self.value_editor = None

    def load_variables(self):
        """Load variables into the tree"""
        self.variables_tree.clear()

        for variable in self.variables_manager.get_all_variables():
            value_str = self.format_value_for_display(variable.value, variable.type)
            item = QTreeWidgetItem([
                variable.name,
                variable.type.value.title(),
                value_str
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, variable)
            self.variables_tree.addTopLevelItem(item)

    def format_value_for_display(self, value, var_type):
        """Format value for display in tree"""
        if var_type == VariableType.COLOR:
            if isinstance(value, list) and len(value) >= 3:
                return f"({value[0]:.2f}, {value[1]:.2f}, {value[2]:.2f}, {value[3]:.2f})"
        elif var_type in [VariableType.VECTOR2, VariableType.VECTOR3]:
            if isinstance(value, list):
                return f"({', '.join(f'{v:.2f}' for v in value)})"
        elif var_type == VariableType.STRING:
            return f'"{value}"'

        return str(value)

    def on_selection_changed(self):
        """Handle selection change in variables tree"""
        items = self.variables_tree.selectedItems()
        if items:
            variable = items[0].data(0, Qt.ItemDataRole.UserRole)
            self.load_variable_details(variable)
            self.remove_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
        else:
            self.clear_details()
            self.remove_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)

    def load_variable_details(self, variable: GlobalVariable):
        """Load variable details into the form"""
        self.current_variable = variable
        self.editing = False

        self.name_edit.setText(variable.name)

        # Set type combo
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == variable.type:
                self.type_combo.setCurrentIndex(i)
                break

        self.description_edit.setPlainText(variable.description)

        # Create value editor for this type
        self.create_value_editor(variable.type, variable.value)

        # Disable editing initially
        self.name_edit.setEnabled(False)
        self.type_combo.setEnabled(False)
        self.description_edit.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    def clear_details(self):
        """Clear the details form"""
        self.current_variable = None
        self.editing = False

        self.name_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.description_edit.clear()

        # Clear value editor
        if self.value_editor:
            self.value_layout.removeWidget(self.value_editor)
            self.value_editor.deleteLater()
            self.value_editor = None

        self.name_edit.setEnabled(False)
        self.type_combo.setEnabled(False)
        self.description_edit.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    def create_value_editor(self, var_type: VariableType, value: Any):
        """Create appropriate value editor for the variable type"""
        # Clear existing editor
        if self.value_editor:
            self.value_layout.removeWidget(self.value_editor)
            self.value_editor.deleteLater()

        if var_type == VariableType.INT:
            self.value_editor = QSpinBox()
            self.value_editor.setRange(-2147483648, 2147483647)
            self.value_editor.setValue(int(value))
            self.value_editor.valueChanged.connect(self.on_details_changed)

        elif var_type == VariableType.FLOAT:
            self.value_editor = QDoubleSpinBox()
            self.value_editor.setRange(-999999.999999, 999999.999999)
            self.value_editor.setDecimals(6)
            self.value_editor.setValue(float(value))
            self.value_editor.valueChanged.connect(self.on_details_changed)

        elif var_type == VariableType.STRING:
            self.value_editor = QLineEdit()
            self.value_editor.setText(str(value))
            self.value_editor.textChanged.connect(self.on_details_changed)

        elif var_type == VariableType.BOOL:
            self.value_editor = QCheckBox()
            self.value_editor.setChecked(bool(value))
            self.value_editor.stateChanged.connect(self.on_details_changed)

        elif var_type == VariableType.COLOR:
            self.value_editor = self.create_color_editor(value)

        elif var_type in [VariableType.VECTOR2, VariableType.VECTOR3]:
            self.value_editor = self.create_vector_editor(var_type, value)

        elif var_type in [VariableType.PATH, VariableType.RESOURCE]:
            self.value_editor = self.create_path_editor(value)

        else:
            self.value_editor = QLineEdit()
            self.value_editor.setText(str(value))
            self.value_editor.textChanged.connect(self.on_details_changed)

        self.value_layout.addWidget(self.value_editor)

    def create_color_editor(self, value):
        """Create color editor widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Color display button
        color_btn = QPushButton()
        color_btn.setFixedSize(50, 25)
        if isinstance(value, list) and len(value) >= 3:
            r, g, b = int(value[0] * 255), int(value[1] * 255), int(value[2] * 255)
            color_btn.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")

        def choose_color():
            if isinstance(value, list) and len(value) >= 3:
                r, g, b = int(value[0] * 255), int(value[1] * 255), int(value[2] * 255)
                initial_color = QColor(r, g, b)
            else:
                initial_color = QColor(255, 255, 255)

            color = QColorDialog.getColor(initial_color, self)
            if color.isValid():
                r, g, b = color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0
                a = value[3] if isinstance(value, list) and len(value) > 3 else 1.0

                # Update the stored value
                widget.color_value = [r, g, b, a]
                color_btn.setStyleSheet(f"background-color: rgb({int(r*255)}, {int(g*255)}, {int(b*255)})")
                self.on_details_changed()

        color_btn.clicked.connect(choose_color)
        layout.addWidget(color_btn)

        # Alpha spinbox
        alpha_spin = QDoubleSpinBox()
        alpha_spin.setRange(0.0, 1.0)
        alpha_spin.setDecimals(3)
        alpha_spin.setValue(value[3] if isinstance(value, list) and len(value) > 3 else 1.0)
        alpha_spin.valueChanged.connect(lambda v: setattr(widget, 'alpha_value', v) or self.on_details_changed())
        layout.addWidget(QLabel("Alpha:"))
        layout.addWidget(alpha_spin)

        layout.addStretch()

        # Store initial value
        widget.color_value = value if isinstance(value, list) else [1.0, 1.0, 1.0, 1.0]
        widget.alpha_value = alpha_spin.value()

        return widget

    def create_vector_editor(self, var_type: VariableType, value):
        """Create vector editor widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        components = ['X', 'Y', 'Z'] if var_type == VariableType.VECTOR3 else ['X', 'Y']
        spinboxes = []

        for i, comp in enumerate(components):
            layout.addWidget(QLabel(f"{comp}:"))
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-999999.999999, 999999.999999)
            spinbox.setDecimals(6)
            spinbox.setValue(value[i] if isinstance(value, list) and len(value) > i else 0.0)
            spinbox.valueChanged.connect(self.on_details_changed)
            spinboxes.append(spinbox)
            layout.addWidget(spinbox)

        layout.addStretch()
        widget.spinboxes = spinboxes
        return widget

    def create_path_editor(self, value):
        """Create path editor widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit()
        line_edit.setText(str(value))
        line_edit.textChanged.connect(self.on_details_changed)
        layout.addWidget(line_edit)

        browse_btn = QPushButton("Browse...")
        def browse_path():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select File",
                str(self.project.project_path),
                "All Files (*)"
            )
            if file_path:
                try:
                    rel_path = str(Path(file_path).relative_to(self.project.project_path))
                    line_edit.setText(rel_path)
                except ValueError:
                    line_edit.setText(file_path)

        browse_btn.clicked.connect(browse_path)
        layout.addWidget(browse_btn)

        widget.line_edit = line_edit
        return widget

    def get_value_from_editor(self):
        """Get the current value from the value editor"""
        if not self.value_editor:
            return None

        var_type = self.type_combo.currentData()

        if var_type == VariableType.INT:
            return self.value_editor.value()
        elif var_type == VariableType.FLOAT:
            return self.value_editor.value()
        elif var_type == VariableType.STRING:
            return self.value_editor.text()
        elif var_type == VariableType.BOOL:
            return self.value_editor.isChecked()
        elif var_type == VariableType.COLOR:
            color_value = getattr(self.value_editor, 'color_value', [1.0, 1.0, 1.0, 1.0])
            alpha_value = getattr(self.value_editor, 'alpha_value', 1.0)
            return [color_value[0], color_value[1], color_value[2], alpha_value]
        elif var_type in [VariableType.VECTOR2, VariableType.VECTOR3]:
            spinboxes = getattr(self.value_editor, 'spinboxes', [])
            return [spinbox.value() for spinbox in spinboxes]
        elif var_type in [VariableType.PATH, VariableType.RESOURCE]:
            return self.value_editor.line_edit.text()
        else:
            return self.value_editor.text() if hasattr(self.value_editor, 'text') else None

    def on_type_changed(self):
        """Handle type change in combo box"""
        if self.editing:
            var_type = self.type_combo.currentData()
            # Create default value for new type
            default_values = {
                VariableType.INT: 0,
                VariableType.FLOAT: 0.0,
                VariableType.STRING: "",
                VariableType.BOOL: False,
                VariableType.COLOR: [1.0, 1.0, 1.0, 1.0],
                VariableType.VECTOR2: [0.0, 0.0],
                VariableType.VECTOR3: [0.0, 0.0, 0.0],
                VariableType.PATH: "",
                VariableType.RESOURCE: ""
            }
            self.create_value_editor(var_type, default_values[var_type])
            self.on_details_changed()

    def on_details_changed(self):
        """Handle changes in details form"""
        if self.editing:
            self.save_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)

    def add_variable(self):
        """Add a new variable"""
        self.current_variable = None
        self.editing = True

        self.name_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.description_edit.clear()

        # Create default value editor
        var_type = self.type_combo.currentData()
        default_values = {
            VariableType.INT: 0,
            VariableType.FLOAT: 0.0,
            VariableType.STRING: "",
            VariableType.BOOL: False,
            VariableType.COLOR: [1.0, 1.0, 1.0, 1.0],
            VariableType.VECTOR2: [0.0, 0.0],
            VariableType.VECTOR3: [0.0, 0.0, 0.0],
            VariableType.PATH: "",
            VariableType.RESOURCE: ""
        }
        self.create_value_editor(var_type, default_values[var_type])

        self.name_edit.setEnabled(True)
        self.type_combo.setEnabled(True)
        self.description_edit.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

        self.name_edit.setFocus()

    def edit_variable(self):
        """Edit the selected variable"""
        if not self.current_variable:
            return

        self.editing = True

        self.name_edit.setEnabled(True)
        self.type_combo.setEnabled(True)
        self.description_edit.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

    def remove_variable(self):
        """Remove the selected variable"""
        if not self.current_variable:
            return

        reply = QMessageBox.question(
            self, "Remove Variable",
            f"Are you sure you want to remove variable '{self.current_variable.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.variables_manager.remove_variable(self.current_variable.name):
                self.variables_manager.save_variables()
                self.load_variables()
                self.clear_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove variable.")

    def reset_all_variables(self):
        """Reset all variables to their default values"""
        reply = QMessageBox.question(
            self, "Reset All Variables",
            "Are you sure you want to reset all variables to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.variables_manager.reset_all_to_defaults()
            self.variables_manager.save_variables()
            self.load_variables()
            if self.current_variable:
                # Reload current variable details
                updated_var = self.variables_manager.get_variable(self.current_variable.name)
                if updated_var:
                    self.load_variable_details(updated_var)

    def save_changes(self):
        """Save changes to variable"""
        name = self.name_edit.text().strip()
        var_type = self.type_combo.currentData()
        description = self.description_edit.toPlainText()
        value = self.get_value_from_editor()

        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return

        success = False

        if self.current_variable is None:
            # Adding new variable
            success = self.variables_manager.add_variable(name, var_type, value, description)
            if not success:
                QMessageBox.warning(self, "Error", "Failed to add variable. Name may already exist or value is invalid.")
        else:
            # Updating existing variable
            success = self.variables_manager.update_variable(
                self.current_variable.name, var_type, value, description
            )
            if not success:
                QMessageBox.warning(self, "Error", "Failed to update variable.")

        if success:
            self.variables_manager.save_variables()
            self.load_variables()
            self.editing = False

            # Find and select the updated/new item
            for i in range(self.variables_tree.topLevelItemCount()):
                item = self.variables_tree.topLevelItem(i)
                if item.text(0) == name:
                    self.variables_tree.setCurrentItem(item)
                    break

    def cancel_changes(self):
        """Cancel changes and revert form"""
        if self.current_variable:
            self.load_variable_details(self.current_variable)
        else:
            self.clear_details()

        self.editing = False


class GlobalsManagerDialog(QDialog):
    """Main dialog for managing singletons and global variables"""

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project

        # Initialize managers
        from core.globals.singleton_manager import initialize_singleton_manager
        from core.globals.variables_manager import initialize_variables_manager

        self.singleton_manager = initialize_singleton_manager(str(project.project_path))
        self.variables_manager = initialize_variables_manager(str(project.project_path))

        self.setWindowTitle("Global Manager")
        self.setModal(True)
        self.resize(900, 700)

        # Apply styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
        """)

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Singletons tab
        self.singletons_widget = SingletonManagerWidget(self.project, self.singleton_manager)
        self.tab_widget.addTab(self.singletons_widget, "Singletons")

        # Variables tab
        self.variables_widget = VariablesManagerWidget(self.project, self.variables_manager)
        self.tab_widget.addTab(self.variables_widget, "Global Variables")

        # Dialog buttons
        buttons_layout = QHBoxLayout()

        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_help)
        buttons_layout.addWidget(self.help_btn)

        buttons_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

    def show_help(self):
        """Show help information"""
        help_text = """
<h3>Global Manager Help</h3>

<h4>Singletons</h4>
<p>Singletons are Python scripts that are automatically loaded when the game starts and remain accessible throughout the game's lifetime. They're similar to Godot's autoload system.</p>

<ul>
<li><b>Name:</b> The global name used to access the singleton in scripts</li>
<li><b>Script Path:</b> Path to the Python script file (relative to project root)</li>
<li><b>Enabled:</b> Whether the singleton should be loaded automatically</li>
</ul>

<p><b>Script Requirements:</b></p>
<ul>
<li>The script can contain a class with the same name as the singleton</li>
<li>Or a class named 'Singleton', 'Main', or 'Global'</li>
<li>If no suitable class is found, the module itself becomes the singleton</li>
<li>Optional methods: <code>_singleton_init()</code> for initialization, <code>_singleton_cleanup()</code> for cleanup</li>
</ul>

<h4>Global Variables</h4>
<p>Global variables are typed values that can be accessed from any script in your game.</p>

<p><b>Supported Types:</b></p>
<ul>
<li><b>Int:</b> Integer numbers</li>
<li><b>Float:</b> Decimal numbers</li>
<li><b>String:</b> Text values</li>
<li><b>Bool:</b> True/False values</li>
<li><b>Color:</b> RGBA color values (0.0-1.0)</li>
<li><b>Vector2:</b> 2D coordinates [x, y]</li>
<li><b>Vector3:</b> 3D coordinates [x, y, z]</li>
<li><b>Path:</b> File paths</li>
<li><b>Resource:</b> Resource file paths</li>
</ul>

<h4>Usage in Scripts</h4>
<p><b>Accessing Singletons:</b></p>
<pre>
from core.globals.singleton_manager import get_singleton
my_singleton = get_singleton("MySingleton")
my_singleton.some_method()
</pre>

<p><b>Accessing Global Variables:</b></p>
<pre>
from core.globals.variables_manager import get_global_var, set_global_var
value = get_global_var("my_variable")
set_global_var("my_variable", new_value)
</pre>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Global Manager Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
