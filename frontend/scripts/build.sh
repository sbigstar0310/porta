#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting Flutter Web Build Process..."

# Check current directory is frontend
if [ "$(basename "$(pwd)")" != "frontend" ]; then
    echo "❌ Error: Current directory is not frontend"
    echo "Please run this script from the frontend directory"
    exit 1
fi

# Function to setup Flutter from GitHub
setup_flutter() {
    echo "📥 Flutter not found, cloning from GitHub..."
    cd ..
    
    # Remove existing flutter directory if it exists
    if [ -d "flutter" ]; then
        echo "🗑️  Removing existing Flutter directory..."
        rm -rf flutter
    fi
    
    # Clone Flutter with specific stable branch
    echo "⬇️  Cloning Flutter (stable branch)..."
    git clone https://github.com/flutter/flutter.git -b stable --depth 1
    
    # Add Flutter to PATH for this session
    export PATH="$PWD/flutter/bin:$PATH"
    
    # Return to frontend directory
    cd frontend
    
    echo "✅ Flutter setup completed"
}

# Function to build with Flutter
build_flutter() {
    local flutter_cmd=$1
    
    echo "🔍 Running Flutter doctor..."
    $flutter_cmd doctor --android-licenses || echo "⚠️  Some licenses not accepted, continuing..."
    
    echo "🧹 Cleaning previous builds..."
    $flutter_cmd clean
    
    echo "🌐 Enabling web platform..."
    $flutter_cmd config --enable-web
    
    echo "🏗️  Building Flutter web app..."
    
    # 환경 변수가 설정되어 있으면 dart-define으로 전달
    if [ ! -z "$API_URL" ]; then
        echo "📡 Using API_URL from environment: $API_URL"
        $flutter_cmd build web --profile \
        --source-maps \
        --no-wasm-dry-run \
        --dart-define=API_URL="$API_URL"
    else
        echo "⚠️  No API_URL environment variable found, using default"
        $flutter_cmd build web --profile \
        --source-maps \
        --no-wasm-dry-run
    fi
    
    # Check if build was successful
    if [ -d "build/web" ]; then
        echo "✅ Build completed successfully!"
        echo "📁 Build output: $(pwd)/build/web"
        echo "📊 Build size: $(du -sh build/web | cut -f1)"
    else
        echo "❌ Build failed - build/web directory not found"
        exit 1
    fi
}

make_env() {
    # check .env file exists
    if [ ! -f ".env" ]; then
        # make .env file
        touch .env
    fi
}

# Check if flutter is installed
if ! command -v flutter &> /dev/null; then
    setup_flutter
    # make .env file
    make_env
    # Use the cloned Flutter
    build_flutter "../flutter/bin/flutter"
else
    echo "✅ Flutter found: $(flutter --version | head -n 1)"
    # Use system Flutter
    build_flutter "flutter"
fi

echo "🎉 Flutter web build process completed!"
