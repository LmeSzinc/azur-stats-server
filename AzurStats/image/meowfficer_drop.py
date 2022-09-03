import re
from dataclasses import dataclass

from AzurStats.scene.base import ImageBase
from module.meowfficer.assets import MEOWFFICER_GET_CHECK
from module.ocr.ocr import Ocr
from module.statistics.assets import MEOWFFICER_NAME
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
        rarity = self._meow_name_to_rarity(name)
        if rarity == 0:
            raise MeowfficerNameInvalid(f'Invalid mewofficer name: {name}')

        return DataMeowfficerDrops(
            name=name,
            rarity=rarity
        )

    def _meow_name_to_rarity(self, name: str) -> int:
        """
        Args:
            name: Such as `毗沙丸`

        Returns:
            int: Rarity 1 to 3
        """
        if REGEX_RARITY_1.search(name):
            return 1
        elif REGEX_RARITY_2.search(name):
            return 2
        elif REGEX_RARITY_3.search(name):
            return 3
        else:
            return 0
