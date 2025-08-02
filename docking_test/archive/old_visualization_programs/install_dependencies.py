#!/usr/bin/env python3
"""
Install dependencies for molecular visualization
"""

import subprocess
import sys

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def main():
    """Install all required packages"""
    
    print("📦 Installing molecular visualization dependencies...")
    print("=" * 50)
    
    # List of required packages
    packages = [
        'matplotlib',
        'plotly',
        'py3dmol',
        'numpy',
        'pandas'
    ]
    
    successful_installs = []
    failed_installs = []
    
    for package in packages:
        print(f"\n🔧 Installing {package}...")
        if install_package(package):
            successful_installs.append(package)
        else:
            failed_installs.append(package)
    
    print(f"\n📊 Installation Summary:")
    print(f"✅ Successful: {len(successful_installs)} packages")
    for pkg in successful_installs:
        print(f"  - {pkg}")
    
    if failed_installs:
        print(f"\n❌ Failed: {len(failed_installs)} packages")
        for pkg in failed_installs:
            print(f"  - {pkg}")
    
    print(f"\n🎉 Installation complete!")
    return len(failed_installs) == 0

if __name__ == "__main__":
    main()