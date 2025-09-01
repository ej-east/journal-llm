from pathlib import Path
import logging


def setup_logging(level = logging.INFO,log_file = None, log_dir="logs", format_string=None):

    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_file:
        Path(log_dir).mkdir(exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            Path(log_dir) / log_file,
            maxBytes=10_485_760, # Max of 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name):
    return logging.getLogger(name)