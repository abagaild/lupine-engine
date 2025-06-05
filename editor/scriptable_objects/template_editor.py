"""
Scriptable Object Template Editor
UI for creating and editing scriptable object templates
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QTextEdit, QFormLayout, QGroupBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QLabel, QMessageBox, QInputDialog,
    QScrollArea, QFrame, QTabWidget, QColorDialog, QFileDialog, QSlider,
    QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QFont, QColor, QDrag, QPainter, QPixmap

from core.project import LupineProject
from core.scriptable_objects.manager import ScriptableObjectManager
from core.scriptable_objects.template import ScriptableObjectTemplate
from core.scriptable_objects.field import ScriptableObjectField, FieldType


class FieldEditorWidget(QWidget):
    """Widget for editing a single field"""
    
    field_changed = pyqtSignal(ScriptableObjectField)
    field_deleted = pyqtSignal(str)  # field name
    
    def __init__(self, field: ScriptableObjectField, parent=None):
        super().__init__(parent)
        self.field = field
        self.setup_ui()
        self.load_field_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Field header
        header_layout = QHBoxLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Field Name")
        self.name_edit.textChanged.connect(self.on_field_changed)
        header_layout.addWidget(QLabel("Name:"))
        header_layout.addWidget(self.name_edit)
        
        self.type_combo = QComboBox()
        for field_type in FieldType:
            self.type_combo.addItem(field_type.value.title(), field_type)
        self.type_combo.currentTextChanged.connect(self.on_field_changed)
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(self.type_combo)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_field)
        header_layout.addWidget(self.delete_btn)
        
        layout.addLayout(header_layout)
        
        # Field details
        details_group = QGroupBox("Field Details")
        details_layout = QFormLayout(details_group)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Field description")
        self.description_edit.textChanged.connect(self.on_field_changed)
        details_layout.addRow("Description:", self.description_edit)
        
        self.group_edit = QLineEdit()
        self.group_edit.setPlaceholderText("Group name (optional)")
        self.group_edit.textChanged.connect(self.on_field_changed)
        details_layout.addRow("Group:", self.group_edit)
        
        # Default value editor (will be populated based on type)
        self.default_value_widget = QWidget()
        self.default_value_layout = QHBoxLayout(self.default_value_widget)
        self.default_value_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addRow("Default Value:", self.default_value_widget)

        # Enhanced field properties
        self.required_check = QCheckBox()
        self.required_check.toggled.connect(self.on_field_changed)
        details_layout.addRow("Required:", self.required_check)

        self.readonly_check = QCheckBox()
        self.readonly_check.toggled.connect(self.on_field_changed)
        details_layout.addRow("Read Only:", self.readonly_check)

        # Min/Max values for numeric types
        self.min_value_spin = QDoubleSpinBox()
        self.min_value_spin.setRange(-999999.0, 999999.0)
        self.min_value_spin.valueChanged.connect(self.on_field_changed)
        details_layout.addRow("Min Value:", self.min_value_spin)

        self.max_value_spin = QDoubleSpinBox()
        self.max_value_spin.setRange(-999999.0, 999999.0)
        self.max_value_spin.valueChanged.connect(self.on_field_changed)
        details_layout.addRow("Max Value:", self.max_value_spin)

        # Enum values (for ENUM type)
        self.enum_values_edit = QTextEdit()
        self.enum_values_edit.setMaximumHeight(60)
        self.enum_values_edit.setPlaceholderText("One value per line")
        self.enum_values_edit.textChanged.connect(self.on_field_changed)
        details_layout.addRow("Enum Values:", self.enum_values_edit)

        # Reference template (for REFERENCE type)
        self.reference_template_combo = QComboBox()
        self.reference_template_combo.currentTextChanged.connect(self.on_field_changed)
        details_layout.addRow("Reference Template:", self.reference_template_combo)

        layout.addWidget(details_group)
        
        # Code snippet
        code_group = QGroupBox("Custom Code")
        code_layout = QVBoxLayout(code_group)
        
        self.code_edit = QTextEdit()
        self.code_edit.setMaximumHeight(100)
        self.code_edit.setPlaceholderText("Custom code for this field (optional)")
        self.code_edit.textChanged.connect(self.on_field_changed)
        code_layout.addWidget(self.code_edit)
        
        layout.addWidget(code_group)
        
        # Update default value widget based on initial type
        self.update_default_value_widget()
    
    def load_field_data(self):
        """Load field data into UI"""
        self.name_edit.setText(self.field.name)
        self.description_edit.setText(self.field.description)
        self.group_edit.setText(self.field.group)
        self.code_edit.setPlainText(self.field.code_snippet)

        # Set type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.field.field_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Load enhanced properties
        self.required_check.setChecked(self.field.required)
        self.readonly_check.setChecked(self.field.readonly)

        if self.field.min_value is not None:
            self.min_value_spin.setValue(self.field.min_value)
        if self.field.max_value is not None:
            self.max_value_spin.setValue(self.field.max_value)

        # Load enum values
        self.enum_values_edit.setPlainText('\n'.join(self.field.enum_values))

        # Load reference template
        self.reference_template_combo.setCurrentText(self.field.reference_template)

        self.update_default_value_widget()
        self.update_field_specific_ui()
    
    def update_default_value_widget(self):
        """Update the default value widget based on field type"""
        # Clear existing widget
        for i in reversed(range(self.default_value_layout.count())):
            self.default_value_layout.itemAt(i).widget().setParent(None)
        
        field_type = self.type_combo.currentData()
        default_value = self.field.get_default_value()
        
        if field_type == FieldType.STRING:
            widget = QLineEdit()
            widget.setText(str(default_value) if default_value else "")
            widget.textChanged.connect(self.on_field_changed)
        elif field_type == FieldType.INT:
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(default_value) if default_value else 0)
            widget.valueChanged.connect(self.on_field_changed)
        elif field_type == FieldType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setValue(float(default_value) if default_value else 0.0)
            widget.valueChanged.connect(self.on_field_changed)
        elif field_type == FieldType.BOOL:
            widget = QCheckBox()
            widget.setChecked(bool(default_value) if default_value else False)
            widget.toggled.connect(self.on_field_changed)
        elif field_type == FieldType.COLOR:
            widget = QPushButton("Choose Color")
            widget.clicked.connect(self.choose_color)
            if default_value:
                color = QColor.fromRgbF(*default_value[:4])
                widget.setStyleSheet(f"background-color: {color.name()}")
        elif field_type in [FieldType.PATH, FieldType.IMAGE, FieldType.SPRITE_SHEET, FieldType.AUDIO]:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            path_edit = QLineEdit()
            path_edit.setText(str(default_value) if default_value else "")
            path_edit.textChanged.connect(self.on_field_changed)
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse_file)
            layout.addWidget(path_edit)
            layout.addWidget(browse_btn)
            widget = container
        elif field_type == FieldType.ENUM:
            widget = QComboBox()
            if self.field.enum_values:
                widget.addItems(self.field.enum_values)
                if default_value in self.field.enum_values:
                    widget.setCurrentText(str(default_value))
            widget.currentTextChanged.connect(self.on_field_changed)
        elif field_type == FieldType.RANGE:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            min_spin = QDoubleSpinBox()
            min_spin.setRange(-999999.0, 999999.0)
            max_spin = QDoubleSpinBox()
            max_spin.setRange(-999999.0, 999999.0)
            if default_value and len(default_value) >= 2:
                min_spin.setValue(float(default_value[0]))
                max_spin.setValue(float(default_value[1]))
            min_spin.valueChanged.connect(self.on_field_changed)
            max_spin.valueChanged.connect(self.on_field_changed)
            layout.addWidget(QLabel("Min:"))
            layout.addWidget(min_spin)
            layout.addWidget(QLabel("Max:"))
            layout.addWidget(max_spin)
            widget = container
        elif field_type == FieldType.REFERENCE:
            widget = QComboBox()
            widget.setEditable(True)
            widget.setCurrentText(str(default_value) if default_value else "")
            widget.currentTextChanged.connect(self.on_field_changed)
        else:
            widget = QLineEdit()
            widget.setText(str(default_value) if default_value else "")
            widget.textChanged.connect(self.on_field_changed)
        
        self.default_value_layout.addWidget(widget)
        self.default_value_widget = widget
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.field.default_value = [color.redF(), color.greenF(), color.blueF(), color.alphaF()]
            self.sender().setStyleSheet(f"background-color: {color.name()}")
            self.on_field_changed()
    
    def browse_file(self):
        """Open file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            # Find the path edit widget
            layout = self.sender().parent().layout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QLineEdit):
                    widget.setText(file_path)
                    break
    
    def update_field_specific_ui(self):
        """Show/hide UI elements based on field type"""
        field_type = self.field.field_type

        # Show/hide enum values
        self.enum_values_edit.setVisible(field_type == FieldType.ENUM)
        self.enum_values_edit.parent().layout().labelForField(self.enum_values_edit).setVisible(field_type == FieldType.ENUM)

        # Show/hide reference template
        self.reference_template_combo.setVisible(field_type == FieldType.REFERENCE)
        self.reference_template_combo.parent().layout().labelForField(self.reference_template_combo).setVisible(field_type == FieldType.REFERENCE)

        # Show/hide min/max for numeric types
        show_minmax = field_type in [FieldType.INT, FieldType.FLOAT, FieldType.RANGE]
        self.min_value_spin.setVisible(show_minmax)
        self.max_value_spin.setVisible(show_minmax)
        self.min_value_spin.parent().layout().labelForField(self.min_value_spin).setVisible(show_minmax)
        self.max_value_spin.parent().layout().labelForField(self.max_value_spin).setVisible(show_minmax)

    def on_field_changed(self):
        """Handle field changes"""
        # Update field object
        self.field.name = self.name_edit.text()
        self.field.description = self.description_edit.text()
        self.field.group = self.group_edit.text()
        self.field.code_snippet = self.code_edit.toPlainText()
        old_type = self.field.field_type
        self.field.field_type = self.type_combo.currentData()

        # Update enhanced properties
        self.field.required = self.required_check.isChecked()
        self.field.readonly = self.readonly_check.isChecked()
        self.field.min_value = self.min_value_spin.value() if self.min_value_spin.isVisible() else None
        self.field.max_value = self.max_value_spin.value() if self.max_value_spin.isVisible() else None

        # Update enum values
        enum_text = self.enum_values_edit.toPlainText().strip()
        self.field.enum_values = [line.strip() for line in enum_text.split('\n') if line.strip()] if enum_text else []

        # Update reference template
        self.field.reference_template = self.reference_template_combo.currentText()

        # Update default value based on type
        self.update_default_value_from_widget()

        # Update UI if type changed
        if old_type != self.field.field_type:
            self.update_default_value_widget()
            self.update_field_specific_ui()

        # Emit signal
        self.field_changed.emit(self.field)
    
    def update_default_value_from_widget(self):
        """Update field default value from widget"""
        field_type = self.field.field_type

        if hasattr(self, 'default_value_widget') and self.default_value_widget:
            if field_type == FieldType.STRING:
                if hasattr(self.default_value_widget, 'text'):
                    self.field.default_value = self.default_value_widget.text()
            elif field_type == FieldType.INT:
                if hasattr(self.default_value_widget, 'value'):
                    self.field.default_value = self.default_value_widget.value()
            elif field_type == FieldType.FLOAT:
                if hasattr(self.default_value_widget, 'value'):
                    self.field.default_value = self.default_value_widget.value()
            elif field_type == FieldType.BOOL:
                if hasattr(self.default_value_widget, 'isChecked'):
                    self.field.default_value = self.default_value_widget.isChecked()
            elif field_type == FieldType.ENUM:
                if hasattr(self.default_value_widget, 'currentText'):
                    self.field.default_value = self.default_value_widget.currentText()
            elif field_type == FieldType.RANGE:
                # Get values from min/max spinboxes
                layout = self.default_value_widget.layout()
                if layout and layout.count() >= 4:
                    min_spin = layout.itemAt(1).widget()
                    max_spin = layout.itemAt(3).widget()
                    if hasattr(min_spin, 'value') and hasattr(max_spin, 'value'):
                        self.field.default_value = [min_spin.value(), max_spin.value()]
            elif field_type in [FieldType.PATH, FieldType.IMAGE, FieldType.SPRITE_SHEET, FieldType.AUDIO]:
                # Get value from path edit
                layout = self.default_value_widget.layout()
                if layout and layout.count() >= 1:
                    path_edit = layout.itemAt(0).widget()
                    if hasattr(path_edit, 'text'):
                        self.field.default_value = path_edit.text()
            elif field_type == FieldType.REFERENCE:
                if hasattr(self.default_value_widget, 'currentText'):
                    self.field.default_value = self.default_value_widget.currentText()
            # Color and other complex types are handled in their respective methods
    
    def delete_field(self):
        """Delete this field"""
        reply = QMessageBox.question(
            self, "Delete Field",
            f"Are you sure you want to delete field '{self.field.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.field_deleted.emit(self.field.name)


class ScriptableObjectTemplateEditor(QWidget):
    """Main template editor widget"""

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.manager = ScriptableObjectManager(str(project.project_path))
        self.current_template: Optional[ScriptableObjectTemplate] = None
        self.field_editors = {}

        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Left panel - Template list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Template list header
        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("Templates:"))

        self.new_template_btn = QPushButton("New Template")
        self.new_template_btn.clicked.connect(self.create_new_template)
        list_header.addWidget(self.new_template_btn)

        left_layout.addLayout(list_header)

        # Template list
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)

        # Template actions
        actions_layout = QHBoxLayout()

        self.delete_template_btn = QPushButton("Delete")
        self.delete_template_btn.clicked.connect(self.delete_template)
        self.delete_template_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_template_btn)

        self.duplicate_template_btn = QPushButton("Duplicate")
        self.duplicate_template_btn.clicked.connect(self.duplicate_template)
        self.duplicate_template_btn.setEnabled(False)
        actions_layout.addWidget(self.duplicate_template_btn)

        left_layout.addLayout(actions_layout)

        left_panel.setMaximumWidth(250)
        layout.addWidget(left_panel)

        # Right panel - Template editor
        self.right_panel = QTabWidget()

        # Template info tab
        self.info_tab = self.create_info_tab()
        self.right_panel.addTab(self.info_tab, "Template Info")

        # Fields tab
        self.fields_tab = self.create_fields_tab()
        self.right_panel.addTab(self.fields_tab, "Fields")

        # Code preview tab
        self.code_tab = self.create_code_tab()
        self.right_panel.addTab(self.code_tab, "Code Preview")

        layout.addWidget(self.right_panel)

        # Initially disable right panel
        self.right_panel.setEnabled(False)

    def create_info_tab(self) -> QWidget:
        """Create the template info tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Template info form
        info_group = QGroupBox("Template Information")
        info_layout = QFormLayout(info_group)

        self.template_name_edit = QLineEdit()
        self.template_name_edit.textChanged.connect(self.on_template_info_changed)
        info_layout.addRow("Name:", self.template_name_edit)

        self.template_description_edit = QTextEdit()
        self.template_description_edit.setMaximumHeight(80)
        self.template_description_edit.textChanged.connect(self.on_template_info_changed)
        info_layout.addRow("Description:", self.template_description_edit)

        self.template_category_edit = QLineEdit()
        self.template_category_edit.textChanged.connect(self.on_template_info_changed)
        info_layout.addRow("Category:", self.template_category_edit)

        self.template_version_edit = QLineEdit()
        self.template_version_edit.textChanged.connect(self.on_template_info_changed)
        info_layout.addRow("Version:", self.template_version_edit)

        layout.addWidget(info_group)

        # Base code
        code_group = QGroupBox("Base Code")
        code_layout = QVBoxLayout(code_group)

        self.base_code_edit = QTextEdit()
        self.base_code_edit.setPlaceholderText("Base Python code for this template (optional)")
        self.base_code_edit.textChanged.connect(self.on_template_info_changed)
        code_layout.addWidget(self.base_code_edit)

        layout.addWidget(code_group)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.save_template_btn = QPushButton("Save Template")
        self.save_template_btn.clicked.connect(self.save_current_template)
        save_layout.addWidget(self.save_template_btn)

        layout.addLayout(save_layout)
        layout.addStretch()

        return tab

    def create_fields_tab(self) -> QWidget:
        """Create the fields editing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Fields header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Fields:"))

        self.add_field_btn = QPushButton("Add Field")
        self.add_field_btn.clicked.connect(self.add_new_field)
        header_layout.addWidget(self.add_field_btn)

        layout.addLayout(header_layout)

        # Fields scroll area
        self.fields_scroll = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_scroll.setWidget(self.fields_widget)
        self.fields_scroll.setWidgetResizable(True)

        layout.addWidget(self.fields_scroll)

        return tab

    def create_code_tab(self) -> QWidget:
        """Create the code preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Code preview
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setFont(QFont("Consolas", 10))
        layout.addWidget(self.code_preview)

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()

        self.refresh_code_btn = QPushButton("Refresh Preview")
        self.refresh_code_btn.clicked.connect(self.update_code_preview)
        refresh_layout.addWidget(self.refresh_code_btn)

        layout.addLayout(refresh_layout)

        return tab

    def load_templates(self):
        """Load all templates into the list"""
        self.template_list.clear()

        for template in self.manager.get_all_templates():
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def on_template_selected(self, current, previous):
        """Handle template selection"""
        if current:
            template = current.data(Qt.ItemDataRole.UserRole)
            self.load_template(template)
            self.right_panel.setEnabled(True)
            self.delete_template_btn.setEnabled(True)
            self.duplicate_template_btn.setEnabled(True)
        else:
            self.current_template = None
            self.right_panel.setEnabled(False)
            self.delete_template_btn.setEnabled(False)
            self.duplicate_template_btn.setEnabled(False)

    def load_template(self, template: ScriptableObjectTemplate):
        """Load a template into the editor"""
        self.current_template = template

        # Load template info
        self.template_name_edit.setText(template.name)
        self.template_description_edit.setPlainText(template.description)
        self.template_category_edit.setText(template.category)
        self.template_version_edit.setText(template.version)
        self.base_code_edit.setPlainText(template.base_code)

        # Load fields
        self.load_fields()

        # Update code preview
        self.update_code_preview()

    def load_fields(self):
        """Load fields into the fields tab"""
        # Clear existing field editors
        for editor in self.field_editors.values():
            editor.setParent(None)
        self.field_editors.clear()

        if not self.current_template:
            return

        # Add field editors
        for field in self.current_template.fields:
            self.add_field_editor(field)

    def add_field_editor(self, field: ScriptableObjectField):
        """Add a field editor widget"""
        editor = FieldEditorWidget(field)
        editor.field_changed.connect(self.on_field_changed)
        editor.field_deleted.connect(self.on_field_deleted)

        self.field_editors[field.name] = editor
        self.fields_layout.addWidget(editor)

    def on_field_changed(self, field: ScriptableObjectField):
        """Handle field changes"""
        # Update field editors dict if name changed
        old_name = None
        for name, editor in self.field_editors.items():
            if editor.field == field and name != field.name:
                old_name = name
                break

        if old_name:
            self.field_editors[field.name] = self.field_editors.pop(old_name)

        # Update code preview
        self.update_code_preview()

    def on_field_deleted(self, field_name: str):
        """Handle field deletion"""
        if field_name in self.field_editors:
            editor = self.field_editors[field_name]
            editor.setParent(None)
            del self.field_editors[field_name]

            # Remove from template
            if self.current_template:
                self.current_template.remove_field(field_name)

            self.update_code_preview()

    def add_new_field(self):
        """Add a new field to the current template"""
        if not self.current_template:
            return

        # Create new field with unique name
        field_count = len(self.current_template.fields)
        field_name = f"field_{field_count + 1}"

        # Ensure unique name
        while self.current_template.get_field(field_name):
            field_count += 1
            field_name = f"field_{field_count}"

        field = ScriptableObjectField(field_name, FieldType.STRING)
        self.current_template.add_field(field)
        self.add_field_editor(field)

        self.update_code_preview()

    def create_new_template(self):
        """Create a new template"""
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if ok and name:
            try:
                template = self.manager.create_template(name)
                self.manager.save_template(template)
                self.load_templates()

                # Select the new template
                for i in range(self.template_list.count()):
                    item = self.template_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole).name == name:
                        self.template_list.setCurrentItem(item)
                        break

            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def delete_template(self):
        """Delete the current template"""
        if not self.current_template:
            return

        reply = QMessageBox.question(
            self, "Delete Template",
            f"Are you sure you want to delete template '{self.current_template.name}'?\n"
            "This will also delete all instances of this template.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_template(self.current_template.name)
            self.load_templates()
            self.current_template = None

    def duplicate_template(self):
        """Duplicate the current template"""
        if not self.current_template:
            return

        name, ok = QInputDialog.getText(
            self, "Duplicate Template",
            "New template name:",
            text=f"{self.current_template.name}_copy"
        )

        if ok and name:
            try:
                # Create new template with copied data
                new_template = ScriptableObjectTemplate.from_dict(self.current_template.to_dict())
                new_template.name = name

                self.manager.save_template(new_template)
                self.load_templates()

                # Select the new template
                for i in range(self.template_list.count()):
                    item = self.template_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole).name == name:
                        self.template_list.setCurrentItem(item)
                        break

            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def save_current_template(self):
        """Save the current template"""
        if not self.current_template:
            return

        try:
            self.manager.save_template(self.current_template)
            QMessageBox.information(self, "Success", "Template saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")

    def on_template_info_changed(self):
        """Handle template info changes"""
        if not self.current_template:
            return

        self.current_template.name = self.template_name_edit.text()
        self.current_template.description = self.template_description_edit.toPlainText()
        self.current_template.category = self.template_category_edit.text()
        self.current_template.version = self.template_version_edit.text()
        self.current_template.base_code = self.base_code_edit.toPlainText()

        # Update list item text
        current_item = self.template_list.currentItem()
        if current_item:
            current_item.setText(self.current_template.name)

        self.update_code_preview()

    def update_code_preview(self):
        """Update the code preview"""
        if not self.current_template:
            self.code_preview.clear()
            return

        try:
            code = self.current_template.generate_python_code()
            self.code_preview.setPlainText(code)
        except Exception as e:
            self.code_preview.setPlainText(f"Error generating code: {e}")
