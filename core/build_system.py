"""
Build System for Lupine Engine
Handles packaging games into standalone executables
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import zipfile


class BuildError(Exception):
    """Exception raised during build process"""
    pass


class GameBuilder:
    """Handles building games into standalone executables"""
    
    def __init__(self, project_path: str, lupine_engine_path: Optional[str] = None):
        self.project_path = Path(project_path)
        self.project_file = self.project_path / "project.lupine"
        
        # Auto-detect lupine engine path if not provided
        if lupine_engine_path is None:
            # Assume this script is in core/ directory of lupine engine
            self.lupine_engine_path = Path(__file__).parent.parent
        else:
            self.lupine_engine_path = Path(lupine_engine_path)
        
        # Load project configuration
        self.project_config = self._load_project_config()
        
        # Build configuration
        self.build_config = {
            "output_dir": self.project_path / "builds",
            "platform": "windows",  # windows, linux, mac, browser
            "build_type": "release",  # debug, release
            "include_console": False,
            "one_file": True,
            "icon_path": None,
            "additional_files": [],
            "exclude_modules": [],
            # Browser-specific settings
            "browser_width": 1920,
            "browser_height": 1080,
            "browser_fullscreen": False,
            "browser_template": "default"
        }
        
        # Progress callback
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        
    def _load_project_config(self) -> Dict[str, Any]:
        """Load project configuration"""
        if not self.project_file.exists():
            raise BuildError(f"Project file not found: {self.project_file}")
        
        try:
            with open(self.project_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise BuildError(f"Failed to load project config: {e}")
    
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set progress callback function"""
        self.progress_callback = callback
    
    def _report_progress(self, message: str, progress: int):
        """Report build progress"""
        if self.progress_callback:
            self.progress_callback(message, progress)
        else:
            print(f"[{progress}%] {message}")
    
    def configure_build(self, **kwargs):
        """Configure build settings"""
        self.build_config.update(kwargs)
    
    def build(self) -> bool:
        """Build the game into a standalone executable or browser package"""
        try:
            self._report_progress("Starting build process...", 0)

            # Validate project
            self._validate_project()
            self._report_progress("Project validation complete", 10)

            # Prepare build directory
            build_dir = self._prepare_build_directory()
            self._report_progress("Build directory prepared", 20)

            platform = self.build_config.get("platform", "windows")

            if platform == "browser":
                # Browser build using pygbag
                return self._build_browser(build_dir)
            else:
                # Desktop build using PyInstaller
                return self._build_desktop(build_dir)

        except Exception as e:
            self._report_progress(f"Build failed: {e}", -1)
            raise BuildError(f"Build failed: {e}")

    def _build_desktop(self, build_dir: Path) -> bool:
        """Build for desktop platforms using PyInstaller"""
        # Create standalone launcher
        launcher_path = self._create_standalone_launcher(build_dir)
        self._report_progress("Standalone launcher created", 30)

        # Collect assets
        self._collect_assets(build_dir)
        self._report_progress("Assets collected", 50)

        # Create PyInstaller spec
        spec_path = self._create_pyinstaller_spec(build_dir, launcher_path)
        self._report_progress("PyInstaller spec created", 60)

        # Run PyInstaller
        self._run_pyinstaller(spec_path)
        self._report_progress("PyInstaller build complete", 90)

        # Post-build cleanup and finalization
        self._finalize_build(build_dir)
        self._report_progress("Build complete!", 100)

        return True

    def _build_browser(self, build_dir: Path) -> bool:
        """Build for browser using pygbag"""
        # Create browser launcher
        launcher_path = self._create_browser_launcher(build_dir)
        self._report_progress("Browser launcher created", 30)

        # Collect assets for browser
        self._collect_browser_assets(build_dir)
        self._report_progress("Browser assets collected", 50)

        # Run pygbag
        self._run_pygbag(build_dir, launcher_path)
        self._report_progress("Pygbag build complete", 90)

        # Finalize browser build
        self._finalize_browser_build(build_dir)
        self._report_progress("Browser build complete!", 100)

        return True
    
    def _validate_project(self):
        """Validate project before building"""
        # Check if main scene exists
        main_scene = self.project_config.get("main_scene")
        if not main_scene:
            raise BuildError("No main scene specified in project settings")
        
        main_scene_path = self.project_path / main_scene
        if not main_scene_path.exists():
            raise BuildError(f"Main scene not found: {main_scene_path}")
        
        # Check if required directories exist
        required_dirs = ["scenes", "scripts"]
        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                # Create missing directories
                dir_path.mkdir(exist_ok=True)
    
    def _prepare_build_directory(self) -> Path:
        """Prepare the build directory"""
        build_dir = self.build_config["output_dir"]
        platform = self.build_config["platform"]
        build_type = self.build_config["build_type"]
        
        # Create platform-specific build directory
        target_dir = build_dir / f"{platform}_{build_type}"
        
        # Clean existing build
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir)
            except OSError as e:
                # If we can't remove it, try to work around it
                print(f"Warning: Could not remove existing build directory: {e}")
                # Try to create a new directory with timestamp
                import time
                timestamp = int(time.time())
                target_dir = target_dir.parent / f"{target_dir.name}_{timestamp}"

        target_dir.mkdir(parents=True, exist_ok=True)
        
        return target_dir
    
    def _create_standalone_launcher(self, build_dir: Path) -> Path:
        """Create the standalone game launcher script"""
        # Get the actual scene path from project config
        main_scene = self.project_config.get('main_scene', 'scenes/Main.scene')
        game_name = self.project_config.get('name', 'Lupine Game')
        game_version = self.project_config.get('version', '1.0.0')

        launcher_content = f'''#!/usr/bin/env python3
"""
Standalone Game Launcher for {game_name}
Generated by Lupine Engine Build System
"""

import sys
import os
from pathlib import Path

# Add the bundled engine to Python path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    engine_path = bundle_dir / "lupine_engine"
    project_path = bundle_dir / "game_data"
else:
    # Running as script (development)
    bundle_dir = Path(__file__).parent
    engine_path = bundle_dir / "lupine_engine"
    project_path = bundle_dir / "game_data"

sys.path.insert(0, str(engine_path))

# Set up global exception handling
from core.exception_handler import setup_global_exception_handling
setup_global_exception_handling()

def main():
    """Main entry point for the standalone game"""
    try:
        # Import the game runner
        from core.simple_game_runner import run_game
        
        # Game configuration
        project_path_str = str(project_path)
        scene_path = "{main_scene}"
        engine_path_str = str(engine_path)

        print(f"[GAME] Starting {game_name}")
        print(f"[GAME] Version: {game_version}")
        print("-" * 50)
        
        # Run the game
        exit_code = run_game(project_path_str, scene_path, engine_path_str)
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"[ERROR] Failed to start game: {{e}}")
        import traceback
        traceback.print_exc()

        # Try to pause for user to see error (works in console builds)
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError):
            # input() doesn't work in bundled executables without console
            import time
            print("[ERROR] Game will exit in 5 seconds...")
            time.sleep(5)

        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        launcher_path = build_dir / "game_launcher.py"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        return launcher_path
    
    def _collect_assets(self, build_dir: Path):
        """Collect all game assets"""
        game_data_dir = build_dir / "game_data"
        game_data_dir.mkdir(exist_ok=True)
        
        # Copy project files
        project_dirs = ["scenes", "scripts", "assets", "nodes", "prefabs"]
        
        for dir_name in project_dirs:
            src_dir = self.project_path / dir_name
            if src_dir.exists():
                dst_dir = game_data_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        
        # Copy project configuration
        dst_project_file = game_data_dir / "project.lupine"
        shutil.copy2(self.project_file, dst_project_file)
        
        # Copy engine files
        engine_data_dir = build_dir / "lupine_engine"
        engine_data_dir.mkdir(exist_ok=True)
        
        # Copy core engine modules
        engine_dirs = ["core", "nodes"]
        for dir_name in engine_dirs:
            src_dir = self.lupine_engine_path / dir_name
            if src_dir.exists():
                dst_dir = engine_data_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        
        # Copy requirements and other necessary files
        req_files = ["requirements.txt"]
        for file_name in req_files:
            src_file = self.lupine_engine_path / file_name
            if src_file.exists():
                dst_file = engine_data_dir / file_name
                shutil.copy2(src_file, dst_file)

    def _create_pyinstaller_spec(self, build_dir: Path, launcher_path: Path) -> Path:
        """Create PyInstaller spec file"""
        project_name = self.project_config.get("name", "LupineGame").replace(" ", "")

        # Determine icon path
        icon_path = None
        if self.build_config.get("icon_path"):
            icon_path = self.build_config["icon_path"]
        elif "export" in self.project_config and "icon" in self.project_config["export"]:
            icon_file = self.project_config["export"]["icon"]
            potential_icon = self.project_path / icon_file
            if potential_icon.exists():
                icon_path = str(potential_icon)

        # Create spec content
        one_file = self.build_config.get("one_file", True)
        include_console = self.build_config.get("include_console", False)
        is_debug = self.build_config.get("build_type") == "debug"
        exclude_modules = self.build_config.get("exclude_modules", [])

        # Build the EXE arguments based on one_file setting
        if one_file:
            exe_args = """    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],"""
        else:
            exe_args = """    pyz,
    a.scripts,
    [],"""

        # Build icon parameter
        icon_param = f"    icon={repr(icon_path)}," if icon_path else ""

        # Use relative paths for the spec file
        launcher_relative = launcher_path.name

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Exclude modules
exclude_modules = {exclude_modules}

a = Analysis(
    [r'{launcher_relative}'],
    pathex=[r'{build_dir}'],
    binaries=[],
    datas=[
        (r'game_data', 'game_data'),
        (r'lupine_engine', 'lupine_engine'),
    ],
    hiddenimports=[
        # Core Python modules
        'json',
        'pathlib',
        'sys',
        'os',
        'traceback',
        'threading',
        'time',
        'math',
        'random',
        'collections',
        'functools',
        'itertools',
        'typing',
        'dataclasses',
        'enum',
        'copy',
        'weakref',
        'inspect',
        'importlib',
        'importlib.util',
        'pkgutil',
        'glob',
        'shutil',
        'subprocess',
        'tempfile',
        'zipfile',
        'io',
        'struct',
        'hashlib',
        'base64',
        'uuid',
        'datetime',
        'decimal',
        'fractions',
        're',
        'string',
        'textwrap',
        'unicodedata',
        'codecs',
        'locale',
        'gettext',
        'argparse',
        'configparser',
        'logging',
        'warnings',
        'contextlib',
        'abc',
        'atexit',
        'signal',
        'socket',
        'ssl',
        'urllib',
        'urllib.parse',
        'urllib.request',
        'http',
        'http.client',
        'ftplib',
        'email',
        'mimetypes',
        'base64',
        'binascii',
        'binhex',
        'uu',
        'quopri',

        # Game engine dependencies
        'pygame',
        'pygame.mixer',
        'pygame.font',
        'pygame.image',
        'pygame.transform',
        'pygame.draw',
        'pygame.surface',
        'pygame.rect',
        'pygame.color',
        'pygame.math',
        'pygame.time',
        'pygame.event',
        'pygame.key',
        'pygame.mouse',
        'pygame.joystick',
        'pygame.display',
        'pygame.locals',
        'pygame.constants',
        'pygame.version',
        'pygame.gfxdraw',
        'pygame.sprite',
        'pygame.mask',
        'pygame.pixelarray',
        'pygame.sndarray',
        'pygame.surfarray',
        'pygame.freetype',
        'pygame.scrap',
        'pygame.cursors',
        'pygame.bufferproxy',
        'pygame.camera',
        'pygame.midi',
        'pygame.tests',

        # OpenGL and graphics
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.GLUT',
        'OpenGL.arrays',
        'OpenGL.arrays.vbo',
        'OpenGL.GL.shaders',
        'OpenGL.GL.framebufferobjects',
        'OpenGL.extensions',
        'OpenGL.platform',
        'OpenGL.error',
        'OpenGL.contextdata',
        'OpenGL.plugins',

        # PyQt6 (for editor compatibility)
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',

        # Scientific computing
        'numpy',
        'numpy.core',
        'numpy.lib',
        'numpy.random',
        'numpy.linalg',
        'numpy.fft',
        'numpy.polynomial',
        'numpy.testing',
        'numpy.distutils',

        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageFilter',
        'PIL.ImageEnhance',
        'PIL.ImageOps',
        'PIL.ImageChops',
        'PIL.ImageColor',
        'PIL.ImageFile',
        'PIL.ImageGrab',
        'PIL.ImagePath',
        'PIL.ImageSequence',
        'PIL.ImageStat',
        'PIL.ImageTk',
        'PIL.ImageWin',
        'PIL.ExifTags',
        'PIL.TiffTags',
        'PIL.JpegImagePlugin',
        'PIL.PngImagePlugin',
        'PIL.BmpImagePlugin',
        'PIL.GifImagePlugin',
        'PIL.TiffImagePlugin',
        'PIL.WebPImagePlugin',

        # Physics
        'pymunk',
        'pymunk.body',
        'pymunk.shape',
        'pymunk.space',
        'pymunk.constraint',
        'pymunk.collision_handler',
        'pymunk.arbiter',
        'pymunk.contact_point_set',
        'pymunk.query_info',
        'pymunk.point_query_info',
        'pymunk.segment_query_info',
        'pymunk.shape_filter',
        'pymunk.transform',
        'pymunk.bb',
        'pymunk.vec2d',
        'pymunk.moment',
        'pymunk.util',
        'pymunk.pygame_util',

        # Audio modules
        'wave',
        'audioop',
        'sndhdr',
        'sunau',
        'aifc',

        # Audio (if using OpenAL)
        'openal',
        'openal.al',
        'openal.alc',
        'openal.audio',
        'openal.loaders',

        # Lupine Engine modules
        'core',
        'core.game_engine',
        'core.simple_game_runner',
        'core.project',
        'core.scene',
        'core.scene.scene_manager',
        'core.scene.scene',
        'core.scene.node',
        'core.rendering',
        'core.rendering.shared_renderer',
        'core.audio',
        'core.audio.openal_audio_system',
        'core.input',
        'core.input.input_manager',
        'core.physics',
        'core.physics.physics_world',
        'core.scripting',
        'core.scripting.python_runtime',
        'core.exception_handler',
        'core.json_utils',
        'core.path_utils',
        'nodes',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=exclude_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
{exe_args}
    name='{project_name}',
    debug={str(is_debug)},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(include_console)},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,{icon_param}
)'''

        # Add COLLECT section for directory mode
        if not one_file:
            spec_content += f'''

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{project_name}'
)'''

        spec_path = build_dir / f"{project_name}.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)

        return spec_path

    def _run_pyinstaller(self, spec_path: Path):
        """Run PyInstaller to build the executable"""
        try:
            # Check if PyInstaller is available
            result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise BuildError("PyInstaller not found. Please install it with: pip install pyinstaller")

            # Run PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_path)
            ]

            result = subprocess.run(cmd, cwd=spec_path.parent, capture_output=True, text=True)

            if result.returncode != 0:
                raise BuildError(f"PyInstaller failed:\n{result.stderr}")

        except FileNotFoundError:
            raise BuildError("Python not found in PATH")

    def _finalize_build(self, build_dir: Path):
        """Finalize the build process"""
        # Clean up temporary files
        temp_dirs = ["build", "__pycache__"]
        for temp_dir in temp_dirs:
            temp_path = build_dir / temp_dir
            if temp_path.exists():
                shutil.rmtree(temp_path)

        # Remove spec file if desired
        spec_files = list(build_dir.glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()

        # Remove temporary launcher
        launcher_file = build_dir / "game_launcher.py"
        if launcher_file.exists():
            launcher_file.unlink()

        # Remove copied engine and game data (they're now bundled)
        temp_data_dirs = ["lupine_engine", "game_data"]
        for temp_dir in temp_data_dirs:
            temp_path = build_dir / temp_dir
            if temp_path.exists():
                shutil.rmtree(temp_path)

    def get_output_path(self) -> Path:
        """Get the path to the built executable or browser package"""
        build_dir = self.build_config["output_dir"]
        platform = self.build_config["platform"]
        build_type = self.build_config["build_type"]
        project_name = self.project_config.get("name", "LupineGame").replace(" ", "")

        target_dir = build_dir / f"{platform}_{build_type}"

        if platform == "browser":
            # Browser build - return the dist directory containing index.html
            return target_dir / "dist"
        elif self.build_config.get("one_file", True):
            # One-file mode
            dist_dir = target_dir / "dist"
            if platform == "windows":
                return dist_dir / f"{project_name}.exe"
            else:
                return dist_dir / project_name
        else:
            # Directory mode
            return target_dir / "dist" / project_name

    # Browser-specific build methods

    def _create_browser_launcher(self, build_dir: Path) -> Path:
        """Create the browser game launcher script for pygbag"""
        project_name = self.project_config.get("name", "Lupine Game")
        main_scene = self.project_config.get("main_scene", "scenes/Main.scene")

        # Browser launcher needs to be async for pygbag
        launcher_content = f'''#!/usr/bin/env python3
"""
Browser Game Launcher for {project_name}
Generated by Lupine Engine Build System for pygbag/WebAssembly
"""

import asyncio
import sys
import os
from pathlib import Path

# Import pygame for pygbag
import pygame

# Game configuration
GAME_WIDTH = {self.build_config.get("browser_width", 1920)}
GAME_HEIGHT = {self.build_config.get("browser_height", 1080)}
GAME_TITLE = "{project_name}"

# Add the bundled engine to Python path
bundle_dir = Path(__file__).parent
engine_path = bundle_dir / "lupine_engine"
project_path = bundle_dir / "game_data"

sys.path.insert(0, str(engine_path))

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()

# Game state
running = True
engine = None

def load_engine():
    """Load the Lupine Engine for browser"""
    global engine
    try:
        # Set up global exception handling
        from core.exception_handler import setup_global_exception_handling
        setup_global_exception_handling()

        from core.game_engine import LupineGameEngine
        engine = LupineGameEngine(str(project_path), "{main_scene}")
        print(f"[BROWSER] Loaded {{GAME_TITLE}}")
    except Exception as e:
        print(f"[ERROR] Failed to load engine: {{e}}")
        engine = None

async def main():
    """Main async game loop for pygbag"""
    global running, engine

    print(f"[BROWSER] Starting {{GAME_TITLE}}")
    print(f"[BROWSER] Resolution: {{GAME_WIDTH}}x{{GAME_HEIGHT}}")
    print("-" * 50)

    # Load engine
    load_engine()

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update and render
        if engine:
            try:
                # Calculate delta time
                delta_time = clock.tick(60) / 1000.0

                # Update game logic
                engine._update(delta_time)

                # Render
                engine._render()

            except Exception as e:
                print(f"[ERROR] Game loop error: {{e}}")
        else:
            # Fallback rendering
            screen.fill((50, 50, 50))
            font = pygame.font.Font(None, 36)
            text = font.render("Game Loading...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2))
            screen.blit(text, text_rect)

        pygame.display.flip()

        # Yield control to browser
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
'''

        launcher_path = build_dir / "main.py"  # pygbag expects main.py
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)

        return launcher_path

    def _collect_browser_assets(self, build_dir: Path):
        """Collect assets for browser build"""
        # Create game data directory
        game_data_dir = build_dir / "game_data"
        game_data_dir.mkdir(exist_ok=True)

        # Copy project files (same as desktop build)
        project_dirs = ["scenes", "scripts", "assets", "nodes", "prefabs"]

        for dir_name in project_dirs:
            src_dir = self.project_path / dir_name
            if src_dir.exists():
                dst_dir = game_data_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

        # Copy project configuration
        dst_project_file = game_data_dir / "project.lupine"
        shutil.copy2(self.project_file, dst_project_file)

        # Copy engine files (minimal set for browser)
        engine_data_dir = build_dir / "lupine_engine"
        engine_data_dir.mkdir(exist_ok=True)

        # Copy core engine modules (browser-compatible subset)
        engine_dirs = ["core"]  # Only core for browser builds
        for dir_name in engine_dirs:
            src_dir = self.lupine_engine_path / dir_name
            if src_dir.exists():
                dst_dir = engine_data_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

        # Copy nodes directory
        nodes_src = self.lupine_engine_path / "nodes"
        if nodes_src.exists():
            nodes_dst = engine_data_dir / "nodes"
            shutil.copytree(nodes_src, nodes_dst, dirs_exist_ok=True)

    def _run_pygbag(self, build_dir: Path, launcher_path: Path):
        """Run pygbag to build for browser"""
        try:
            # Check if pygbag is available (pygbag doesn't have a proper --version flag)
            result = subprocess.run([sys.executable, "-c", "import pygbag; print('pygbag available')"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise BuildError("pygbag not found. Please install it with: pip install pygbag")

            # Prepare pygbag arguments
            project_name = self.project_config.get("name", "LupineGame").replace(" ", "")
            width = self.build_config.get("browser_width", 1920)
            height = self.build_config.get("browser_height", 1080)

            # Run pygbag
            cmd = [
                sys.executable, "-m", "pygbag",
                "--width", str(width),
                "--height", str(height),
                "--app_name", project_name,
                str(build_dir)  # Directory containing main.py
            ]

            # Add debug flag if debug build
            if self.build_config.get("build_type") == "debug":
                cmd.append("--debug")

            self._report_progress("Running pygbag...", 70)
            result = subprocess.run(cmd, cwd=build_dir.parent, capture_output=True, text=True)

            if result.returncode != 0:
                raise BuildError(f"pygbag failed:\\n{result.stderr}")

            self._report_progress("pygbag completed successfully", 85)

        except FileNotFoundError:
            raise BuildError("Python not found in PATH")

    def _finalize_browser_build(self, build_dir: Path):
        """Finalize the browser build"""
        # pygbag creates a build/web directory with the web files
        web_dir = build_dir / "build" / "web"
        dist_dir = build_dir / "dist"

        if not web_dir.exists():
            raise BuildError("Browser build failed - no web directory created")

        # Create dist directory and copy web files
        dist_dir.mkdir(exist_ok=True)
        for item in web_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, dist_dir)
            else:
                shutil.copytree(item, dist_dir / item.name, dirs_exist_ok=True)

        # Check for required files
        required_files = ["index.html"]
        for file_name in required_files:
            file_path = dist_dir / file_name
            if not file_path.exists():
                raise BuildError(f"Browser build incomplete - missing {file_name}")

        # Create a simple README for browser deployment
        readme_content = f'''# {self.project_config.get("name", "Lupine Game")} - Browser Build

This directory contains your game built for web browsers using pygbag.

## Files:
- index.html - Main game page (open this in a browser)
- {self.project_config.get("name", "game").replace(" ", "_").lower()}.apk - Game code and assets package
- favicon.png - Browser icon

## How it works:
- The Python WebAssembly runtime is downloaded from pygame-web.github.io CDN
- Your game code and assets are packaged in the .apk file
- The index.html coordinates loading everything

## Deployment:
1. Upload all files in this directory to your web server
2. Access index.html through a web browser
3. For itch.io: Upload as HTML5 game, set index.html as main file

## Requirements:
- Modern web browser with WebAssembly support
- Internet connection (for CDN resources)
- HTTPS connection recommended

## Troubleshooting:
- If the game doesn't load, check browser console for errors
- Ensure all files are uploaded and accessible
- Test with a local web server (not file:// protocol)
- Check that CDN resources can be accessed

## Local Testing:
Run: python -m pygbag --serve .
Then open: http://localhost:8000

Built with Lupine Engine Build System + pygbag
'''

        readme_path = dist_dir / "README.txt"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        # Clean up temporary files in build directory (keep dist)
        temp_items = ["main.py", "game_data", "lupine_engine"]
        for item_name in temp_items:
            item_path = build_dir / item_name
            if item_path.exists():
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()
