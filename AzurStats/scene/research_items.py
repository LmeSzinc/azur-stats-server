import re
from dataclasses import dataclass

from AzurStats.image.get_items import GetItems, merge_get_items
from AzurStats.image.research_list import ResearchList, DataResearchList
from AzurStats.image.research_queue import ResearchQueue
from AzurStats.scene.base import SceneBase
from module.research.project import get_research_finished, ResearchProject
from module.research_s4.project import get_research_finished as get_research_finished_s4
from module.statistics.utils import ImageError

REGEX_EQUIPMENT = re.compile(r'_T[01234]$')


class ResearchItemsFromNowhere(ImageError):
    """No project finished, but get items """
    pass


class ResearchQueueMismatch(ImageError):
    """ Research queue has 1 finished projects but has 2 get_items """
    pass


@dataclass
class DataResearchItems:
    imgid: str
    server: str
    series: int
    project: str
    item: str
    amount: int
    tag: str


class SceneResearchItems(SceneBase, ResearchList, ResearchQueue, GetItems):
    ITEM_TEMPLATE_FOLDER = './assets/stats/research_items'
    finished_project: DataResearchList

    def extract_assets(self):
        if not self.is_research_queue(self.first) and not self.is_research_list(self.first):
            return

        for image in self.images:
            if self.get_items_count(image):
                self.extract_item_template(image)

    def parse_scene(self):
        """
        Returns:
            Iter[DataResearchItems]:
        """
        if self.is_research_list(self.first) and self.drop_has_get_items(self.images):
            if self.is_s5_research_list(self.first):
                # Receiving 6th research
                return self._parse_research_item_s5()
            else:
                # Receiving from PR4
                return self._parse_research_item_s4()
        elif self.is_research_queue(self.first):
            # Receiving from research queue
            return self._parse_queue_list()
        else:
            return []

    def revise_item(self, item):
        # event, bonus, catchup are in the amount from 1 to 3
        if item.tag:
            item.amount %= 10
        # BlueprintHakuryuu and BlueprintMarcopolo may be detected as 4** and 7*
        # Blueprints are about 10 at max
        if 'Blueprint' in item.name and item.tag is None:
            project = ResearchProject(series=self.finished_project.series, name=self.finished_project.project)
            if item.amount > 20:
                item.amount %= 10
            if project.ship_rarity == 'dr':
                # DR blueprints should < 10
                item.amount %= 10
            else:
                if project.genre == 'D' and project.duration == '0.5':
                    # PRY0.5, blueprints 5~12
                    if item.amount <= 2:
                        item.amount += 10
                    if item.amount >= 15:
                        item.amount %= 10
                else:
                    # PRY other, blueprints 1~9
                    item.amount %= 10
        if item.name == 'SpecializedCores' and item.amount > 24:
            # 2 SpecializedCores per hour, so it's 24 at max
            item.amount = int(str(item.amount)[1:])
        # Prototype gears are rarely dropped, should < 10
        # Prototype_Tenrai_T0 may detected as 441
        if 'Prototype' in item.name:
            item.amount %= 10
        # CognitiveChips should >= 21
        if item.name == 'CognitiveChips' and item.amount < 20:
            item.amount *= 10
        if item.name == 'High_Performance_Hydraulic_Steering_Gear_T0':
            # 111 -> 1
            item.amount %= 10
        if item.amount == 'Rammer_T3':
            # 41 -> 1
            item.amount %= 10

        return item

    def _parse_research_item_s5(self):
        """
        Parse the drop record from the 6th research.
        Images are:
        - Research list
        - Get items

        Yields:
            DataResearchItems:
        """
        finished = get_research_finished(self.first)
        if finished is None:
            raise ResearchItemsFromNowhere('No project finished, but get items')
        project_list = list(self.parse_research_list_cached(self.first))
        project = project_list[finished]
        self.finished_project = project

        all_items = []
        for image in self.followings:
            if not self.is_get_items(image):
                continue
            items = self.parse_get_items(image)
            all_items = merge_get_items(all_items, items)

        for item in all_items:
            yield DataResearchItems(
                imgid=self.imgid,
                server=self.server,
                series=project.series,
                project=project.project,
                item=item.name,
                amount=item.amount,
                tag=item.tag
            )

    def _parse_research_item_s4(self):
        """
        Parse the drop record from PR4 or before.
        Images are:
        - Research list
        - Get items

        Yields:
            DataResearchItems:
        """
        finished = get_research_finished_s4(self.first)
        if finished is None:
            raise ResearchItemsFromNowhere('No project finished, but get items')
        project_list = list(self.parse_research_list_cached(self.first))
        project = project_list[finished]
        self.finished_project = project

        all_items = []
        for image in self.followings:
            if not self.is_get_items(image):
                continue
            items = self.parse_get_items(image)
            all_items = merge_get_items(all_items, items)

        for item in all_items:
            yield DataResearchItems(
                imgid=self.imgid,
                server=self.server,
                series=project.series,
                project=project.project,
                item=item.name,
                amount=item.amount,
                tag=item.tag
            )

    def _parse_queue_list(self):
        """
        Parse the drop record from the 6th research.
        Images are:
        - Research queue
        - Get items
        - Get items
        - Get items
        - Get items
        - Get items

        Yields:
            DataResearchItems:
        """
        finished_list = list(self.parse_research_queue_project(self.first))
        drop_items_list = list(self.parse_get_items_chain(self.followings))

        if len(finished_list) != len(drop_items_list):
            raise ResearchQueueMismatch(
                f'Research queue has {len(finished_list)} finished projects '
                f'but has {len(drop_items_list)} get_items')
        for project, drop_items in zip(finished_list, drop_items_list):
            self.finished_project = DataResearchList(
                focus_series=project.raw_series,
                series=project.raw_series,
                project=project.name
            )
            for item in drop_items:
                yield DataResearchItems(
                    imgid=self.imgid,
                    server=self.server,
                    series=project.raw_series,
                    project=project.name,
                    item=item.name,
                    amount=item.amount,
                    tag=item.tag
                )
