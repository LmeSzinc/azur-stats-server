import dataclasses
import os
import re

import pymysql

from AzurStats.database.base import AzurStatsDatabase
from module.config.utils import iter_folder
from module.logger import logger


class DatabaseTools(AzurStatsDatabase):
    ALL_TABLES = [
        'research_items',
        'research_projects',
        'parse_records',
        'meowfficer_talents'
    ]

    def chuck_execute(self, sql, seq, chunk_size=1000):
        """
        Args:
            sql:
            seq (iterable):
            chunk_size (int):

        Returns:
            int: Amount of affected rows
        """
        total = len(seq)
        connection = pymysql.connect(**self.database_config)
        try:
            for pos in range(0, total, chunk_size):
                logger.attr('Chunk', f'{pos}/{total}')
                chunk = seq[pos:pos + chunk_size]
                with connection.cursor() as cursor:
                    result = cursor.executemany(sql, chunk)
                connection.commit()
                logger.info(f'{result} rows affected')
        finally:
            connection.close()

    def delete_record(self, table, condition, confirm=True):
        """
        Delete records from the given condition

        Args:
            table (str):
            condition (str):

        Examples:
            Delete all records with `item = "BlueprintMarcopolo"`:
                self = DatabaseTools()
                self.delete_record('research_items', 'item = "BlueprintMarcopolo"')
        """
        logger.info(f'Delete record from table "{table}" where "{condition}"')
        sql = f"""
        SELECT imgid FROM {table}
        WHERE {condition}
        GROUP BY imgid
        """

        @dataclasses.dataclass
        class DataImaid:
            imgid: str

        records = self.query(sql, DataImaid).get('imgid')
        logger.info(f'Found {len(records)} records')
        if confirm:
            input('\nInput any key to confirm delete:\n')

        for delete_table in self.ALL_TABLES:
            logger.info(f'Delete record from table: {delete_table}')
            sql = f"""
            DELETE FROM {delete_table}
            WHERE imgid = %s
            """
            self.chuck_execute(sql, records)

    def delete_unknown_templates(self, table, confirm=True):
        # Show
        sql = f"""
                SELECT item, COUNT(DISTINCT(imgid)) as amount, imgid
                FROM {table}
                GROUP BY item
                """

        @dataclasses.dataclass
        class DataItem:
            item: str
            amount: int
            example: str

            @property
            def is_unknown(self):
                return self.item.isdigit()

        items = self.query(sql, DataItem).select(is_unknown=True)
        for item in items:
            print('\t'.join(map(str, dataclasses.astuple(item))))

        # Query
        sql = f"""
        SELECT DISTINCT(item)
        FROM {table}
        """

        @dataclasses.dataclass
        class DataItem:
            item: str

        items = self.query(sql, DataItem).get('item')
        items = [item for item in items if item.isdigit()]
        logger.info(f'Found {len(items)} items')

        folder = f'./assets/stats/{table}'
        regex = re.compile(r'/\d+.png$')
        templates = [t for t in iter_folder(folder) if regex.search(t)]
        logger.info(f'Found {len(templates)} templates')

        # Execute
        if confirm:
            input('\nInput any key to confirm delete:\n')
        for template in templates:
            os.remove(template)
        for item in items:
            self.delete_record(table, condition=f'item = {item}', confirm=False)

    def delete_redundant_research_projects(self, table='research_projects'):
        logger.info(f'Delete redundant research projects from table "{table}"')
        sql = f"""
        SELECT imgid, COUNT(*)
        FROM research_projects
        GROUP BY imgid
        """

        @dataclasses.dataclass
        class DataImaid:
            imgid: str
            count: int

        records = self.query(sql, DataImaid)
        records.grids = [row for row in records.grids if row.count > 5]
        records = records.get('imgid')
        logger.info(f'Found {len(records)} records')

        input('\nInput any key to confirm delete:\n')

        for delete_table in self.ALL_TABLES:
            logger.info(f'Delete record from table: {delete_table}')
            sql = f"""
            DELETE FROM {delete_table}
            WHERE imgid = %s
            """
            self.chuck_execute(sql, records)


if __name__ == '__main__':
    self = DatabaseTools()
    self.delete_unknown_templates('research_items')
    # self.delete_record('parse_records', 'scene = "ResearchInvalid"')
