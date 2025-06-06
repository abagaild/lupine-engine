#!/usr/bin/env python3
"""
Lupine Engine Standalone Compiler
Compiles the entire Lupine Engine into a standalone executable
Run this from the main engine directory to create a distributable .exe
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import time


class EngineCompilerError(Exception):
    """Exception raised during engine compilation"""
    pass


class LupineEngineCompiler:
    """Compiles the Lupine Engine into a standalone executable"""
    
    def __init__(self, engine_path: Optional[str] = None):
        # Set engine path to current directory if not provided
        if engine_path is None:
            self.engine_path = Path.cwd()
        else:
            self.engine_path = Path(engine_path)
        
        # Validate engine path
        if not (self.engine_path / "main.py").exists():
            raise EngineCompilerError(f"Invalid engine path: {self.engine_path}. main.py not found.")
        
        # Build configuration
        self.build_config = {
            "output_dir": self.engine_path / "dist",
            "platform": "windows",  # windows, linux, mac
            "build_type": "release",  # debug, release
            "include_console": False,
            "one_file": True,
            "icon_path": self.engine_path / "icon.png",
            "app_name": "LupineEngine",
            "app_version": "1.0.0",
            "exclude_modules": [
                # Exclude test modules and development files
                "test_*",
                "tests",
                "pytest",
                "unittest",
                "doctest",
            ]
        }
        
    def configure_build(self, **kwargs):
        """Configure build settings"""
        self.build_config.update(kwargs)
    
    def _report_progress(self, message: str, progress: int):
        """Report build progress"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{progress:3d}%] {message}")
    
    def compile_engine(self) -> bool:
        """Compile the engine into a standalone executable"""
        try:
            self._report_progress("Starting Lupine Engine compilation...", 0)
            
            # Check dependencies
            self._check_dependencies()
            self._report_progress("Dependencies verified", 5)
            
            # Prepare build directory
            build_dir = self._prepare_build_directory()
            self._report_progress("Build directory prepared", 10)
            
            # Create engine launcher
            launcher_path = self._create_engine_launcher(build_dir)
            self._report_progress("Engine launcher created", 20)
            
            # Collect engine files
            self._collect_engine_files(build_dir)
            self._report_progress("Engine files collected", 40)
            
            # Create PyInstaller spec
            spec_path = self._create_pyinstaller_spec(build_dir, launcher_path)
            self._report_progress("PyInstaller spec created", 60)
            
            # Run PyInstaller
            self._run_pyinstaller(spec_path)
            self._report_progress("PyInstaller compilation complete", 90)
            
            # Finalize build
            self._finalize_build(build_dir)
            self._report_progress("Engine compilation complete!", 100)
            
            return True
            
        except Exception as e:
            self._report_progress(f"Compilation failed: {e}", -1)
            raise EngineCompilerError(f"Engine compilation failed: {e}")
    
    def _check_dependencies(self):
        """Check if required dependencies are installed"""
        # Map package names to their import names
        package_imports = {
            "pyinstaller": "PyInstaller",
            "PyQt6": "PyQt6",
            "pygame": "pygame",
            "PyOpenGL": "OpenGL",
            "numpy": "numpy",
            "Pillow": "PIL",
            "pymunk": "pymunk"
        }

        missing_packages = []

        for package, import_name in package_imports.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            raise EngineCompilerError(
                f"Missing required packages: {', '.join(missing_packages)}. "
                f"Install with: pip install {' '.join(missing_packages)}"
            )
        
        # Check PyInstaller specifically
        try:
            result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise EngineCompilerError("PyInstaller not found or not working properly")
        except FileNotFoundError:
            raise EngineCompilerError("PyInstaller not found. Install with: pip install pyinstaller")
    
    def _prepare_build_directory(self) -> Path:
        """Prepare the build directory"""
        build_dir = self.build_config["output_dir"]
        platform = self.build_config["platform"]
        build_type = self.build_config["build_type"]
        
        # Create platform-specific build directory
        target_dir = build_dir / f"engine_{platform}_{build_type}"
        
        # Clean existing build
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir)
            except OSError as e:
                # If we can't remove it, try to work around it
                print(f"Warning: Could not remove existing build directory: {e}")
                # Try to create a new directory with timestamp
                timestamp = int(time.time())
                target_dir = target_dir.parent / f"{target_dir.name}_{timestamp}"
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return target_dir

    def _create_engine_launcher(self, build_dir: Path) -> Path:
        """Create the engine launcher script"""
        app_name = self.build_config["app_name"]
        app_version = self.build_config["app_version"]

        launcher_content = f'''#!/usr/bin/env python3
"""
Lupine Engine Standalone Launcher
Generated by Lupine Engine Compiler
"""

import sys
import os
from pathlib import Path

# Add the bundled engine to Python path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    engine_path = bundle_dir / "lupine_engine"
else:
    # Running as script (development)
    bundle_dir = Path(__file__).parent
    engine_path = bundle_dir / "lupine_engine"

sys.path.insert(0, str(engine_path))

# Set up global exception handling BEFORE importing anything else
from core.exception_handler import setup_global_exception_handling
setup_global_exception_handling()

def main():
    """Main entry point for Lupine Engine"""
    try:
        # Import the main engine entry point
        from main import main as engine_main

        print(f"[ENGINE] Starting {app_name}")
        print(f"[ENGINE] Version: {app_version}")
        print("-" * 50)

        # Run the engine
        engine_main()

    except Exception as e:
        print(f"[ERROR] Failed to start engine: {{e}}")
        import traceback
        traceback.print_exc()

        # Try to pause for user to see error (works in console builds)
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError):
            # input() doesn't work in bundled executables without console
            import time
            print("[ERROR] Engine will exit in 5 seconds...")
            time.sleep(5)

        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        launcher_path = build_dir / "engine_launcher.py"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)

        return launcher_path

    def _collect_engine_files(self, build_dir: Path):
        """Collect all engine files"""
        engine_data_dir = build_dir / "lupine_engine"
        engine_data_dir.mkdir(exist_ok=True)

        # Core engine directories to include
        engine_dirs = [
            "core",
            "nodes",
            "editor",
            "prefabs"
        ]

        for dir_name in engine_dirs:
            src_dir = self.engine_path / dir_name
            if src_dir.exists():
                dst_dir = engine_data_dir / dir_name
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

        # Essential engine files
        engine_files = [
            "main.py",
            "requirements.txt",
            "icon.png",
            "logo.png",
            "splash.png"
        ]

        for file_name in engine_files:
            src_file = self.engine_path / file_name
            if src_file.exists():
                dst_file = engine_data_dir / file_name
                shutil.copy2(src_file, dst_file)

        # Copy scripts directory if it exists
        scripts_dir = self.engine_path / "scripts"
        if scripts_dir.exists():
            dst_scripts = engine_data_dir / "scripts"
            shutil.copytree(scripts_dir, dst_scripts, dirs_exist_ok=True)

    def _create_pyinstaller_spec(self, build_dir: Path, launcher_path: Path) -> Path:
        """Create PyInstaller spec file for the engine"""
        app_name = self.build_config["app_name"]
        icon_path = self.build_config.get("icon_path")
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
        icon_param = f"    icon={repr(str(icon_path))}," if icon_path and icon_path.exists() else ""

        # Use relative paths for the spec file
        launcher_relative = launcher_path.name

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Lupine Engine PyInstaller Specification
# Generated by Lupine Engine Compiler

block_cipher = None

# Exclude modules
exclude_modules = {exclude_modules}

a = Analysis(
    [r'{launcher_relative}'],
    pathex=[r'{build_dir}'],
    binaries=[],
    datas=[
        (r'lupine_engine', 'lupine_engine'),
    ],
    hiddenimports=[
        # Core Python modules
        'json', 'pathlib', 'sys', 'os', 'traceback', 'threading', 'time',
        'math', 'random', 'collections', 'functools', 'itertools', 'typing',
        'dataclasses', 'enum', 'copy', 'weakref', 'inspect', 'importlib',
        'importlib.util', 'pkgutil', 'glob', 'shutil', 'subprocess', 'tempfile',
        'zipfile', 'io', 'struct', 'hashlib', 'base64', 'uuid', 'datetime',
        'decimal', 'fractions', 're', 'string', 'textwrap', 'unicodedata',
        'codecs', 'locale', 'gettext', 'argparse', 'configparser', 'logging',
        'warnings', 'contextlib', 'abc', 'atexit', 'signal',

        # Game engine dependencies
        'pygame', 'pygame.mixer', 'pygame.font', 'pygame.image', 'pygame.transform',
        'pygame.draw', 'pygame.surface', 'pygame.rect', 'pygame.color', 'pygame.math',
        'pygame.time', 'pygame.event', 'pygame.key', 'pygame.mouse', 'pygame.joystick',
        'pygame.display', 'pygame.locals', 'pygame.constants', 'pygame.version',
        'pygame.gfxdraw', 'pygame.sprite', 'pygame.mask', 'pygame.pixelarray',
        'pygame.sndarray', 'pygame.surfarray', 'pygame.freetype', 'pygame.scrap',
        'pygame.cursors', 'pygame.bufferproxy',

        # OpenGL and graphics
        'OpenGL', 'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT', 'OpenGL.arrays',
        'OpenGL.arrays.vbo', 'OpenGL.GL.shaders', 'OpenGL.GL.framebufferobjects',
        'OpenGL.extensions', 'OpenGL.platform', 'OpenGL.error', 'OpenGL.contextdata',
        'OpenGL.plugins',

        # PyQt6 (for editor)
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets', 'PyQt6.sip',

        # Scientific computing
        'numpy', 'numpy.core', 'numpy.lib', 'numpy.random', 'numpy.linalg',
        'numpy.fft', 'numpy.polynomial', 'numpy.testing',

        # Image processing
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageFilter',
        'PIL.ImageEnhance', 'PIL.ImageOps', 'PIL.ImageChops', 'PIL.ImageStat',
        'PIL.ImageColor', 'PIL.ImageMode', 'PIL.ImageSequence', 'PIL.ImageFile',
        'PIL.ImagePath', 'PIL.ImageShow', 'PIL.ImageTk', 'PIL.ImageWin',

        # Physics
        'pymunk', 'pymunk.pygame_util',

        # Audio
        'openal', 'openal.al', 'openal.alc',

        # Syntax highlighting
        'pygments', 'pygments.lexers', 'pygments.formatters', 'pygments.styles',
        'pygments.filters', 'pygments.token',
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
    name='{app_name}',
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
    name='{app_name}'
)'''

        spec_path = build_dir / f"{app_name}.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)

        return spec_path

    def _run_pyinstaller(self, spec_path: Path):
        """Run PyInstaller to build the executable"""
        try:
            # Run PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_path)
            ]

            self._report_progress("Running PyInstaller (this may take several minutes)...", 70)

            result = subprocess.run(cmd, cwd=spec_path.parent, capture_output=True, text=True)

            if result.returncode != 0:
                raise EngineCompilerError(f"PyInstaller failed:\n{result.stderr}")

            # Print PyInstaller output for debugging
            if result.stdout:
                print("\nPyInstaller output:")
                print(result.stdout)

        except FileNotFoundError:
            raise EngineCompilerError("Python not found in PATH")

    def _finalize_build(self, build_dir: Path):
        """Finalize the build and clean up"""
        app_name = self.build_config["app_name"]
        one_file = self.build_config.get("one_file", True)

        # Find the generated executable
        if one_file:
            # Single file executable
            exe_source = build_dir / "dist" / f"{app_name}.exe"
            exe_dest = self.build_config["output_dir"] / f"{app_name}.exe"
        else:
            # Directory distribution
            exe_source = build_dir / "dist" / app_name
            exe_dest = self.build_config["output_dir"] / app_name

        # Ensure output directory exists
        self.build_config["output_dir"].mkdir(parents=True, exist_ok=True)

        # Move the executable to the final location
        if exe_source.exists():
            if exe_dest.exists():
                try:
                    if exe_dest.is_dir():
                        shutil.rmtree(exe_dest)
                    else:
                        exe_dest.unlink()
                except OSError as e:
                    # If we can't remove the existing file, try a different name
                    import time
                    timestamp = int(time.time())
                    if exe_dest.is_dir():
                        exe_dest = exe_dest.parent / f"{exe_dest.name}_{timestamp}"
                    else:
                        exe_dest = exe_dest.parent / f"{exe_dest.stem}_{timestamp}{exe_dest.suffix}"

            if exe_source.is_dir():
                shutil.copytree(exe_source, exe_dest)
            else:
                shutil.copy2(exe_source, exe_dest)
        else:
            raise EngineCompilerError(f"Generated executable not found at: {exe_source}")

        # Clean up build directory (optional)
        try:
            shutil.rmtree(build_dir)
        except OSError:
            # If cleanup fails, it's not critical
            print(f"Warning: Could not clean up build directory: {build_dir}")

        # Verify the final executable exists
        if not exe_dest.exists():
            raise EngineCompilerError(f"Final executable not found at: {exe_dest}")


def main():
    """Main entry point for the engine compiler"""
    print("=" * 60)
    print("Lupine Engine Standalone Compiler")
    print("=" * 60)
    
    try:
        compiler = LupineEngineCompiler()
        
        # Allow command line configuration
        if len(sys.argv) > 1:
            if "--debug" in sys.argv:
                compiler.configure_build(build_type="debug", include_console=True)
            if "--console" in sys.argv:
                compiler.configure_build(include_console=True)
            if "--directory" in sys.argv:
                compiler.configure_build(one_file=False)
        
        success = compiler.compile_engine()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ENGINE COMPILATION SUCCESSFUL!")
            print("=" * 60)
            print(f"📁 Output directory: {compiler.build_config['output_dir']}")
            print(f"🎯 Executable: {compiler.build_config['app_name']}.exe")
            print("=" * 60)
        else:
            print("\n❌ Engine compilation failed!")
            sys.exit(1)
            
    except EngineCompilerError as e:
        print(f"\n❌ Compilation Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Compilation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
