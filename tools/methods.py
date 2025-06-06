#!/usr/bin/env python3

"""
Build methods and utilities for Lupine Engine
Based on Godot's build system but adapted for Lupine Engine
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def add_source_files(self, sources, files, warn_duplicates=True):
    """
    Add source files to the build list
    """
    for path in files:
        if isinstance(path, str):
            # Convert to absolute path
            abs_path = os.path.abspath(path)
            if warn_duplicates and abs_path in sources:
                print(f"Warning: Duplicate source file {abs_path}")
            sources.append(abs_path)


def disable_warnings(self):
    """
    Disable compiler warnings
    """
    if self["platform"] == "windows":
        self.Append(CCFLAGS=["/w"])
    else:
        self.Append(CCFLAGS=["-w"])


def add_library(self, name, sources, **args):
    """
    Add a library to the build
    """
    lib = self.Library(name, sources, **args)
    self.Prepend(LIBS=[lib])


def get_version_info():
    """
    Get version information from git or version file
    """
    version = {"major": 1, "minor": 0, "patch": 0, "status": "dev", "build": "unknown"}
    
    try:
        # Try to get version from git
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            version["build"] = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return version


def detect_modules(path="modules"):
    """
    Detect available modules in the modules directory
    """
    modules = []
    if os.path.exists(path):
        for item in os.listdir(path):
            module_path = os.path.join(path, item)
            if os.path.isdir(module_path):
                config_file = os.path.join(module_path, "config.py")
                if os.path.exists(config_file):
                    modules.append(item)
    return modules


def configure_for_web(env):
    """
    Configure environment for web/Emscripten build
    """
    if env["platform"] != "web":
        return
    
    # Emscripten-specific settings
    env.Append(CCFLAGS=["-s", "USE_SDL=2"])
    env.Append(LINKFLAGS=["-s", "USE_SDL=2"])
    env.Append(LINKFLAGS=["-s", "WASM=1"])
    env.Append(LINKFLAGS=["-s", "ALLOW_MEMORY_GROWTH=1"])


def setup_msvc_manual(env):
    """
    Manually setup MSVC environment if needed
    """
    if env["platform"] != "windows":
        return
    
    # Try to find MSVC installation
    import winreg
    
    try:
        # Look for Visual Studio installations
        vs_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\VisualStudio\SxS\VS7")
        vs_path = winreg.QueryValueEx(vs_key, "15.0")[0]  # VS 2017
        winreg.CloseKey(vs_key)
        
        # Setup environment
        vcvars_path = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
        if os.path.exists(vcvars_path):
            print(f"Found MSVC at {vs_path}")
            
    except (WindowsError, FileNotFoundError):
        pass


def setup_mingw(env):
    """
    Setup MinGW environment for Windows
    """
    if env["platform"] != "windows":
        return
    
    # MinGW-specific settings
    env.Append(CCFLAGS=["-static-libgcc", "-static-libstdc++"])
    env.Append(LINKFLAGS=["-static-libgcc", "-static-libstdc++"])


def get_compiler_version(env):
    """
    Get compiler version information
    """
    try:
        if env["CC"] == "cl" or env["CC"] == "cl.exe":
            # MSVC
            result = subprocess.run([env["CC"]], capture_output=True, text=True)
            return result.stderr.split('\n')[0] if result.stderr else "Unknown MSVC"
        else:
            # GCC/Clang
            result = subprocess.run([env["CC"], "--version"], capture_output=True, text=True)
            return result.stdout.split('\n')[0] if result.stdout else "Unknown GCC/Clang"
    except (subprocess.SubprocessError, FileNotFoundError):
        return "Unknown compiler"


def setup_sanitizers(env):
    """
    Setup sanitizers for debugging builds
    """
    if env["target"] not in ["editor", "template_debug"]:
        return
    
    sanitizers = []
    
    if env.get("use_asan", False):
        sanitizers.append("address")
    if env.get("use_ubsan", False):
        sanitizers.append("undefined")
    if env.get("use_tsan", False):
        sanitizers.append("thread")
    
    if sanitizers and env["platform"] != "windows":
        sanitizer_flags = [f"-fsanitize={','.join(sanitizers)}"]
        env.Append(CCFLAGS=sanitizer_flags)
        env.Append(LINKFLAGS=sanitizer_flags)


def setup_lto(env):
    """
    Setup Link Time Optimization
    """
    if env["target"] != "template_release":
        return
    
    if env.get("use_lto", False):
        if env["platform"] == "windows":
            env.Append(CCFLAGS=["/GL"])
            env.Append(LINKFLAGS=["/LTCG"])
        else:
            env.Append(CCFLAGS=["-flto"])
            env.Append(LINKFLAGS=["-flto"])


def generate_version_header(target, source, env):
    """
    Generate version header file
    """
    version = get_version_info()
    
    header_content = f"""
#pragma once

// Auto-generated version information
#define LUPINE_VERSION_MAJOR {version["major"]}
#define LUPINE_VERSION_MINOR {version["minor"]}
#define LUPINE_VERSION_PATCH {version["patch"]}
#define LUPINE_VERSION_STATUS "{version["status"]}"
#define LUPINE_VERSION_BUILD "{version["build"]}"

#define LUPINE_VERSION_FULL_CONFIG "{version["major"]}.{version["minor"]}.{version["patch"]}-{version["status"]}"
#define LUPINE_VERSION_FULL_BUILD "{version["major"]}.{version["minor"]}.{version["patch"]}-{version["status"]}+{version["build"]}"

// Platform information
#ifdef WINDOWS_ENABLED
#define LUPINE_PLATFORM_NAME "Windows"
#elif defined(LINUX_ENABLED)
#define LUPINE_PLATFORM_NAME "Linux"
#elif defined(MACOS_ENABLED)
#define LUPINE_PLATFORM_NAME "macOS"
#elif defined(WEB_ENABLED)
#define LUPINE_PLATFORM_NAME "Web"
#else
#define LUPINE_PLATFORM_NAME "Unknown"
#endif

// Build configuration
#ifdef TOOLS_ENABLED
#define LUPINE_BUILD_TYPE "Editor"
#elif defined(DEBUG_ENABLED)
#define LUPINE_BUILD_TYPE "Debug"
#else
#define LUPINE_BUILD_TYPE "Release"
#endif
"""
    
    with open(str(target[0]), 'w') as f:
        f.write(header_content)


def setup_environment_extensions(env):
    """
    Add custom methods to the SCons environment
    """
    env.AddMethod(add_source_files, "add_source_files")
    env.AddMethod(disable_warnings, "disable_warnings")
    env.AddMethod(add_library, "add_library")


def print_build_summary(env):
    """
    Print build configuration summary
    """
    print("\n" + "="*60)
    print("Lupine Engine Build Configuration")
    print("="*60)
    print(f"Platform: {env['platform']}")
    print(f"Architecture: {env['arch']}")
    print(f"Target: {env['target']}")
    print(f"Compiler: {get_compiler_version(env)}")
    print(f"Python: {'Enabled' if env['python_enabled'] == 'yes' else 'Disabled'}")
    print(f"Renderer: {env['renderer']}")
    print(f"Audio: {env['audio']}")
    print(f"Physics: {env['physics']}")
    print(f"Build directory: {env['build_dir']}")
    print("="*60 + "\n")


# Export functions for use in SConstruct
__all__ = [
    "add_source_files",
    "disable_warnings", 
    "add_library",
    "get_version_info",
    "detect_modules",
    "configure_for_web",
    "setup_msvc_manual",
    "setup_mingw",
    "get_compiler_version",
    "setup_sanitizers",
    "setup_lto",
    "generate_version_header",
    "setup_environment_extensions",
    "print_build_summary"
]
