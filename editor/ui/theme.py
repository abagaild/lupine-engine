"""
Dark theme with desaturated purple accents for Arcade Lupine Game Engine
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


class LupineTheme:
    """Dark theme with purple accents"""

    # Color palette
    BACKGROUND_DARK = "#1e1e1e"      # Very dark gray
    BACKGROUND_MEDIUM = "#2d2d2d"    # Medium dark gray
    BACKGROUND_LIGHT = "#3c3c3c"     # Light dark gray

    SURFACE_DARK = "#252525"         # Dark surface
    SURFACE_MEDIUM = "#353535"       # Medium surface
    SURFACE_LIGHT = "#454545"        # Light surface

    ACCENT_PURPLE = "#8b5fbf"        # Desaturated purple
    ACCENT_PURPLE_LIGHT = "#a67dd4"  # Lighter purple
    ACCENT_PURPLE_DARK = "#6b4a9a"   # Darker purple

    TEXT_PRIMARY = "#e0e0e0"         # Light gray text
    TEXT_SECONDARY = "#b0b0b0"       # Medium gray text
    TEXT_DISABLED = "#707070"        # Dark gray text

    BORDER_COLOR = "#555555"         # Border color
    SELECTION_COLOR = "#4a4a4a"      # Selection background

    SUCCESS_COLOR = "#4caf50"        # Green
    WARNING_COLOR = "#ff9800"        # Orange
    ERROR_COLOR = "#f44336"          # Red
    INFO_COLOR = "#2196f3"           # Blue

    @staticmethod
    def get_stylesheet() -> str:
        """Get the complete stylesheet for the application"""
        return f"""
        /* Main application style */
        QMainWindow {{
            background-color: {LupineTheme.BACKGROUND_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
        }}

        /* Menu bar */
        QMenuBar {{
            background-color: {LupineTheme.BACKGROUND_MEDIUM};
            color: {LupineTheme.TEXT_PRIMARY};
            border-bottom: 1px solid {LupineTheme.BORDER_COLOR};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}

        QMenuBar::item:selected {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QMenu {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
        }}

        QMenu::item {{
            padding: 4px 20px;
        }}

        QMenu::item:selected {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* Tool bar */
        QToolBar {{
            background-color: {LupineTheme.BACKGROUND_MEDIUM};
            border: none;
            spacing: 2px;
        }}

        QToolButton {{
            background-color: transparent;
            border: none;
            padding: 4px;
            margin: 1px;
        }}

        QToolButton:hover {{
            background-color: {LupineTheme.SURFACE_LIGHT};
        }}

        QToolButton:pressed {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* Status bar */
        QStatusBar {{
            background-color: {LupineTheme.BACKGROUND_MEDIUM};
            color: {LupineTheme.TEXT_SECONDARY};
            border-top: 1px solid {LupineTheme.BORDER_COLOR};
        }}

        /* Dock widgets */
        QDockWidget {{
            background-color: {LupineTheme.SURFACE_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }}

        QDockWidget::title {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            padding: 4px;
            border-bottom: 1px solid {LupineTheme.BORDER_COLOR};
        }}

        /* Tab widget */
        QTabWidget::pane {{
            border: 1px solid {LupineTheme.BORDER_COLOR};
            background-color: {LupineTheme.SURFACE_DARK};
        }}

        QTabBar::tab {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            color: {LupineTheme.TEXT_SECONDARY};
            padding: 6px 12px;
            margin-right: 1px;
        }}

        QTabBar::tab:selected {{
            background-color: {LupineTheme.ACCENT_PURPLE};
            color: {LupineTheme.TEXT_PRIMARY};
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {LupineTheme.SURFACE_LIGHT};
        }}

        /* Tree widget */
        QTreeWidget {{
            background-color: {LupineTheme.SURFACE_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            selection-background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QTreeWidget::item {{
            padding: 2px;
        }}

        QTreeWidget::item:hover {{
            background-color: {LupineTheme.SURFACE_LIGHT};
        }}

        QTreeWidget::item:selected {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* List widget */
        QListWidget {{
            background-color: {LupineTheme.SURFACE_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            selection-background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QListWidget::item {{
            padding: 4px;
        }}

        QListWidget::item:hover {{
            background-color: {LupineTheme.SURFACE_LIGHT};
        }}

        QListWidget::item:selected {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* Text edit */
        QTextEdit, QPlainTextEdit {{
            background-color: {LupineTheme.SURFACE_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            selection-background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* Line edit */
        QLineEdit {{
            background-color: {LupineTheme.SURFACE_DARK};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            padding: 4px;
        }}

        QLineEdit:focus {{
            border: 2px solid {LupineTheme.ACCENT_PURPLE};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            color: {LupineTheme.TEXT_PRIMARY};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            padding: 6px 12px;
            min-width: 60px;
        }}

        QPushButton:hover {{
            background-color: {LupineTheme.SURFACE_LIGHT};
        }}

        QPushButton:pressed {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QPushButton:default {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        /* Scroll bars */
        QScrollBar:vertical {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {LupineTheme.SURFACE_LIGHT};
            min-height: 20px;
            margin: 1px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QScrollBar:horizontal {{
            background-color: {LupineTheme.SURFACE_MEDIUM};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {LupineTheme.SURFACE_LIGHT};
            min-width: 20px;
            margin: 1px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {LupineTheme.ACCENT_PURPLE};
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {LupineTheme.BORDER_COLOR};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* Group box */
        QGroupBox {{
            color: {LupineTheme.TEXT_PRIMARY};
            background-color: {LupineTheme.SURFACE_DARK};
            border: 1px solid {LupineTheme.BORDER_COLOR};
            margin-top: 10px;
            padding-top: 10px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: {LupineTheme.SURFACE_DARK};
        }}

        /* Scroll area */
        QScrollArea {{
            background-color: {LupineTheme.SURFACE_DARK};
            border: 1px solid {LupineTheme.BORDER_COLOR};
        }}

        QScrollArea > QWidget > QWidget {{
            background-color: {LupineTheme.SURFACE_DARK};
        }}

        /* Form layout */
        QFormLayout {{
            background-color: {LupineTheme.SURFACE_DARK};
        }}
        """

    @staticmethod
    def apply_theme(app: QApplication):
        """Apply the theme to the application"""
        app.setStyleSheet(LupineTheme.get_stylesheet())

        # Set application palette
        palette = QPalette()

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(LupineTheme.BACKGROUND_DARK))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(LupineTheme.TEXT_PRIMARY))

        # Base colors (for input widgets)
        palette.setColor(QPalette.ColorRole.Base, QColor(LupineTheme.SURFACE_DARK))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(LupineTheme.SURFACE_MEDIUM))

        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(LupineTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(LupineTheme.TEXT_PRIMARY))

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(LupineTheme.SURFACE_MEDIUM))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(LupineTheme.TEXT_PRIMARY))

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(LupineTheme.ACCENT_PURPLE))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(LupineTheme.TEXT_PRIMARY))

        app.setPalette(palette)
