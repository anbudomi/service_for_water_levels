# src/logging_config.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_dir="error_logging", log_file="service.log", level=logging.INFO):
    # Erstelle den Log-Ordner, falls er nicht existiert
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, log_file)
    
    logger = logging.getLogger()
    logger.setLevel(level)
    
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    
    # Konsolen-Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # FileHandler: TimedRotatingFileHandler rotiert alle 10 Minuten
    file_handler = TimedRotatingFileHandler(log_path, when="M", interval=10, backupCount=6, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

