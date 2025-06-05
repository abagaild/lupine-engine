"""
Database Manager for Scriptable Objects
UI for managing scriptable object instances organized by template type
"""

import os
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QTextEdit, QFormLayout, QGroupBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QLabel, QMessageBox, QInputDialog,
    QScrollArea, QSplitter, QTabWidget, QColorDialog, QFileDialog, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap

from core.project import LupineProject
from core.scriptable_objects.manager import ScriptableObjectManager
from core.scriptable_objects.template import ScriptableObjectTemplate
from core.scriptable_objects.instance import ScriptableObjectInstance
from core.scriptable_objects.field import ScriptableObjectField, FieldType


class InstanceEditorWidget(QWidget):
    """Widget for editing a scriptable object instance"""
    
    instance_changed = pyqtSignal(ScriptableObjectInstance)
    
    def __init__(self, instance: ScriptableObjectInstance, template: ScriptableObjectTemplate, parent=None):
        super().__init__(parent)
        self.instance = instance
        self.template = template
        self.field_widgets = {}
        
        self.setup_ui()
        self.load_instance_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instance info
        info_group = QGroupBox("Instance Information")
        info_layout = QFormLayout(info_group)
        
        self.instance_name_edit = QLineEdit()
        self.instance_name_edit.textChanged.connect(self.on_instance_changed)
        info_layout.addRow("Name:", self.instance_name_edit)
        
        self.instance_id_label = QLabel()
        self.instance_id_label.setStyleSheet("color: #888;")
        info_layout.addRow("ID:", self.instance_id_label)
        
        layout.addWidget(info_group)
        
        # Fields scroll area
        self.fields_scroll = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_scroll.setWidget(self.fields_widget)
        self.fields_scroll.setWidgetResizable(True)
        
        layout.addWidget(self.fields_scroll)
        
        # Create field editors based on template
        self.create_field_editors()
    
    def create_field_editors(self):
        """Create field editor widgets based on template"""
        # Group fields by group
        grouped_fields = self.template.get_grouped_fields()
        
        for group_name, fields in grouped_fields.items():
            # Create group
            group_widget = QGroupBox(group_name)
            group_layout = QFormLayout(group_widget)
            
            for field in fields:
                widget = self.create_field_widget(field)
                self.field_widgets[field.name] = widget
                
                label = QLabel(field.name + ":")
                if field.description:
                    label.setToolTip(field.description)
                
                group_layout.addRow(label, widget)
            
            self.fields_layout.addWidget(group_widget)
    
    def create_field_widget(self, field: ScriptableObjectField) -> QWidget:
        """Create appropriate widget for field type"""
        if field.field_type == FieldType.STRING:
            widget = QLineEdit()
            widget.textChanged.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.INT:
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.valueChanged.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.valueChanged.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.BOOL:
            widget = QCheckBox()
            widget.toggled.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.COLOR:
            widget = QPushButton("Choose Color")
            widget.clicked.connect(lambda: self.choose_color(field.name))
            return widget
        elif field.field_type == FieldType.ENUM:
            widget = QComboBox()
            if field.enum_values:
                widget.addItems(field.enum_values)
            widget.currentTextChanged.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.RANGE:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            min_spin = QDoubleSpinBox()
            min_spin.setRange(-999999.0, 999999.0)
            min_spin.valueChanged.connect(self.on_instance_changed)
            max_spin = QDoubleSpinBox()
            max_spin.setRange(-999999.0, 999999.0)
            max_spin.valueChanged.connect(self.on_instance_changed)

            layout.addWidget(QLabel("Min:"))
            layout.addWidget(min_spin)
            layout.addWidget(QLabel("Max:"))
            layout.addWidget(max_spin)

            return container
        elif field.field_type == FieldType.REFERENCE:
            widget = QComboBox()
            widget.setEditable(True)
            widget.currentTextChanged.connect(self.on_instance_changed)
            return widget
        elif field.field_type == FieldType.AUDIO:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            path_edit = QLineEdit()
            path_edit.textChanged.connect(self.on_instance_changed)
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(lambda: self.browse_audio_file(field.name))

            layout.addWidget(path_edit)
            layout.addWidget(browse_btn)

            return container
        elif field.field_type in [FieldType.PATH, FieldType.IMAGE, FieldType.SPRITE_SHEET]:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            # File path input
            path_layout = QHBoxLayout()
            path_edit = QLineEdit()
            path_edit.textChanged.connect(self.on_instance_changed)
            path_edit.textChanged.connect(lambda: self.update_image_preview(field.name))
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(lambda: self.browse_file(field.name))

            path_layout.addWidget(path_edit)
            path_layout.addWidget(browse_btn)
            layout.addLayout(path_layout)

            # Image preview (for IMAGE and SPRITE_SHEET types)
            if field.field_type in [FieldType.IMAGE, FieldType.SPRITE_SHEET]:
                preview_label = QLabel()
                preview_label.setFixedSize(100, 100)
                preview_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_label.setText("No Image")
                preview_label.setScaledContents(True)
                layout.addWidget(preview_label)

            return container
        elif field.field_type == FieldType.VECTOR2:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            x_spin = QDoubleSpinBox()
            x_spin.setRange(-999999.0, 999999.0)
            x_spin.valueChanged.connect(self.on_instance_changed)
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-999999.0, 999999.0)
            y_spin.valueChanged.connect(self.on_instance_changed)
            
            layout.addWidget(QLabel("X:"))
            layout.addWidget(x_spin)
            layout.addWidget(QLabel("Y:"))
            layout.addWidget(y_spin)
            
            return container
        elif field.field_type == FieldType.VECTOR3:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            x_spin = QDoubleSpinBox()
            x_spin.setRange(-999999.0, 999999.0)
            x_spin.valueChanged.connect(self.on_instance_changed)
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-999999.0, 999999.0)
            y_spin.valueChanged.connect(self.on_instance_changed)
            z_spin = QDoubleSpinBox()
            z_spin.setRange(-999999.0, 999999.0)
            z_spin.valueChanged.connect(self.on_instance_changed)
            
            layout.addWidget(QLabel("X:"))
            layout.addWidget(x_spin)
            layout.addWidget(QLabel("Y:"))
            layout.addWidget(y_spin)
            layout.addWidget(QLabel("Z:"))
            layout.addWidget(z_spin)
            
            return container
        else:
            # Default to text edit for complex types
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            widget.textChanged.connect(self.on_instance_changed)
            return widget
    
    def load_instance_data(self):
        """Load instance data into widgets"""
        self.instance_name_edit.setText(self.instance.name)
        self.instance_id_label.setText(self.instance.instance_id)
        
        # Load field values
        for field in self.template.fields:
            widget = self.field_widgets.get(field.name)
            if not widget:
                continue
            
            value = self.instance.get_value(field.name, field.get_default_value())
            self.set_widget_value(widget, field, value)
    
    def set_widget_value(self, widget: QWidget, field: ScriptableObjectField, value):
        """Set widget value based on field type"""
        if not widget:
            return

        try:
            if field.field_type == FieldType.STRING:
                if hasattr(widget, 'setText'):
                    widget.setText(str(value) if value else "")
            elif field.field_type == FieldType.INT:
                if hasattr(widget, 'setValue'):
                    widget.setValue(int(value) if value is not None else 0)
            elif field.field_type == FieldType.FLOAT:
                if hasattr(widget, 'setValue'):
                    widget.setValue(float(value) if value is not None else 0.0)
            elif field.field_type == FieldType.BOOL:
                if hasattr(widget, 'setChecked'):
                    widget.setChecked(bool(value) if value is not None else False)
            elif field.field_type == FieldType.COLOR:
                if value and len(value) >= 4 and hasattr(widget, 'setStyleSheet'):
                    color = QColor.fromRgbF(*value[:4])
                    widget.setStyleSheet(f"background-color: {color.name()}")
            elif field.field_type == FieldType.ENUM:
                if hasattr(widget, 'setCurrentText'):
                    widget.setCurrentText(str(value) if value else "")
            elif field.field_type == FieldType.RANGE:
                if value and len(value) >= 2 and widget.layout():
                    layout = widget.layout()
                    if layout.count() >= 4:
                        min_spin = layout.itemAt(1).widget()
                        max_spin = layout.itemAt(3).widget()
                        if min_spin and hasattr(min_spin, 'setValue'):
                            min_spin.setValue(float(value[0]))
                        if max_spin and hasattr(max_spin, 'setValue'):
                            max_spin.setValue(float(value[1]))
            elif field.field_type == FieldType.REFERENCE:
                if hasattr(widget, 'setCurrentText'):
                    widget.setCurrentText(str(value) if value else "")
            elif field.field_type in [FieldType.PATH, FieldType.IMAGE, FieldType.SPRITE_SHEET, FieldType.AUDIO]:
                layout = widget.layout()
                if layout and layout.count() >= 1:
                    # For image/sprite sheet, the path edit is in the first layout item
                    first_item = layout.itemAt(0)
                    if first_item:
                        if hasattr(first_item, 'layout') and first_item.layout():
                            # It's a nested layout (for image preview)
                            path_layout = first_item.layout()
                            if path_layout.count() >= 1:
                                path_edit = path_layout.itemAt(0).widget()
                                if path_edit and hasattr(path_edit, 'setText'):
                                    path_edit.setText(str(value) if value else "")
                        else:
                            # It's a direct widget
                            path_edit = first_item.widget()
                            if path_edit and hasattr(path_edit, 'setText'):
                                path_edit.setText(str(value) if value else "")

                # Update image preview if it's an image field
                if field.field_type in [FieldType.IMAGE, FieldType.SPRITE_SHEET]:
                    self.update_image_preview(field.name)

            elif field.field_type == FieldType.VECTOR2:
                if value and len(value) >= 2 and widget.layout():
                    layout = widget.layout()
                    if layout.count() >= 4:
                        x_spin = layout.itemAt(1).widget()
                        y_spin = layout.itemAt(3).widget()
                        if x_spin and hasattr(x_spin, 'setValue'):
                            x_spin.setValue(float(value[0]))
                        if y_spin and hasattr(y_spin, 'setValue'):
                            y_spin.setValue(float(value[1]))
            elif field.field_type == FieldType.VECTOR3:
                if value and len(value) >= 3 and widget.layout():
                    layout = widget.layout()
                    if layout.count() >= 6:
                        x_spin = layout.itemAt(1).widget()
                        y_spin = layout.itemAt(3).widget()
                        z_spin = layout.itemAt(5).widget()
                        if x_spin and hasattr(x_spin, 'setValue'):
                            x_spin.setValue(float(value[0]))
                        if y_spin and hasattr(y_spin, 'setValue'):
                            y_spin.setValue(float(value[1]))
                        if z_spin and hasattr(z_spin, 'setValue'):
                            z_spin.setValue(float(value[2]))
            else:
                # Default to text widget
                if hasattr(widget, 'setPlainText'):
                    widget.setPlainText(str(value) if value else "")
                elif hasattr(widget, 'setText'):
                    widget.setText(str(value) if value else "")
        except Exception as e:
            print(f"Error setting widget value for field {field.name}: {e}")
    
    def get_widget_value(self, widget: QWidget, field: ScriptableObjectField):
        """Get value from widget based on field type"""
        if not widget:
            return field.get_default_value()

        try:
            if field.field_type == FieldType.STRING:
                return widget.text() if hasattr(widget, 'text') else ""
            elif field.field_type == FieldType.INT:
                return widget.value() if hasattr(widget, 'value') else 0
            elif field.field_type == FieldType.FLOAT:
                return widget.value() if hasattr(widget, 'value') else 0.0
            elif field.field_type == FieldType.BOOL:
                return widget.isChecked() if hasattr(widget, 'isChecked') else False
            elif field.field_type == FieldType.COLOR:
                # Color is stored in instance data, return current value
                return self.instance.get_value(field.name, field.get_default_value())
            elif field.field_type == FieldType.ENUM:
                return widget.currentText() if hasattr(widget, 'currentText') else ""
            elif field.field_type == FieldType.RANGE:
                layout = widget.layout()
                if layout and layout.count() >= 4:
                    min_spin = layout.itemAt(1).widget()
                    max_spin = layout.itemAt(3).widget()
                    if min_spin and max_spin and hasattr(min_spin, 'value') and hasattr(max_spin, 'value'):
                        return [min_spin.value(), max_spin.value()]
                return [0.0, 1.0]
            elif field.field_type == FieldType.REFERENCE:
                return widget.currentText() if hasattr(widget, 'currentText') else ""
            elif field.field_type in [FieldType.PATH, FieldType.IMAGE, FieldType.SPRITE_SHEET, FieldType.AUDIO]:
                layout = widget.layout()
                if layout and layout.count() >= 1:
                    # For image/sprite sheet, the path edit might be in a nested layout
                    first_item = layout.itemAt(0)
                    if first_item:
                        if hasattr(first_item, 'layout') and first_item.layout():
                            # It's a nested layout (for image preview)
                            path_layout = first_item.layout()
                            if path_layout.count() >= 1:
                                path_edit = path_layout.itemAt(0).widget()
                                if path_edit and hasattr(path_edit, 'text'):
                                    return path_edit.text()
                        else:
                            # It's a direct widget
                            path_edit = first_item.widget()
                            if path_edit and hasattr(path_edit, 'text'):
                                return path_edit.text()
                return ""
            elif field.field_type == FieldType.VECTOR2:
                layout = widget.layout()
                if layout and layout.count() >= 4:
                    x_spin = layout.itemAt(1).widget()
                    y_spin = layout.itemAt(3).widget()
                    if x_spin and y_spin and hasattr(x_spin, 'value') and hasattr(y_spin, 'value'):
                        return [x_spin.value(), y_spin.value()]
                return [0.0, 0.0]
            elif field.field_type == FieldType.VECTOR3:
                layout = widget.layout()
                if layout and layout.count() >= 6:
                    x_spin = layout.itemAt(1).widget()
                    y_spin = layout.itemAt(3).widget()
                    z_spin = layout.itemAt(5).widget()
                    if (x_spin and y_spin and z_spin and
                        hasattr(x_spin, 'value') and hasattr(y_spin, 'value') and hasattr(z_spin, 'value')):
                        return [x_spin.value(), y_spin.value(), z_spin.value()]
                return [0.0, 0.0, 0.0]
            else:
                # Default to text widget
                if hasattr(widget, 'toPlainText'):
                    return widget.toPlainText()
                elif hasattr(widget, 'text'):
                    return widget.text()
                return ""
        except Exception as e:
            print(f"Error getting widget value for field {field.name}: {e}")
            return field.get_default_value()
    
    def choose_color(self, field_name: str):
        """Open color chooser for field"""
        color = QColorDialog.getColor()
        if color.isValid():
            value = [color.redF(), color.greenF(), color.blueF(), color.alphaF()]
            self.instance.set_value(field_name, value)
            
            # Update button color
            widget = self.field_widgets[field_name]
            widget.setStyleSheet(f"background-color: {color.name()}")
            
            self.on_instance_changed()
    
    def browse_file(self, field_name: str):
        """Open file browser for field"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            widget = self.field_widgets.get(field_name)
            if widget:
                try:
                    layout = widget.layout()
                    if layout and layout.count() >= 1:
                        # Get the path edit widget
                        first_item = layout.itemAt(0)
                        path_edit = None

                        if first_item:
                            if hasattr(first_item, 'layout') and first_item.layout():
                                # It's a nested layout
                                path_layout = first_item.layout()
                                if path_layout.count() >= 1:
                                    path_edit = path_layout.itemAt(0).widget()
                            else:
                                # It's a direct widget
                                path_edit = first_item.widget()

                        if path_edit and hasattr(path_edit, 'setText'):
                            path_edit.setText(file_path)
                            self.on_instance_changed()

                            # Update image preview if it's an image field
                            field = next((f for f in self.template.fields if f.name == field_name), None)
                            if field and field.field_type in [FieldType.IMAGE, FieldType.SPRITE_SHEET]:
                                self.update_image_preview(field_name)
                except Exception as e:
                    print(f"Error setting file path for {field_name}: {e}")

    def on_instance_changed(self):
        """Handle instance data changes"""
        # Update instance name
        self.instance.name = self.instance_name_edit.text()

        # Update field values
        for field in self.template.fields:
            widget = self.field_widgets.get(field.name)
            if widget:
                value = self.get_widget_value(widget, field)
                self.instance.set_value(field.name, value)

        # Emit signal
        self.instance_changed.emit(self.instance)

    def update_image_preview(self, field_name: str):
        """Update image preview for image fields"""
        widget = self.field_widgets.get(field_name)
        if not widget:
            return

        try:
            # Get the path from the path edit widget
            layout = widget.layout()
            if layout and layout.count() >= 1:
                # Get the path from the first layout item (which contains the path input)
                first_item = layout.itemAt(0)
                image_path = ""

                if first_item:
                    if hasattr(first_item, 'layout') and first_item.layout():
                        # It's a nested layout containing the path edit and browse button
                        path_layout = first_item.layout()
                        if path_layout.count() >= 1:
                            path_edit = path_layout.itemAt(0).widget()
                            if path_edit and hasattr(path_edit, 'text'):
                                image_path = path_edit.text()
                    else:
                        # It's a direct widget
                        path_edit = first_item.widget()
                        if path_edit and hasattr(path_edit, 'text'):
                            image_path = path_edit.text()

                # Find the preview label (should be the second item in the main layout)
                if layout.count() >= 2:
                    preview_label = layout.itemAt(1).widget()
                    if isinstance(preview_label, QLabel):
                        self.load_image_preview(preview_label, image_path)
        except Exception as e:
            print(f"Error updating image preview for {field_name}: {e}")

    def load_image_preview(self, label: QLabel, image_path: str):
        """Load image preview into label"""
        if not image_path or not os.path.exists(image_path):
            label.setText("No Image")
            label.setPixmap(QPixmap())
            return

        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)
                label.setText("")
            else:
                label.setText("Invalid Image")
                label.setPixmap(QPixmap())
        except Exception as e:
            label.setText("Error Loading")
            label.setPixmap(QPixmap())
            print(f"Error loading image preview: {e}")

    def browse_audio_file(self, field_name: str):
        """Open audio file browser for field"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac);;All Files (*)"
        )
        if file_path:
            widget = self.field_widgets.get(field_name)
            if widget:
                try:
                    layout = widget.layout()
                    if layout and layout.count() >= 1:
                        path_edit = layout.itemAt(0).widget()
                        if path_edit and hasattr(path_edit, 'setText'):
                            path_edit.setText(file_path)
                            self.on_instance_changed()
                except Exception as e:
                    print(f"Error setting audio file path for {field_name}: {e}")


class DatabaseManager(QWidget):
    """Main database manager widget"""

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.manager = ScriptableObjectManager(str(project.project_path))
        self.current_instance: Optional[ScriptableObjectInstance] = None
        self.current_template: Optional[ScriptableObjectTemplate] = None

        self.setup_ui()
        self.load_database()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Left panel - Database tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Database tree header
        tree_header = QHBoxLayout()
        tree_header.addWidget(QLabel("Database:"))

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_database)
        tree_header.addWidget(self.refresh_btn)

        left_layout.addLayout(tree_header)

        # Database tree
        self.database_tree = QTreeWidget()
        self.database_tree.setHeaderLabels(["Name", "Type"])
        self.database_tree.currentItemChanged.connect(self.on_item_selected)
        left_layout.addWidget(self.database_tree)

        # Database actions
        actions_layout = QVBoxLayout()

        self.new_instance_btn = QPushButton("New Instance")
        self.new_instance_btn.clicked.connect(self.create_new_instance)
        self.new_instance_btn.setEnabled(False)
        actions_layout.addWidget(self.new_instance_btn)

        self.duplicate_instance_btn = QPushButton("Duplicate")
        self.duplicate_instance_btn.clicked.connect(self.duplicate_instance)
        self.duplicate_instance_btn.setEnabled(False)
        actions_layout.addWidget(self.duplicate_instance_btn)

        self.delete_instance_btn = QPushButton("Delete")
        self.delete_instance_btn.clicked.connect(self.delete_instance)
        self.delete_instance_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_instance_btn)

        actions_layout.addStretch()

        self.save_instance_btn = QPushButton("Save Instance")
        self.save_instance_btn.clicked.connect(self.save_current_instance)
        self.save_instance_btn.setEnabled(False)
        actions_layout.addWidget(self.save_instance_btn)

        left_layout.addLayout(actions_layout)

        left_panel.setMaximumWidth(300)
        layout.addWidget(left_panel)

        # Right panel - Instance editor
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)

        # No selection message
        self.no_selection_label = QLabel("Select an instance to edit")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #888; font-size: 14px;")
        right_layout.addWidget(self.no_selection_label)

        # Instance editor (will be added dynamically)
        self.instance_editor: Optional[InstanceEditorWidget] = None

        layout.addWidget(self.right_panel)

    def load_database(self):
        """Load all templates and instances into the tree"""
        self.database_tree.clear()

        # Reload from disk
        self.manager.load_all_templates()
        self.manager.load_all_instances()

        # Get all instances organized by template
        all_instances = self.manager.get_all_instances()

        # Add template categories
        for template in self.manager.get_all_templates():
            template_item = QTreeWidgetItem([template.name, "Template"])
            template_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "template", "data": template})

            # Add instances of this template
            instances = all_instances.get(template.name, [])
            for instance in instances:
                instance_item = QTreeWidgetItem([instance.name, "Instance"])
                instance_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "instance", "data": instance})
                template_item.addChild(instance_item)

            self.database_tree.addTopLevelItem(template_item)

        # Expand all items
        self.database_tree.expandAll()

    def on_item_selected(self, current, previous):
        """Handle tree item selection"""
        if not current:
            self.clear_editor()
            return

        item_data = current.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            self.clear_editor()
            return

        if item_data["type"] == "template":
            self.select_template(item_data["data"])
        elif item_data["type"] == "instance":
            self.select_instance(item_data["data"])

    def select_template(self, template: ScriptableObjectTemplate):
        """Select a template (enables new instance creation)"""
        self.current_template = template
        self.current_instance = None
        self.clear_editor()

        # Enable new instance button
        self.new_instance_btn.setEnabled(True)
        self.duplicate_instance_btn.setEnabled(False)
        self.delete_instance_btn.setEnabled(False)
        self.save_instance_btn.setEnabled(False)

        # Show template info
        self.no_selection_label.setText(f"Template: {template.name}\n\nClick 'New Instance' to create an instance of this template.")

    def select_instance(self, instance: ScriptableObjectInstance):
        """Select an instance for editing"""
        self.current_instance = instance
        self.current_template = self.manager.get_template(instance.template_name)

        if not self.current_template:
            QMessageBox.warning(self, "Error", f"Template '{instance.template_name}' not found!")
            return

        # Enable instance actions
        self.new_instance_btn.setEnabled(True)
        self.duplicate_instance_btn.setEnabled(True)
        self.delete_instance_btn.setEnabled(True)
        self.save_instance_btn.setEnabled(True)

        # Load instance editor
        self.load_instance_editor()

    def clear_editor(self):
        """Clear the instance editor"""
        if self.instance_editor:
            self.instance_editor.setParent(None)
            self.instance_editor = None

        self.no_selection_label.setText("Select an instance to edit")
        self.no_selection_label.show()

        # Disable actions
        self.new_instance_btn.setEnabled(False)
        self.duplicate_instance_btn.setEnabled(False)
        self.delete_instance_btn.setEnabled(False)
        self.save_instance_btn.setEnabled(False)

    def load_instance_editor(self):
        """Load the instance editor for the current instance"""
        if not self.current_instance or not self.current_template:
            return

        # Remove existing editor
        if self.instance_editor:
            self.instance_editor.setParent(None)

        # Hide no selection label
        self.no_selection_label.hide()

        # Create new editor
        self.instance_editor = InstanceEditorWidget(self.current_instance, self.current_template)
        self.instance_editor.instance_changed.connect(self.on_instance_changed)

        # Add to layout
        self.right_panel.layout().addWidget(self.instance_editor)

    def on_instance_changed(self, instance: ScriptableObjectInstance):
        """Handle instance changes"""
        # Update tree item name if changed
        current_item = self.database_tree.currentItem()
        if current_item and current_item.text(0) != instance.name:
            current_item.setText(0, instance.name)

    def create_new_instance(self):
        """Create a new instance of the current template"""
        if not self.current_template:
            return

        name, ok = QInputDialog.getText(
            self, "New Instance",
            f"Instance name for {self.current_template.name}:"
        )

        if ok and name:
            instance = self.manager.create_instance(self.current_template.name, name)
            if instance:
                self.manager.save_instance(instance)
                self.load_database()

                # Select the new instance
                self.select_instance_in_tree(instance)

    def duplicate_instance(self):
        """Duplicate the current instance"""
        if not self.current_instance:
            return

        name, ok = QInputDialog.getText(
            self, "Duplicate Instance",
            "New instance name:",
            text=f"{self.current_instance.name}_copy"
        )

        if ok and name:
            new_instance = self.current_instance.clone(name)
            self.manager.save_instance(new_instance)
            self.load_database()

            # Select the new instance
            self.select_instance_in_tree(new_instance)

    def delete_instance(self):
        """Delete the current instance"""
        if not self.current_instance:
            return

        reply = QMessageBox.question(
            self, "Delete Instance",
            f"Are you sure you want to delete instance '{self.current_instance.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_instance(
                self.current_instance.template_name,
                self.current_instance.instance_id
            )
            self.load_database()
            self.clear_editor()

    def save_current_instance(self):
        """Save the current instance"""
        if not self.current_instance:
            return

        try:
            self.manager.save_instance(self.current_instance)
            QMessageBox.information(self, "Success", "Instance saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save instance: {e}")

    def select_instance_in_tree(self, instance: ScriptableObjectInstance):
        """Select an instance in the tree"""
        for i in range(self.database_tree.topLevelItemCount()):
            template_item = self.database_tree.topLevelItem(i)
            for j in range(template_item.childCount()):
                instance_item = template_item.child(j)
                item_data = instance_item.data(0, Qt.ItemDataRole.UserRole)
                if (item_data and item_data["type"] == "instance" and
                    item_data["data"].instance_id == instance.instance_id):
                    self.database_tree.setCurrentItem(instance_item)
                    return
