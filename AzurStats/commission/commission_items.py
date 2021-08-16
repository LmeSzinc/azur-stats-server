from AzurStats.classification.image_classification import ImageClassification, COMMISSION_DONE, COMMISSION_PERFECT
from AzurStats.commission.utils import *
from AzurStats.research4.research4_items import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from AzurStats.utils.utils import *
from module.base.utils import *
from module.ocr.ocr import Ocr, OCR_MODEL
from module.statistics.assets import COMMISSION_NAME
from module.statistics.get_items import GetItemsStatistics, ITEM_GROUP, ITEM_GRIDS_1_EVEN, ITEM_GRIDS_1_ODD, \
    ITEM_GRIDS_2, ITEM_GRIDS_3, INFO_BAR_1

ASSETS_FOLDER = r'./AzurStats/commission/assets'
OCR_MODEL['azur_lane'].prediction_threshold = 0.9


class NameOcr(Ocr):
    server = 'cn'
    _server_to_lang = {
        'cn': 'cnocr',
        'en': 'cnocr',
        'jp': 'jp'
    }

    def set_server(self, server):
        self.server = server
        lang = self._server_to_lang.get(server, 'cnocr')
        self.cnocr = OCR_MODEL[lang]


class SuffixOcr(Ocr):
    def pre_process(self, image):
        image = super().pre_process(image)

        left = np.where(np.min(image[5:-5, :], axis=0) < 85)[0]
        if len(left):
            image = image[:, left[-1] - 15:]

        return image


OCR_SUFFIX = SuffixOcr(
    COMMISSION_NAME, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='IV', name='OCR_SUFFIX')
OCR_COMMISSION = NameOcr(COMMISSION_NAME, lang='cnocr', letter=(255, 255, 255), threshold=128)


class CommissionItems(ImageClassification, GetItemsStatistics):
    SQL_SOURCE = 'images'
    SQL_SOURCE_COLUMN = 'imgid, path, server'
    SQL_TARGET = 'commission_items'
    SQL_TARGET_COLUMN = 'imgid, server, valid, perfect, comm, name_ocr, suffix_ocr, item, amount, error'
    SQL_WHERE = "AND valid = 1 AND stats = 'commission'"

    for_extraction = False

    def __init__(self, **kwarg):
        super().__init__(**kwarg)
        logger.info('Load template folder')
        self.load_template_folder(folder=ASSETS_FOLDER)

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

    def parse_exp_info(self, image):
        perfect = False
        server = COMMISSION_DONE.match(image)
        if server is None:
            server = COMMISSION_PERFECT.match(image)
            perfect = True
        if server is None:
            return None
        if server == 'tw':
            raise ImageError('TW commission stats not supported')

        OCR_COMMISSION.set_server(server)
        comm = CommissionName(OCR_COMMISSION.ocr(image), OCR_SUFFIX.ocr(image), server)
        if not comm.valid:
            raise ImageError(f'Invalid commission: {(comm.name, comm.suffix)}')

        # valid, perfect, comm, name_ocr, suffix_ocr
        return [comm.valid, perfect, comm.comm, comm.name, comm.suffix]

    def parse_get_items(self, image):
        try:
            items = self.stats_get_items(image, name=True, amount=True)
        except ImageError:
            return None
        # valid, item, amount
        return [[3 if item.name.isdigit() else 1, item.name, item.amount] for item in items]

    def merge_parse_result(self, exp_info, get_items):
        if get_items is None:
            return [[*exp_info, 'PlaceHolder', 1], ]
        # valid, perfect, comm, name_ocr, suffix_ocr, item, amount
        return [[item[0]] + exp_info[1:] + item[1:] for item in get_items]

    def images_to_data(self, images):
        """
        Args:
            images: List of pillow images

        Returns:
            List of output data
        """
        if self.for_extraction:
            for image in images:
                try:
                    self.extract_template(image, folder=ASSETS_FOLDER)
                except ImageError:
                    continue
            return [[2, None, None, None, None, None, None]]

        data = []
        exp_info = None
        for image in images:
            result = self.parse_exp_info(image)
            if result is not None:
                if exp_info is not None:
                    data += self.merge_parse_result(result, None)
                exp_info = result
                continue

            result = self.parse_get_items(image)
            if result is not None:
                if exp_info is not None:
                    data += self.merge_parse_result(exp_info, result)
                    exp_info = None
                else:
                    logger.warning('No exp_info matches this get_items screenshot')
                    continue

        if exp_info is not None:
            data += self.merge_parse_result(exp_info, None)

        # valid, perfect, comm, name_ocr, suffix_ocr, item, amount
        return data

    def merge_data(self, data_in, data_out):
        """
        Args:
            data_in: Results in SQL query
            data_out: A row of data to insert

        Returns:
            list:
        """
        # imgid, server, valid, perfect, comm, name_ocr, suffix_ocr, item, amount, error
        return [data_in[0], data_in[2], *data_out, None]

    def merge_data_error(self, data_in, error):
        """
        Args:
            data_in: Results in SQL query
            error: Error messages

        Returns:
            list:
        """
        # imgid, server, valid, perfect, comm, name_ocr, suffix_ocr, item, amount, error
        return [data_in[0], data_in[2], 0, None, None, None, None, None, None, error]

    def run(self):
        # Use this if most templates are named.
        # logger.info('delete_temp_rows')
        # self.delete_temp_rows(valid=3)

        logger.info('Extract item template')
        self.for_extraction = True
        super().run()
        logger.info('delete_temp_rows')
        self.delete_temp_rows(table='commission_items', valid=2)

        logger.info('Extract drop data')
        self.for_extraction = False
        super().run()


def run():
    CommissionItems().run()
