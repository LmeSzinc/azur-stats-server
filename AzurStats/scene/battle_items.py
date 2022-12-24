from dataclasses import dataclass

from AzurStats.image.battle_status import BattleStatus
from AzurStats.image.get_items import GetItems
from AzurStats.scene.base import SceneBase


@dataclass
class DataBattleItems:
    imgid: str
    server: str

    # Enemy name, such as `中型主力舰队`, `敌方旗舰`
    enemy: str
    # Battle status: S, A, B, C, D, CF
    status: str

    item: str
    amount: int


class SceneBattleItems(SceneBase, BattleStatus, GetItems):
    ITEM_TEMPLATE_FOLDER = './assets/stats/battle_items'

    def extract_assets(self):
        if not self.is_battle_status(self.first):
            return

        for image in self.followings:
            if self.is_get_items(image):
                self.extract_item_template(image)

    def parse_scene(self):
        if not self.is_battle_status(self.first):
            return []

        status = self.parse_battle_status(self.first)
        for image in self.followings:
            if self.is_get_items(image):
                items = self.parse_get_items(image, name=True, amount=True, tag=False)
                for item in items:
                    yield DataBattleItems(
                        imgid=self.imgid,
                        server=self.server,
                        enemy=status.enemy,
                        status=status.status,
                        item=item.name,
                        amount=item.amount
                    )
            # Should only have 1 get_items image
            return
