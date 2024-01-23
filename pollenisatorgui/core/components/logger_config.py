import logging
import sys
import os
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                              "%Y-%m-%d %H:%M:%S")
log_path = os.path.expanduser("~/.pollenisator")
os.makedirs(log_path, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_path, 'debug.log'), encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger.addHandler(handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Exception", exc_info=(exc_type, exc_value, exc_traceback))
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception