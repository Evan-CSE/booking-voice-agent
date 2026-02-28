import logging
import sys

def setup_logger(name: str = "app") -> logging.Logger:
    """
    Creates and configures a centralized logger instance.
    """
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, it might have been configured already, 
    # but we can ensure standard configuration here.
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler with standard formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a child logger for a specific module, inheriting the centralized configuration.
    """
    # Initialize the root 'app' logger to ensure handlers are set up
    setup_logger("app")
    return logging.getLogger(f"app.{module_name}")
