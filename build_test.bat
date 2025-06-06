@echo off
echo Building Lupine Engine Core Test...

REM Try to find Visual Studio compiler
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" (
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
) else if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" (
    call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
) else (
    echo Visual Studio not found. Please install Visual Studio or use the Developer Command Prompt.
    pause
    exit /b 1
)

REM Compile the test
cl /EHsc /std:c++17 /I. ^
   test_basic.cpp ^
   src/core/core_types.cpp ^
   src/core/lupine_engine.cpp ^
   src/core/platform/platform.cpp ^
   src/core/scene/node.cpp ^
   src/core/scene/scene.cpp ^
   src/core/rendering/renderer.cpp ^
   src/core/audio/audio_system.cpp ^
   src/core/physics/physics_world.cpp ^
   src/core/input/input_manager.cpp ^
   src/core/scripting/script_runtime.cpp ^
   /Fe:test_basic.exe

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful! Running test...
    echo.
    test_basic.exe
) else (
    echo.
    echo Build failed!
)

pause
