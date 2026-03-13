import logging
import sys
from datetime import datetime, timezone
import fcntl
from pathlib import Path

from app.scripts.import_pauper_tournaments import import_pauper_tournaments
from app.scripts.process_moxfield_decklists import process_unprocessed_decklists
from app.scripts.classify_decks import classify_all_processed_decks

LOCK_PATH = Path("/tmp/spicerack_sync.lock")

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


def run_spicerack_sync(days: int = 2) -> int:
  lock_file = LOCK_PATH.open("w")

  try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except BlockingIOError:
    logger.warning("Another Spicerack sync is already running, exiting")
    return 0

  logger.info("Starting Spicerack sync")
  logger.info("UTC time: %s", datetime.now(timezone.utc).isoformat())

  try:
    import_pauper_tournaments(days)
    logger.info("Spicerack sync completed successfully\n")

    process_unprocessed_decklists()
    logger.info("Decklists successfully fetched\n")

    classify_all_processed_decks(overwrite=False)
    logger.info("Decklists successfully classified\n")

  except Exception:
    logger.exception("An element of the synchronisation failed")
    return 1
  finally:
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()

  return 0


def main() -> int:
  return run_spicerack_sync()

if __name__ == "__main__":
  sys.exit(main())