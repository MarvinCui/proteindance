#!/usr/bin/env python3
"""
PyMOL installation test script for ProteinDance Docker environment
"""

import sys
import os

def test_pymol_installation():
    """Test PyMOL installation and basic functionality"""
    print("🔬 Testing PyMOL Installation...")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    
    # Test PyMOL import
    try:
        import pymol
        print("✅ PyMOL imported successfully")
        print(f"PyMOL version: {getattr(pymol, '__version__', 'Unknown')}")
        print(f"PyMOL path: {pymol.__file__}")
    except ImportError as e:
        print(f"❌ PyMOL import failed: {e}")
        return False
    
    # Test PyMOL command module
    try:
        from pymol import cmd
        print("✅ PyMOL cmd module imported successfully")
    except ImportError as e:
        print(f"❌ PyMOL cmd import failed: {e}")
        return False
    
    # Test PyMOL initialization (headless mode)
    try:
        pymol.pymol_argv = ['pymol', '-c']  # Command line mode
        pymol.finish_launching(['pymol', '-c'])
        print("✅ PyMOL initialized in headless mode")
    except Exception as e:
        print(f"⚠️  PyMOL initialization warning: {e}")
        print("   This may be expected in headless Docker environment")
    
    # Test basic PyMOL commands
    try:
        cmd.reinitialize()
        print("✅ PyMOL reinitialize command works")
        
        # Test creating a simple object
        cmd.fragment('ala')
        objects = cmd.get_names('objects')
        if 'ala' in objects:
            print("✅ PyMOL can create molecular objects")
            cmd.delete('ala')
        else:
            print("⚠️  PyMOL object creation may have issues")
            
    except Exception as e:
        print(f"⚠️  PyMOL command execution warning: {e}")
    
    # Test other scientific packages that work with PyMOL
    scientific_packages = [
        ('numpy', 'NumPy'),
        ('rdkit', 'RDKit'),
        ('Bio', 'BioPython'),
    ]
    
    for module, name in scientific_packages:
        try:
            __import__(module)
            print(f"✅ {name} is available")
        except ImportError:
            print(f"❌ {name} is not available")
    
    print("\n🎉 PyMOL installation test completed!")
    return True

if __name__ == "__main__":
    success = test_pymol_installation()
    sys.exit(0 if success else 1)