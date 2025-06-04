#!/usr/bin/env python3
"""
Test script to verify global exception handling is working properly
"""

import sys
import os
import threading
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and set up global exception handling
from core.exception_handler import setup_global_exception_handling
setup_global_exception_handling()

def test_main_thread_exception():
    """Test unhandled exception in main thread"""
    print("Testing main thread exception...")
    time.sleep(1)
    raise ValueError("This is a test exception in the main thread")

def test_thread_exception():
    """Test unhandled exception in a separate thread"""
    print("Testing thread exception...")
    time.sleep(1)
    raise RuntimeError("This is a test exception in a thread")

def test_nested_exception():
    """Test nested exception with multiple stack frames"""
    def inner_function():
        def deeper_function():
            raise ZeroDivisionError("Division by zero in nested function")
        deeper_function()
    
    print("Testing nested exception...")
    time.sleep(1)
    inner_function()

def main():
    """Main test function"""
    print("Exception Handling Test Suite")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python test_exception_handling.py <test_type>")
        print("Test types:")
        print("  main    - Test main thread exception")
        print("  thread  - Test thread exception")
        print("  nested  - Test nested exception")
        print("  all     - Run all tests (sequentially)")
        return 1
    
    test_type = sys.argv[1].lower()
    
    if test_type == "main":
        test_main_thread_exception()
    elif test_type == "thread":
        # Create and start a thread that will raise an exception
        thread = threading.Thread(target=test_thread_exception, name="TestThread")
        thread.start()
        thread.join()
        print("Thread test completed")
    elif test_type == "nested":
        test_nested_exception()
    elif test_type == "all":
        print("Running all tests sequentially...\n")
        
        # Test 1: Nested exception
        print("1. Testing nested exception:")
        try:
            test_nested_exception()
        except:
            pass  # Expected to be handled by global handler
        
        time.sleep(2)
        
        # Test 2: Thread exception
        print("\n2. Testing thread exception:")
        thread = threading.Thread(target=test_thread_exception, name="TestThread")
        thread.start()
        thread.join()
        
        time.sleep(2)
        
        # Test 3: Main thread exception (this will terminate the program)
        print("\n3. Testing main thread exception:")
        test_main_thread_exception()
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
