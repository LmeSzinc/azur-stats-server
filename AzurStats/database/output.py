import json
import os
import shutil

from AzurStats.config.config import CONFIG, TEMP_DATA
from module.config.utils import deep_get
from module.logger import logger


def path_to_output(*args):
    return os.path.join(TEMP_DATA, *args)


def write_file(file, data):
    """
    A simple file writer for faster

    Args:
        file:
        data:

    Returns:

    """
    with open(file, mode='w', encoding='utf-8') as f:
        s = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False, default=str)
        f.write(s)


class ResultOutput:
    def output(self, data, *args):
        """
        Write a file to output directory
        Make dirs if sub directories do not exist

        Args:
            data:
            *args: 'path', 'to', 'file.json'
        """
        try:
            write_file(path_to_output(*args), data)
        except FileNotFoundError:
            os.makedirs(path_to_output(*args[:-1]), exist_ok=True)
            write_file(path_to_output(*args), data)

    def copy_to_output_folder(self):
        src = TEMP_DATA
        dst = deep_get(CONFIG, keys='Folder.output', default=None)
        if dst:
            logger.info(f'Copying {src} to {dst}')
            try:
                shutil.copytree(src, dst)
            except FileExistsError:
                shutil.rmtree(dst)
                shutil.copytree(src, dst)
        else:
            logger.info(f'Empty folder/target, skip copying')
