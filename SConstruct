#!/usr/bin/env python3

"""
SCons build script for Lupine Engine C++
Based on Godot's build system but adapted for Lupine Engine architecture
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# Ensure we're using Python 3.7+
if sys.version_info < (3, 7):
    print("ERROR: Python 3.7+ is required to build Lupine Engine")
    sys.exit(1)

# Add tools directory to path
sys.path.insert(0, "tools")
import methods

# Platform detection
platform_list = ["windows", "linux", "macos", "web"]
platform_opts = ["p", "platform"]

# Architecture detection  
arch_list = ["x86_32", "x86_64", "arm32", "arm64"]
arch_opts = ["a", "arch"]

# Build type options
target_list = ["editor", "template_debug", "template_release"]
target_opts = ["t", "target"]

# Default values
env_base = Environment(tools=["default"])
platform_arg = ARGUMENTS.get("platform", ARGUMENTS.get("p", ""))
if platform_arg == "":
    # Auto-detect platform
    if os.name == "nt":
        platform_arg = "windows"
    elif sys.platform == "darwin":
        platform_arg = "macos"
    else:
        platform_arg = "linux"

# Validate platform
if platform_arg not in platform_list:
    print(f"ERROR: Invalid platform '{platform_arg}'. Valid platforms: {platform_list}")
    sys.exit(1)

# Architecture detection
arch_arg = ARGUMENTS.get("arch", ARGUMENTS.get("a", ""))
if arch_arg == "":
    # Auto-detect architecture
    machine = platform.machine().lower()
    if machine in ["amd64", "x86_64"]:
        arch_arg = "x86_64"
    elif machine in ["i386", "i686", "x86"]:
        arch_arg = "x86_32"
    elif machine in ["arm64", "aarch64"]:
        arch_arg = "arm64"
    elif machine.startswith("arm"):
        arch_arg = "arm32"
    else:
        arch_arg = "x86_64"  # Default fallback

# Target detection
target_arg = ARGUMENTS.get("target", ARGUMENTS.get("t", "editor"))

# Build configuration
env = Environment()
env["platform"] = platform_arg
env["arch"] = arch_arg
env["target"] = target_arg
env["tools"] = target_arg == "editor"
env["editor_build"] = target_arg == "editor"
env["debug_symbols"] = ARGUMENTS.get("debug_symbols", "yes" if target_arg != "template_release" else "no")
env["optimize"] = ARGUMENTS.get("optimize", "debug" if target_arg == "template_debug" else "speed")
env["dev_build"] = ARGUMENTS.get("dev_build", "yes" if target_arg == "editor" else "no")

# Python integration settings
env["python_enabled"] = ARGUMENTS.get("python_enabled", "yes")
env["python_version"] = ARGUMENTS.get("python_version", "3.11")

# Rendering backend
env["renderer"] = ARGUMENTS.get("renderer", "opengl3")

# Audio backend  
env["audio"] = ARGUMENTS.get("audio", "openal")

# Physics backend
env["physics"] = ARGUMENTS.get("physics", "box2d")

# Build directories
env["build_dir"] = f"build/{platform_arg}_{arch_arg}_{target_arg}"
env["bin_dir"] = "bin"

# Create build directory
build_path = Path(env["build_dir"])
build_path.mkdir(parents=True, exist_ok=True)

# Platform-specific configuration
if platform_arg == "windows":
    env.Tool("msvc")
    env.Append(CPPDEFINES=["WINDOWS_ENABLED", "_WIN32_WINNT=0x0601"])
    env.Append(LIBS=["kernel32", "user32", "gdi32", "winspool", "shell32", "ole32", "oleaut32", "uuid", "comdlg32", "advapi32"])
    
elif platform_arg == "linux":
    env.Tool("gcc")
    env.Append(CPPDEFINES=["LINUX_ENABLED", "UNIX_ENABLED"])
    env.Append(LIBS=["pthread", "dl", "m"])
    
elif platform_arg == "macos":
    env.Tool("clang")
    env.Append(CPPDEFINES=["MACOS_ENABLED", "UNIX_ENABLED"])
    env.Append(FRAMEWORKS=["Cocoa", "Carbon", "AudioUnit", "AudioToolbox", "CoreAudio", "CoreMIDI", "IOKit", "ForceFeedback", "CoreVideo", "AVFoundation", "CoreMedia", "QuartzCore", "Security", "CFNetwork"])

# Compiler configuration
if env["target"] == "template_release":
    env.Append(CPPDEFINES=["NDEBUG"])
    if platform_arg == "windows":
        env.Append(CCFLAGS=["/O2", "/Ob2", "/Ot", "/GL"])
        env.Append(LINKFLAGS=["/LTCG"])
    else:
        env.Append(CCFLAGS=["-O3", "-ffast-math"])
        env.Append(LINKFLAGS=["-O3"])
        
elif env["target"] == "template_debug":
    env.Append(CPPDEFINES=["DEBUG_ENABLED"])
    if platform_arg == "windows":
        env.Append(CCFLAGS=["/Od", "/Zi"])
        env.Append(LINKFLAGS=["/DEBUG"])
    else:
        env.Append(CCFLAGS=["-O0", "-g3"])
        
else:  # editor
    env.Append(CPPDEFINES=["DEBUG_ENABLED", "TOOLS_ENABLED"])
    if platform_arg == "windows":
        env.Append(CCFLAGS=["/Od", "/Zi"])
        env.Append(LINKFLAGS=["/DEBUG"])
    else:
        env.Append(CCFLAGS=["-O0", "-g3"])

# C++ standard
env.Append(CXXFLAGS=["-std=c++17"])

# Include paths
env.Append(CPPPATH=[
    ".",
    "core",
    "thirdparty"
])

# Python integration
if env["python_enabled"] == "yes":
    python_config = subprocess.run([sys.executable, "-c", 
        "import sysconfig; print(sysconfig.get_path('include')); print(sysconfig.get_config_var('LIBDIR')); print(sysconfig.get_config_var('LDLIBRARY'))"],
        capture_output=True, text=True)
    
    if python_config.returncode == 0:
        lines = python_config.stdout.strip().split('\n')
        python_include = lines[0]
        python_libdir = lines[1] if lines[1] != 'None' else ""
        python_lib = lines[2] if lines[2] != 'None' else ""
        
        env.Append(CPPPATH=[python_include])
        env.Append(CPPDEFINES=["PYTHON_ENABLED"])
        
        if python_libdir:
            env.Append(LIBPATH=[python_libdir])
        if python_lib:
            env.Append(LIBS=[python_lib.replace("lib", "").replace(".so", "").replace(".dll", "").replace(".dylib", "")])

# OpenGL configuration
env.Append(CPPDEFINES=["OPENGL_ENABLED"])
if platform_arg == "windows":
    env.Append(LIBS=["opengl32", "glu32"])
elif platform_arg == "linux":
    env.Append(LIBS=["GL", "GLU"])
elif platform_arg == "macos":
    env.Append(FRAMEWORKS=["OpenGL"])

# Audio configuration (OpenAL)
if env["audio"] == "openal":
    env.Append(CPPDEFINES=["OPENAL_ENABLED"])
    if platform_arg == "windows":
        env.Append(LIBS=["OpenAL32"])
    elif platform_arg == "linux":
        env.Append(LIBS=["openal"])
    elif platform_arg == "macos":
        env.Append(FRAMEWORKS=["OpenAL"])

# Physics configuration
if env["physics"] == "box2d":
    env.Append(CPPDEFINES=["BOX2D_ENABLED"])

# Source files
env.core_sources = []
env.main_sources = []
env.editor_sources = []

# Export environment
Export("env")

# Build subdirectories
print(f"Building Lupine Engine for {platform_arg} {arch_arg} ({target_arg})")

# Core engine
SConscript("src/core/SCsub")

# Main executable
SConscript("src/main/SCsub")

# Editor (if building editor)
if env["editor_build"]:
    SConscript("src/editor/SCsub")

# Platform-specific code
SConscript(f"src/platform/{platform_arg}/SCsub")

# Build the executable
if env["editor_build"]:
    program_name = "lupine_editor"
else:
    program_name = "lupine"

if platform_arg == "windows":
    program_name += ".exe"

program = env.Program(
    target=f"{env['bin_dir']}/{program_name}",
    source=env.main_sources + env.core_sources + (env.editor_sources if env["editor_build"] else [])
)

# Default target
Default(program)

# Help text
Help(f"""
Lupine Engine Build System

Usage: scons [options]

Platform options:
  platform=<platform>     Target platform ({', '.join(platform_list)})
  arch=<architecture>      Target architecture ({', '.join(arch_list)})
  target=<target>          Build target ({', '.join(target_list)})

Features:
  python_enabled=<yes/no>  Enable Python scripting support (default: yes)
  renderer=<backend>       Rendering backend (default: opengl3)
  audio=<backend>          Audio backend (default: openal)
  physics=<backend>        Physics backend (default: box2d)

Build options:
  debug_symbols=<yes/no>   Include debug symbols
  optimize=<level>         Optimization level (debug/speed/size)
  dev_build=<yes/no>       Development build with extra debugging

Examples:
  scons                           # Build editor for current platform
  scons target=template_release   # Build release template
  scons platform=linux target=editor  # Build Linux editor
""")
