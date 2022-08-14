from module.logger import logger


def run():
    # logger.hr('StatsResearchItem', level=1)
    # from AzurStats.stats.research_items import StatsResearchItem
    # StatsResearchItem().generate()

    logger.hr('Overview', level=1)
    from AzurStats.stats.overview import Overview
    Overview().generate()
