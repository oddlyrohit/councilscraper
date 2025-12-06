#!/bin/bash
# Council Scraper - Cron Schedule Setup with Monitoring
# Run this as the 'scraper' user on DigitalOcean

# Scraping Schedule (All times in AEST/Sydney timezone)
# =====================================================
#
# TIER 1 (Daily) - ~19 major metro councils
#   - 6:00 AM AEST daily
#   - Highest priority, most DA activity
#
# TIER 2 (Every 3 days) - ~42 suburban councils
#   - Split into 3 batches, one batch per day
#   - 9:00 AM AEST
#
# TIER 3 (Weekly) - ~53 regional councils
#   - Split into 7 batches, one batch per day
#   - 2:00 PM AEST
#
# TIER 4 (Weekly) - ~62 smaller councils
#   - Split into 7 batches, one batch per day
#   - 3:00 PM AEST
#
# TIER 5 (Weekly) - ~74 rural councils
#   - Split into 7 batches, one batch per day
#   - 4:00 PM AEST
#
# MONITORING
#   - Daily digest email at 8:00 PM AEST
#   - Immediate email alerts on failures
#
# =====================================================

SCRAPER_DIR="/home/scraper/councilscraper"
LOG_DIR="/home/scraper/logs"
VENV="$SCRAPER_DIR/venv/bin/python"
RUNNER="$SCRAPER_DIR/scripts/run_with_monitoring.py"

# Ensure log directory exists
mkdir -p $LOG_DIR

# Set timezone to Australia/Sydney
export TZ="Australia/Sydney"

# Create cron file
CRON_FILE="/tmp/scraper_cron"

cat > $CRON_FILE << 'CRON'
# Council Scraper Schedule with Monitoring
# All times in AEST (Australia/Sydney)
SHELL=/bin/bash
TZ=Australia/Sydney
PATH=/usr/local/bin:/usr/bin:/bin

# Environment file
ENV_FILE=/home/scraper/.env

# ============================================
# TIER 1: Daily at 6:00 AM AEST
# Major metro councils (~19 councils)
# ============================================
0 6 * * * cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 1 --concurrent 3 >> /home/scraper/logs/tier1_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# TIER 2: Every day at 9:00 AM AEST
# Rotates through 3 batches (each council scraped every 3 days)
# ============================================
# Batch 1: Days 1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31
0 9 1,4,7,10,13,16,19,22,25,28,31 * * cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 2 --batch 1 --concurrent 3 >> /home/scraper/logs/tier2_b1_$(date +\%Y\%m\%d).log 2>&1

# Batch 2: Days 2, 5, 8, 11, 14, 17, 20, 23, 26, 29
0 9 2,5,8,11,14,17,20,23,26,29 * * cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 2 --batch 2 --concurrent 3 >> /home/scraper/logs/tier2_b2_$(date +\%Y\%m\%d).log 2>&1

# Batch 3: Days 3, 6, 9, 12, 15, 18, 21, 24, 27, 30
0 9 3,6,9,12,15,18,21,24,27,30 * * cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 2 --batch 3 --concurrent 3 >> /home/scraper/logs/tier2_b3_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# TIER 3: Every day at 2:00 PM AEST
# Rotates through 7 batches (each council scraped weekly)
# ============================================
0 14 * * 1 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 1 --concurrent 3 >> /home/scraper/logs/tier3_b1_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 2 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 2 --concurrent 3 >> /home/scraper/logs/tier3_b2_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 3 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 3 --concurrent 3 >> /home/scraper/logs/tier3_b3_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 4 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 4 --concurrent 3 >> /home/scraper/logs/tier3_b4_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 5 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 5 --concurrent 3 >> /home/scraper/logs/tier3_b5_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 6 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 6 --concurrent 3 >> /home/scraper/logs/tier3_b6_$(date +\%Y\%m\%d).log 2>&1
0 14 * * 0 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 3 --batch 7 --concurrent 3 >> /home/scraper/logs/tier3_b7_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# TIER 4: Every day at 3:00 PM AEST
# Rotates through 7 batches (each council scraped weekly)
# ============================================
0 15 * * 1 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 1 --concurrent 3 >> /home/scraper/logs/tier4_b1_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 2 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 2 --concurrent 3 >> /home/scraper/logs/tier4_b2_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 3 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 3 --concurrent 3 >> /home/scraper/logs/tier4_b3_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 4 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 4 --concurrent 3 >> /home/scraper/logs/tier4_b4_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 5 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 5 --concurrent 3 >> /home/scraper/logs/tier4_b5_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 6 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 6 --concurrent 3 >> /home/scraper/logs/tier4_b6_$(date +\%Y\%m\%d).log 2>&1
0 15 * * 0 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 4 --batch 7 --concurrent 3 >> /home/scraper/logs/tier4_b7_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# TIER 5: Every day at 4:00 PM AEST
# Rotates through 7 batches (each council scraped weekly)
# ============================================
0 16 * * 1 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 1 --concurrent 3 >> /home/scraper/logs/tier5_b1_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 2 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 2 --concurrent 3 >> /home/scraper/logs/tier5_b2_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 3 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 3 --concurrent 3 >> /home/scraper/logs/tier5_b3_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 4 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 4 --concurrent 3 >> /home/scraper/logs/tier5_b4_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 5 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 5 --concurrent 3 >> /home/scraper/logs/tier5_b5_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 6 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 6 --concurrent 3 >> /home/scraper/logs/tier5_b6_$(date +\%Y\%m\%d).log 2>&1
0 16 * * 0 cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --tier 5 --batch 7 --concurrent 3 >> /home/scraper/logs/tier5_b7_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# MONITORING
# ============================================
# Daily digest email at 8:00 PM AEST
0 20 * * * cd /home/scraper/councilscraper && source venv/bin/activate && source ~/.env && python scripts/run_with_monitoring.py --digest >> /home/scraper/logs/digest_$(date +\%Y\%m\%d).log 2>&1

# ============================================
# MAINTENANCE
# ============================================
# Clean logs older than 30 days (daily at midnight)
0 0 * * * find /home/scraper/logs -name "*.log" -mtime +30 -delete

# Pull latest code (weekly on Sunday at 5 AM)
0 5 * * 0 cd /home/scraper/councilscraper && git pull >> /home/scraper/logs/git_pull.log 2>&1

CRON

# Install the cron file
crontab $CRON_FILE

echo "Cron schedule installed. Current crontab:"
echo "==========================================="
crontab -l
echo "==========================================="
echo ""
echo "Schedule Summary (AEST):"
echo "  - Tier 1: Daily at 6:00 AM (~19 councils)"
echo "  - Tier 2: Daily at 9:00 AM (rotating, ~14 councils/day)"
echo "  - Tier 3: Daily at 2:00 PM (rotating, ~8 councils/day)"
echo "  - Tier 4: Daily at 3:00 PM (rotating, ~9 councils/day)"
echo "  - Tier 5: Daily at 4:00 PM (rotating, ~11 councils/day)"
echo "  - Daily digest: 8:00 PM"
echo ""
echo "Total: 250 councils covered"
echo ""
echo "Email alerts: rohit.trivedi81@gmail.com"
echo "Logs stored in: $LOG_DIR"
