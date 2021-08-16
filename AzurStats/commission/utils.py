import re
from AzurStats.commission.data import LIST_COMMISSION_DATA
from module.logger import logger

REGEX_ROMAN = re.compile(r'([ⅠⅡⅢⅣⅤⅥ])')
REGEX_PUNCTUATION = re.compile(r'([“”\- ])')


def beautify_name(name):
    name = name.strip()
    name = re.sub(r'VI$', 'Ⅵ', name)
    name = re.sub(r'IV$', 'Ⅳ', name)
    name = re.sub(r'V$', 'Ⅴ', name)
    name = re.sub(r'III$', 'Ⅲ', name)
    name = re.sub(r'II$', 'Ⅱ', name)
    name = re.sub(r'I$', 'Ⅰ', name)
    return name


def to_detection_name(name):
    name = name.replace('曰', '日')
    return REGEX_PUNCTUATION.sub('', name).upper()


def split_name(name):
    suffix = REGEX_ROMAN.search(name)
    if suffix:
        suffix = suffix.group(1)
    else:
        suffix = ''
    name = REGEX_ROMAN.sub('', name).strip()
    name = to_detection_name(name)
    return name, suffix


class CommissionName:
    def __init__(self, name, suffix, server):
        self.name = name
        self.suffix = suffix
        self.server = server
        self.comm = self.match_name(name, suffix)
        self.valid = self.comm is not None

    def match_name(self, ocr_name, ocr_suffix):
        name = to_detection_name(ocr_name)
        suffix = beautify_name(ocr_suffix)
        for data in LIST_COMMISSION_DATA:
            n, s = data[self.server]
            if n in name:
                if s:
                    if s == suffix:
                        return data['comm']
                else:
                    return data['comm']

        logger.warning(f'Invalid commission: {(ocr_name, ocr_suffix)}')
        return None
