import dataclasses
import os
import typing as t

import inflection
import pymysql

from AzurStats.azurstats import AzurStats
from AzurStats.config.config import CONFIG
from AzurStats.database.item_info import ItemInfo
from AzurStats.database.output import ResultOutput
from module.config.utils import deep_get, read_file, write_file
from module.device.method.utils import remove_prefix
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import Ocr

Ocr.SHOW_LOG = False


@dataclasses.dataclass
class DataImage:
    imgid: str
    path: str


class AzurStatsDatabase(ItemInfo, ResultOutput):
    # Numbers of images processed on each batch
    BATCH_SIZE = 100

    def __init__(self):
        self.image_folder = str(deep_get(CONFIG, 'Folder.images'))
        self.database_config = deep_get(CONFIG, 'Database')

    def abspath(self, path):
        """
        Args:
            path (str, DataImage): Such as `/imgs/2021/07/d91b7b6637c400ee.png`

        Returns:
            str: Path to image, such as `F:/azurstats.lyoko.io/imgs/2021/07/d91b7b6637c400ee.png`
        """
        if isinstance(path, DataImage):
            path = path.path
        path = remove_prefix(path, '/imgs/')
        return os.path.abspath(os.path.join(self.image_folder, path)).replace('\\', '/')

    def get_total_updates(self) -> int:
        """
        Get the amount of images that haven't been parsed
        """
        sql = f"""
        SELECT COUNT(*)
        FROM azurstat.img_images a
        WHERE (
            SELECT COUNT(*)
            FROM azurstat_data.parse_records b
            WHERE a.imgid = b.imgid
        ) = 0
        """
        connection = pymysql.connect(**self.database_config)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                return rows[0][0]
        finally:
            connection.close()

    def query(self, sql: str, data_class: dataclasses.dataclass) -> SelectedGrids:
        """
        Args:
            sql:
            data_class:

        Returns:
            SelectedGrids[data_class()]
        """
        connection = pymysql.connect(**self.database_config)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                return SelectedGrids([data_class(*row) for row in rows])
        finally:
            connection.close()

    def select_batch_images(self) -> SelectedGrids(DataImage):
        """
        Get list a batch of images to process
        """
        sql = f"""
        SELECT a.imgid, a.path
        FROM azurstat.img_images a
        LEFT JOIN azurstat_data.parse_records b ON a.imgid = b.imgid
        WHERE ISNULL(b.imgid)
        LIMIT {AzurStatsDatabase.BATCH_SIZE}
        """
        # sql = f"""
        # SELECT imgid, path
        # FROM azurstat.img_images a
        # WHERE (
        #     SELECT COUNT(*)
        #     FROM azurstat_data.parse_records b
        #     WHERE a.imgid = b.imgid
        # ) = 0
        # ORDER BY id ASC
        # LIMIT {AzurStatsDatabase.BATCH_SIZE}
        # """
        return self.query(sql, DataImage)

    def record_to_json(self, record: SelectedGrids, file: str = None) -> t.Dict:
        out = {}
        for index, data in enumerate(record):
            out[index] = dataclasses.asdict(data)

        if file is not None:
            write_file(file, data=out)
        return out

    def record_from_json(self, record: [SelectedGrids, str], data_class: dataclasses.dataclass) -> SelectedGrids:
        if isinstance(record, str):
            record = read_file(record)
        out = [data_class(**data) for data in record.values()]
        return SelectedGrids(out)

    @staticmethod
    def _insert_data(data_list: t.List, cursor: pymysql.connections.Cursor):
        # First row of data
        first = next(iter(data_list), None)
        if first is None:
            return

        columns = [field.name for field in dataclasses.fields(first)]
        # %s, %s
        placeholders = ', '.join(['%s'] * len(columns))
        # imgid, path
        columns = ', '.join(columns)
        # ResearchItem
        scene = remove_prefix(first.__class__.__name__, 'Data')
        # research_item
        table = inflection.underscore(scene)
        sql = f"""
        INSERT INTO `azurstat_data`.`{table}` ({columns})
        VALUES ({placeholders})
        """
        logger.info(sql)

        batch = [dataclasses.astuple(data) for data in data_list]
        rows = cursor.executemany(sql, batch)
        logger.info(f'Rows inserted: {rows}')

    def insert_azurstats(self, azurstats: AzurStats):
        connection = pymysql.connect(**self.database_config)
        try:
            with connection.cursor() as cursor:
                for attr in azurstats.all_data_type:
                    print(attr, len(getattr(azurstats, attr)))
                    self._insert_data(getattr(azurstats, attr), cursor=cursor)
                connection.commit()
        finally:
            connection.close()

    def update(self):
        total = self.get_total_updates()
        processed = 0
        while 1:
            logger.hr(f'Execute {processed}/{total}', level=1)
            images = self.select_batch_images()
            images = [self.abspath(image) for image in images]

            # Parse
            azurstats = AzurStats(images)
            self.insert_azurstats(azurstats)

            processed += len(images)
            if processed >= total:
                break


if __name__ == '__main__':
    self = AzurStatsDatabase()
    self.update()
