"""
Zookout AI Telegram Bot Root Entrypoint.
Delegates directly to v2.telegram.bot to ensure production environments (such as Railway)
always execute the V2 AI Deal Concierge engine regardless of launch command.
"""

import sys
import logging
from pathlib import Path

# Add project root directory to python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger(__name__)
logger.info(f"Launching Zookout AI Deal Concierge from root bot.py...")

from v2.telegram.bot import main

if __name__ == "__main__":
    main()