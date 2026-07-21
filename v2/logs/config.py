from loguru import logger
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger.remove()
logger.add(
    "v2/logs/zookout_ai.log",
    level=LOG_LEVEL,
    rotation="10 MB",
    retention="7 days",
    backtrace=True,
    diagnose=True,
)
