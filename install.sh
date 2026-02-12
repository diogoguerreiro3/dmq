#!/bin/bash
set -e

echo "=========================================="
echo "  DMQ - Disney Music Quiz"
echo "  Installation Script (Linux/macOS)"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ------------------------------------------------------------
# 1) Check for Python
# ------------------------------------------------------------
echo "[1/6] Checking for Python..."

if ! command -v python3 &> /dev/null; then
  echo -e "${RED}[ERROR] Python 3 was not found in PATH.${NC}"
  echo "Please install Python 3.10+"
  exit 1
fi

python3 --version
echo ""

# ------------------------------------------------------------
# 2) Create / ensure virtual environment
# ------------------------------------------------------------
echo "[2/6] Preparing virtual environment..."

if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
  echo "Virtual environment already exists. OK."
else
  python3 -m venv venv
  echo -e "${GREEN}Virtual environment created.${NC}"
fi

echo ""

# ------------------------------------------------------------
# 3) Always use venv python (avoid system/user installs)
# ------------------------------------------------------------
VENV_PYTHON="./venv/bin/python"

# ------------------------------------------------------------
# 4) Upgrade pip, setuptools, wheel INSIDE venv
# ------------------------------------------------------------
echo "[3/6] Updating pip, setuptools, and wheel in venv..."
$VENV_PYTHON -m pip install -U pip setuptools wheel
echo ""

# ------------------------------------------------------------
# 5) Install dependencies
# ------------------------------------------------------------
if [ ! -f "requirements.txt" ]; then
  echo -e "${RED}[ERROR] requirements.txt not found in: $(pwd)${NC}"
  exit 1
fi

echo "[4/6] Installing dependencies from requirements.txt..."
$VENV_PYTHON -m pip install -r requirements.txt
echo ""

# ------------------------------------------------------------
# 6) Check for ffmpeg
# ------------------------------------------------------------
echo "[5/6] Checking for ffmpeg..."

if ! command -v ffmpeg &> /dev/null; then
  echo -e "${YELLOW}[WARN] ffmpeg was NOT found in PATH.${NC}"
  echo ""
  echo "Install it with:"
  echo "  Ubuntu/Debian:"
  echo "    sudo apt update && sudo apt install ffmpeg"
  echo ""
  echo "  macOS (Homebrew):"
  echo "    brew install ffmpeg"
  echo ""
  echo "  Fedora:"
  echo "    sudo dnf install ffmpeg"
else
  echo -e "${GREEN}ffmpeg OK:${NC}"
  ffmpeg -version | head -n 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Installation completed!${NC}"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  ./run.sh"
