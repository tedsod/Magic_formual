# logger_setup.py
import logging

# Define ANSI escape codes for colors
ANSI_RESET = "\033[0m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_CYAN = "\033[36m"

def setup_logger():
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter(
        f"{ANSI_CYAN}%(asctime)s - %(levelname)s - %(message)s{ANSI_RESET}"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logger.addHandler(console_handler)
    # File handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    return logger
