import re
from dataclasses import dataclass

import numpy as np

from AzurStats.commission.data import LIST_COMMISSION_DATA
from AzurStats.scene.base import ImageBase
from module.azur_stats.assets import COMMISSION_DONE, COMMISSION_PERFECT, COMMISSION_NAME
from module.ocr.ocr import Ocr
from module.statistics.utils import ImageError


class SuffixOcr(Ocr):
    def pre_process(self, image):
        image = super().pre_process(image)

        left = np.where(np.min(image[5:-5, :], axis=0) < 85)[0]
        if len(left):
            image = image[:, left[-1] - 15:]

        return image

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('1', 'I').replace('J', 'I')
        return result


OCR_SUFFIX = SuffixOcr(
    COMMISSION_NAME, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='IV1J', name='OCR_SUFFIX')
OCR_SUFFIX_JP = SuffixOcr(
    COMMISSION_NAME, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='IV1', name='OCR_SUFFIX')
OCR_NAME_MULTI = {
    'cn': Ocr(COMMISSION_NAME, lang='cnocr', letter=(255, 255, 255), threshold=128),
    'en': Ocr(COMMISSION_NAME, lang='cnocr', letter=(255, 255, 255), threshold=128),
    'jp': Ocr(COMMISSION_NAME, lang='jp', letter=(255, 255, 255), threshold=128),
    'tw': Ocr(COMMISSION_NAME, lang='tw', letter=(255, 255, 255), threshold=128),
}
REGEX_PUNCTUATION = re.compile(r'[ \\/\-_\'\"“”\.、,，。\(\)（）\[\]]')


@dataclass
class DataCommissionStatus:
    comm: str
    status: int


class CommissionInvalid(ImageError):
    """ Invalid commission name and suffix """
    pass


class CommissionStatus(ImageBase):
    _commission_status_last = -1

    def parse_commission_status(self, image) -> DataCommissionStatus:
        """
        `is_commission_status()` or `_commission_status()` must be called before `parse_commission_status()`
        """
        status = self._commission_status_last
        comm = self._commission_name(image)
        return DataCommissionStatus(
            comm=comm,
            status=status,
        )

    def _commission_status(self, image):
        """
        Args:
            image:

        Returns:
            int:
                0 for DONE
                1 for PERFECT
                -1 for unknown
        """
        if self.classify_server(COMMISSION_DONE, image):
            self._commission_status_last = 0
            return 0
        elif self.classify_server(COMMISSION_PERFECT, image):
            self._commission_status_last = 1
            return 1
        else:
            self._commission_status_last = -1
            return -1

    def is_commission_status(self, image) -> bool:
        return self._commission_status(image) >= 0

    def _commission_name_convert(self, name, suffix):
        """
        Args:
            name (str): Raw commission name OCR result, such as `小型油田开发 III`
            suffix (str): Raw commission suffix OCR result, such as `III`

        Returns:
            str: Standardized commission name in English, such as `Small-scale Oil Extraction Ⅲ`

        Raises:
            CommissionInvalid:
        """
        suffix = suffix.strip()
        suffix = re.sub(r'VI$', 'Ⅵ', suffix)
        suffix = re.sub(r'IV$', 'Ⅳ', suffix)
        suffix = re.sub(r'V$', 'Ⅴ', suffix)
        suffix = re.sub(r'III$', 'Ⅲ', suffix)
        suffix = re.sub(r'II$', 'Ⅱ', suffix)
        suffix = re.sub(r'I$', 'Ⅰ', suffix)

        name = REGEX_PUNCTUATION.sub('', name).upper()
        # Missing character in TW
        name = name.replace('鑑', '艦')
        # CN ocr errors
        name = name.replace('曰', '日')
        # EN ocr errors
        name = name.replace('CORMBAT', 'COMBAT')
        name = name.replace('ENERMY', 'ENEMY')
        name = name.replace('RESOUIRCE', 'RESOURCE')
        name = name.replace('ALIDING', 'AIDING')
        name = name.replace('BIVWI', 'BIW').replace('BIWL', 'BIW').replace('BILW', 'BIW').replace('BIVW', 'BIW')

        for data in LIST_COMMISSION_DATA:
            n, s = data[self.server]
            if n in name:
                if s:
                    if s == suffix:
                        return data['comm']
                else:
                    return data['comm']

        raise CommissionInvalid(f'Invalid commission: {name} | {suffix}')

    def _commission_name(self, image):
        """
        Args:
            image:

        Returns:

        """
        name = OCR_NAME_MULTI[self.server].ocr(image)
        if self.server == 'jp':
            suffix = OCR_SUFFIX_JP.ocr(image)
        else:
            suffix = OCR_SUFFIX.ocr(image)
        return self._commission_name_convert(name, suffix)
