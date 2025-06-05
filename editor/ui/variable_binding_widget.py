"""
Variable Binding Widget for Lupine Engine Menu and HUD Builder
Provides UI for configuring variable bindings for UI elements
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QTextEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, List, Optional

from core.ui.variable_binding import (
    VariableBinding, BindingType, BINDING_TEMPLATES, 
    create_binding_from_template, get_binding_manager
)
from core.globals.variables_manager import get_variables_manager


class BindingConfigDialog(QDialog):
    """Dialog for configuring a single variable binding"""
    
    def __init__(self, binding: VariableBinding = None, available_variables: List[str] = None):
        super().__init__()
        self.binding = binding
        self.available_variables = available_variables or []
        self.setup_ui()
        
        if binding:
            self.load_binding(binding)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Configure Variable Binding")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout for binding configuration
        form_layout = QFormLayout()
        
        # Binding type
        self.type_combo = QComboBox()
        for binding_type in BindingType:
            self.type_combo.addItem(binding_type.value.title(), binding_type)
        form_layout.addRow("Binding Type:", self.type_combo)
        
        # Variable name
        self.variable_combo = QComboBox()
        self.variable_combo.setEditable(True)
        for var_name in self.available_variables:
            self.variable_combo.addItem(var_name)
        form_layout.addRow("Variable Name:", self.variable_combo)
        
        # Property name
        self.property_edit = QLineEdit()
        form_layout.addRow("Property Name:", self.property_edit)
        
        # Format string
        self.format_edit = QLineEdit()
        self.format_edit.setPlaceholderText("{value}")
        form_layout.addRow("Format String:", self.format_edit)
        
        # Condition (for visibility/enable bindings)
        self.condition_edit = QLineEdit()
        self.condition_edit.setPlaceholderText("{value} > 0")
        form_layout.addRow("Condition:", self.condition_edit)
        
        layout.addLayout(form_layout)
        
        # Transform function
        transform_group = QGroupBox("Transform Function (Optional)")
        transform_layout = QVBoxLayout(transform_group)
        
        self.transform_edit = QTextEdit()
        self.transform_edit.setPlaceholderText(
            "# Custom transformation code\n"
            "# Input: value\n"
            "# Output: result\n"
            "result = value * 2"
        )
        self.transform_edit.setMaximumHeight(80)
        transform_layout.addWidget(self.transform_edit)
        
        layout.addWidget(transform_group)
        
        # Template selection
        template_group = QGroupBox("Quick Templates")
        template_layout = QVBoxLayout(template_group)
        
        template_combo = QComboBox()
        template_combo.addItem("Select Template...")
        for template_name, template_data in BINDING_TEMPLATES.items():
            template_combo.addItem(f"{template_name} - {template_data['description']}", template_name)
        template_combo.currentTextChanged.connect(self.apply_template)
        template_layout.addWidget(template_combo)
        
        layout.addWidget(template_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def apply_template(self, template_text: str):
        """Apply a binding template"""
        if not template_text or template_text == "Select Template...":
            return
        
        template_name = template_text.split(" - ")[0]
        template = BINDING_TEMPLATES.get(template_name)
        if not template:
            return
        
        # Set form values from template
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == template["type"]:
                self.type_combo.setCurrentIndex(i)
                break
        
        self.format_edit.setText(template.get("format", "{value}"))
        self.condition_edit.setText(template.get("condition", ""))
    
    def load_binding(self, binding: VariableBinding):
        """Load binding data into the form"""
        # Set binding type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == binding.binding_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        self.variable_combo.setCurrentText(binding.variable_name)
        self.property_edit.setText(binding.property_name)
        self.format_edit.setText(binding.format_string)
        self.condition_edit.setText(binding.condition or "")
        self.transform_edit.setPlainText(binding.transform_function or "")
    
    def get_binding(self) -> Optional[VariableBinding]:
        """Get the configured binding"""
        if not self.variable_combo.currentText() or not self.property_edit.text():
            return None
        
        return VariableBinding(
            binding_type=self.type_combo.currentData(),
            variable_name=self.variable_combo.currentText(),
            property_name=self.property_edit.text(),
            format_string=self.format_edit.text() or "{value}",
            condition=self.condition_edit.text() or None,
            transform_function=self.transform_edit.toPlainText() or None
        )


class VariableBindingWidget(QWidget):
    """Widget for managing variable bindings for a UI element"""
    
    bindings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_node = None
        self.bindings = []  # List of VariableBinding objects
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Title
        title_label = QLabel("Variable Bindings")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Bindings list
        self.bindings_list = QListWidget()
        self.bindings_list.itemDoubleClicked.connect(self.edit_binding)
        layout.addWidget(self.bindings_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_binding)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_selected_binding)
        button_layout.addWidget(edit_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_binding)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(button_layout)
        
        # Test section
        test_group = QGroupBox("Test Bindings")
        test_layout = QVBoxLayout(test_group)
        
        test_button_layout = QHBoxLayout()
        
        self.test_variable_combo = QComboBox()
        self.test_variable_combo.setEditable(True)
        test_button_layout.addWidget(QLabel("Variable:"))
        test_button_layout.addWidget(self.test_variable_combo)
        
        self.test_value_edit = QLineEdit()
        self.test_value_edit.setPlaceholderText("Test value")
        test_button_layout.addWidget(QLabel("Value:"))
        test_button_layout.addWidget(self.test_value_edit)
        
        test_button = QPushButton("Test")
        test_button.clicked.connect(self.test_bindings)
        test_button_layout.addWidget(test_button)
        
        test_layout.addLayout(test_button_layout)
        
        self.test_result_edit = QTextEdit()
        self.test_result_edit.setMaximumHeight(60)
        self.test_result_edit.setReadOnly(True)
        test_layout.addWidget(self.test_result_edit)
        
        layout.addWidget(test_group)
    
    def set_node(self, node_data: Dict[str, Any]):
        """Set the current node and load its bindings"""
        self.current_node = node_data
        self.load_bindings()
        self.update_test_variables()
    
    def load_bindings(self):
        """Load bindings for the current node"""
        self.bindings.clear()
        self.bindings_list.clear()
        
        if not self.current_node:
            return
        
        # Load bindings from node data
        node_bindings = self.current_node.get("variable_bindings", [])
        for binding_data in node_bindings:
            binding = VariableBinding.from_dict(binding_data)
            self.bindings.append(binding)
            self.add_binding_to_list(binding)
    
    def add_binding_to_list(self, binding: VariableBinding):
        """Add a binding to the list widget"""
        item_text = f"{binding.binding_type.value.title()}: {binding.variable_name} -> {binding.property_name}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, binding)
        self.bindings_list.addItem(item)
    
    def get_available_variables(self) -> List[str]:
        """Get list of available global variables"""
        try:
            variables_manager = get_variables_manager()
            if variables_manager:
                return [var.name for var in variables_manager.get_all_variables()]
        except:
            pass
        return ["player_health", "player_score", "player_level"]  # Default examples
    
    def add_binding(self):
        """Add a new binding"""
        dialog = BindingConfigDialog(available_variables=self.get_available_variables())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            binding = dialog.get_binding()
            if binding:
                self.bindings.append(binding)
                self.add_binding_to_list(binding)
                self.save_bindings()
                self.bindings_changed.emit()
    
    def edit_selected_binding(self):
        """Edit the selected binding"""
        current_item = self.bindings_list.currentItem()
        if current_item:
            self.edit_binding(current_item)
    
    def edit_binding(self, item: QListWidgetItem):
        """Edit a binding"""
        binding = item.data(Qt.ItemDataRole.UserRole)
        if not binding:
            return
        
        dialog = BindingConfigDialog(binding, self.get_available_variables())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_binding = dialog.get_binding()
            if new_binding:
                # Update the binding in the list
                index = self.bindings.index(binding)
                self.bindings[index] = new_binding
                item.setData(Qt.ItemDataRole.UserRole, new_binding)
                
                # Update item text
                item_text = f"{new_binding.binding_type.value.title()}: {new_binding.variable_name} -> {new_binding.property_name}"
                item.setText(item_text)
                
                self.save_bindings()
                self.bindings_changed.emit()
    
    def remove_binding(self):
        """Remove the selected binding"""
        current_item = self.bindings_list.currentItem()
        if not current_item:
            return
        
        binding = current_item.data(Qt.ItemDataRole.UserRole)
        if binding in self.bindings:
            self.bindings.remove(binding)
        
        self.bindings_list.takeItem(self.bindings_list.row(current_item))
        self.save_bindings()
        self.bindings_changed.emit()
    
    def save_bindings(self):
        """Save bindings to the current node"""
        if not self.current_node:
            return
        
        # Convert bindings to dict format
        binding_data = [binding.to_dict() for binding in self.bindings]
        self.current_node["variable_bindings"] = binding_data
    
    def update_test_variables(self):
        """Update the test variable combo box"""
        self.test_variable_combo.clear()
        for var_name in self.get_available_variables():
            self.test_variable_combo.addItem(var_name)
    
    def test_bindings(self):
        """Test the bindings with a sample value"""
        variable_name = self.test_variable_combo.currentText()
        test_value = self.test_value_edit.text()
        
        if not variable_name or not test_value:
            self.test_result_edit.setPlainText("Please enter a variable name and test value.")
            return
        
        try:
            # Try to convert test value to appropriate type
            if test_value.lower() in ['true', 'false']:
                test_value = test_value.lower() == 'true'
            elif '.' in test_value:
                test_value = float(test_value)
            elif test_value.isdigit():
                test_value = int(test_value)
        except:
            pass  # Keep as string
        
        # Test each binding
        results = []
        binding_manager = get_binding_manager()
        binding_manager.update_variable(variable_name, test_value)
        
        for binding in self.bindings:
            if binding.variable_name == variable_name:
                result = binding_manager.evaluate_binding(binding, self.current_node or {})
                results.append(f"{binding.property_name}: {result}")
        
        if results:
            self.test_result_edit.setPlainText("\n".join(results))
        else:
            self.test_result_edit.setPlainText(f"No bindings found for variable '{variable_name}'.")
