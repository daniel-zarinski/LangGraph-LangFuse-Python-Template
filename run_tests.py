#!/usr/bin/env python3
"""Test runner script for the FastAPI LangGraph Agent application.

This script provides a convenient way to run different test suites
with various options.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code.
    
    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does
        
    Returns:
        Exit code from the command
    """
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
        return result.returncode
    except KeyboardInterrupt:
        print(f"\n⚠️  {description} interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return 1


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for FastAPI LangGraph Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --fast             # Skip slow tests
  python run_tests.py --file tests/unit/test_sanitization.py  # Run specific file
        """
    )
    
    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit", 
        action="store_true", 
        help="Run only unit tests"
    )
    test_group.add_argument(
        "--integration", 
        action="store_true", 
        help="Run only integration tests"
    )
    test_group.add_argument(
        "--file", 
        type=str, 
        help="Run tests from specific file"
    )
    
    # Test behavior options
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Run tests with verbose output"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Skip slow tests (exclude tests marked as 'slow')"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Drop into debugger on test failures"
    )
    parser.add_argument(
        "--stop-on-first", "-x", 
        action="store_true", 
        help="Stop on first test failure"
    )
    parser.add_argument(
        "--parallel", "-n", 
        type=int, 
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["uv", "run", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.append("tests/integration/")
    elif args.file:
        if not Path(args.file).exists():
            print(f"❌ Test file not found: {args.file}")
            return 1
        cmd.append(args.file)
    else:
        cmd.append("tests/")
    
    # Add behavior options
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.debug:
        cmd.append("--pdb")
    
    if args.stop_on_first:
        cmd.append("-x")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Determine description based on options
    description_parts = []
    if args.unit:
        description_parts.append("unit tests")
    elif args.integration:
        description_parts.append("integration tests")
    elif args.file:
        description_parts.append(f"tests from {args.file}")
    else:
        description_parts.append("all tests")
    
    if args.coverage:
        description_parts.append("with coverage")
    if args.fast:
        description_parts.append("(fast mode)")
    
    description = f"Running {' '.join(description_parts)}"
    
    # Run the tests
    exit_code = run_command(cmd, description)
    
    # Show coverage report if generated
    if args.coverage and exit_code == 0:
        coverage_html = Path("htmlcov/index.html")
        if coverage_html.exists():
            print(f"\n📊 Coverage report generated: {coverage_html.absolute()}")
            print("Open the HTML file in your browser to view the detailed report.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
