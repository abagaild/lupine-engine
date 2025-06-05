"""
Animation Editor for Lupine Engine
Comprehensive animation editing tool with timeline, tracks, and keyframe management
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QFrame, QScrollArea, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QSlider, QTabWidget, QListWidget, QListWidgetItem,
    QToolBar, QMenuBar, QMenu, QStatusBar, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPainter, QPen, QBrush, QColor, QFont

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import math

from core.project import LupineProject
from core.animation import Animation, AnimationLibrary, AnimationTrack
from core.animation.animation_track import PropertyTrack, TransformTrack, ColorTrack, SpriteFrameTrack
from core.animation.animation_player import get_preset_animation, get_preset_animation_names
from core.animation.tween import TweenType, EaseType


class TimelineWidget(QWidget):
    """
    Timeline widget for animation editing
    Shows time ruler and allows scrubbing
    """
    
    time_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
        
        # Timeline properties
        self.duration = 5.0  # seconds
        self.current_time = 0.0
        self.zoom = 100.0  # pixels per second
        self.offset = 0.0
        
        # Interaction
        self.dragging = False
        
        self.setMouseTracking(True)
    
    def set_duration(self, duration: float):
        """Set timeline duration"""
        self.duration = max(0.1, duration)
        self.update()
    
    def set_current_time(self, time: float):
        """Set current time position"""
        self.current_time = max(0.0, min(time, self.duration))
        self.update()
    
    def set_zoom(self, zoom: float):
        """Set timeline zoom level"""
        self.zoom = max(10.0, min(1000.0, zoom))
        self.update()
    
    def time_to_pixel(self, time: float) -> float:
        """Convert time to pixel position"""
        return (time * self.zoom) - self.offset
    
    def pixel_to_time(self, pixel: float) -> float:
        """Convert pixel position to time"""
        return (pixel + self.offset) / self.zoom
    
    def paintEvent(self, event):
        """Paint the timeline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        # Time ruler
        self._draw_time_ruler(painter)
        
        # Current time indicator
        self._draw_current_time(painter)
    
    def _draw_time_ruler(self, painter: QPainter):
        """Draw time ruler with tick marks"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # Calculate tick spacing
        tick_spacing = 1.0  # 1 second intervals
        if self.zoom > 200:
            tick_spacing = 0.1
        elif self.zoom < 50:
            tick_spacing = 5.0
        
        # Draw ticks
        start_time = self.pixel_to_time(0)
        end_time = self.pixel_to_time(self.width())
        
        time = math.floor(start_time / tick_spacing) * tick_spacing
        while time <= end_time:
            x = self.time_to_pixel(time)
            if 0 <= x <= self.width():
                # Major tick every second, minor ticks for subdivisions
                if abs(time % 1.0) < 0.001:  # Major tick
                    painter.drawLine(int(x), 20, int(x), self.height())
                    painter.drawText(int(x) + 2, 15, f"{time:.1f}s")
                else:  # Minor tick
                    painter.drawLine(int(x), 30, int(x), self.height())
            
            time += tick_spacing
    
    def _draw_current_time(self, painter: QPainter):
        """Draw current time indicator"""
        x = self.time_to_pixel(self.current_time)
        if 0 <= x <= self.width():
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.drawLine(int(x), 0, int(x), self.height())
    
    def mousePressEvent(self, event):
        """Handle mouse press for scrubbing"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            time = self.pixel_to_time(event.position().x())
            self.set_current_time(time)
            self.time_changed.emit(self.current_time)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for scrubbing"""
        if self.dragging:
            time = self.pixel_to_time(event.position().x())
            self.set_current_time(time)
            self.time_changed.emit(self.current_time)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False


class TrackWidget(QWidget):
    """
    Widget for displaying and editing a single animation track
    """
    
    keyframe_added = pyqtSignal(object, float)  # track, time
    keyframe_removed = pyqtSignal(object, float)  # track, time
    keyframe_selected = pyqtSignal(object, float)  # track, time
    
    def __init__(self, track: AnimationTrack, timeline: TimelineWidget, parent=None):
        super().__init__(parent)
        self.track = track
        self.timeline = timeline
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        
        # Visual properties
        self.selected_keyframe_time = None
        
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """Paint the track"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        color = QColor(60, 60, 60) if self.track.enabled else QColor(40, 40, 40)
        painter.fillRect(self.rect(), color)
        
        # Track name
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawText(5, 20, f"{self.track.target_path}.{self.track.property_name}")
        
        # Keyframes
        self._draw_keyframes(painter)
    
    def _draw_keyframes(self, painter: QPainter):
        """Draw keyframes on the track"""
        for keyframe in self.track.keyframes:
            x = self.timeline.time_to_pixel(keyframe.time)
            if 0 <= x <= self.width():
                # Keyframe diamond
                size = 6
                if self.selected_keyframe_time == keyframe.time:
                    painter.setBrush(QBrush(QColor(255, 255, 100)))
                    painter.setPen(QPen(QColor(255, 255, 100), 2))
                else:
                    painter.setBrush(QBrush(QColor(100, 150, 255)))
                    painter.setPen(QPen(QColor(100, 150, 255), 1))
                
                # Draw diamond shape
                points = [
                    QPoint(int(x), int(self.height() / 2 - size)),
                    QPoint(int(x + size), int(self.height() / 2)),
                    QPoint(int(x), int(self.height() / 2 + size)),
                    QPoint(int(x - size), int(self.height() / 2))
                ]
                painter.drawPolygon(points)
    
    def mousePressEvent(self, event):
        """Handle mouse press for keyframe selection/creation"""
        if event.button() == Qt.MouseButton.LeftButton:
            time = self.timeline.pixel_to_time(event.position().x())
            
            # Check if clicking on existing keyframe
            for keyframe in self.track.keyframes:
                if abs(self.timeline.time_to_pixel(keyframe.time) - event.position().x()) < 10:
                    self.selected_keyframe_time = keyframe.time
                    self.keyframe_selected.emit(self.track, keyframe.time)
                    self.update()
                    return
            
            # Create new keyframe
            self.keyframe_added.emit(self.track, time)
            self.selected_keyframe_time = time
            self.update()
        
        elif event.button() == Qt.MouseButton.RightButton:
            # Remove keyframe
            time = self.timeline.pixel_to_time(event.position().x())
            for keyframe in self.track.keyframes:
                if abs(self.timeline.time_to_pixel(keyframe.time) - event.position().x()) < 10:
                    self.keyframe_removed.emit(self.track, keyframe.time)
                    if self.selected_keyframe_time == keyframe.time:
                        self.selected_keyframe_time = None
                    self.update()
                    return


class AnimationEditor(QWidget):
    """
    Main animation editor widget
    """
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.current_animation: Optional[Animation] = None
        self.current_animation_player = None
        self.track_widgets: List[TrackWidget] = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_animation_players()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Animation player selection
        toolbar_layout.addWidget(QLabel("Animation Player:"))
        self.player_combo = QComboBox()
        self.player_combo.setMinimumWidth(200)
        toolbar_layout.addWidget(self.player_combo)
        
        toolbar_layout.addWidget(QLabel("Animation:"))
        self.animation_combo = QComboBox()
        self.animation_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(self.animation_combo)
        
        # Animation controls
        self.new_animation_btn = QPushButton("New")
        self.duplicate_animation_btn = QPushButton("Duplicate")
        self.delete_animation_btn = QPushButton("Delete")
        
        toolbar_layout.addWidget(self.new_animation_btn)
        toolbar_layout.addWidget(self.duplicate_animation_btn)
        toolbar_layout.addWidget(self.delete_animation_btn)
        
        toolbar_layout.addStretch()
        
        # Playback controls
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        
        toolbar_layout.addWidget(self.play_btn)
        toolbar_layout.addWidget(self.pause_btn)
        toolbar_layout.addWidget(self.stop_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Track list and properties
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Timeline and tracks
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 800])
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with track list and properties"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Animation properties
        props_group = QGroupBox("Animation Properties")
        props_layout = QFormLayout(props_group)
        
        self.animation_name_edit = QLineEdit()
        self.animation_length_spin = QDoubleSpinBox()
        self.animation_length_spin.setRange(0.1, 3600.0)
        self.animation_length_spin.setSingleStep(0.1)
        self.animation_length_spin.setSuffix(" s")
        
        self.animation_loop_check = QCheckBox()
        self.animation_autoplay_check = QCheckBox()
        
        props_layout.addRow("Name:", self.animation_name_edit)
        props_layout.addRow("Length:", self.animation_length_spin)
        props_layout.addRow("Loop:", self.animation_loop_check)
        props_layout.addRow("Autoplay:", self.animation_autoplay_check)
        
        layout.addWidget(props_group)
        
        # Track management
        tracks_group = QGroupBox("Tracks")
        tracks_layout = QVBoxLayout(tracks_group)
        
        track_buttons_layout = QHBoxLayout()
        self.add_track_btn = QPushButton("Add Track")
        self.remove_track_btn = QPushButton("Remove Track")
        
        track_buttons_layout.addWidget(self.add_track_btn)
        track_buttons_layout.addWidget(self.remove_track_btn)
        tracks_layout.addLayout(track_buttons_layout)
        
        self.tracks_list = QListWidget()
        tracks_layout.addWidget(self.tracks_list)
        
        layout.addWidget(tracks_group)
        
        # Keyframe properties
        keyframe_group = QGroupBox("Keyframe Properties")
        keyframe_layout = QFormLayout(keyframe_group)
        
        self.keyframe_time_spin = QDoubleSpinBox()
        self.keyframe_time_spin.setRange(0.0, 3600.0)
        self.keyframe_time_spin.setSingleStep(0.1)
        self.keyframe_time_spin.setSuffix(" s")
        
        self.keyframe_value_edit = QLineEdit()
        
        self.tween_type_combo = QComboBox()
        for tween_type in TweenType:
            self.tween_type_combo.addItem(tween_type.value.title(), tween_type)
        
        self.ease_type_combo = QComboBox()
        for ease_type in EaseType:
            self.ease_type_combo.addItem(ease_type.value.replace("_", " ").title(), ease_type)
        
        keyframe_layout.addRow("Time:", self.keyframe_time_spin)
        keyframe_layout.addRow("Value:", self.keyframe_value_edit)
        keyframe_layout.addRow("Tween:", self.tween_type_combo)
        keyframe_layout.addRow("Ease:", self.ease_type_combo)
        
        layout.addWidget(keyframe_group)
        
        layout.addStretch()
        
        return widget
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with timeline and track editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Timeline
        self.timeline = TimelineWidget()
        layout.addWidget(self.timeline)
        
        # Track area
        self.track_scroll = QScrollArea()
        self.track_scroll.setWidgetResizable(True)
        self.track_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setContentsMargins(0, 0, 0, 0)
        self.track_layout.setSpacing(1)
        
        self.track_scroll.setWidget(self.track_container)
        layout.addWidget(self.track_scroll)
        
        return widget

    def setup_connections(self):
        """Setup signal connections"""
        # Animation player selection
        self.player_combo.currentTextChanged.connect(self.on_player_changed)
        self.animation_combo.currentTextChanged.connect(self.on_animation_changed)

        # Animation controls
        self.new_animation_btn.clicked.connect(self.new_animation)
        self.duplicate_animation_btn.clicked.connect(self.duplicate_animation)
        self.delete_animation_btn.clicked.connect(self.delete_animation)

        # Playback controls
        self.play_btn.clicked.connect(self.play_animation)
        self.pause_btn.clicked.connect(self.pause_animation)
        self.stop_btn.clicked.connect(self.stop_animation)

        # Timeline
        self.timeline.time_changed.connect(self.on_timeline_changed)

        # Animation properties
        self.animation_name_edit.textChanged.connect(self.on_animation_name_changed)
        self.animation_length_spin.valueChanged.connect(self.on_animation_length_changed)
        self.animation_loop_check.toggled.connect(self.on_animation_loop_changed)
        self.animation_autoplay_check.toggled.connect(self.on_animation_autoplay_changed)

        # Track management
        self.add_track_btn.clicked.connect(self.add_track)
        self.remove_track_btn.clicked.connect(self.remove_track)
        self.tracks_list.currentRowChanged.connect(self.on_track_selected)

    def load_animation_players(self):
        """Load available animation players from the current scene"""
        self.player_combo.clear()

        # TODO: Get animation players from current scene
        # For now, add a placeholder
        self.player_combo.addItem("No Animation Players Found")

    def on_player_changed(self, player_name: str):
        """Handle animation player selection change"""
        # TODO: Load animations from selected player
        self.animation_combo.clear()
        self.current_animation_player = None
        self.current_animation = None
        self.update_ui()

    def on_animation_changed(self, animation_name: str):
        """Handle animation selection change"""
        if not self.current_animation_player or not animation_name:
            self.current_animation = None
            self.update_ui()
            return

        # TODO: Load selected animation
        self.current_animation = None
        self.update_ui()

    def new_animation(self):
        """Create a new animation"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "New Animation", "Animation name:")
        if ok and name:
            animation = Animation(name)
            animation.length = 1.0

            # TODO: Add to current animation player
            self.current_animation = animation
            self.update_ui()

    def duplicate_animation(self):
        """Duplicate the current animation"""
        if not self.current_animation:
            return

        new_animation = self.current_animation.duplicate()
        # TODO: Add to current animation player
        self.current_animation = new_animation
        self.update_ui()

    def delete_animation(self):
        """Delete the current animation"""
        if not self.current_animation:
            return

        reply = QMessageBox.question(
            self, "Delete Animation",
            f"Are you sure you want to delete '{self.current_animation.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Remove from animation player
            self.current_animation = None
            self.update_ui()

    def play_animation(self):
        """Play the current animation"""
        if self.current_animation:
            self.current_animation.play()

    def pause_animation(self):
        """Pause the current animation"""
        if self.current_animation:
            self.current_animation.pause()

    def stop_animation(self):
        """Stop the current animation"""
        if self.current_animation:
            self.current_animation.stop()

    def on_timeline_changed(self, time: float):
        """Handle timeline scrubbing"""
        if self.current_animation:
            self.current_animation.seek(time)

    def on_animation_name_changed(self, name: str):
        """Handle animation name change"""
        if self.current_animation:
            self.current_animation.name = name

    def on_animation_length_changed(self, length: float):
        """Handle animation length change"""
        if self.current_animation:
            self.current_animation.length = length
            self.timeline.set_duration(length)

    def on_animation_loop_changed(self, loop: bool):
        """Handle animation loop change"""
        if self.current_animation:
            self.current_animation.loop = loop

    def on_animation_autoplay_changed(self, autoplay: bool):
        """Handle animation autoplay change"""
        if self.current_animation:
            self.current_animation.autoplay = autoplay

    def add_track(self):
        """Add a new animation track"""
        if not self.current_animation:
            return

        # TODO: Show dialog to select track type and target
        from PyQt6.QtWidgets import QInputDialog

        target_path, ok = QInputDialog.getText(self, "Add Track", "Target path (e.g., 'Player/Sprite'):")
        if not ok or not target_path:
            return

        property_name, ok = QInputDialog.getText(self, "Add Track", "Property name (e.g., 'position'):")
        if not ok or not property_name:
            return

        # Create appropriate track type
        if property_name in ["position", "rotation", "scale"]:
            track = TransformTrack(target_path, property_name)
        elif property_name in ["modulate", "color"]:
            track = ColorTrack(target_path, property_name)
        elif property_name == "frame":
            track = SpriteFrameTrack(target_path)
        else:
            track = PropertyTrack(target_path, property_name)

        self.current_animation.add_track(track)
        self.update_tracks()

    def remove_track(self):
        """Remove the selected track"""
        if not self.current_animation:
            return

        current_row = self.tracks_list.currentRow()
        if current_row >= 0 and current_row < len(self.current_animation.tracks):
            track = self.current_animation.tracks[current_row]
            self.current_animation.remove_track(track)
            self.update_tracks()

    def on_track_selected(self, row: int):
        """Handle track selection"""
        # TODO: Update track properties in UI
        pass

    def update_ui(self):
        """Update the entire UI based on current state"""
        self.update_animation_properties()
        self.update_tracks()
        self.update_timeline()

    def update_animation_properties(self):
        """Update animation properties UI"""
        if self.current_animation:
            self.animation_name_edit.setText(self.current_animation.name)
            self.animation_length_spin.setValue(self.current_animation.length)
            self.animation_loop_check.setChecked(self.current_animation.loop)
            self.animation_autoplay_check.setChecked(self.current_animation.autoplay)
        else:
            self.animation_name_edit.clear()
            self.animation_length_spin.setValue(1.0)
            self.animation_loop_check.setChecked(False)
            self.animation_autoplay_check.setChecked(False)

    def update_tracks(self):
        """Update tracks list and track widgets"""
        # Clear existing track widgets
        for widget in self.track_widgets:
            widget.setParent(None)
        self.track_widgets.clear()

        # Clear tracks list
        self.tracks_list.clear()

        if not self.current_animation:
            return

        # Add tracks to list
        for track in self.current_animation.tracks:
            item = QListWidgetItem(f"{track.target_path}.{track.property_name}")
            self.tracks_list.addItem(item)

            # Create track widget
            track_widget = TrackWidget(track, self.timeline)
            track_widget.keyframe_added.connect(self.on_keyframe_added)
            track_widget.keyframe_removed.connect(self.on_keyframe_removed)
            track_widget.keyframe_selected.connect(self.on_keyframe_selected)

            self.track_layout.addWidget(track_widget)
            self.track_widgets.append(track_widget)

    def update_timeline(self):
        """Update timeline display"""
        if self.current_animation:
            self.timeline.set_duration(self.current_animation.length)
            self.timeline.set_current_time(self.current_animation.current_time)
        else:
            self.timeline.set_duration(1.0)
            self.timeline.set_current_time(0.0)

    def on_keyframe_added(self, track: AnimationTrack, time: float):
        """Handle keyframe addition"""
        # TODO: Get appropriate value for the keyframe
        # For now, use a default value
        default_value = self.get_default_value_for_property(track.property_name)
        track.add_keyframe(time, default_value)

        # Update track widget
        for widget in self.track_widgets:
            if widget.track == track:
                widget.update()
                break

    def on_keyframe_removed(self, track: AnimationTrack, time: float):
        """Handle keyframe removal"""
        track.remove_keyframe(time)

        # Update track widget
        for widget in self.track_widgets:
            if widget.track == track:
                widget.update()
                break

    def on_keyframe_selected(self, track: AnimationTrack, time: float):
        """Handle keyframe selection"""
        keyframe = track.get_keyframe_at_time(time)
        if keyframe:
            # Update keyframe properties UI
            self.keyframe_time_spin.setValue(keyframe.time)
            self.keyframe_value_edit.setText(str(keyframe.value))

            # Set tween and ease type
            for i in range(self.tween_type_combo.count()):
                if self.tween_type_combo.itemData(i) == keyframe.tween_type:
                    self.tween_type_combo.setCurrentIndex(i)
                    break

            for i in range(self.ease_type_combo.count()):
                if self.ease_type_combo.itemData(i) == keyframe.ease_type:
                    self.ease_type_combo.setCurrentIndex(i)
                    break

    def get_default_value_for_property(self, property_name: str):
        """Get default value for a property type"""
        if property_name == "position":
            return [0.0, 0.0]
        elif property_name == "scale":
            return [1.0, 1.0]
        elif property_name == "rotation":
            return 0.0
        elif property_name in ["modulate", "color"]:
            return [1.0, 1.0, 1.0, 1.0]
        elif property_name == "frame":
            return 0
        else:
            return 0.0


class AnimationEditorWindow(QMainWindow):
    """
    Animation Editor main window
    """

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()

    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Animation Editor - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Create the main widget
        self.animation_editor = AnimationEditor(self.project)
        self.setCentralWidget(self.animation_editor)

        # Set window icon if available
        try:
            from PyQt6.QtGui import QIcon
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

    def closeEvent(self, event):
        """Handle window close event"""
        # Save any unsaved changes or ask user
        event.accept()
