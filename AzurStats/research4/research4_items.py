import pymysql

from AzurStats.classification.image_classification import ImageClassification, MultiServerButton
from AzurStats.research4.items_stats import ItemStatsGenerator
from AzurStats.utils.utils import *
from module.research.project import *
from module.statistics.get_items import *

ASSETS_FOLDER = './AzurStats/research4/assets'
GET_ITEMS_1 = MultiServerButton(
    area={'cn': (538, 217, 741, 253), 'en': (550, 215, 739, 246), 'jp': (539, 220, 741, 252),
          'tw': (539, 217, 742, 253)},
    color={'cn': (160, 192, 248), 'en': (157, 187, 233), 'jp': (146, 184, 249), 'tw': (155, 190, 248)},
    button={'cn': (1000, 631, 1055, 689), 'en': (999, 630, 1047, 691), 'jp': (1000, 631, 1055, 689),
            'tw': (1000, 631, 1055, 689)},
    file={'cn': './assets/cn/combat/GET_ITEMS_1.png', 'en': './assets/en/combat/GET_ITEMS_1.png',
          'jp': './assets/jp/combat/GET_ITEMS_1.png', 'tw': './assets/tw/combat/GET_ITEMS_1.png'})
GET_ITEMS_2 = MultiServerButton(
    area={'cn': (538, 146, 742, 182), 'en': (549, 140, 740, 176), 'jp': (536, 146, 741, 182),
          'tw': (537, 146, 742, 182)},
    color={'cn': (160, 192, 248), 'en': (152, 185, 236), 'jp': (145, 182, 249), 'tw': (155, 190, 248)},
    button={'cn': (1000, 631, 1055, 689), 'en': (999, 630, 1047, 691), 'jp': (1000, 631, 1055, 689),
            'tw': (1000, 631, 1055, 689)},
    file={'cn': './assets/cn/combat/GET_ITEMS_2.png', 'en': './assets/en/combat/GET_ITEMS_2.png',
          'jp': './assets/jp/combat/GET_ITEMS_2.png', 'tw': './assets/tw/combat/GET_ITEMS_2.png'})
GET_ITEMS_3 = MultiServerButton(
    area={'cn': (539, 143, 742, 179), 'en': (548, 136, 740, 172), 'jp': (540, 143, 742, 179),
          'tw': (539, 217, 742, 253)},
    color={'cn': (161, 193, 248), 'en': (152, 185, 237), 'jp': (145, 182, 248), 'tw': (155, 190, 248)},
    button={'cn': (1000, 631, 1055, 689), 'en': (999, 630, 1047, 691), 'jp': (1000, 631, 1055, 689),
            'tw': (1000, 631, 1055, 689)},
    file={'cn': './assets/cn/combat/GET_ITEMS_3.png', 'en': './assets/en/combat/GET_ITEMS_3.png',
          'jp': './assets/jp/combat/GET_ITEMS_3.png', 'tw': './assets/tw/combat/GET_ITEMS_3.png'})


def predict_tag(image):
    threshold = 50
    color = cv2.mean(np.array(image))[:3]
    if color_similar(color1=color, color2=(49, 125, 222), threshold=threshold):
        # Blue
        return 'catchup'
    elif color_similar(color1=color, color2=(33, 199, 239), threshold=threshold):
        # Cyan
        return 'bonus'
    elif color_similar(color1=color, color2=(255, 85, 41), threshold=threshold):
        # red
        return 'event'
    else:
        return None


ITEM_GROUP.predict_tag = predict_tag


class Research4Items(ImageClassification, GetItemsStatistics):
    SQL_SOURCE = 'images'
    SQL_SOURCE_COLUMN = 'imgid, path, server'
    SQL_TARGET = 'research4_items'
    SQL_TARGET_COLUMN = 'imgid, server, valid, series, project, project_ocr, item, amount, tag, error'
    SQL_WHERE = "AND valid = 1 AND stats = 'research4'"

    for_extraction = False

    def __init__(self, **kwarg):
        super().__init__(**kwarg)
        logger.info('Load template folder')
        self.load_template_folder(folder=ASSETS_FOLDER)

    def images_to_data(self, images):
        """
        Args:
            images: List of pillow images

        Returns:
            List of output data
        """
        count = len(images)
        if count == 1:
            raise ImageError('No items dropped, might be a project reset')
        if count > 3:
            raise ImageError(f'Too many drop screenshots: {count}, expects 1 to 3')

        image = images[0]
        finish = get_research_finished(image)
        if finish is None:
            raise ImageError('No project finished, but get items')
        series = get_research_series(image)[finish]

        if self.for_extraction:
            self.extract_template(images[1], folder=ASSETS_FOLDER)
            if count == 3:
                self.extract_template(images[2], folder=ASSETS_FOLDER)
            return [[2, 0, None, None, None, None, None]]

        # names_ocr = get_research_name(image)[finish]
        backup = OCR_RESEARCH.buttons
        OCR_RESEARCH.buttons = [OCR_RESEARCH.buttons[finish]]
        names_ocr = OCR_RESEARCH.ocr(image)
        OCR_RESEARCH.buttons = backup
        project = ResearchProject(name=names_ocr, series=series)
        if series != 4:
            raise ImageError('Not a S4 project, the finished project is')
        if not project.valid:
            raise ImageError('Not a valid project, the finished project is')

        items = self.stats_get_items(images[1], name=True, amount=True, tag=True)
        if count == 3:
            items2 = self.stats_get_items(images[2], name=True, amount=True, tag=True)
            items = merge_get_items(items, items2)
        if not len(items):
            raise ImageError('No items detected in drop screenshots')

        # valid, series, project, project_ocr, item, amount, tag
        data = []
        for item in items:
            valid = 3 if item.name.isdigit() else 1
            if 'Blueprint' in item.name and item.amount > 20:
                # BlueprintHakuryuu and BlueprintMarcopolo may be detected as 4** and 7*
                # Blueprints are about 10 at max
                amount = int(str(item.amount)[1:])
                logger.info(f'Amount of {item.name}: {item.amount} is revised to {amount}')
                item.amount = amount
            if item.name == 'SpecializedCores' and item.amount > 24:
                # 2 SpecializedCores per hour, so it's 24 at max
                amount = int(str(item.amount)[1:])
                logger.info(f'Amount of {item.name}: {item.amount} is revised to {amount}')
                item.amount = amount
            if item.name == 'Prototype_Tenrai_T0' and item.amount > 10:
                # May detected as 441
                amount = item.amount % 10
                logger.info(f'Amount of {item.name}: {item.amount} is revised to {amount}')
                item.amount = amount
            data.append([valid, series, project.name, names_ocr, item.name, item.amount, item.tag])
        return data

    def merge_data(self, data_in, data_out):
        """
        Args:
            data_in: Results in SQL query
            data_out: A row of data to insert

        Returns:
            list:
        """
        # imgid, server, valid, series, project, project_ocr, item, amount, tag, error
        return [data_in[0], data_in[2], *data_out, None]

    def merge_data_error(self, data_in, error):
        """
        Args:
            data_in: Results in SQL query
            error: Error messages

        Returns:
            list:
        """
        # imgid, server, valid, series, project, project_ocr, item, amount, tag, error
        return [data_in[0], data_in[2], 0, 0, None, None, None, None, None, error]

    def _stats_get_items_load(self, image):
        """
        Args:
            image: Pillow image, 1280x720.
        """
        ITEM_GROUP.grids = None
        if INFO_BAR_1.appear_on(image):
            raise ImageError('Stat image has info_bar')
        elif GET_ITEMS_1.match(image, offset=(5, 0)):
            ITEM_GROUP.grids = ITEM_GRIDS_1_ODD if self._stats_get_items_is_odd(image) else ITEM_GRIDS_1_EVEN
        elif GET_ITEMS_2.match(image, offset=(5, 0)):
            ITEM_GROUP.grids = ITEM_GRIDS_2
        elif GET_ITEMS_3.match(image, offset=(5, 0)):
            ITEM_GROUP.grids = ITEM_GRIDS_3
        else:
            raise ImageError('Stat image is not a get_items image')

    def delete_temp_rows(self, valid):
        """
        Args:
            valid (int): Valid column in database.
                2 for Temp rows for template extraction
                3 for Unclassified items (in auto increased numbers)
        """
        connection = pymysql.connect(**CONFIG['database'])
        try:
            with connection.cursor() as cursor:
                sql = f"""
                DELETE
                FROM research4_items 
                WHERE imgid IN (
                    SELECT DISTINCT imgid 
                    FROM (SELECT * FROM research4_items) AS a
                    WHERE valid = {valid})
                """
                cursor.execute(sql)
                connection.commit()
        finally:
            connection.close()

    def run(self):
        # Use this if most templates are named.
        # logger.info('delete_temp_rows')
        # self.delete_temp_rows(valid=3)

        logger.info('Extract item template')
        self.for_extraction = True
        super().run()
        logger.info('delete_temp_rows')
        self.delete_temp_rows(valid=2)

        logger.info('Extract drop data')
        self.for_extraction = False
        super().run()


def run():
    Research4Items().run()
    ItemStatsGenerator().run()
