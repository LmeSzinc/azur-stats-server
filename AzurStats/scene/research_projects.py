from dataclasses import dataclass

from AzurStats.image.get_items import GetItems
from AzurStats.image.research_list import ResearchList
from AzurStats.image.research_queue import ResearchQueue
from AzurStats.scene.base import SceneBase


@dataclass
class DataResearchProjects:
    imgid: str
    server: str
    focus_series: int
    series: int
    project: str


class SceneResearchProjects(SceneBase, ResearchList, ResearchQueue, GetItems):
    def parse_scene(self):
        """
        Returns:
            Iter[DataResearchItems]:
        """
        if not self.is_research_list(self.first):
            return []

        if self.is_s5_research_list(self.first):
            if self.drop_has_get_items(self.images):
                # Receive the 6th research
                return []
            else:
                # Before selecting research
                return self._parse_research_select_s5()
        else:
            # PR4, detect the first image
            return self._parse_research_select_s4()

    def _parse_research_select_s5(self):
        """
        Images before selecting a research, get the projects in it.
        Images are:
        - Research list
        - Research list
        - Research list
        - Research list
        - Research list

        Yields:
            DataResearchProjects:
        """
        for image in self.images:
            for data in self.parse_research_list_cached(image):
                yield DataResearchProjects(
                    imgid=self.imgid,
                    server=self.server,
                    focus_series=data.focus_series,
                    series=data.series,
                    project=data.project
                )

    def _parse_research_select_s4(self):
        """
        Images when receiving rewards or Image before refresh.
        Images are:
        - Research list
        - Get items

        Yields:
            DataResearchProjects:
        """
        for data in self.parse_research_list_cached(self.first):
            yield DataResearchProjects(
                imgid=self.imgid,
                server=self.server,
                focus_series=data.focus_series,
                series=data.series,
                project=data.project
            )
