"""Central logging configuration (console + rotating log file)."""

import logging
import logging.handlers
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level=logging.INFO, log_dir="logs"):
    root = logging.getLogger("vdsim")
    if root.handlers:
        return root
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT, "%H:%M:%S"))
    root.addHandler(console)

    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            Path(log_dir) / "vdsim.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(file_handler)
    return root


def get_logger(name):
    return logging.getLogger(f"vdsim.{name}")
