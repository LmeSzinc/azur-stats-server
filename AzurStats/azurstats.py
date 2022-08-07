import os
import typing as t
from dataclasses import dataclass

import numpy as np

from AzurStats.scene.base import SceneBase
from AzurStats.scene.research_items import SceneResearchItems
from AzurStats.scene.research_projects import SceneResearchProjects
from module.base.decorator import cached_property
from module.config.utils import iter_folder
from module.device.method.utils import remove_prefix
from module.logger import logger
from module.statistics.utils import ImageUnknown, ImageDiscarded, ImageError


class SceneWrapper(SceneBase):
    scenes: t.List[SceneBase] = [
        SceneResearchProjects(),
        SceneResearchItems(),
    ]
    last_data = None

    def load_file(self, file):
        """
        Args:
            file: Image file, or image array, or list of image array

        Raises:
            ImageError: If unable to read image file
        """
        self.last_data = None
        super().load_file(file)
        for scene in SceneWrapper.scenes:
            scene.load_file(self.images)

    def extract_assets(self):
        """
        Extract item templates from all scenes
        """
        for scene in SceneWrapper.scenes:
            scene.extract_assets()

    def parse_scene(self):
        """
        Yields:
            Any dataclass

        Raises:
            ImageUnknown: If no scene matched this image
        """
        self.last_data = None
        for scene in SceneWrapper.scenes:
            for data in scene.parse_scene():
                if not self.server:
                    self.server = scene.server
                self.last_data = data
                yield data

        if self.last_data is None:
            raise ImageUnknown('Image unknown')


@dataclass
class DataParseRecord:
    imgid: str
    server: str
    scene: str
    error: int
    error_msg: str


class AzurStats(SceneWrapper):
    def __init__(self, files):
        """
        Args:
            files:
                - Image folder with PNG files
                - Image file
                - Image in np.ndarray
                - List of image files
                - List of images in np.ndarray
        """
        logger.hr('AzurStats', level=1)
        if isinstance(files, str):
            if os.path.isdir(files):
                files = list(iter_folder(files, ext='.png'))
            else:
                files = [files]
        elif isinstance(files, np.ndarray):
            files = [files]
        else:
            raise ImageError(f'Unknown image file: {files}')
        logger.info(f'AzurStats is now parsing {len(files)} images')
        self.files = files
        self.all_data = []
        self.all_record = []

        self.extract_assets()
        self.parse_scene()

    def extract_assets(self):
        """
        Extract item templates from all scenes
        """
        logger.hr('Extract assets', level=2)
        for file in self.files:
            try:
                super().load_file(file)
                super().extract_assets()
            except (ImageUnknown, ImageDiscarded, ImageError):
                pass
            except Exception as e:
                logger.error(f'Unexpected error on image {self.imgid}: {e}')

    def _add_record(self, data):
        if isinstance(data, Exception):
            data = DataParseRecord(
                imgid=self.imgid,
                server=self.server,
                scene=data.__class__.__name__,
                error=1,
                error_msg=str(data)
            )
        else:
            data = DataParseRecord(
                imgid=self.imgid,
                server=self.server,
                scene=remove_prefix(self.last_data.__class__.__name__, 'Data'),
                error=0,
                error_msg=''
            )
        self.all_record.append(data)

    def _add_data(self, data):
        self.all_data += data

    def parse_scene(self):
        logger.hr('Parse scene', level=2)
        for file in self.files:
            try:
                super().load_file(file)
                data = list(super().parse_scene())
                self._add_record(self.last_data)
                self._add_data(data)
            except (ImageUnknown, ImageDiscarded, ImageError) as e:
                self._add_record(e)
            except Exception as e:
                self._add_record(ImageError(str(e)))

    def _filter_data(self, data_class):
        return [data for data in self.all_data if isinstance(data, data_class)]

    @property
    def DataParseRecord(self):
        return self.all_data

    @cached_property
    def DataResearchProject(self):
        from AzurStats.scene.research_projects import DataResearchProject
        return self._filter_data(DataResearchProject)

    @cached_property
    def DataResearchItem(self):
        from AzurStats.scene.research_items import DataResearchItem
        return self._filter_data(DataResearchItem)


if __name__ == '__main__':
    """
    Examples
    """
    az = AzurStats(r'./assets/test')
    for d in az.DataResearchItem:
        print(d)
