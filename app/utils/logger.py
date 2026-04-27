import logging


def setup_logger(name: str) -> logging.Logger:
    """
    Creates project logger.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    return logging.getLogger(name)
