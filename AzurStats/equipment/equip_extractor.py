import json
import os
import re
import urllib.parse
from io import BytesIO

import requests
from PIL import Image

from AzurStats.research4.research4_items import ASSETS_FOLDER
from module.logger import logger

EQUIPMENT_DATA = './AzurStats/equipment/equipments.json'
EQUIPMENT_IMAGES = './AzurStats/equipment/assets'


class EquipItem:
    REGEX_NAME = re.compile('(T0|T1|T2|T3)$')

    def __init__(self, data):
        self.data = data
        self.image = data['image']
        self.wiki = data['wikiUrl']
        self.en = data['names']['en']
        self.cn = data['names']['cn']
        self.name = re.subn('[-\.\\\/\"\(\) ]', '_', self.en)[0] \
            .strip('_').replace('__', '_').replace('__', '_').replace('__', '_')

    def _download(self, url):
        logger.info(f'Downloading {url}')
        resp = requests.get(url)
        if resp.status_code == 200:
            image = Image.open(BytesIO(resp.content))
            return image
        else:
            logger.warning(f'Error while downloading {self.en}, {resp.status_code}, {resp.text}')
            return None

    def download_image(self):
        file = os.path.join(EQUIPMENT_IMAGES, f'{self.name}.png')
        if os.path.exists(file):
            return False
        url = self.image

        for _ in range(2):
            image = self._download(url)
            if image is not None:
                image = image.resize((40, 40))
                image.save(file)
                break
            else:
                # https://raw.githubusercontent.com/AzurAPI/azurapi-js-setup/master/images/equipments/Triple_406mm_1650_Mk_7.png
                # is actually at
                # https://raw.githubusercontent.com/AzurAPI/azurapi-js-setup/master/images/equipments/Triple_406mm_(16%22_50_Mk_7).png
                # Following the name in wiki
                wiki_name = urllib.parse.unquote(self.wiki.split('/', 3)[3]).replace('/', '_')
                path = self.image.rsplit('/', 1)[0]
                url = f'{path}/{wiki_name}.png'

    def expand_tier(self):
        """
        Returns:
            list[EquipTierItem]:
        """
        expand = [EquipTierItem(self, tier) for tier in self.data['tiers'] if tier is not None]
        if self.cn == '试作型三联装305mmSKC39主炮':
            # Prototype Triple 305mm SK C/39 Main Gun Mount
            # Odin gun and Agir gun
            extra = EquipItem(self.data)
            extra.cn += '(超巡用)'
            extra.en += ' CB'
            extra.name += '_CB'
            expand += [EquipTierItem(extra, tier) for tier in self.data['tiers'] if tier is not None]

        return expand

    def split_name_tier(self, name):
        res = re.search(self.REGEX_NAME, name)
        tier = res.group(1) if res else None
        name = re.sub(self.REGEX_NAME, '', name)
        name = name.strip(' _')
        return name, tier

    def match_name(self, name):
        name, tier = self.split_name_tier(name)
        if name == self.cn:
            return f'{self.cn}{tier}'
        elif name == self.en:
            return f'{self.cn} {tier}'
        else:
            return None


class EquipTierItem:
    def __init__(self, equip, tier):
        self.data = equip.data
        self.tier = f'T{tier["tier"]}'
        self.rarity = tier['rarity'].replace(' ', '').capitalize()
        self.name = f'{equip.name}_{self.tier}'
        self.cn = f'{equip.cn}{self.tier}'
        self.en = f'{equip.en} {self.tier}'
        self.image = f'/static/equip/{equip.name}.png'

    @property
    def selector_row(self):
        return {
            'name': self.name,
            'group': self.rarity,
            'image': self.image,
            'zh-CN': self.cn,
            'en-US': self.en
        }

    @property
    def database_row(self):
        pass

    def match_name(self, name):
        if name == self.cn:
            return True
        elif name == self.en:
            return True
        else:
            return False


class EquipExtractor:
    PROTECT_NAMES = ['Blueprint', 'SpecializedCores', 'Retrofit', 'CognitiveChips', 'Coins']

    def __init__(self):
        with open(EQUIPMENT_DATA, 'rb') as f:
            self.data = json.load(f)

        # Parse equipment data
        self.equipments = []
        for data in self.data:
            equip = EquipItem(data)
            self.equipments += equip.expand_tier()

    def translate_names(self, folder=ASSETS_FOLDER):
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            name = os.path.splitext(os.path.basename(file))[0]
            if any([protect in name for protect in self.PROTECT_NAMES]):
                continue
            if name.isdigit():
                logger.warning(f'{name} is still in digit')

            matched = None
            for equip in self.equipments:
                if equip.match_name(name):
                    matched = equip
                    break
            if matched is None:
                logger.warning(f'Unable to translate {name}')
                continue

            # if name != matched.name:
            #     logger.info(f'Rename {name} to {matched.name}')

    def init(self):
        for data in self.data:
            equip = EquipItem(data)
            equip.download_image()

if __name__ == '__main__':
    ex = EquipExtractor()
    ex.translate_names()