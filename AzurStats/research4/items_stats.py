from decimal import Decimal

import pymysql

from AzurStats.research4.utils import *
from AzurStats.utils.utils import *
from module.research.project import *


def format_number(n):
    if isinstance(n, Decimal):
        n = float(n)
    if isinstance(n, float):
        if n > 0.1:
            return round(n, 3)
        else:
            return float(f'{n:.3g}')
    return n


class ItemGroup:
    DEFAULT_GROUP = [
        ('ByGenreduration', 'ResearchGroup', 'ResearchGroup'),
        ('ByGenre', 'ResearchGroup', 'ResearchGroup'),
        ('ByDuration', 'ResearchGroup', 'ResearchGroup'),
        ('ByProject', 'ResearchGroup', 'ResearchGroup'),
    ]

    def __init__(self):
        self.item_to_group1 = {}
        self.item_to_group2 = {}
        connection = pymysql.connect(**CONFIG['database'])
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT item, group1, group2 FROM items_group
                """
                cursor.execute(sql)
                res = cursor.fetchall()
        finally:
            connection.close()
        for item, group1, group2 in res:
            self.item_to_group1[item] = group1
            self.item_to_group1[group1] = group1
            self.item_to_group2[item] = group2
            self.item_to_group2[group1] = group2
            self.item_to_group2[group2] = group2
        for item, group1, group2 in self.DEFAULT_GROUP:
            self.item_to_group1[item] = group1
            self.item_to_group1[group1] = group1
            self.item_to_group2[item] = group2
            self.item_to_group2[group1] = group2
            self.item_to_group2[group2] = group2

        # self.items_group = {
        #     'EquipmentUltrarare': {
        #         'EquipmentUltrarare': {'name': 'EquipmentUltrarare', 'image': '/Equipment/EquipmentUltrarare'},
        #         'Prototype_Tenrai_T0': {'name': 'Prototype_Tenrai_T0', 'image': '/Equipment/Prototype_Tenrai_T0'},
        #     },
        #     'EquipmentSuperrare': {...}
        # }
        self.items_group = dict()
        # self.data_group = {
        #     'ResearchGroup': {
        #         'ByGenreduration': {'name': 'ByGenreduration', 'image': None},
        #         'ByGenre': {'name': 'ByGenre', 'image': None},
        #         'ByDuration': {'name': 'ByDuration', 'image': None},
        #         'ByProject': {'name': 'ByProject', 'image': None},
        #     }
        # }
        self.data_group = dict()
        # self.i18n = {
        #     'zh-CN': {
        #         'EquipmentUltrarare': '彩色装备',
        #         'Prototype_Tenrai_T0': '试作舰载型天雷T0',
        #         'ByGenreduration': '按类别和时长',
        #         'ByGenre': '按类别',
        #         'ByDuration': '按时长',
        #         'ByProject': '展开全部',
        #     },
        #     'en-US': {
        #         'EquipmentUltrarare': 'Ultra Rare Equipments',
        #         'Prototype_Tenrai_T0': 'Prototype Tenrai T0',
        #         'ByGenreduration': 'By Genre and Duration',
        #         'ByGenre': 'By Genre',
        #         'ByDuration': 'By Duration',
        #         'ByProject': 'Show All',
        #     }
        # }
        self.i18n = {
            'zh-CN': {},
            'en-US': {}
        }

    def _name_to_i18n(self, name, lang, lang_short):
        """
        Args:
            name (str):
            lang (str): Such as `zh-CN`
            lang_short (str): Such as `cn`

        Returns:
            str: Translation, or original name if translation not found
        """
        i18n = DEFAULT_I18N[lang].get(name, None)
        if i18n is None and self.item_to_group2.get(name, '') == 'Equipment' and name in EQUIPMENT_DATA:
            i18n = EQUIPMENT_DATA[name][lang_short]
        return i18n if i18n is not None else name

    def add_i18n(self, name):
        self.i18n['zh-CN'][name] = self._name_to_i18n(name, lang='zh-CN', lang_short='cn')
        self.i18n['en-US'][name] = self._name_to_i18n(name, lang='en-US', lang_short='en')

    def add_i18n_project(self, name):
        self.i18n['zh-CN'][name] = name_to_i18n_project(name, lang='zh-CN')
        self.i18n['en-US'][name] = name_to_i18n_project(name, lang='en-US')

    def _name_to_image(self, name):
        group2 = self.item_to_group2.get(name, 'Default')
        if '_' in name:
            pre, suffix = name.rsplit('_', 1)
            if suffix in ['T1', 'T2', 'T3', 'T0']:
                name = pre
        return f'/{group2}/{name}.png'

    def add_data_group(self, name):
        group1 = self.item_to_group1.get(name, 'Default')
        self.add_i18n(group1)
        option = {
            'name': name,
            'image': self._name_to_image(name)
        }
        if group1 not in self.data_group:
            self.data_group[group1] = {}
        self.data_group[group1][name] = option

    def add_items_group(self, name):
        group1 = self.item_to_group1.get(name, 'Default')
        self.add_i18n(group1)
        option = {
            'name': name,
            'image': self._name_to_image(name)
        }
        if group1 not in self.items_group:
            self.items_group[group1] = {}
        self.items_group[group1][name] = option

    def gen_data(self, data):
        self.items_group = {}
        self.data_group = {}
        self.i18n = {
            'zh-CN': {},
            'en-US': {}
        }
        for data_group_name, data_group in data.items():
            self.add_data_group(data_group_name)
            self.add_i18n(data_group_name)
            for row in data_group:
                name = row.get('item', 'Default')
                self.add_items_group(name)
                self.add_i18n(name)
                self.add_i18n_project(row['project'])

        self.items_group = {k: list(v.values()) for k, v in self.items_group.items()}
        self.data_group = {k: list(v.values()) for k, v in self.data_group.items()}
        return {
            'items_group': self.items_group,
            'data_group': self.data_group,
            'data': data,
            'i18n': self.i18n
        }

    def _pick_data(self, data, group1_list):
        out = []
        for group1 in group1_list:
            out += [row for row in data if
                    self.item_to_group1.get(row.get('item', 'Default'), 'Default') == group1 and row.get('item',
                                                                                                         'Default') != 'Currency']
        return out

    def pick_data(self, data, group1_list):
        return {k: self._pick_data(v, group1_list) for k, v in data.items()}


class ItemStatsGenerator:
    def __init__(self):
        column = 'item, project, samples, drop_rate, drop_min, drop_max, drop_avg,' \
                 'bonus_rate, bonus_min, bonus_max, bonus_avg, average, hourly'
        self.column = column.replace(' ', '').split(',')
        self.blueprints = []

    def sql(self, item, project):
        return f"""
        SELECT
            ig1.{item} AS item,
            rg1.{project} AS project,
            sample_mixin.samples,
            COUNT(amount) / sample_mixin.samples AS drop_rate,
            MIN(amount) AS drop_min,
            MAX(amount) AS drop_max,
            AVG(amount) AS drop_avg,
            bonus_mixin.bonus_count / sample_mixin.samples AS bonus_rate,
            bonus_mixin.bonus_min AS bonus_min,
            bonus_mixin.bonus_max AS bonus_max,
            bonus_mixin.bonus_avg AS bonus_avg,
            (AVG(amount) * COUNT(amount) + IFNULL(bonus_mixin.bonus_avg, 0) * IFNULL(bonus_mixin.bonus_count, 0)) / sample_mixin.samples AS average,
            (AVG(amount) * COUNT(amount) + IFNULL(bonus_mixin.bonus_avg, 0) * IFNULL(bonus_mixin.bonus_count, 0)) / sample_mixin.samples / rg1.duration AS hourly
        FROM research4_items AS stats LEFT JOIN items_group AS ig1 ON stats.item = ig1.item LEFT JOIN research_group AS rg1 ON stats.project = rg1.project AND stats.series = rg1.series
        LEFT JOIN (
            SELECT rg3.{project}, COUNT(DISTINCT imgid) AS samples
            FROM research4_items AS sample LEFT JOIN research_group AS rg3 ON sample.project = rg3.project AND sample.series = rg3.series
            WHERE sample.series = 4 AND valid = 1 AND tag IS NULL
            GROUP BY rg3.{project}
        ) AS sample_mixin
        ON sample_mixin.{project} = rg1.{project}
        LEFT JOIN (
            SELECT
                ig2.{item},
                rg2.{project},
                COUNT(amount) AS bonus_count,
                MIN(amount) AS bonus_min,
                MAX(amount) AS bonus_max,
                AVG(amount) AS bonus_avg
            FROM research4_items AS bonus LEFT JOIN items_group AS ig2 ON bonus.item = ig2.item LEFT JOIN research_group AS rg2 ON bonus.project = rg2.project AND bonus.series = rg2.series
            WHERE bonus.series = 4 AND valid = 1 AND tag = 'bonus'
            GROUP BY ig2.{item}, rg2.{project}
        ) AS bonus_mixin
        ON bonus_mixin.{item} = ig1.{item} AND bonus_mixin.{project} = rg1.{project}
        WHERE stats.series = 4 AND valid = 1 AND tag IS NULL AND ig1.{item} IS NOT NULL AND rg1.{project} IS NOT NULL
        GROUP BY ig1.{item}, rg1.{project}
        ORDER BY ig1.{item} ASC, rg1.{project} ASC 
        ;
        """

    def get_data(self):
        data = {}
        connection = pymysql.connect(**CONFIG['database'])
        try:
            with connection.cursor() as cursor:
                for project in ['genre_duration', 'genre', 'duration', 'project']:
                    for item in ['group1', 'item']:
                        cursor.execute(self.sql(item=item, project=project))
                        key = f'By{project.replace("_", "").capitalize()}'
                        data[key] = data.get(key, []) + self.result_to_json(cursor.fetchall())

        finally:
            connection.close()

        return data

    def result_to_json(self, data):
        list_data = []
        for row in data:
            row = {k: v for k, v in zip(self.column, row)}
            for key, value in row.items():
                if isinstance(value, Decimal) or isinstance(value, float):
                    value = format_number(value)
                    row[key] = value
                if key == 'project':
                    if isinstance(value, float):
                        row[key] = f'{str(value).rstrip(".0")}'
                #     elif isinstance(value, str) and value.count('-') == 1:
                #         genre, duration = value.split('-', 1)
                #         row[key] = f'{genre.rjust(2)}-{duration.ljust(3)}'
            list_data.append(row)
        return list_data

    def run(self):
        logger.info('Generate research4 blueprint data')
        data = self.get_data()

        logger.info('Splitting data')
        ig = ItemGroup()
        write_json(
            ig.gen_data(ig.pick_data(data, group1_list=['BlueprintS4DR', 'BlueprintS4PRY'])),
            'research4_blueprints'
        )
        write_json(
            ig.gen_data(ig.pick_data(data, group1_list=['EquipmentUltrarare', 'EquipmentSuperrare', 'EquipmentElite',
                                                        'EquipmentRare', 'EquipmentNormal'])),
            'research4_equipments'
        )
        write_json(
            ig.gen_data(ig.pick_data(data, group1_list=['Currency', 'RetrofitT3', 'RetrofitT2', 'RetrofitT1'])),
            'research4_others'
        )
