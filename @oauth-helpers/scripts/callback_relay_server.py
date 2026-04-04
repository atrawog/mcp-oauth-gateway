#!/usr/bin/env python3
"""Run the callback relay FastAPI service."""

import logging
import os

import uvicorn

try:
    from scripts.callback_relay import create_app
except ModuleNotFoundError:
    from callback_relay import create_app


def main() -> None:
    """Launch the callback relay service."""
    log_level = os.getenv("LOG_LEVEL", "info")
    host = os.getenv("CALLBACK_RELAY_HOST", "127.0.0.1")
    port = int(os.getenv("CALLBACK_RELAY_PORT", "39001"))

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(create_app(), host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()
