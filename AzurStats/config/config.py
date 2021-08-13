import os

import toml

from module.logger import logger

TEMP_DATA = './AzurStats/data'
CONFIG_FILE = './AzurStats/config/prod.toml'

if not os.path.exists(TEMP_DATA):
    os.mkdir(TEMP_DATA)

logger.info(f'Using {CONFIG_FILE}')
CONFIG = toml.load(CONFIG_FILE)
