# Global Exception Handling in Lupine Engine

The Lupine Engine now includes comprehensive global exception handling that ensures all unhandled exceptions are properly logged with full tracebacks, regardless of thread, context, or execution environment.

## Features

### 1. Main Thread Exception Handling
- Catches all unhandled exceptions in the main thread
- Provides detailed error messages with full stack traces
- Includes timestamp and context information

### 2. Threading Exception Handling
- Catches unhandled exceptions in all threads (Python 3.8+)
- Identifies the thread name and ID where the exception occurred
- Maintains full traceback information across thread boundaries

### 3. Signal Handling
- Graceful handling of system signals (SIGINT, SIGTERM, etc.)
- Provides stack traces when signals are received
- Platform-specific signal support (Windows SIGBREAK, Unix SIGHUP)

### 4. PyQt6 Integration
- Custom Qt message handler for GUI-related errors
- Captures Qt critical and fatal messages
- Integrates with the global exception logging system

### 5. Consistent Error Reporting
- All exceptions are formatted consistently
- Both console output and logging system integration
- Detailed context information for debugging

## How It Works

### Automatic Setup
The exception handling is automatically set up when the `core` module is imported:

```python
# This happens automatically when importing core
from core.exception_handler import setup_global_exception_handling
setup_global_exception_handling()
```

### Entry Points
The system is initialized at all major entry points:

1. **Main Editor** (`main.py`) - PyQt6 application
2. **Game Runner** (`core/simple_game_runner.py`) - Standalone game execution
3. **Core Module** (`core/__init__.py`) - Automatic setup

### Exception Format
All unhandled exceptions are displayed in this format:

```
================================================================================
UNHANDLED EXCEPTION IN [CONTEXT]
================================================================================
Exception Type: ExceptionClassName
Exception Message: Exception message here
Timestamp: 2025-06-04 16:47:06

Full Traceback:
[Complete Python traceback with file names, line numbers, and code context]
================================================================================
```

## Testing

A test script is provided to verify the exception handling works correctly:

```bash
# Test main thread exceptions
python test_exception_handling.py main

# Test thread exceptions  
python test_exception_handling.py thread

# Test nested exceptions
python test_exception_handling.py nested

# Run all tests
python test_exception_handling.py all
```

## Integration with Existing Code

### Enhanced Exception Handling
Many existing exception handlers throughout the codebase have been enhanced to include full tracebacks:

- **Game Engine** (`core/game_engine.py`) - Game loop and system initialization
- **Python Runtime** (`core/python_runtime.py`) - Script execution
- **Physics System** (`core/physics.py`) - Collision callbacks
- **Node System** (`nodes/base/Node.py`) - Lifecycle methods
- **Timer System** (`nodes/base/Timer.py`) - Timeout callbacks
- **Game Runner** (`editor/game_runner.py`) - Process management

### Decorator Support
A decorator is available for adding exception handling to specific contexts:

```python
from core.exception_handler import handle_exception_in_context

@handle_exception_in_context("Custom Context")
def my_function():
    # Function code here
    pass
```

## Benefits

1. **No More Silent Failures**: All exceptions are caught and reported
2. **Better Debugging**: Full stack traces with context information
3. **Thread Safety**: Exceptions in any thread are properly handled
4. **Consistent Reporting**: Uniform error format across the entire engine
5. **Signal Handling**: Graceful shutdown on system signals
6. **PyQt Integration**: GUI errors are properly captured

## Configuration

The exception handler can be customized by modifying `core/exception_handler.py`:

- **Logging Level**: Change the logging level for exception messages
- **Output Format**: Customize the exception message format
- **Signal Handlers**: Add or remove signal handling
- **Context Information**: Add additional context to exception reports

## Backward Compatibility

The global exception handling system is designed to be completely backward compatible:

- Existing try/catch blocks continue to work normally
- Original exception hooks are preserved and called when appropriate
- No changes required to existing code

## Performance Impact

The exception handling system has minimal performance impact:

- Only activates when exceptions occur
- Lightweight signal handlers
- Efficient logging system
- No impact on normal execution flow

This comprehensive exception handling system ensures that developers will never encounter silent failures or mysterious crashes without proper error information.
