"""Centralized logging system."""
from __future__ import annotations

import logging
from pathlib import Path

import config


_LOGGER_NAME = "game"


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    """Return a configured logger."""
    root_logger = logging.getLogger(_LOGGER_NAME)

    if not getattr(root_logger, "_game_configured", False):
        config.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

        root_logger.setLevel(logging.DEBUG)
        root_logger.propagate = False

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(
            config.LOG_FILE, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO) 
        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger._game_configured = True

    if name == _LOGGER_NAME:
        return root_logger

    if name.startswith(f"{_LOGGER_NAME}."):
        return logging.getLogger(name)

    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
