from AzurStats.database.const import GENRE_I18N
from module.base.decorator import cached_property
from module.config.utils import read_file, deep_iter
from module.research.project import ResearchProject, ResearchProjectJp
from module.research.project_data import LIST_RESEARCH_PROJECT


class ItemInfo:
    @cached_property
    def _dict_DataResearchItemRow_to_FilterName(self) -> dict:
        """
        Returns:
            dict: Key: (series, project), value: filter_name
        """
        data = {}
        for row in LIST_RESEARCH_PROJECT:
            project = ResearchProject(series=row['series'], name=row['name'])
            if project.ship_rarity:
                filter_name = f'{project.ship_rarity}-{project.duration}'.upper()
            else:
                filter_name = f'{project.genre}-{project.duration}'.upper()
            data[(project.raw_series, project.name)] = filter_name
        return data

    def DataResearchItemRow_to_FilterName(self, row) -> str:
        """
        Args:
            row (DataResearchItemRow):

        Returns:
            str: Filter name, Such as `DR-2.5`, `Q-4`,
                If failed to convert, return None.
        """
        return self._dict_DataResearchItemRow_to_FilterName.get((row.series, row.project), None)

    @cached_property
    def equip_data(self) -> dict:
        """
        Returns:
            <equipment>:
                "name": "Prototype_Twin_150mm_SK_C_28_Main_Gun_Mount_T0",
                "cn": "default_cn_nameT0",
                "en": "Prototype Twin 150mm SK C/28 Main Gun Mount T0",
                "rarity": "Superrare",
                "tier": "T0",
                "image": "https://azurlane.netojuu.com/images/b/b6/42080.png"
        """
        return read_file('./AzurStats/equipment/data.json')

    @cached_property
    def _dict_ItemName_to_ItemGenre(self) -> dict:
        data = {}
        # Equipments
        for equip, info in self.equip_data.items():
            data[equip] = f'Equipment{info["rarity"]}'
        # Blueprints
        for ship in ResearchProjectJp.SHIP_ALL:
            data[f'Blueprint{ship.capitalize()}'] = 'BlueprintPRY'
        for ship in ResearchProjectJp.DR_SHIP:
            # Alas internal uses hakuryu
            if ship == 'hakuryu':
                ship = 'hakuryuu'
            data[f'Blueprint{ship.capitalize()}'] = 'BlueprintDR'
        # Retrofit blueprints
        for tier in [1, 2, 3]:
            for ship in ['Destroyer', 'Cruiser', 'Battleship', 'Carrier']:
                data[f'Retrofit{ship}T{tier}'] = f'RetrofitT{tier}'
        return data

    def ItemName_to_ItemGenre(self, item: str) -> str:
        """
        Args:
            item: Item name, such as `Prototype_Triple_152mm_Mk_XXV_Main_Gun_Mount_T0`, `BlueprintHakuryuu`

        Returns:
            str: Item genre, such as `EquipmentUltrarare`, `BlueprintDR`
                If failed to convert, return None.
        """
        return self._dict_ItemName_to_ItemGenre.get(item, None)

    @cached_property
    def _i18n(self):
        """
        Returns:
            <lang>: zh-CN, en-US
                <name>:
                    translated
        """
        return read_file('./AzurStats/database/i18n.json')

    @cached_property
    def _dict_translate(self):
        """
        Returns:
            dict: Key: (name, lang), value: translated
        """
        data = {}
        # Equipments
        for equip, info in self.equip_data.items():
            name = info['cn']
            if name.startswith('default'):
                name = equip.replace('_', ' ')
            data[(equip, 'zh-CN')] = name
            name = info['en']
            if name.startswith('default'):
                name = equip.replace('_', ' ')
            data[(equip, 'en-US')] = name
        # Build-ins
        for path, value in deep_iter(self._i18n, depth=2):
            lang, name = path
            data[(name, lang)] = value
        # Research projects
        for path, value in deep_iter(GENRE_I18N, depth=2):
            lang, name = path
            for duration in [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
                data[(f'{name}-{duration}', lang)] = f'{value} {duration}H'
        return data

    @cached_property
    def all_lang(self):
        return list(self._i18n.keys())

    def translate(self, name: str, lang: str) -> str:
        """
        Args:
            name:
            lang: Language, zh-CN, en-US

        Returns:
            str: Translation or original name if unable to translate
        """
        return self._dict_translate.get((name, lang), name)
