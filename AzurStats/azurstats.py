import os
import typing as t
from dataclasses import dataclass

import numpy as np

from AzurStats.scene.base import SceneBase
from AzurStats.scene.commission_items import SceneCommissionItems
from AzurStats.scene.meowfficer_talent import SceneMeowfficerTalent
from AzurStats.scene.research_items import SceneResearchItems
from AzurStats.scene.research_projects import SceneResearchProjects
from AzurStats.scene.operation_siren import SceneOperationSiren
from AzurStats.scene.battle_items import SceneBattleItems
from module.base.decorator import cached_property
from module.config.utils import iter_folder
from module.device.method.utils import remove_prefix
from module.logger import logger
from module.statistics.utils import ImageError


class ImageUnknown(ImageError):
    """ Image from a unknown drop scene, no such method to parse """
    pass


class SceneWrapper(SceneBase):
    scenes: t.List[SceneBase] = [
        SceneCommissionItems(),
        SceneResearchProjects(),
        SceneResearchItems(),
        SceneMeowfficerTalent(),
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
        for scene in self.__class__.scenes:
            scene.load_file(self.images)
            scene.__dict__['imgid'] = self.imgid

    def extract_assets(self):
        """
        Extract item templates from all scenes
        """
        for scene in self.__class__.scenes:
            scene.extract_assets()

    def parse_scene(self):
        """
        Yields:
            Any dataclass

        Raises:
            ImageUnknown: If no scene matched this image
        """
        self.last_data = None
        for scene in self.__class__.scenes:
            try:
                for data in scene.parse_scene():
                    self.last_data = data
                    yield data
            finally:
                if not self.server:
                    self.server = scene.server

        if self.last_data is None:
            raise ImageUnknown('Image unknown')


@dataclass
class DataParseRecords:
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
        elif isinstance(files, list):
            pass
        else:
            raise ImageError(f'Unknown image file: {files}')
        logger.info(f'AzurStats is now parsing {len(files)} images')
        self.files = files
        self.all_data = []
        self.all_record = []

        self.parse_scene()

    def _add_record(self, data):
        if isinstance(data, Exception):
            data = DataParseRecords(
                imgid=self.imgid,
                server=self.server,
                scene=data.__class__.__name__,
                error=1,
                error_msg=str(data)
            )
        else:
            data = DataParseRecords(
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
                super().extract_assets()
                data = list(super().parse_scene())
                self._add_record(self.last_data)
                self._add_data(data)
            except (ImageError, FileNotFoundError) as e:
                self._add_record(e)
            except Exception as e:
                self._add_record(ImageError(str(e)))

    @cached_property
    def all_data_type(self):
        """
        Returns:
            list[str]: Such as ['DataParseRecords', 'DataResearchProjects', 'DataResearchItems']
        """
        return [attr for attr in dir(self) if attr.startswith('Data')]

    def _filter_data(self, data_class):
        return [data for data in self.all_data if isinstance(data, data_class)]

    @property
    def DataParseRecords(self):
        return self.all_record

    @cached_property
    def DataCommissionItems(self):
        from AzurStats.scene.commission_items import DataCommissionItems
        return self._filter_data(DataCommissionItems)

    @cached_property
    def DataResearchProjects(self):
        from AzurStats.scene.research_projects import DataResearchProjects
        return self._filter_data(DataResearchProjects)

    @cached_property
    def DataResearchItems(self):
        from AzurStats.scene.research_items import DataResearchItems
        return self._filter_data(DataResearchItems)

    @cached_property
    def DataMeowfficerTalents(self):
        from AzurStats.scene.meowfficer_talent import DataMeowfficerTalents
        return self._filter_data(DataMeowfficerTalents)


class AzurStatsOpsi(AzurStats):
    scenes = [
        SceneOperationSiren(),
    ]

    @cached_property
    def DataOpsiItems(self):
        from AzurStats.scene.operation_siren import DataOpsiItems
        return self._filter_data(DataOpsiItems)


class AzurStatsBattle(AzurStats):
    scenes = [
        SceneBattleItems(),
    ]

    @cached_property
    def DataBattleItems(self):
        from AzurStats.scene.battle_items import DataBattleItems
        return self._filter_data(DataBattleItems)


if __name__ == '__main__':
    """
    Examples
    """
    az = AzurStats(r'./assets/test')
    for d in az.DataParseRecords:
        print(d)
    for d in az.DataResearchItems:
        print(d)
