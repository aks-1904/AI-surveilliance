#!/bin/bash

# Quick Start Script for AI Video Processing Service

echo "=================================================="
echo "AI SURVEILLANCE CO-PILOT - QUICK START"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created - please edit it with your settings"
fi

# Download YOLO model
echo ""
echo "🤖 Checking YOLO model..."
python3 << EOF
from ultralytics import YOLO
print("Downloading YOLO model...")
model = YOLO("yolov8n.pt")
print("✅ Model ready!")
EOF

echo ""
echo "=================================================="
echo "✅ SETUP COMPLETE!"
echo "=================================================="
echo ""
echo "To start the Flask API server:"
echo "  python app.py"
echo ""
echo "To process a video file:"
echo "  python example_file_processing.py"
echo ""
echo "To connect to RTSP camera:"
echo "  python example_rtsp_stream.py"
echo ""
echo "For more information, see README.md"
echo "=================================================="