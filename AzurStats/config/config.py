import toml

from module.logger import logger

TEMP_DATA = './AzurStats/data'
CONFIG_FILE = './AzurStats/config/prod.toml'

logger.info(f'Using {CONFIG_FILE}')
CONFIG = toml.load(CONFIG_FILE)
