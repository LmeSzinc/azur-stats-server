from AzurStats.image.get_items import GetItems
from module.base.button import ButtonGrid
from module.base.utils import crop, rgb2gray
from module.ocr.ocr import Ocr
from module.research.assets import *
from module.research.project import get_research_series, get_research_name, ResearchProject
from module.statistics.utils import ImageError

QUEUE_NAME = [QUEUE_OCR_RESEARCH_1, QUEUE_OCR_RESEARCH_2, QUEUE_OCR_RESEARCH_3, QUEUE_OCR_RESEARCH_4,
              QUEUE_OCR_RESEARCH_5]
QUEUE_SERIES = [QUEUE_SETIES_1, QUEUE_SETIES_2, QUEUE_SETIES_3, QUEUE_SETIES_4, QUEUE_SETIES_5]
OCR_RESEARCH = Ocr(QUEUE_NAME, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
STATUS_GRID = ButtonGrid(
    origin=(83, 576), button_shape=(197, 32), delta=(229, 0), grid_shape=(5, 1), name='STATUS_GRID')



class ResearchQueue(GetItems):
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
            if not TEMPLATE_FINISHED.match(piece, scaling=scaling):
                if index > 0:
                    return index
                else:
                    raise ImageError('Research queue has no finished project')
        return 5

    def research_queue_project(self, image):
        """
        Get the finished research projects from research queue

        Args:
            image:

        Yields:
            ResearchProject:
        """
        finished = self._research_queue_finish_count(image)
        series_list = get_research_series(image, series_button=QUEUE_SERIES[:finished])
        backup, OCR_RESEARCH.buttons = OCR_RESEARCH.buttons, OCR_RESEARCH.buttons[:finished]
        name_list = get_research_name(image, ocr_button=OCR_RESEARCH)
        OCR_RESEARCH.buttons = backup

        for series, name in zip(series_list, name_list):
            project = ResearchProject(series=series, name=name)
            yield project
