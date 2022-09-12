import re
from dataclasses import dataclass

import numpy as np

from AzurStats.meowfficer_talent.talent_data import DICT_MEOWFFICER_TALENT
from AzurStats.scene.base import ImageBase
from module.base.utils import rgb2gray
from module.meowfficer.assets import MEOWFFICER_TALENT_CLOSE
from module.ocr.ocr import Ocr
from module.statistics.assets import MEOWFFICER_TALENT_DETAIL
from module.statistics.utils import ImageError


class MeowfficerTalentInvalid(ImageError):
    """ Unknown meowfficer talent """
    pass


@dataclass
class DataMeowfficerTalents:
    talent_name: str
    talent_genre: str
    talent_level: int


class TalentOcr(Ocr):
    def pre_process(self, image):
        image = rgb2gray(image)

        return image.astype(np.uint8)


OCR_MEOWFFICER_TALENT = TalentOcr(
    MEOWFFICER_TALENT_DETAIL, lang='cnocr', letter=(255, 255, 255), name='OCR_MEOWFFICER_TALENT')
REGEX_COMMA = re.compile(r'[,.\'"，。、 ]')


class MeowfficerTalent(ImageBase):
    def is_meowfficer_talent(self, image):
        return bool(self.classify_server(MEOWFFICER_TALENT_CLOSE, image))

    def parse_meowfficer_talent(self, image):
        """
        Args:
            image:

        Returns:
            DataMeowfficerTalents

        Raises:
            MeowfficerTalentInvalid:
        """
        info = OCR_MEOWFFICER_TALENT.ocr(image)
        info = self._meowfficer_info_fix(info)

        talent = self._mewofficer_info_to_talent(info)
        return talent

    @staticmethod
    def _mewofficer_info_to_talent(info: str) -> DataMeowfficerTalents:
        """
        Args:
            info: Such as `铁血炮击提高12点、雷击提高14点、命中提高3点`

        Returns:

        """
        for row, regex in DICT_MEOWFFICER_TALENT.items():
            if regex.search(info):
                genre, level, name = row
                return DataMeowfficerTalents(
                    talent_name=name,
                    talent_genre=genre,
                    talent_level=level,
                )

        raise MeowfficerTalentInvalid(f'Unknown talent: {info}')

    @staticmethod
    def _meowfficer_info_fix(info: str) -> str:
        info = REGEX_COMMA.sub('', info)

        # 战列战巡正航航战超巡机动提高l点
        # 战巡战列耐久提高70点炮击提高1l点
        info = info.replace('|', '1').replace('l', '1')

        # 驱逐轻巡霍击提高15点鱼雷暴击率提高3%
        info = info.replace('霍击', '雷击')
        # 重樱雷击提高1点航空提高8点机动提高2点
        info = info.replace('重樱雷击提高1点', '重樱雷击提高11点')
        # 白鹰防空提高1点航空提高1点装填提高4点
        info = info.replace('白鹰防空提高1点', '白鹰防空提高11点')
        # 主力命中提高点
        info = info.replace('主力命中提高点', '主力命中提高1点')

        return info
