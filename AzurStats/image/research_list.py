import re
from dataclasses import dataclass

from AzurStats.image.base import ImageBase
from module.research.assets import HAS_RESEARCH_QUEUE
from module.research.project import get_research_name, get_research_series, ResearchProject
from module.research_s4.project import get_research_name as get_research_name_s4
from module.research_s4.project import get_research_series as get_research_series_s4
from module.statistics.utils import ImageError
from module.ui.assets import RESEARCH_CHECK

REGEX_PROJECT_NAME = re.compile(r'[A-Z]-\d\d\d-[A-Z][A-Z]')


class ResearchJpDiscarded(ImageError):
    """ JP research has no names, discard this image """
    pass


class ResearchInvalid(ImageError):
    pass


@dataclass
class DataResearchList:
    focus_series: int
    series: int
    project: str


class ResearchList(ImageBase):
    _cached_research_list = None

    def is_research_list(self, image):
        return bool(self.classify_server(RESEARCH_CHECK, image))

    def parse_research_list(self, image):
        """
        Args:
            image:

        Yields:
            DataResearchList:
        """
        if self.server == 'jp':
            raise ResearchJpDiscarded('JP research list has no project names')

        if self.is_s5_research_list(image):
            for data in self._research_list_s5(image):
                yield data
        else:
            for data in self._research_list_s4(image):
                yield data

    def parse_research_list_cached(self, image):
        """
        DataResearchList is used in both SceneResearchItems and SceneResearchProjects, so cache it

        Args:
            image:

        Yields:
            DataResearchList:
        """
        if ResearchList._cached_research_list is None:
            ResearchList._cached_research_list = list(self.parse_research_list(image))
        for data in ResearchList._cached_research_list:
            yield data

    def clear_cache(self):
        super().clear_cache()
        ResearchList._cached_research_list = None

    def is_s5_research_list(self, image):
        """
        Whether image is after PR5 (with research queue) or not

        Pages:
            in: RESEARCH_CHECK
        """
        return bool(self.classify_server(HAS_RESEARCH_QUEUE, image))

    def _research_list_s5(self, image):
        """
        Parse an image from PR5 or later (with research queue)

        Args:
            image:

        Yields:
            DataResearchList:
        """
        series_list = get_research_series(image)

        # Get focus series
        focus_series = 0
        for series in series_list:
            if series_list.count(series) >= 3:
                focus_series = series
                break

        name_list = get_research_name(image)
        project_list = [ResearchProject(name=name, series=series) for name, series in zip(name_list, series_list)]

        # Check project valid
        for project in project_list:
            if not project.valid:
                raise ResearchInvalid(f'Invalid research project: {project}')
            if not REGEX_PROJECT_NAME.match(project.name):
                raise ResearchInvalid(f'Invalid research project name: {project}')
            if project.series == 0:
                raise ResearchInvalid(f'Invalid research project series: {project}')

        for series, project in zip(series_list, project_list):
            yield DataResearchList(
                focus_series=focus_series,
                series=series,
                project=project.name
            )

    def _research_list_s4(self, image):
        """
        Parse an image from PR4 or before (without research queue)

        Args:
            image:

        Yields:
            DataResearchList:
        """
        series_list = get_research_series_s4(image)

        # Get focus series
        focus_series = 0
        for series in series_list:
            if series_list.count(series) >= 3:
                focus_series = series
                break

        name_list = get_research_name_s4(image)
        project_list = [ResearchProject(name=name, series=series) for name, series in zip(name_list, series_list)]

        # Check project valid
        for project in project_list:
            if not project.valid:
                raise ResearchInvalid(f'Invalid research project: {project}')
            if not REGEX_PROJECT_NAME.match(project.name):
                raise ResearchInvalid(f'Invalid research project name: {project}')
            if project.series == 0:
                raise ResearchInvalid(f'Invalid research project series: {project}')

        for series, project in zip(series_list, project_list):
            yield DataResearchList(
                focus_series=focus_series,
                series=series,
                project=project.name
            )
