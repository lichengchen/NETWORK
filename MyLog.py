import logging
from logging.handlers import TimedRotatingFileHandler
logger = logging.getLogger('simple_example')
logger.setLevel(logging.INFO)
ch = TimedRotatingFileHandler("requestLog.log", when='D', encoding="utf-8")
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)