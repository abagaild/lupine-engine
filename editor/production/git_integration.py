"""
Git Integration Tool for Lupine Engine
Provides git operations and repository management within the editor
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QGroupBox, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QProgressBar, QCheckBox,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor

from core.project import LupineProject


class GitOperationThread(QThread):
    """Thread for running git operations without blocking UI"""
    
    operation_finished = pyqtSignal(bool, str)  # success, output
    progress_updated = pyqtSignal(str)  # status message
    
    def __init__(self, command: List[str], working_dir: str):
        super().__init__()
        self.command = command
        self.working_dir = working_dir
        
    def run(self):
        """Execute git command"""
        try:
            self.progress_updated.emit(f"Running: {' '.join(self.command)}")
            
            result = subprocess.run(
                self.command,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.operation_finished.emit(True, result.stdout)
            else:
                self.operation_finished.emit(False, result.stderr)
                
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Operation timed out")
        except Exception as e:
            self.operation_finished.emit(False, str(e))


class GitStatusWidget(QWidget):
    """Widget showing git repository status"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.setup_ui()
        self.refresh_status()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def setup_ui(self):
        """Setup the status UI"""
        layout = QVBoxLayout(self)
        
        # Repository info
        repo_group = QGroupBox("Repository Information")
        repo_layout = QVBoxLayout(repo_group)
        
        self.repo_path_label = QLabel("Path: Not a git repository")
        self.branch_label = QLabel("Branch: N/A")
        self.commit_label = QLabel("Last Commit: N/A")
        self.remote_label = QLabel("Remote: N/A")
        
        repo_layout.addWidget(self.repo_path_label)
        repo_layout.addWidget(self.branch_label)
        repo_layout.addWidget(self.commit_label)
        repo_layout.addWidget(self.remote_label)
        
        layout.addWidget(repo_group)
        
        # Status files
        status_group = QGroupBox("Working Directory Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_tree = QTreeWidget()
        self.status_tree.setHeaderLabels(["File", "Status"])
        self.status_tree.setRootIsDecorated(False)
        
        status_layout.addWidget(self.status_tree)
        layout.addWidget(status_group)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_status)
        
        self.stage_all_btn = QPushButton("Stage All")
        self.stage_all_btn.clicked.connect(self.stage_all_changes)
        
        self.unstage_all_btn = QPushButton("Unstage All")
        self.unstage_all_btn.clicked.connect(self.unstage_all_changes)
        
        actions_layout.addWidget(self.refresh_btn)
        actions_layout.addWidget(self.stage_all_btn)
        actions_layout.addWidget(self.unstage_all_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
    def refresh_status(self):
        """Refresh git status information"""
        if not self.is_git_repo():
            self.repo_path_label.setText("Path: Not a git repository")
            self.branch_label.setText("Branch: N/A")
            self.commit_label.setText("Last Commit: N/A")
            self.remote_label.setText("Remote: N/A")
            self.status_tree.clear()
            return
            
        # Update repository info
        self.repo_path_label.setText(f"Path: {self.project.project_path}")
        
        # Get current branch
        branch = self.run_git_command(["git", "branch", "--show-current"])
        self.branch_label.setText(f"Branch: {branch.strip() if branch else 'N/A'}")
        
        # Get last commit
        commit = self.run_git_command(["git", "log", "-1", "--oneline"])
        self.commit_label.setText(f"Last Commit: {commit.strip() if commit else 'N/A'}")
        
        # Get remote
        remote = self.run_git_command(["git", "remote", "get-url", "origin"])
        self.remote_label.setText(f"Remote: {remote.strip() if remote else 'N/A'}")
        
        # Update status tree
        self.update_status_tree()
        
    def update_status_tree(self):
        """Update the status tree with current file statuses"""
        self.status_tree.clear()
        
        # Get git status
        status_output = self.run_git_command(["git", "status", "--porcelain"])
        if not status_output:
            return
            
        for line in status_output.strip().split('\n'):
            if not line:
                continue
                
            status_code = line[:2]
            file_path = line[3:]
            
            # Determine status description
            status_desc = self.get_status_description(status_code)
            
            item = QTreeWidgetItem([file_path, status_desc])
            
            # Color code based on status
            if 'M' in status_code:  # Modified
                item.setForeground(0, QColor(255, 165, 0))  # Orange
            elif 'A' in status_code:  # Added
                item.setForeground(0, QColor(0, 255, 0))  # Green
            elif 'D' in status_code:  # Deleted
                item.setForeground(0, QColor(255, 0, 0))  # Red
            elif '?' in status_code:  # Untracked
                item.setForeground(0, QColor(128, 128, 128))  # Gray
                
            self.status_tree.addTopLevelItem(item)
            
    def get_status_description(self, status_code: str) -> str:
        """Convert git status code to description"""
        descriptions = {
            'M ': 'Modified (staged)',
            ' M': 'Modified (unstaged)',
            'MM': 'Modified (staged and unstaged)',
            'A ': 'Added (staged)',
            ' A': 'Added (unstaged)',
            'D ': 'Deleted (staged)',
            ' D': 'Deleted (unstaged)',
            'R ': 'Renamed (staged)',
            ' R': 'Renamed (unstaged)',
            'C ': 'Copied (staged)',
            ' C': 'Copied (unstaged)',
            '??': 'Untracked',
            '!!': 'Ignored'
        }
        return descriptions.get(status_code, f'Unknown ({status_code})')
        
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        git_dir = Path(self.project.project_path) / '.git'
        return git_dir.exists()
        
    def run_git_command(self, command: List[str]) -> str:
        """Run a git command and return output"""
        try:
            result = subprocess.run(
                command,
                cwd=self.project.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else ""
        except:
            return ""
            
    def stage_all_changes(self):
        """Stage all changes"""
        self.run_git_command(["git", "add", "."])
        self.refresh_status()
        
    def unstage_all_changes(self):
        """Unstage all changes"""
        self.run_git_command(["git", "reset", "HEAD"])
        self.refresh_status()


class GitCommitWidget(QWidget):
    """Widget for creating git commits"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the commit UI"""
        layout = QVBoxLayout(self)
        
        # Commit message
        message_group = QGroupBox("Commit Message")
        message_layout = QVBoxLayout(message_group)
        
        self.commit_message = QTextEdit()
        self.commit_message.setMaximumHeight(100)
        self.commit_message.setPlaceholderText("Enter commit message...")
        
        message_layout.addWidget(self.commit_message)
        layout.addWidget(message_group)
        
        # Commit options
        options_layout = QHBoxLayout()
        
        self.amend_checkbox = QCheckBox("Amend last commit")
        self.sign_checkbox = QCheckBox("Sign commit")
        
        options_layout.addWidget(self.amend_checkbox)
        options_layout.addWidget(self.sign_checkbox)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Commit button
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.clicked.connect(self.commit_changes)
        layout.addWidget(self.commit_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def commit_changes(self):
        """Create a git commit"""
        message = self.commit_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a commit message")
            return
            
        # Build commit command
        command = ["git", "commit", "-m", message]
        
        if self.amend_checkbox.isChecked():
            command.append("--amend")
            
        if self.sign_checkbox.isChecked():
            command.append("-S")
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.commit_btn.setEnabled(False)
        
        # Run commit in thread
        self.commit_thread = GitOperationThread(command, str(self.project.project_path))
        self.commit_thread.operation_finished.connect(self.on_commit_finished)
        self.commit_thread.start()
        
    def on_commit_finished(self, success: bool, output: str):
        """Handle commit completion"""
        self.progress_bar.setVisible(False)
        self.commit_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", "Commit created successfully!")
            self.commit_message.clear()
        else:
            QMessageBox.critical(self, "Error", f"Commit failed:\n{output}")


class GitIntegrationWindow(QMainWindow):
    """Main Git Integration window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Git Integration - Lupine Engine")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Status tab
        self.status_widget = GitStatusWidget(self.project)
        self.tab_widget.addTab(self.status_widget, "Status")
        
        # Commit tab
        self.commit_widget = GitCommitWidget(self.project)
        self.tab_widget.addTab(self.commit_widget, "Commit")
        
        layout.addWidget(self.tab_widget)
