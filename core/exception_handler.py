"""
Global Exception Handler for Lupine Engine
Ensures all unhandled exceptions are properly logged with full tracebacks
regardless of thread, context, or execution environment.
"""

import sys
import threading
import traceback
import signal
import logging
from typing import Optional, Callable, Any
from datetime import datetime
import os


class LupineExceptionHandler:
    """Centralized exception handler for the Lupine Engine"""
    
    def __init__(self):
        self.original_excepthook = sys.excepthook
        self.original_threading_excepthook = getattr(threading, 'excepthook', None)
        self.logger = self._setup_logger()
        self._setup_complete = False
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for exception handling"""
        logger = logging.getLogger('lupine_exceptions')
        logger.setLevel(logging.ERROR)
        
        # Create console handler if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.ERROR)
            
            # Create formatter
            formatter = logging.Formatter(
                '[%(asctime)s] [EXCEPTION] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def handle_exception(self, exc_type, exc_value, exc_traceback, context: str = "Main Thread"):
        """Handle an unhandled exception with full traceback"""
        if exc_type is KeyboardInterrupt:
            # Handle keyboard interrupt gracefully
            print(f"\n[{context}] Interrupted by user (Ctrl+C)")
            return
            
        # Format the exception with full traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)
        
        # Create detailed error message
        error_msg = f"""
{'='*80}
UNHANDLED EXCEPTION IN {context.upper()}
{'='*80}
Exception Type: {exc_type.__name__}
Exception Message: {str(exc_value)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Full Traceback:
{tb_text}
{'='*80}
"""
        
        # Print to stderr immediately
        print(error_msg, file=sys.stderr, flush=True)
        
        # Also log it
        self.logger.error(error_msg)
        
        # Call original handler if it exists (for compatibility)
        if self.original_excepthook and self.original_excepthook != sys.__excepthook__:
            try:
                self.original_excepthook(exc_type, exc_value, exc_traceback)
            except:
                pass  # Don't let the exception handler itself crash
    
    def handle_threading_exception(self, args):
        """Handle unhandled exceptions in threads (Python 3.8+)"""
        exc_type = args.exc_type
        exc_value = args.exc_value
        exc_traceback = args.exc_traceback
        thread = args.thread
        
        context = f"Thread '{thread.name}' (ID: {thread.ident})"
        self.handle_exception(exc_type, exc_value, exc_traceback, context)
        
        # Call original threading excepthook if it exists
        if self.original_threading_excepthook:
            try:
                self.original_threading_excepthook(args)
            except:
                pass
    
    def handle_signal(self, signum, frame):
        """Handle system signals that might cause crashes"""
        signal_names = {
            signal.SIGTERM: "SIGTERM",
            signal.SIGINT: "SIGINT",
        }
        
        # Add platform-specific signals
        if hasattr(signal, 'SIGBREAK'):
            signal_names[signal.SIGBREAK] = "SIGBREAK"
        if hasattr(signal, 'SIGHUP'):
            signal_names[signal.SIGHUP] = "SIGHUP"
            
        signal_name = signal_names.get(signum, f"Signal {signum}")
        
        print(f"\n[SIGNAL] Received {signal_name}, shutting down gracefully...", file=sys.stderr)
        
        # Try to get a stack trace of where we were when the signal occurred
        if frame:
            print("\nStack trace at signal:", file=sys.stderr)
            traceback.print_stack(frame, file=sys.stderr)
        
        # Exit gracefully
        sys.exit(1)
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGINT, self.handle_signal)
            signal.signal(signal.SIGTERM, self.handle_signal)
            
            # Platform-specific signals
            if hasattr(signal, 'SIGBREAK'):  # Windows
                signal.signal(signal.SIGBREAK, self.handle_signal)
            if hasattr(signal, 'SIGHUP'):  # Unix
                signal.signal(signal.SIGHUP, self.handle_signal)
                
        except (OSError, ValueError) as e:
            # Some signals might not be available on all platforms
            print(f"Warning: Could not set up some signal handlers: {e}", file=sys.stderr)
    
    def setup_pyqt_exception_handling(self):
        """Set up exception handling for PyQt applications"""
        try:
            from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
            
            def qt_message_handler(msg_type, context, message):
                """Handle Qt messages and errors"""
                msg_types = {
                    QtMsgType.QtDebugMsg: "DEBUG",
                    QtMsgType.QtWarningMsg: "WARNING", 
                    QtMsgType.QtCriticalMsg: "CRITICAL",
                    QtMsgType.QtFatalMsg: "FATAL",
                    QtMsgType.QtInfoMsg: "INFO"
                }
                
                level = msg_types.get(msg_type, "UNKNOWN")
                
                if msg_type in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                    error_msg = f"""
[QT {level}] {message}
Context: {context.file}:{context.line} in {context.function}
Category: {context.category}
"""
                    print(error_msg, file=sys.stderr, flush=True)
                    self.logger.error(error_msg)
                else:
                    print(f"[QT {level}] {message}", file=sys.stderr)
            
            qInstallMessageHandler(qt_message_handler)
            
        except ImportError:
            # PyQt6 not available, skip Qt-specific handling
            pass
        except Exception as e:
            print(f"Warning: Could not set up PyQt exception handling: {e}", file=sys.stderr)


# Global instance
_global_exception_handler: Optional[LupineExceptionHandler] = None


def setup_global_exception_handling() -> LupineExceptionHandler:
    """Set up global exception handling for the entire application"""
    global _global_exception_handler
    
    if _global_exception_handler is not None and _global_exception_handler._setup_complete:
        return _global_exception_handler
    
    _global_exception_handler = LupineExceptionHandler()
    
    # Set up main thread exception handling
    sys.excepthook = _global_exception_handler.handle_exception
    
    # Set up threading exception handling (Python 3.8+)
    if hasattr(threading, 'excepthook'):
        threading.excepthook = _global_exception_handler.handle_threading_exception
    
    # Set up signal handlers
    _global_exception_handler.setup_signal_handlers()
    
    # Set up PyQt exception handling
    _global_exception_handler.setup_pyqt_exception_handling()
    
    _global_exception_handler._setup_complete = True
    
    print("[OK] Global exception handling initialized", file=sys.stderr)
    return _global_exception_handler


def get_exception_handler() -> Optional[LupineExceptionHandler]:
    """Get the global exception handler instance"""
    return _global_exception_handler


def handle_exception_in_context(context: str):
    """Decorator to handle exceptions in a specific context"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if _global_exception_handler:
                    _global_exception_handler.handle_exception(
                        type(e), e, e.__traceback__, context
                    )
                else:
                    # Fallback if global handler not set up
                    print(f"[{context}] Unhandled exception: {e}", file=sys.stderr)
                    traceback.print_exc()
                raise
        return wrapper
    return decorator


def log_exception(exception: Exception, context: str = "Manual"):
    """Manually log an exception with the global handler"""
    if _global_exception_handler:
        _global_exception_handler.handle_exception(
            type(exception), exception, exception.__traceback__, context
        )
    else:
        print(f"[{context}] Exception: {exception}", file=sys.stderr)
        traceback.print_exc()


def is_exception_handling_active() -> bool:
    """Check if global exception handling is active"""
    return _global_exception_handler is not None and _global_exception_handler._setup_complete
