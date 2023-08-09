import logging
import colorlog

def setup_logger():
    # Create a logger object.
    logger = logging.getLogger()
    
    # Set the level of the logger.
    logger.setLevel(logging.DEBUG)
    
    # Create a file handler object
    fileh = logging.FileHandler('debug.log', 'w')  # 'w' mode overwrites the file
    
    # Set the log level of the file handler. In this case, DEBUG
    fileh.setLevel(logging.DEBUG)
    
    # Create a stream handler object
    streah = logging.StreamHandler()
    
    # Set the log level of the stream handler. In this case, DEBUG
    streah.setLevel(logging.INFO)
    
    # Create formatters
    formatter_color = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(filename)s:%(lineno)d - %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red',
        }
    )



    formatter_plain = logging.Formatter("%(levelname)-8s [%(asctime)s] %(filename)s:%(lineno)d - %(message)s")


    # Set the formatter for the file and stream handler
    fileh.setFormatter(formatter_plain)  # Plain formatter for file
    streah.setFormatter(formatter_color)  # Color formatter for terminal
    
    # Add the file and stream handler to the logger
    logger.addHandler(fileh)
    logger.addHandler(streah)

    return logger

# Create a global logger instance
logger = setup_logger()

if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical error message")
