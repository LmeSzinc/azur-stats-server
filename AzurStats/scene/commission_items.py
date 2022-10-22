import typing as t
from dataclasses import dataclass

from AzurStats.image.commission_status import CommissionStatus, DataCommissionStatus
from AzurStats.image.get_items import GetItems
from AzurStats.scene.base import SceneBase
from module.base.decorator import cached_property
from module.statistics.item import Item, ItemGrid
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


class CommissionItemAmountInvalid(ImageError):
    pass


class SceneCommissionItems(SceneBase, CommissionStatus, GetItems):
    ITEM_TEMPLATE_FOLDER = './assets/stats/commission_items'
    finished_commission: DataCommissionStatus = None

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
                    self.finished_commission = comm
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

    def before_revise_items(self, items: t.List[Item]) -> t.List[Item]:
        comm = self.finished_commission.comm

        def convert_night(n, i, lower, higher):
            if self.finished_commission.comm == n and item.name == i and lower <= item.amount <= higher:
                if not self.finished_commission.comm.endswith(' N'):
                    self.finished_commission.comm += ' N'

        for item in items:
            # Change extra commissions to night commissions
            convert_night('Small Merchant Escort', 'Coins', 260, 450)
            convert_night('Medium Merchant Escort', 'Coins', 300, 550)
            convert_night('Large Merchant Escort', 'Coins', 350, 660)
            convert_night('Coastal Defense Patrol', 'Oil', 65, 105)
            convert_night('Buoy Inspection', 'Oil', 100, 160)
            convert_night('Frontier Defense Patrol', 'Oil', 150, 230)

            # In JP, Gems-8 and Gems-2 have the same name,
            # so separate them using the amount of gems and oil
            if item.name == 'Gems':
                if comm == 'BIW VIP Escort' and 50 <= item.amount <= 80:
                    self.finished_commission.comm = 'BIW Patrol Escort'
                if comm == 'NYB VIP Escort' and 50 <= item.amount <= 80:
                    self.finished_commission.comm = 'NYB Patrol Escort'
            if item.name == 'Oil':
                if comm == 'BIW VIP Escort' and 480 <= item.amount <= 720:
                    self.finished_commission.comm = 'BIW Patrol Escort'
                if comm == 'NYB VIP Escort' and 480 <= item.amount <= 720:
                    self.finished_commission.comm = 'NYB Patrol Escort'
            if item.name == 'Coins':
                # Re-arrange `Cargo Defense ⅠⅡⅢ` by coins
                if comm.startswith('Cargo Defense'):
                    if 50 <= item.amount <= 80:
                        self.finished_commission.comm = 'Cargo Defense Ⅰ'
                    if 85 <= item.amount <= 125:
                        self.finished_commission.comm = 'Cargo Defense Ⅱ'
                    if 145 <= item.amount <= 225:
                        self.finished_commission.comm = 'Cargo Defense Ⅲ'
                # Re-arrange `Cargo Defense ⅠⅡⅢ` by coins
                # 20~40, 40~85, 70~190
                if comm == 'Forest Protection Commission Ⅱ':
                    if 20 <= item.amount <= 39:
                        self.finished_commission.comm = 'Forest Protection Commission Ⅰ'
                    if 86 <= item.amount <= 190:
                        self.finished_commission.comm = 'Forest Protection Commission Ⅲ'
                if comm == 'Vein Protection Commission Ⅱ':
                    if 20 <= item.amount <= 39:
                        self.finished_commission.comm = 'Vein Protection Commission Ⅰ'
                    if 86 <= item.amount <= 190:
                        self.finished_commission.comm = 'Vein Protection Commission Ⅲ'
                if comm == 'Forest Protection Commission Ⅲ':
                    if 20 <= item.amount <= 39:
                        self.finished_commission.comm = 'Forest Protection Commission Ⅰ'
                    if 41 <= item.amount <= 69:
                        self.finished_commission.comm = 'Forest Protection Commission Ⅱ'
                if comm == 'Vein Protection Commission Ⅲ':
                    if 20 <= item.amount <= 39:
                        self.finished_commission.comm = 'Vein Protection Commission Ⅰ'
                    if 41 <= item.amount <= 69:
                        self.finished_commission.comm = 'Vein Protection Commission Ⅱ'

        return items

    def revise_item(self, item: Item) -> Item:

        def raise_limit(lower, higher):
            if not (higher >= item.amount >= lower):
                raise CommissionItemAmountInvalid(
                    f'"{item.name}" from "{self.finished_commission.comm}" should be {lower}~{higher} but get {item.amount}'
                )

        comm = self.finished_commission.comm
        if item.name == 'CognitiveChips':
            # 44xx -> xx
            if 4500 > item.amount > 4400:
                item.amount %= 100
            # 41xx -> xx
            if item.amount > 1000:
                item.amount %= 100
            # 4xx -> xx, 2xx -> xx, 1xx -> xx
            if 1000 > item.amount:
                item.amount %= 100
            # 8x -> 3x
            if 80 >= item.amount > 70:
                item.amount = 30 + item.amount % 10
            # Can only get 32 at max
            if 80 > item.amount > 32:
                item.amount %= 10

            # Awakening Tactical Research Ⅰ is 10~18
            if comm == 'Awakening Tactical Research Ⅰ':
                if item.amount < 10:
                    item.amount += 10
                raise_limit(10, 18)
            # Awakening Tactical Research Ⅱ is 24~32
            if comm == 'Awakening Tactical Research Ⅱ':
                if item.amount == 0:
                    item.amount = 30
                if item.amount <= 3:
                    item.amount *= 10
                raise_limit(24, 32)
            # 0~2
            if comm == 'Short-range Sailing Training':
                item.amount %= 10
            # 2~4
            if comm == 'Mid-range Sailing Training':
                item.amount %= 10
            # 4~10
            if comm == 'Long-range Sailing Training':
                if item.amount == 0:
                    item.amount = 10
                if item.amount <= 1:
                    item.amount *= 10
                if item.amount > 10:
                    item.amount %= 10
            # 4~8
            if comm == 'Coastal Defense Patrol':
                item.amount %= 10
            # 18~24
            if comm == 'Coastal Defense Patrol N':
                if item.amount == 0:
                    item.amount = 20
                if item.amount <= 2:
                    item.amount *= 10
            # 8~14
            if comm == 'Buoy Inspection':
                if item.amount == 0:
                    item.amount = 10
                if item.amount <= 1:
                    item.amount *= 10
                if item.amount > 14:
                    item.amount %= 10
            # 20~28
            if comm == 'Buoy Inspection N':
                if item.amount == 0:
                    item.amount = 20
                if item.amount <= 2:
                    item.amount *= 10
            # 14~22
            if comm == 'Frontier Defense Patrol':
                if item.amount == 0:
                    item.amount = 20
                if item.amount <= 2:
                    item.amount *= 10
            # 22~32
            if comm == 'Frontier Defense Patrol N':
                if item.amount == 0:
                    item.amount = 30
                if item.amount <= 3:
                    item.amount *= 10
                if item.amount < 10:
                    item.amount += 20

        # Cubes always < 10
        if item.name == 'Cubes' and item.amount > 10:
            item.amount %= 10

        if item.name == 'Coins' or item.name == 'Oil':
            if comm == 'Awakening Tactical Research Ⅰ':
                raise_limit(50, 80)
            if comm == 'Awakening Tactical Research Ⅱ':
                raise_limit(100, 170)
            # Cannot distinguish daily commissions, drop all errors
            if comm == 'Daily Resource Extraction Ⅰ':
                raise_limit(50, 80)
            if comm == 'Daily Resource Extraction Ⅱ':
                raise_limit(100, 170)
            if comm == 'Daily Resource Extraction Ⅲ':
                raise_limit(60, 90)
            if comm == 'Daily Resource Extraction Ⅳ':
                raise_limit(120, 200)
            if comm == 'Daily Resource Extraction Ⅴ':
                raise_limit(70, 100)
            if comm == 'Daily Resource Extraction Ⅵ':
                raise_limit(140, 220)
        if item.name == 'Coins':
            # Major commissions
            if comm in [
                'Cargo Transport Ⅲ',
                'Defense Exercise Ⅲ',
                'Research Mission Ⅲ',
                'Self Training Ⅲ',
                'Tactical Class Ⅲ',
                'Tool Prep Ⅲ',
            ]:
                raise_limit(4500, 6000)
            # 20~40, 40~85, 70~190
            if comm == 'Forest Protection Commission Ⅱ':
                raise_limit(40, 85)
            if comm == 'Vein Protection Commission Ⅱ':
                raise_limit(40, 85)
            if comm == 'Forest Protection Commission Ⅲ':
                raise_limit(70, 190)
            if comm == 'Vein Protection Commission Ⅲ':
                raise_limit(70, 190)
            # extra_book
            # Too many samples larger than limit, not determined
            # if comm == 'Small Merchant Escort':
            #     raise_limit(210, 350)
            # if comm == 'Medium Merchant Escort':
            #     raise_limit(260, 450)
            if comm == 'Large Merchant Escort':
                raise_limit(350, 660)
            # Launch Ceremony
            if comm == 'Small Launch Ceremony':
                raise_limit(420, 540)
            if comm == 'Fleet Launch Ceremony':
                raise_limit(880, 1040)
            if comm == 'Alliance Launch Ceremony':
                raise_limit(1760, 2000)
        if item.name == 'Oil':
            # Oil extraction
            if comm == 'Small-scale Oil Extraction Ⅰ':
                raise_limit(15, 30)
            if comm == 'Small-scale Oil Extraction Ⅱ':
                raise_limit(20, 40)
            if comm == 'Small-scale Oil Extraction Ⅲ':
                raise_limit(25, 50)
            if comm == 'Mid-scale Oil Extraction Ⅰ':
                raise_limit(80, 140)
            if comm == 'Mid-scale Oil Extraction Ⅱ':
                raise_limit(100, 180)
            if comm == 'Mid-scale Oil Extraction Ⅲ':
                raise_limit(120, 220)
            if comm == 'Large-scale Oil Extraction Ⅰ':
                raise_limit(150, 300)
            if comm == 'Large-scale Oil Extraction Ⅱ':
                raise_limit(200, 400)
            if comm == 'Large-scale Oil Extraction Ⅲ':
                raise_limit(250, 500)
            # extra_drill
            if comm == 'Coastal Defense Patrol':
                raise_limit(12, 28)
            if comm == 'Buoy Inspection':
                raise_limit(15, 35)
            if comm == 'Frontier Defense Patrol':
                raise_limit(25, 55)

        return item
