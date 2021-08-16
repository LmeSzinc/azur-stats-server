from AzurStats.classification.image_classification import ImageClassification
from AzurStats.commission import commission_items
from AzurStats.research4 import research4_projects, research4_items
from AzurStats.utils import overview
from module.logger import logger


def run():
    logger.hr('Image classification', level=1)
    ImageClassification().run()

    # logger.hr('Research4 projects', level=1)
    # research4_projects.run()
    #
    # logger.hr(f'Research4 items', level=1)
    # research4_items.run()

    logger.hr(f'Commission items', level=1)
    commission_items.run()

    logger.hr('Overview', level=1)
    overview.run()
