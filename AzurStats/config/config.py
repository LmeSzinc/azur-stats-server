import os

from module.config.utils import read_file
from module.logger import logger

TEMP_DATA = './AzurStats/data'
CONFIG_FILE = './AzurStats/config/prod.yaml'

if not os.path.exists(TEMP_DATA):
    os.mkdir(TEMP_DATA)

logger.info(f'Using {CONFIG_FILE}')
CONFIG = read_file(CONFIG_FILE)
