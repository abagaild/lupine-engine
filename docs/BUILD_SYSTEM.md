# Lupine Engine Build System

The Lupine Engine build system allows you to package your games into standalone executable files that can be distributed and run on target platforms without requiring Python or the Lupine Engine to be installed.

## Features

- **Single Executable**: Package your entire game into one `.exe` file (Windows) or executable (Linux/Mac)
- **Browser Export**: Export games as HTML5/WebAssembly for web browsers and itch.io
- **Cross-Platform**: Build for Windows, Linux, macOS, and web browsers
- **Asset Bundling**: Automatically includes all game assets, scenes, scripts, and dependencies
- **Icon Support**: Set custom icons for your executable
- **Debug/Release Builds**: Choose between debug builds (with console) and release builds
- **Progress Tracking**: Real-time build progress with detailed logging

## Requirements

Before using the build system, ensure you have the required tools installed:

**For Desktop Builds:**
```bash
pip install pyinstaller>=5.0.0
```

**For Browser Builds:**
```bash
pip install pygbag>=0.8.0
```

Both are automatically included in the Lupine Engine requirements.txt file.

## How to Use

### 1. Access the Build Dialog

In the Lupine Engine editor:
1. Open your project
2. Go to **File** → **Build Game** (or press `Ctrl+B`)
3. The Build Dialog will open

### 2. Configure Build Settings

#### Build Settings Tab:
- **Output Directory**: Where the built executable/web files will be saved (defaults to `project/builds/`)
- **Target Platform**: Choose Windows, Linux, macOS, or Browser
- **Build Type**:
  - **Release**: Optimized build without console window
  - **Debug**: Build with console window for debugging
- **Create single executable file**: Bundle everything into one file (desktop only)
- **Include console window**: Show console for debugging (desktop only)
- **Icon File**: Optional custom icon for your executable (desktop only)

#### Browser Settings (when Browser platform is selected):
- **Game Width**: Width of the game canvas in pixels (default: 1920)
- **Game Height**: Height of the game canvas in pixels (default: 1080)
- **Allow fullscreen**: Enable fullscreen mode in browser

#### Advanced Tab:
- **Exclude Modules**: Comma-separated list of Python modules to exclude from the build
- **Additional Files**: (Future feature) Extra files to include with the build

### 3. Start the Build

1. Click **Build Game**
2. The dialog will switch to the Progress tab
3. Monitor the build progress and logs
4. When complete, you'll see a success message with the output path

## Build Output

The build system creates the following structure:

**Desktop Builds:**
```
project/
├── builds/
│   └── windows_release/          # Platform and build type
│       └── dist/
│           └── YourGame.exe      # Your standalone game executable
```

**Browser Builds:**
```
project/
├── builds/
│   └── browser_release/          # Platform and build type
│       └── dist/
│           ├── index.html        # Main game page
│           ├── YourGame.js       # Game engine
│           ├── YourGame.wasm     # WebAssembly binary
│           ├── YourGame.data     # Game assets
│           └── README.txt        # Deployment instructions
```

## How It Works

The build system:

1. **Validates** your project (checks for main scene, required files)
2. **Creates** a standalone launcher script that initializes your game
3. **Collects** all project assets (scenes, scripts, images, audio, etc.)
4. **Bundles** the Lupine Engine core with your project
5. **Generates** a PyInstaller specification file
6. **Runs** PyInstaller to create the executable
7. **Cleans up** temporary files

## Standalone Game Structure

The built executable contains:
- **Game Launcher**: Initializes the Lupine Engine and starts your game
- **Lupine Engine Core**: All necessary engine components
- **Your Project**: All scenes, scripts, assets, and configuration
- **Dependencies**: Python runtime and required libraries

## Distribution

### Desktop Games
The built executable is completely standalone and can be distributed to users who don't have Python or Lupine Engine installed. Simply share the `.exe` file (or the entire folder for directory builds).

### Browser Games
Browser builds create web-ready files that can be:
- **Uploaded to itch.io**: Upload the entire `dist` folder as an HTML5 game, set `index.html` as the main file
- **Hosted on any web server**: Upload all files and access `index.html` through a browser
- **Shared locally**: Serve through a local web server (required due to browser security restrictions)

#### itch.io Upload Instructions:
1. In your itch.io game page, go to "Upload files"
2. Select "HTML" as the kind of project
3. Upload all files from the `dist` folder
4. Set `index.html` as the main HTML file
5. Set the viewport dimensions to match your game size
6. Enable "Mobile friendly" if desired

## Troubleshooting

### Common Issues:

1. **PyInstaller not found**: Install PyInstaller with `pip install pyinstaller`
2. **Missing assets**: Ensure all assets are in the project directory structure
3. **Import errors**: Check that all required modules are available
4. **Large file size**: This is normal - the executable includes Python runtime and all dependencies
5. **"NameError: name 'self' is not defined"**: This was a bug in earlier versions - update to the latest build system
6. **"RuntimeError: input(): lost sys.stdin"**: Fixed in current version with proper error handling for bundled executables

### Build Logs:

The Progress tab shows detailed build logs. If a build fails:
1. Check the error message in the logs
2. Ensure your main scene is set in Project Settings
3. Verify all assets and scripts are accessible
4. Try a debug build to see runtime errors

### Performance:

- **First run**: May be slower as the executable extracts bundled files
- **Subsequent runs**: Should run at normal speed
- **File size**: Expect 50-200MB depending on your game's complexity

## Advanced Configuration

### Custom Build Scripts:

For advanced users, you can directly use the `GameBuilder` class:

```python
from core.build_system import GameBuilder

builder = GameBuilder("path/to/project")
builder.configure_build(
    output_dir="custom/output",
    platform="windows",
    build_type="release",
    one_file=True,
    icon_path="custom_icon.ico"
)
success = builder.build()
```

### Project Settings:

Build settings can be pre-configured in your project's `project.lupine` file under the `export` section:

```json
{
  "export": {
    "platforms": ["windows", "linux", "mac"],
    "icon": "icon.png"
  }
}
```

## Browser Build Limitations

When building for browsers, be aware of these limitations:
- **File Access**: Limited file system access compared to desktop
- **Performance**: May be slower than native desktop builds
- **Dependencies**: Some Python libraries may not work in WebAssembly
- **Audio**: Limited audio format support in browsers
- **Networking**: Browser security restrictions apply

## Future Enhancements

Planned features for future versions:
- Code signing for executables
- Installer generation
- Steam integration
- Mobile platform support (Android/iOS)
- Custom splash screens
- Compression options
- Plugin system for build hooks
- Progressive Web App (PWA) support for browsers
- WebGL optimization for better browser performance
