#!/usr/bin/env python3
"""
Test runner script for PNMP monitoring system
"""
import sys
import subprocess


def run_tests():
    """Run all monitoring tests"""
    print("=" * 70)
    print("PNMP Monitoring System - Test Suite")
    print("=" * 70)
    print()
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("ERROR: pytest is not installed")
        print("Please install with: pip install pytest pytest-asyncio")
        return 1
    
    # Run tests
    print("Running tests...")
    print()
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd="."
    )
    
    print()
    print("=" * 70)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
