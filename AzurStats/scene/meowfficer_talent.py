from dataclasses import dataclass

from AzurStats.image.meowfficer_drop import MeowfficerDrop, DataMeowfficerDrops
from AzurStats.image.meowfficer_talent import MeowfficerTalent
from AzurStats.scene.base import SceneBase


@dataclass
class DataMeowfficerTalents:
    imgid: str
    server: str
    name: str
    rarity: int
    talent_name: str
    talent_genre: str
    talent_level: int


class SceneMeowfficerTalent(SceneBase, MeowfficerDrop, MeowfficerTalent):
    meowfficer_drop: DataMeowfficerDrops

    def parse_scene(self):
        """
        Returns:
            Iter[DataMeowfficerTalents]:

        Raises:
            MeowfficerNonCnDiscarded:
            MeowfficerNameInvalid:
            MeowfficerTalentInvalid:
        """
        if not self.is_meowfficer_drop(self.first):
            return []

        if len(self.followings):
            meow = self.parse_meowfficer_drop(self.followings[0])
        else:
            meow = self.parse_meowfficer_drop(self.first)
        self.meowfficer_drop = meow
        for image in self.followings:
            talent = self.parse_meowfficer_talent(image)
            yield DataMeowfficerTalents(
                imgid=self.imgid,
                server=self.server,
                name=meow.name,
                rarity=meow.rarity,
                talent_name=talent.talent_name,
                talent_genre=talent.talent_genre,
                talent_level=talent.talent_level
            )
