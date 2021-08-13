import json
import os
import shutil

from AzurStats.config.config import CONFIG, TEMP_DATA
from module.logger import logger
from module.statistics.utils import ImageError


def human_format(num):
    """
    Args:
        num (int):

    Returns:
        str: Such as 3.95K.
    """
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{:f}'.format(num).rstrip('0').rstrip('.') + ['', 'K', 'M', 'B', 'T'][magnitude]


def write_json(data, name, folder=TEMP_DATA):
    file = os.path.join(folder, f'{name}.json')
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def unpack(image):
    """
    Args:
        image:

    Returns:
        list: List of pillow image.
    """
    if image.size == (1280, 720):
        return [image]
    else:
        size = image.size
        if size[0] != 1280 or size[1] % 720 != 0:
            raise ImageError(f'Unexpected image size: {size}')
        return [image.crop((0, n * 720, 1280, (n + 1) * 720)) for n in range(size[1] // 720)]


def copy_to_output_folder():
    src = TEMP_DATA
    dst = CONFIG['folder']["output"]
    if dst:
        logger.info(f'Copying {src} to {dst}')
        try:
            shutil.copytree(src, dst)
        except FileExistsError:
            shutil.rmtree(dst)
            shutil.copytree(src, dst)
    else:
        logger.info(f'Empty folder/target, skip copying')


