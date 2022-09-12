import re
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from AzurStats.scene.base import ImageBase
from module.base.decorator import cached_property
from module.base.utils import area_offset
from module.base.utils import crop
from module.meowfficer.assets import MEOWFFICER_GET_CHECK
from module.ocr.ocr import Ocr
from module.statistics.assets import MEOWFFICER_NAME, TEMPLATE_MEOWFFICER_NAME_CHECK
from module.statistics.utils import ImageError

OCR_MEOWFFICER_NAME = Ocr(MEOWFFICER_NAME, lang='cnocr', letter=(115, 85, 66), name='OCR_MEOWFFICER_NAME')


class MeowfficerNonCnDiscarded(ImageError):
    """ Meowfficer talent statistics support CN only """
    pass


class MeowfficerNameInvalid(ImageError):
    """ Unknown mewofficer name """
    pass


@dataclass
class DataMeowfficerDrops:
    name: str
    rarity: int


REGEX_RARITY_1 = re.compile('(埃里喵|查理喵|乔治喵|朝丸|谢尔喵|小胜丸|海耶喵|贝尔喵)')
REGEX_RARITY_2 = re.compile('(帕特喵|弗里喵|莫德喵|小吉丸|威廉喵|汉克喵|莫赫喵|赫尔喵|次郎丸|莫里喵|鲁普喵)')
REGEX_RARITY_3 = re.compile('(奥古喵|庞德喵|伯克喵|约翰喵|林德喵|毗沙丸|小竹丸|克雷喵)')
REGEX_COMMA = re.compile(r'[,.\'"，。、丶 _/\\|1lv\-]')


class MeowfficerDrop(ImageBase):
    def is_meowfficer_drop(self, image):
        return bool(self.classify_server(MEOWFFICER_GET_CHECK, image))

    def parse_meowfficer_drop(self, image):
        """
        Args:
            image:

        Returns:
            DataMeowfficerDrops:

        Raises:
            MeowfficerNameInvalid:
        """
        if self.server != 'cn':
            raise MeowfficerNonCnDiscarded('Meowfficer talent statistics support CN only')

        name = OCR_MEOWFFICER_NAME.ocr(image)
        name = self._meow_name_fix(name)
        meow = self._meow_name_to_drop(name)
        if meow is not None:
            return meow

        name = self._meow_name_search(image)
        name = self._meow_name_fix(name)
        meow = self._meow_name_to_drop(name)
        if meow is not None:
            return meow

        raise MeowfficerNameInvalid(f'Invalid mewofficer name: {name}')

    @staticmethod
    def _meow_name_fix(name):
        # Invalid mewofficer name: 林德l喵
        name = REGEX_COMMA.sub('', name)

        # 吡沙丸
        name = name.replace('吡', '毗')
        # 林德嘧
        name = name.replace('嘧', '喵')
        # 奥占喵
        name = name.replace('占', '古')
        # 竹丸
        if name == '竹丸':
            name = '小竹丸'
        # 伯克’d
        if '伯克' in name:
            name = '伯克喵'
        # 伯克’d
        if '伯克' in name:
            name = '伯克喵'
        # 品毗少丸, 毗沙丈丸, 毗沙士
        if re.search(r'毗[沙少]|[沙少]丸', name):
            name = '毗沙丸'

        return name

    @staticmethod
    def _meow_name_to_drop(name: str):
        """
        Args:
            name: Such as `毗沙丸`

        Returns:
            DataMeowfficerDrops:
        """
        res = REGEX_RARITY_1.search(name)
        if res:
            return DataMeowfficerDrops(
                name=res.group(1),
                rarity=1
            )
        res = REGEX_RARITY_2.search(name)
        if res:
            return DataMeowfficerDrops(
                name=res.group(1),
                rarity=2
            )
        res = REGEX_RARITY_3.search(name)
        if res:
            return DataMeowfficerDrops(
                name=res.group(1),
                rarity=3
            )

        return None

    @cached_property
    def _meow_check_templates(self):
        """
        Returns:
            dict: Key: Rotation range(-10, 10, 0.1), Value: their images
        """
        raw = Image.fromarray(TEMPLATE_MEOWFFICER_NAME_CHECK.image)
        images = {}
        for rotation in np.arange(-10, 10, 0.1):
            image = np.array(raw.rotate(rotation, resample=Image.CUBIC, expand=True, fillcolor=(255, 255, 247)))
            images[rotation] = image
        return images

    @cached_property
    def _meow_check_search_area(self):
        return (831, 163, 947, 242)

    @cached_property
    def _meow_name_search_area(self):
        return (831, 126, 1185, 242)

    def _meow_name_search(self, image):
        # Search rotated character `指挥喵`, and record best match
        check_image = crop(image, self._meow_check_search_area)
        best_sim, best_rotation, best_point = None, None, None
        for rotation, template in self._meow_check_templates.items():
            res = cv2.matchTemplate(check_image, template, cv2.TM_CCOEFF_NORMED)
            _, sim, _, point = cv2.minMaxLoc(res)
            if best_sim is None or sim > best_sim:
                best_sim, best_rotation, best_point = sim, rotation, point

        # No match
        if best_sim is None or best_sim < 0.75:
            return None

        # Rotate image to normal
        name_image = Image.fromarray(crop(image, self._meow_name_search_area))
        name_image = np.array(name_image.rotate(-best_rotation, resample=Image.CUBIC, fillcolor=(255, 255, 247)))
        # match character `指挥喵` again
        _, check_button = TEMPLATE_MEOWFFICER_NAME_CHECK.match_result(name_image)
        # Get the location of name
        # (856, 214) is the upper-left pixel of character `指挥喵`
        vector = area_offset(MEOWFFICER_NAME.area, offset=(-856, -214 + 2))
        check_button = check_button.crop(vector)
        name_image = crop(name_image, check_button.area)
        # Image.fromarray(name_image).show()

        return OCR_MEOWFFICER_NAME.ocr([name_image], direct_ocr=True)
