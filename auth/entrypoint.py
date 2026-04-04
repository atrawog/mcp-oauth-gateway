"""Auth service entrypoint with colored logging via rich."""

import logging
import os

from rich.logging import RichHandler


def configure_logging() -> None:
    """Set up colored console logging with optional file handler."""
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    handlers: list[logging.Handler] = [
        RichHandler(
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True,
            log_time_format="[%X]",
        )
    ]

    log_file = os.environ.get("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(message)s",
        handlers=handlers,
        force=True,
    )


def main() -> None:
    """Configure logging then launch the auth CLI."""
    configure_logging()

    from mcp_oauth_dynamicclient.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
