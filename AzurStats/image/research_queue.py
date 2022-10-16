from AzurStats.image.base import ImageBase
from AzurStats.image.research_list import REGEX_PROJECT_NAME, ResearchInvalid
from AzurStats.image.research_list import ResearchJpDiscarded
from module.azur_stats.assets import *
from module.base.button import ButtonGrid
from module.base.utils import crop, rgb2gray
from module.ocr.ocr import Ocr
from module.research.assets import QUEUE_CHECK
from module.research.project import get_research_series, get_research_name, ResearchProject
from module.statistics.utils import ImageError

QUEUE_SERIES = [QUEUE_SETIES_1, QUEUE_SETIES_2, QUEUE_SETIES_3, QUEUE_SETIES_4, QUEUE_SETIES_5]
QUEUE_NAME = [QUEUE_OCR_RESEARCH_1, QUEUE_OCR_RESEARCH_2, QUEUE_OCR_RESEARCH_3, QUEUE_OCR_RESEARCH_4,
              QUEUE_OCR_RESEARCH_5]
# EN and TW is 24px higher
QUEUE_SERIES_EN = [b.move((0, -24)) for b in QUEUE_SERIES]
QUEUE_NAME_EN = [b.move((0, -24)) for b in QUEUE_NAME]
STATUS_GRID = ButtonGrid(
    origin=(83, 576 - 24), button_shape=(197, 32 + 24), delta=(229, 0), grid_shape=(5, 1), name='STATUS_GRID')


class ResearchQueueUnfinished(ImageError):
    """ Research queue has no finished project """
    pass


class ResearchQueue(ImageBase):
    def is_research_queue(self, image):
        return bool(self.classify_server(QUEUE_CHECK, image))

    def _research_queue_finish_count(self, image):
        """
        Args:
            image:

        Returns:
            int: amount of finished projects, 1 to 5
        """
        scaling = 530 / 558
        for index, button in enumerate(STATUS_GRID.buttons):
            piece = rgb2gray(crop(image, button.area))
            if not self.classify_server(TEMPLATE_RESEARCH_FINISHED, piece, scaling=scaling):
                if index > 0:
                    return index
                else:
                    raise ResearchQueueUnfinished('Research queue has no finished project')
        return 5

    def parse_research_queue_project(self, image):
        """
        Get the finished research projects from research queue

        Args:
            image:

        Yields:
            ResearchProject:
        """
        if self.server == 'jp':
            raise ResearchJpDiscarded('JP research list has no project names')

        finished = self._research_queue_finish_count(image)

        if self.server == 'en':
            series_button = QUEUE_SERIES_EN[:finished]
            ocr_button = QUEUE_NAME_EN[:finished]
            ocr = Ocr(ocr_button, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
        elif self.server == 'tw':
            series_button = QUEUE_SERIES_EN[:finished]
            ocr_button = QUEUE_NAME_EN[:finished]
            ocr = Ocr(ocr_button, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
        else:
            series_button = QUEUE_SERIES[:finished]
            ocr_button = QUEUE_NAME[:finished]
            ocr = Ocr(ocr_button, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')

        series_list = get_research_series(image, series_button=series_button)
        name_list = get_research_name(image, ocr=ocr)

        for series, name in zip(series_list, name_list):
            project = ResearchProject(series=series, name=name)

            if not project.valid:
                raise ResearchInvalid(f'Invalid research project: {project}')
            if not REGEX_PROJECT_NAME.match(project.name):
                raise ResearchInvalid(f'Invalid research project name: {project}')
            if project.series == 0:
                raise ResearchInvalid(f'Invalid research project series: {project}')

            yield project
