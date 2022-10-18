import typing as t
from dataclasses import dataclass

from AzurStats.image.commission_status import CommissionStatus
from AzurStats.image.get_items import GetItems
from AzurStats.scene.base import SceneBase
from module.base.decorator import cached_property
from module.statistics.item import ItemGrid
from module.statistics.utils import ImageError


@dataclass
class DataCommissionItems:
    imgid: str
    server: str
    comm: str
    status: int
    item: str
    amount: int


class CommissionItemsFromNowhere(ImageError):
    """ No commission finished, but get items """
    pass


class SceneCommissionItems(SceneBase, CommissionStatus, GetItems):
    ITEM_TEMPLATE_FOLDER = './assets/stats/commission_items'

    @cached_property
    def item_grid(self) -> ItemGrid:
        grid = super(SceneCommissionItems, self).item_grid
        # -10px to OCR 4 digits
        grid.amount_area = (50, 71, 91, 92)
        return grid

    def extract_assets(self):
        if not self.is_commission_status(self.first):
            return

        for image in self.images:
            if self.get_items_count(image):
                self.extract_item_template(image)

    def parse_scene(self) -> t.Iterator[DataCommissionItems]:
        """
        Returns:
            Iter[DataCommissionItems]:
        """
        if not self.is_commission_status(self.first):
            return []

        comm = None
        for image in self.images:
            if self.is_commission_status(image):
                if comm is not None:
                    for data in self._commission_drop_product(comm, None):
                        yield data
                comm = self.parse_commission_status(image)
                continue

            if self.is_get_items(image):
                if comm is not None:
                    items = self.parse_get_items(image, tag=False)
                    for data in self._commission_drop_product(comm, items):
                        yield data
                    comm = None
                    continue
                else:
                    raise CommissionItemsFromNowhere('No commission finished, but get items')

        if comm is not None:
            for data in self._commission_drop_product(comm, None):
                yield data

    def _commission_drop_product(self, comm, items) -> t.Iterator[DataCommissionItems]:
        if items is None:
            yield DataCommissionItems(
                imgid=self.imgid,
                server=self.server,
                comm=comm.comm,
                status=comm.status,
                item='PlaceHolder',
                amount=1
            )
        else:
            for item in items:
                yield DataCommissionItems(
                    imgid=self.imgid,
                    server=self.server,
                    comm=comm.comm,
                    status=comm.status,
                    item=item.name,
                    amount=item.amount
                )
