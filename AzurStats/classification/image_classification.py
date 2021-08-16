import pymysql

import module.config.server as server
from AzurStats.utils.utils import *
from module.base.button import Button
from module.logger import logger
from module.statistics.utils import load_image

VALID_SERVER = ['cn', 'en', 'jp', 'tw']


class MultiServerButton:
    def __init__(self, area, color, button, file=None, name=None):
        """Initialize a Button instance.

        Args:
            area (dict[tuple], tuple): Area that the button would appear on the image.
                          (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
            color (dict[tuple], tuple): Color we expect the area would be.
                           (r, g, b)
            button (dict[tuple], tuple): Area to be click if button appears on the image.
                            (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
                            If tuple is empty, this object can be use as a checker.
        Examples:
            BATTLE_PREPARATION = Button(
                area=(1562, 908, 1864, 1003),
                color=(231, 181, 90),
                button=(1562, 908, 1864, 1003)
            )
        """
        self.buttons = {}
        for s in VALID_SERVER:
            server.server = s
            self.buttons[s] = Button(area=area, color=color, button=button, file=file, name=name)
        server.server = 'cn'

    def match(self, image, offset=(20, 20), threshold=0.85):
        """Detects button by template matching. To Some button, its location may not be static.

        Args:
            image: Screenshot, or filepath to it
            offset (int, tuple): Detection area offset.
            threshold (float): 0-1. Similarity.

        Returns:
            str: Server, or None if none of them matched.
        """
        for s, button in self.buttons.items():
            if button.match(image, offset=offset, threshold=threshold):
                return s

        return None


RESEARCH_CHECK = MultiServerButton(
    area={'cn': (118, 15, 170, 39), 'en': (119, 14, 259, 36), 'jp': (117, 14, 171, 40), 'tw': (118, 15, 170, 39)},
    color={'cn': (165, 179, 215), 'en': (118, 133, 174), 'jp': (135, 154, 195), 'tw': (165, 179, 215)},
    button={'cn': (118, 15, 170, 39), 'en': (119, 14, 259, 36), 'jp': (117, 14, 171, 40), 'tw': (118, 15, 170, 39)},
    file={'cn': './assets/cn/ui/RESEARCH_CHECK.png', 'en': './assets/en/ui/RESEARCH_CHECK.png',
          'jp': './assets/jp/ui/RESEARCH_CHECK.png', 'tw': './assets/tw/ui/RESEARCH_CHECK.png'})
COMMISSION_DONE = MultiServerButton(
    area={'cn': (189, 100, 318, 155), 'en': (352, 103, 444, 144), 'jp': (190, 96, 319, 150), 'tw': (190, 96, 319, 150)},
    color={'cn': (180, 177, 152), 'en': (191, 182, 149), 'jp': (187, 182, 151), 'tw': (187, 182, 151)},
    button={'cn': (189, 100, 318, 155), 'en': (352, 103, 444, 144), 'jp': (190, 96, 319, 150),
            'tw': (190, 96, 319, 150)},
    file={'cn': './assets/cn/statistics/COMMISSION_DONE.png', 'en': './assets/en/statistics/COMMISSION_DONE.png',
          'jp': './assets/jp/statistics/COMMISSION_DONE.png', 'tw': './assets/tw/statistics/COMMISSION_DONE.png'})
COMMISSION_PERFECT = MultiServerButton(
    area={'cn': (189, 101, 300, 155), 'en': (251, 97, 430, 144), 'jp': (190, 97, 302, 150), 'tw': (190, 97, 302, 150)},
    color={'cn': (193, 185, 150), 'en': (171, 170, 151), 'jp': (204, 194, 151), 'tw': (204, 194, 151)},
    button={'cn': (189, 101, 300, 155), 'en': (251, 97, 430, 144), 'jp': (190, 97, 302, 150),
            'tw': (190, 97, 302, 150)},
    file={'cn': './assets/cn/statistics/COMMISSION_PERFECT.png', 'en': './assets/en/statistics/COMMISSION_PERFECT.png',
          'jp': './assets/jp/statistics/COMMISSION_PERFECT.png', 'tw': './assets/tw/statistics/COMMISSION_PERFECT.png'})


class ImageClassification:
    SQL_SOURCE = 'azurstat.`img_images`'
    SQL_SOURCE_COLUMN = 'id, imgid, path'
    SQL_TARGET = 'azurstat_data.`images`'
    SQL_TARGET_COLUMN = 'id, imgid, path, valid, stats, server, error'
    SQL_WHERE = ''
    SQL_LIMIT = 100

    def __init__(self, **kwargs):
        self.path_index = self.SQL_SOURCE_COLUMN.replace(' ', '').split(',').index('path')
        self.image_path = CONFIG['folder']['images']
        self.__dict__.update(kwargs)

    def _data_in_to_path(self, data_in):
        return str(data_in[self.path_index])

    def path_to_images(self, path):
        """
        Args:
            path (str): Such as `/imgs/2021/07/d91b7b6637c400ee.png`

        Returns:
            list: List of pillow images
        """
        path = str(self.image_path) + str(path)
        return unpack(load_image(path))

    def images_to_data(self, images):
        """
        Args:
            images: List of pillow images

        Returns:
            List of output data
        """
        # Research
        image = images[0]
        server = RESEARCH_CHECK.match(image, offset=(20, 20))
        if server is not None:
            if server == 'jp':
                raise ImageError('JP research screenshots are not supported')
            return [[1, "research4", server], ]

        # Commission
        server = COMMISSION_DONE.match(image, offset=(20, 20))
        if server is None:
            server = COMMISSION_PERFECT.match(image, offset=(20, 20))
        if server is not None:
            return [[1, "commission", server], ]

        # No matches
        return [[0, "", None], ]

    def merge_data(self, data_in, data_out):
        """
        Args:
            data_in: Results in SQL query
            data_out: A row of data to insert

        Returns:
            list:
        """
        # id, imgid, path, valid, stats, server, error
        return [*data_in, *data_out, None]

    def merge_data_error(self, data_in, error):
        """
        Args:
            data_in: Results in SQL query
            error: Error messages

        Returns:
            list:
        """
        # id, imgid, path, valid, stats, server, error
        return [*data_in, 0, "", None, error]

    def test_image(self, file):
        print(f'Results of {file}')
        images = unpack(load_image(file))
        for row in self.images_to_data(images):
            print(row)

    def process_one(self, data_in):
        try:
            images = self.path_to_images(self._data_in_to_path(data_in))
            data_out = self.images_to_data(images)
            data_out = [self.merge_data(data_in=data_in, data_out=out) for out in data_out if out is not None]
            if len(data_out) == 0:
                raise ImageError('Get empty data')
        except Exception as e:
            data_out = [self.merge_data_error(data_in=data_in, error=str(e))]

        return [out for out in data_out if isinstance(out, list)]

    def process_all(self, list_data):
        data_out = []
        for data_in in list_data:
            data_out += self.process_one(data_in=data_in)
        return data_out

    def run(self):
        connection = pymysql.connect(**CONFIG['database'])
        try:
            with connection.cursor() as cursor:
                sql = f"""
                SELECT COUNT(*)
                FROM {self.SQL_SOURCE} a
                WHERE (SELECT COUNT(*) FROM {self.SQL_TARGET} b WHERE a.imgid = b.imgid) = 0 {self.SQL_WHERE}
                """
                cursor.execute(sql)
                total = cursor.fetchall()[0][0]
                for n in range(total // self.SQL_LIMIT + 1):
                    logger.hr(f'Execute {n * self.SQL_LIMIT}/{total}', level=2)
                    sql = f"""
                    SELECT {self.SQL_SOURCE_COLUMN}
                    FROM {self.SQL_SOURCE} a
                    WHERE (SELECT COUNT(*)
                    FROM {self.SQL_TARGET} b WHERE a.imgid = b.imgid) = 0 {self.SQL_WHERE} ORDER BY id ASC LIMIT {self.SQL_LIMIT}
                    """
                    cursor.execute(sql)
                    batch = cursor.fetchall()
                    batch = self.process_all(batch)

                    sql = f"""
                    INSERT INTO {self.SQL_TARGET}({self.SQL_TARGET_COLUMN}) 
                    VALUES({', '.join(['%s'] * len(self.SQL_TARGET_COLUMN.split(',')))})"""
                    cursor.executemany(sql, batch)
                    connection.commit()
        finally:
            connection.close()

    def delete_temp_rows(self, table, valid):
        """
        Args:
            table (str):
            valid (int): Valid column in database.
                2 for Temp rows for template extraction
                3 for Unclassified items (in auto increased numbers)
        """
        connection = pymysql.connect(**CONFIG['database'])
        try:
            with connection.cursor() as cursor:
                sql = f"""
                DELETE
                FROM {table} 
                WHERE imgid IN (
                    SELECT DISTINCT imgid 
                    FROM (SELECT * FROM {table}) AS a
                    WHERE valid = {valid})
                """
                cursor.execute(sql)
                connection.commit()
        finally:
            connection.close()


def run():
    ImageClassification().run()
