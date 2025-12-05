#!/bin/bash
# Council Scraper - VPS Deployment Script
# Run this on your DigitalOcean droplet as root

set -e  # Exit on error

echo "=========================================="
echo "Council Scraper - VPS Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: System Update
echo -e "${YELLOW}[1/7] Updating system...${NC}"
apt update && apt upgrade -y

# Step 2: Install Python 3.11
echo -e "${YELLOW}[2/7] Installing Python 3.11...${NC}"
apt install -y python3.11 python3.11-venv python3-pip git curl

# Step 3: Install Playwright system dependencies
echo -e "${YELLOW}[3/7] Installing Playwright dependencies...${NC}"
apt install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 libxshmfence1 \
    fonts-liberation libappindicator3-1 xdg-utils

# Step 4: Create scraper user
echo -e "${YELLOW}[4/7] Creating scraper user...${NC}"
if id "scraper" &>/dev/null; then
    echo "User 'scraper' already exists"
else
    useradd -m -s /bin/bash scraper
fi

# Step 5: Clone/update repository
echo -e "${YELLOW}[5/7] Setting up repository...${NC}"
REPO_DIR="/home/scraper/councilscraper"
if [ -d "$REPO_DIR" ]; then
    echo "Repository exists, pulling latest..."
    cd $REPO_DIR
    sudo -u scraper git pull
else
    echo "Cloning repository..."
    sudo -u scraper git clone https://github.com/oddlyrohit/councilscraper.git $REPO_DIR
fi

# Step 6: Set up Python environment
echo -e "${YELLOW}[6/7] Setting up Python environment...${NC}"
cd $REPO_DIR
if [ ! -d "venv" ]; then
    sudo -u scraper python3.11 -m venv venv
fi
sudo -u scraper bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -e ."

# Step 7: Install Playwright browsers
echo -e "${YELLOW}[7/7] Installing Playwright browsers...${NC}"
sudo -u scraper bash -c "source venv/bin/activate && playwright install chromium"

# Create logs directory
mkdir -p /home/scraper/logs
chown scraper:scraper /home/scraper/logs

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Create .env file: nano /home/scraper/.env"
echo "2. Switch to scraper user: su - scraper"
echo "3. Test a scraper: cd councilscraper && source venv/bin/activate"
echo "4. Set up cron jobs (see scripts/cron_schedule.sh)"
echo ""
