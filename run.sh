#!/bin/bash
set -e

echo "=========================================="
echo "  DMQ - Disney Music Quiz"
echo "  Starting Application..."
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ------------------------------------------------------------
# 1) Check venv exists
# ------------------------------------------------------------
if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then
  echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
  echo "Please run ./install.sh first."
  exit 1
fi

# ------------------------------------------------------------
# 2) Activate venv
# ------------------------------------------------------------
echo "[1/2] Activating virtual environment..."
source venv/bin/activate

# ------------------------------------------------------------
# 3) Run app
# ------------------------------------------------------------
echo ""
echo "[2/2] Starting Flask + SocketIO application..."
echo ""
echo "=========================================="
echo -e "${GREEN}Server running at: ${CYAN}http://localhost:44444${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo "=========================================="
echo ""

python app.py

# (If the script reaches here, deactivate)
deactivate
