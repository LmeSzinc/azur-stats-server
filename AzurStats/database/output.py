import json
import os

from AzurStats.config.config import TEMP_DATA


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
