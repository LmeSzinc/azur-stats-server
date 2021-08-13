import json
import os
import re
import urllib.parse
from io import BytesIO

import requests
from PIL import Image
from ruia import AttrField, TextField, Item, Spider, Request, HtmlField

ASSETS_FOLDER = './AzurStats/research4/assets'
EQUIPMENT_IMAGES = './AzurStats/equipment/assets'
PROTECT_NAMES = ['Blueprint', 'SpecializedCores', 'Retrofit', 'CognitiveChips', 'Coins']


def en_to_name(name):
    return re.subn('[-\:\.\\\/\"\(\) ]', '_', name)[0] \
        .strip('_').replace('__', '_').replace('__', '_').replace('__', '_')


class EquipListItem(Item):
    target_item = HtmlField(xpath_select='//*[@id="mw-content-text"]/div[1]/ul[1]')
    url = AttrField('href', xpath_select='./li/a', many=True)


class EquipEntranceItem(Item):
    target_item = HtmlField(xpath_select='//div[@title="Min Stats"]/table/tbody/tr/td[1]')
    url = AttrField('href', xpath_select='./a', many=True)


JSON_DATA = {}


class EquipItem(Item):
    target_item = HtmlField(xpath_select='//div[@class="eq-head"]')
    cn = TextField(xpath_select='.//span[@lang="zh"]', default='CN:default_cn_name')
    en = TextField(xpath_select='.//span[@lang="en"]', default='EN:default_en_name')
    rarity = AttrField('title', xpath_select='.//div[@class="eq-info"]//tr[2]//a')
    tier = TextField(xpath_select='.//div[contains(@class, "eqtech")]')
    image = AttrField('src', xpath_select='.//div[contains(@class, "eq-icon")]//img')


class WikiCrawler(Spider):
    site = 'https://azurlane.koumakan.jp'
    start_urls = ['https://azurlane.koumakan.jp/Equipment_List']

    # start_urls = ['https://azurlane.koumakan.jp/List_of_Destroyer_Guns']
    # start_urls = ['https://azurlane.koumakan.jp/Triple_305mm_(SK_C/39_Prototype)']

    async def parse(self, response):
        # await self.parse_equip(response)
        html = await response.text()
        async for item in EquipListItem.get_items(html=html):
            for url in item.url:
                yield Request(self.site + url, callback=self.list_to_item)

    async def list_to_item(self, response):
        html = await response.text()
        async for item in EquipEntranceItem.get_items(html=html):
            for url in item.url:
                url = urllib.parse.unquote(url)
                yield Request(self.site + url, callback=self.parse_equip)

    async def parse_equip(self, response):
        html = await response.text()
        try:
            async for item in EquipItem.get_items(html=html):
                name = en_to_name(item.en.split(':', 1)[1]) + '_' + item.tier
                data = {
                    'name': name,
                    'cn': item.cn.split(':', 1)[1] + item.tier,
                    'en': item.en.split(':', 1)[1] + ' ' + item.tier,
                    'rarity': item.rarity.replace(' ', '').capitalize(),
                    'tier': item.tier,
                    'image': self.site + item.image,
                }
                # print(data)
                JSON_DATA[name] = data
        except:
            print(f'Error in {response}')


def download_images():
    for data in JSON_DATA.values():
        print(f'Downloading {data["image"]}')
        url = data['image']
        name = data["name"].rsplit('_', 1)[0]

        file = os.path.join(EQUIPMENT_IMAGES, f'{name}.png')
        if os.path.exists(file):
            print(file)
            continue
        resp = requests.get(url)
        if resp.status_code == 200:
            image = Image.open(BytesIO(resp.content))
            image = image.resize((40, 40))
            image.save(file)
        else:
            print(f'Error while downloading {data["name"]}, {resp.status_code}, {resp.text}')
            return None


def translate_names(folder=ASSETS_FOLDER):
    for file in os.listdir(folder):
        file = os.path.join(folder, file)
        name = os.path.splitext(os.path.basename(file))[0]
        if any([protect in name for protect in PROTECT_NAMES]):
            continue
        if '_' in name and name.rsplit('_', 1)[1].isdigit():
            continue
        if name.isdigit():
            print(f'{name} is still in digit')

        matched = None
        for equip in JSON_DATA.values():
            if any([equip['cn'] == name, equip['en'] == name]):
                matched = equip['name']
                break
        if matched is None:
            print(f'Unable to translate {name}')
            continue

        if name != matched:
            name += '.png'
            matched += '.png'
            print(f'Rename {name} to {matched}')
            os.rename(os.path.join(ASSETS_FOLDER, name), os.path.join(ASSETS_FOLDER, matched))


def insert_data():
    import pymysql
    from AzurStats.config.config import CONFIG
    connection = pymysql.connect(**CONFIG['database'])
    data = [(equip['name'], f'Equipment{equip["rarity"]}', 'Equipment') for equip in JSON_DATA.values()]
    try:
        with connection.cursor() as cursor:
            sql = f"""
            INSERT INTO items_group (item, group1, group2)
            VALUES (%s, %s, %s)
            """
            cursor.executemany(sql, data)
            connection.commit()
    finally:
        connection.close()


file = './AzurStats/equipment/data.json'
if __name__ == '__main__':
    # WikiCrawler.start()
    # with open(file, 'w', encoding='utf-8') as f:
    #     json.dump(JSON_DATA, f, indent=2, ensure_ascii=False)

    os.chdir('../../')
    with open(file, 'r', encoding='utf-8') as f:
        JSON_DATA = json.load(f)

    # download_images()

    # translate_names()

    insert_data()
