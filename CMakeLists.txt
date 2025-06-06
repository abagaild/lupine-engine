cmake_minimum_required(VERSION 3.16)
project(LupineEngine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform detection
if(WIN32)
    add_definitions(-DWINDOWS_ENABLED)
    set(PLATFORM_NAME "windows")
elseif(UNIX AND NOT APPLE)
    add_definitions(-DLINUX_ENABLED -DUNIX_ENABLED)
    set(PLATFORM_NAME "linux")
elseif(APPLE)
    add_definitions(-DMACOS_ENABLED -DUNIX_ENABLED)
    set(PLATFORM_NAME "macos")
endif()

# Build configuration
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_definitions(-DDEBUG_ENABLED)
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_definitions(-DNDEBUG)
endif()

# Include directories
include_directories(
    src
    src/core
    thirdparty
)

# Core source files
set(CORE_SOURCES
    src/core/core_types.cpp
    src/core/lupine_engine.cpp
    src/core/platform/platform.cpp
    src/core/scene/node.cpp
    src/core/scene/scene.cpp
    src/core/rendering/renderer.cpp
    src/core/audio/audio_system.cpp
    src/core/physics/physics_world.cpp
    src/core/input/input_manager.cpp
    src/core/scripting/script_runtime.cpp
)

# Platform-specific sources
if(WIN32)
    list(APPEND CORE_SOURCES
        src/platform/windows/platform_windows.cpp
        src/platform/windows/platform_windows_wndproc.cpp
        src/platform/windows/platform_windows_opengl.cpp
    )
endif()

# Main executable sources
set(MAIN_SOURCES
    src/main/main.cpp
)

# Create executable
add_executable(lupine_engine ${MAIN_SOURCES} ${CORE_SOURCES})

# Platform-specific libraries
if(WIN32)
    target_link_libraries(lupine_engine
        opengl32
        glu32
        gdi32
        user32
        kernel32
        shell32
        ole32
        oleaut32
        uuid
        comdlg32
        advapi32
        psapi
        shlwapi
    )
elseif(UNIX AND NOT APPLE)
    target_link_libraries(lupine_engine
        GL
        GLU
        pthread
        dl
        m
    )
elseif(APPLE)
    find_library(OPENGL_FRAMEWORK OpenGL)
    find_library(COCOA_FRAMEWORK Cocoa)
    target_link_libraries(lupine_engine
        ${OPENGL_FRAMEWORK}
        ${COCOA_FRAMEWORK}
    )
endif()

# Optional features
option(ENABLE_PYTHON "Enable Python scripting support" ON)
option(ENABLE_AUDIO "Enable audio system" ON)
option(ENABLE_PHYSICS "Enable physics system" ON)

if(ENABLE_PYTHON)
    add_definitions(-DPYTHON_ENABLED)
    # TODO: Find and link Python
endif()

if(ENABLE_AUDIO)
    add_definitions(-DOPENAL_ENABLED)
    # TODO: Find and link OpenAL
endif()

if(ENABLE_PHYSICS)
    add_definitions(-DBOX2D_ENABLED)
    # TODO: Find and link Box2D
endif()

# OpenGL is always enabled
add_definitions(-DOPENGL_ENABLED)

# Set output directory
set_target_properties(lupine_engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Copy assets to build directory (if any)
# file(COPY assets DESTINATION ${CMAKE_BINARY_DIR})

# Print configuration
message(STATUS "Lupine Engine Configuration:")
message(STATUS "  Platform: ${PLATFORM_NAME}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Python Support: ${ENABLE_PYTHON}")
message(STATUS "  Audio Support: ${ENABLE_AUDIO}")
message(STATUS "  Physics Support: ${ENABLE_PHYSICS}")
