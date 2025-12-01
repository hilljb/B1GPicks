#!/usr/bin/env python
"""
Verification script to check if the B1GPicks package is properly installed.
Run this AFTER creating and activating the conda environment.

Usage:
    conda activate b1gpicks
    python verify_setup.py
"""

import sys
from datetime import datetime

def check_imports():
    """Check if required packages can be imported."""
    print("Checking imports...")
    required_packages = [
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4'),
        ('lxml', 'lxml'),
        ('pytest', 'pytest'),
    ]
    
    all_ok = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_b1gpicks():
    """Check if b1gpicks package is installed."""
    print("\nChecking b1gpicks package...")
    try:
        from b1gpicks import Scraper
        print("  ✓ b1gpicks.Scraper imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import b1gpicks: {e}")
        print("\n  Make sure you:")
        print("    1. Created the conda environment: conda env create -f environment.yml")
        print("    2. Activated it: conda activate b1gpicks")
        return False


def test_basic_functionality():
    """Test basic scraper functionality."""
    print("\nTesting basic functionality...")
    try:
        from b1gpicks import Scraper
        
        # Test initialization
        scraper = Scraper()
        print("  ✓ Scraper initialized")
        
        # Check user agent
        if "Macintosh" in scraper.user_agent and "Chrome" in scraper.user_agent:
            print("  ✓ User agent configured correctly")
        else:
            print("  ⚠ User agent may not be optimal")
        
        scraper.close()
        
        # Test URL generation
        test_date = datetime(2025, 12, 1)
        url = Scraper.get_schedule_url(test_date)
        expected = "https://www.espn.com/mens-college-basketball/schedule/_/date/20251201/group/7"
        if url == expected:
            print("  ✓ URL generation works correctly")
        else:
            print(f"  ✗ URL generation failed")
            print(f"    Expected: {expected}")
            print(f"    Got: {url}")
            return False
        
        # Test context manager
        with Scraper() as s:
            pass
        print("  ✓ Context manager works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification function."""
    print("=" * 70)
    print("B1GPicks Package Verification")
    print("=" * 70)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print()
    
    # Run checks
    imports_ok = check_imports()
    package_ok = check_b1gpicks()
    
    if not (imports_ok and package_ok):
        print("\n" + "=" * 70)
        print("SETUP INCOMPLETE")
        print("=" * 70)
        print("\nPlease follow the instructions in SETUP.md")
        sys.exit(1)
    
    functionality_ok = test_basic_functionality()
    
    print("\n" + "=" * 70)
    if functionality_ok:
        print("✓ ALL CHECKS PASSED!")
        print("=" * 70)
        print("\nYour environment is ready! Next steps:")
        print("  1. Run example: python examples/scrape_predictors.py")
        print("  2. Run tests: pytest")
        print("  3. Start building your own scripts!")
    else:
        print("⚠ SOME CHECKS FAILED")
        print("=" * 70)
        print("\nThe package is installed but some functionality may not work correctly.")
        sys.exit(1)


if __name__ == "__main__":
    main()

