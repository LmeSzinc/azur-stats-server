import typing as t

import cv2
import numpy as np

from AzurStats.image.base import CLASSIFY_CACHE
from AzurStats.image.base import ImageBase
from AzurStats.image.get_items import GetItems, TooManyNewTemplate, ZeroAmountError
from module.azur_stats.assets import AUTO_SEARCH_REWARD_TITLE
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.utils import area_offset, crop
from module.base.utils import color_similar
from module.logger import logger
from module.ocr.ocr import Digit
from module.os_handler.assets import AUTO_SEARCH_REWARD
from module.statistics.item import Item, ItemGrid
from module.statistics.utils import ImageError


class AutoSearchRewardNoTitle(ImageError):
    """ Drop title not found """


class AutoSearchItem(Item):
    def predict_valid(self):
        # Std of items:
        # 70.20733640432516
        # 71.35918518046846
        # 68.82552251304783
        # 13.536856900404807
        # 19.32105580099661
        std = np.std(self.image, ddof=1)
        return std > 40


class AutoSearchAmount(Digit):
    def pre_process(self, image):
        # group.amount_area = (35, 51, 63, 63)
        # Target height: 32
        scale = 32 / 12
        #     CV_INTER_NN       =0,
        #     CV_INTER_LINEAR   =1,
        #     CV_INTER_CUBIC    =2,
        #     CV_INTER_AREA     =3,
        #     CV_INTER_LANCZOS4 =4,
        image = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=2)

        image = super().pre_process(image)

        return image


class AutoSearchItemGrid(ItemGrid):
    @staticmethod
    def predict_tag(image):
        """
        Args:
            image (np.ndarray): The tag_area of the item.
            Replace this method to predict tags.

        Returns:
            str: Tags are like `catchup`, `bonus`. Default to None
        """
        threshold = 35
        color = cv2.mean(np.array(image))[:3]
        if color_similar(color1=color, color2=(181, 205, 255), threshold=threshold):
            # Blue drops
            return 'meow'
        elif color_similar(color1=color, color2=(231, 187, 255), threshold=threshold):
            # Purple drops
            return 'meow'
        elif color_similar(color1=color, color2=(255, 225, 111), threshold=threshold):
            # Gold drops
            return 'meow'
        else:
            return None


class AutoSearchReward(ImageBase):
    AUTO_SEARCH_ITEM_TEMPLATE_FOLDER = f'./assets/auto_search'

    def is_opsi_reward(self, image) -> bool:
        return bool(self.classify_server(AUTO_SEARCH_REWARD, image, offset=(50, 50)))

    def parse_auto_search_reward(self, image, name=True, amount=True, tag=True) -> t.Iterator[AutoSearchItem]:
        """
        Args:
            image (np.ndarray):
            name (bool):
            amount (bool):
            tag (bool):

        Yields:
            AutoSearchItem:
        """
        self._auto_search_get_items_load(image)

        if self.auto_search_item_group.grids is None:
            return
        else:
            self.auto_search_item_group.predict(image, name=name, amount=amount, tag=tag)
            items = self.auto_search_before_revise_items(self.auto_search_item_group.items)
            for item in items:
                before = str(item)
                item = self.auto_search_revise_item(item)
                after = str(item)
                if before != after:
                    logger.info(f'Item {before} is revised to {after}')
                if item.amount == 0:
                    raise ZeroAmountError(f'Invalid item amount: {item}')
                yield item

    def extract_auto_search_item_template(self, image, folder=None):
        """
        Args:
            image:
            folder: Folder to save new templates.
                If None, use self.ITEM_TEMPLATE_FOLDER
        """
        if folder is None:
            folder = self.AUTO_SEARCH_ITEM_TEMPLATE_FOLDER
        self._auto_search_get_items_load(image)
        if self.auto_search_item_group.grids is not None:
            new = self.auto_search_item_group.extract_template(image, folder=folder)
            new = len(new.keys())
            if not GetItems.ALLOW_TOO_MANY_NEW_TEMPLATE and new >= 2:
                raise TooManyNewTemplate(f'Extracted {new} new templates')

    @cached_property
    def auto_search_item_group(self) -> ItemGrid:
        group = AutoSearchItemGrid(None, {}, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92))
        group.item_class = AutoSearchItem
        group.similarity = 0.85
        group.amount_area = (35, 51, 63, 63)
        # (81, 1, 91, 5) * (64/96)
        group.tag_area = (54, 1, 60, 3)
        group.amount_ocr = AutoSearchAmount([], threshold=96, name='Amount_ocr')
        group.load_template_folder(self.AUTO_SEARCH_ITEM_TEMPLATE_FOLDER)
        return group

    def auto_search_before_revise_items(self, items: t.List[AutoSearchItem]) -> t.List[AutoSearchItem]:
        return items

    def auto_search_revise_item(self, item: AutoSearchItem) -> AutoSearchItem:
        return item

    def _auto_search_get_items_load(self, image):
        if not self.classify_server(AUTO_SEARCH_REWARD_TITLE, image, offset=(-80, -20, 80, 500)):
            raise AutoSearchRewardNoTitle('Drop title not found')

        title = CLASSIFY_CACHE[AUTO_SEARCH_REWARD_TITLE][self.server]
        origin = area_offset(title.button, offset=(-7, 34))[:2]
        grids = ButtonGrid(origin=origin, button_shape=(64, 64), grid_shape=(7, 5), delta=(72 + 2 / 3, 75 + 1 / 3))
        # grids.save_mask()

        # std of 4 rows items are like
        # 46.67023661327788
        # 45.298255916160215
        # 62.176250939998155
        # 14.132807630470628
        for y in [1, 2, 3, 4]:
            left_grid = grids[0, y].crop((0, -5, grids.button_shape[0], 5))
            std = np.std(crop(image, left_grid.area), ddof=1)
            if std < 25:
                grids.grid_shape = (grids.grid_shape[0], y)
                break

        reward_bottom = AUTO_SEARCH_REWARD.button[1]
        grids.buttons = [button for button in grids.buttons if button.area[3] < reward_bottom]
        self.auto_search_item_group.grids = grids
