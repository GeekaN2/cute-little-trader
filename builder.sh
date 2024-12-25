#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🐰 Building Cute Little Trader...${NC}"

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}❌ PyInstaller not found. Installing...${NC}"
    pip install pyinstaller
fi

echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Clean previous builds
echo -e "${BLUE}🧹 Cleaning previous builds...${NC}"
rm -rf build dist

# Build the executable
echo -e "${BLUE}🔨 Building executable...${NC}"
pyinstaller --clean bot.spec

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo -e "${BLUE}📁 Executable is in: dist/cute-little-trader${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi