#!/bin/bash
# Start script for Molecular Docking Web Interface

echo "=== Molecular Docking Web Interface ==="
echo ""

# Use the Python with PyMOL
PYTHON_CMD="/Users/wenzhenxiong/Documents/DevProj/proteindance/.conda/bin/python"

if [ -f "$PYTHON_CMD" ]; then
    echo "✓ Using Python with PyMOL: $PYTHON_CMD"
else
    echo "✗ PyMOL Python not found at: $PYTHON_CMD"
    echo "Please install PyMOL with: pip install pymol"
    exit 1
fi

# Test PyMOL availability
echo "Testing PyMOL availability..."
if $PYTHON_CMD -c "import pymol; print('✓ PyMOL available')" 2>/dev/null; then
    echo "✓ PyMOL is working"
else
    echo "✗ PyMOL not available, installing..."
    $PYTHON_CMD -m pip install pymol
fi

# Check Flask
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "Installing Flask and Flask-CORS..."
    $PYTHON_CMD -m pip install flask flask-cors
fi

# Make scripts executable and use correct Python
chmod +x docking_web_api.py
chmod +x molecular_docking.py  
chmod +x docking_visualization.py
chmod +x run_docking_pipeline.py

# Start the web API server
echo ""
echo "Starting web API server with PyMOL support..."
echo "Interface will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the API directly with the correct Python
$PYTHON_CMD docking_web_api.py