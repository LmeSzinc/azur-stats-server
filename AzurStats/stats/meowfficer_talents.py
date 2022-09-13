from dataclasses import dataclass

from AzurStats.database.base import AzurStatsDatabase
from module.base.decorator import cached_property
from module.logger import logger
from module.map.map_grids import SelectedGrids


@dataclass
class DataMeowfficerTalents:
    name: str
    rarity: int
    talent_name: str
    talent_genre: str
    talent_level: int
    drop_count: int
    samples: int = 0

    def __post_init__(self):
        self.rarity = int(self.rarity)
        self.talent_level = int(self.talent_level)
        self.samples = int(self.samples)


@dataclass
class DataMeowfficerSamples:
    name: str
    samples: int

    def __post_init__(self):
        self.samples = int(self.samples)


class StatsMeowfficerTalents(AzurStatsDatabase):
    @cached_property
    def drop_data(self) -> SelectedGrids(DataMeowfficerTalents):
        sql = """
        SELECT
            `name`,
            rarity,
            talent_name,
            talent_genre,
            talent_level,
            COUNT(DISTINCT imgid) AS drop_count
        FROM meowfficer_talents
        GROUP BY `name`, talent_name
        ORDER BY `name`, talent_name
        """
        data = self.query(sql, data_class=DataMeowfficerTalents)
        logger.info('raw_drop_data')

        sql = """
        SELECT
            `name`,
            COUNT(DISTINCT imgid) AS drop_count
        FROM meowfficer_talents
        GROUP BY `name`
        ORDER BY `name`
        """
        sample = self.query(sql, data_class=DataMeowfficerSamples)
        logger.info('raw_drop_samples')

        data = data.left_join(sample, on_attr=('name', ), set_attr=('samples', ), default=0)
        data = data.sort('rarity', 'name', 'talent_genre', 'talent_level')[::-1]
        logger.info('drop_data')
        return data


if __name__ == '__main__':
    self = StatsMeowfficerTalents()
    self.record_to_csv(self.drop_data, 'meowfficer_talents.csv', encoding='gbk')
