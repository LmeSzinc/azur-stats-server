import re
from dataclasses import dataclass

from AzurStats.image.base import ImageBase
from module.azur_stats.assets import BATTLE_STATUS_ENEMY_NAME
from module.combat.assets import BATTLE_STATUS_S, BATTLE_STATUS_A, BATTLE_STATUS_B, BATTLE_STATUS_C, BATTLE_STATUS_D
from module.ocr.ocr import Ocr


@dataclass
class DataBattleStatus:
    # Enemy name, such as `中型主力舰队`, `敌方旗舰`
    enemy: str
    # Battle status: S, A, B, C, D, CF
    status: str


OCR_ENEMY_NAME = Ocr(BATTLE_STATUS_ENEMY_NAME, lang='cnocr', threshold=128, name='OCR_ENEMY_NAME')
REGEX_COMMA = re.compile(r'[,.\'"，。、 一个―~(]')


class BattleStatus(ImageBase):
    def is_battle_status(self, image) -> bool:
        status = bool(self._parse_battle_status(image))
        # BATTLE_STATUS detection is using appear_on, cannot classify server
        # Use 'cn' always
        if status:
            self.server = 'cn'
        return status

    def parse_battle_status(self, image) -> DataBattleStatus:
        status = self._parse_battle_status(image)
        enemy = self._parse_enemy_name(image)
        return DataBattleStatus(
            enemy=enemy,
            status=status,
        )

    def _parse_battle_status(self, image) -> str:
        """
        Args:
            image:

        Returns:
            str: Battle status: S, A, B, C, D, CF, or ''
        """
        if BATTLE_STATUS_S.appear_on(image):
            return 'S'
        if BATTLE_STATUS_A.appear_on(image):
            return 'A'
        if BATTLE_STATUS_B.appear_on(image):
            return 'B'
        if BATTLE_STATUS_C.appear_on(image):
            return 'C'
        if BATTLE_STATUS_D.appear_on(image):
            return 'D'
        return ''

    def _parse_enemy_name(self, image) -> str:
        """
        Args:
            image:

        Returns:
            str: Enemy name, such as `中型主力舰队`, `敌方旗舰`
        """
        name = OCR_ENEMY_NAME.ocr(image)
        # Delete wrong OCR result
        name = REGEX_COMMA.sub('', name)
        return name
