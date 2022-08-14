import re
from dataclasses import dataclass

from AzurStats.database.base import AzurStatsDatabase
from module.base.decorator import cached_property
from module.config.utils import deep_get, deep_set, deep_iter
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.research.project import ResearchProject, ResearchProjectJp

REGEX_PROJECT_FILTER = re.compile(r'-(\d.\d|\d\d?)$')


@dataclass
class DataResearchItemResult:
    series: int
    project: str
    item: str
    tag: str
    samples: int
    drop_count: int
    drop_total: int
    drop_min: int
    drop_max: int

    def __post_init__(self):
        self.drop_count = int(self.drop_count)
        self.drop_total = int(self.drop_total)
        self.drop_min = int(self.drop_min)
        self.drop_max = int(self.drop_max)


def to_range(lower, upper, samples=1, count=1):
    if count / samples < 0.98:
        lower = 0
    if lower == 0 and upper == 0:
        return '0'
    elif lower == upper:
        return str(lower)
    else:
        return f'{lower}~{upper}'


def pretty(data):
    # Keep 3 significant digits
    if data == 0:
        return None
    elif data >= 10:
        return round(data, 1)
    elif data >= 1:
        return round(data, 2)
    elif data >= 0.1:
        return round(data, 3)
    else:
        return round(data, 4)


def merge_min(prev, new):
    if prev == 0:
        return new
    elif new > 0:
        return min(prev, new)
    else:
        return prev


def equipment_to_image(name):
    if '_' in name:
        pre, suffix = name.rsplit('_', 1)
        if suffix in ['T1', 'T2', 'T3', 'T0']:
            name = pre
    return name


@dataclass
class DataResearchItemRow:
    series: int
    project: str
    item: str
    tag: str
    samples: int
    drop_count: int
    drop_total: int
    drop_min: int
    drop_max: int
    bonus_count: int = 0
    bonus_total: int = 0
    bonus_min: int = 0
    bonus_max: int = 0

    def load_drop(self, data):
        self.samples += data.samples
        self.drop_count += data.drop_count
        self.drop_total += data.drop_total
        self.drop_min = merge_min(self.drop_min, data.drop_min)
        self.drop_max = max(self.drop_max, data.drop_max)
        self.bonus_count += data.bonus_count
        self.bonus_total += data.bonus_total
        self.bonus_min = merge_min(self.bonus_min, data.bonus_min)
        self.bonus_max = max(self.bonus_max, data.bonus_max)

    def load_bonus(self, data: DataResearchItemResult):
        self.bonus_count = data.drop_count
        self.bonus_total = data.drop_total
        self.bonus_min = data.drop_min
        self.bonus_max = data.drop_max

    @cached_property
    def research_project(self):
        return ResearchProject(series=self.series, name=self.project)

    @cached_property
    def duration(self):
        res = REGEX_PROJECT_FILTER.search(self.project)
        if res:
            return float(res.group(1))
        else:
            return float(self.research_project.duration)

    @cached_property
    def is_valid(self):
        return not self.item.isdigit() and self.research_project.valid

    @cached_property
    def drop_avg(self):
        return self.drop_total / self.samples

    @cached_property
    def drop_range(self):
        return to_range(self.drop_min, self.drop_max, samples=self.samples, count=self.drop_count)

    @cached_property
    def bonus_avg(self):
        if self.bonus_count:
            return self.bonus_total / self.samples
        else:
            return 0.

    @cached_property
    def bonus_range(self):
        if self.bonus_count:
            return to_range(self.bonus_min, self.bonus_max, samples=self.samples, count=self.bonus_count)
        else:
            return None

    @cached_property
    def average(self):
        return self.drop_avg + self.bonus_avg

    @cached_property
    def hourly(self):
        return self.average / self.duration

    @cached_property
    def is_show(self):
        # Not enough samples
        return self.average > 0.001 and self.samples > 50

    @cached_property
    def output(self):
        """
        Generate output data
        """
        return dict(
            series=self.series,
            project=self.project,
            item=self.item,
            samples=self.samples,
            drop_avg=pretty(self.drop_avg),
            drop_range=self.drop_range,
            bonus_avg=pretty(self.bonus_avg),
            bonus_range=self.bonus_range,
            average=pretty(self.average),
            hourly=pretty(self.hourly),
        )


class StatsResearchItem(AzurStatsDatabase):
    @cached_property
    def raw_data(self) -> SelectedGrids(DataResearchItemResult):
        """
        Grouped results from database
        """

        sql = """
        SELECT
            base.series,
            base.project,
            base.item,
            base.tag,
            sample.samples AS samples,
            COUNT(distinct imgid) AS drop_count,
            SUM(base.amount) AS drop_total,
            MIN(base.amount) AS drop_min,
            MAX(base.amount) AS drop_max
        FROM research_items AS base
        LEFT JOIN (
            SELECT series, project, COUNT(DISTINCT imgid) AS samples
            FROM research_items
            GROUP BY series, project
            ORDER BY series, project
        ) AS sample
        ON base.series = sample.series AND base.project = sample.project
        WHERE ISNULL(tag) OR tag = "bonus"
        GROUP BY series, project, item, tag
        ORDER BY series, project, item, tag
        """
        data = self.query(sql, DataResearchItemResult)
        logger.info('raw_data')
        return data

    @cached_property
    def drop_data(self) -> SelectedGrids(DataResearchItemRow):
        """
        Left join BONUS
        """
        # Convert DataResearchItemResult to DataResearchItemRow
        # And remove invalid rows
        data = SelectedGrids([DataResearchItemRow(
            row.series,
            row.project,
            row.item,
            row.tag,
            row.samples,
            row.drop_count,
            row.drop_total,
            row.drop_min,
            row.drop_max
        ) for row in self.raw_data])
        data = data.select(is_valid=True)

        # Join bonus
        base = data.select(tag=None)
        bonus = data.select(tag='bonus')
        base.create_index('series', 'project', 'item')
        bonus.create_index('series', 'project', 'item')
        for key, base_row in base.indexes.items():
            base_row = base_row.first_or_none()
            bonus_row = bonus.indexed_select(*key).first_or_none()
            if bonus_row is not None:
                base_row.load_bonus(bonus_row)

        logger.info('drop_data')
        return base

    @cached_property
    def drop_result(self):
        """
        Returns:
            <series>: Research series, 1 to 5
                <item>: Item name, with item genre in it
                    <project>: Project name, with filter name in it
                        DataResearchItemRow
        """
        data = {}
        samples = {}

        def new_row(series, item, project):
            return DataResearchItemRow(
                series=series, project=project, item=item,
                tag='', samples=0, drop_count=0, drop_total=0, drop_min=0, drop_max=0
            )

        def load_drop(r, path):
            filter_row = deep_get(data, keys=path)
            if filter_row is None:
                filter_row = new_row(*path)
            filter_row.load_drop(r)
            deep_set(data, keys=path, value=filter_row)

        # Group project_filter
        for row in self.drop_data:
            row: DataResearchItemRow = row
            project_filter = self.DataResearchItemRow_to_FilterName(row)
            load_drop(row, [row.series, row.item, row.project])
            if project_filter is not None:
                load_drop(row, [row.series, row.item, project_filter])
        # Backup samples count
        for path, row in deep_iter(data, depth=3):
            series, _, project = path
            key = (series, project)
            samples[key] = max(samples.get(key, 0), row.samples)
        # Group project_filter, item_genre+project_filter
        for row in self.drop_data:
            row: DataResearchItemRow = row
            project_filter = self.DataResearchItemRow_to_FilterName(row)
            item_genre = self.ItemName_to_ItemGenre(row.item)
            if item_genre is not None:
                load_drop(row, [row.series, item_genre, row.project])
            if project_filter is not None and item_genre is not None:
                load_drop(row, [row.series, item_genre, project_filter])
        # Recover samples count
        for path, row in deep_iter(data, depth=3):
            series, _, project = path
            row.samples = samples[(series, project)]

        logger.info('drop_result')
        return data

    @cached_property
    def all_series(self):
        return list(self.drop_result.keys())

    @cached_property
    def drop_data_expanded(self):
        data = {}
        for path, row in deep_iter(self.drop_result, depth=3):
            _, _, project = path
            if not REGEX_PROJECT_FILTER.search(project):
                deep_set(data, keys=path, value=row)
        logger.info('drop_data_expanded')
        return data

    @cached_property
    def drop_data_collapsed(self):
        data = {}
        for path, row in deep_iter(self.drop_result, depth=3):
            _, _, project = path
            if REGEX_PROJECT_FILTER.search(project):
                deep_set(data, keys=path, value=row)
        logger.info('drop_data_collapsed')
        return data

    @cached_property
    def grouping_filter(self):
        """
        Returns:
            <series>: 1 to 5
                <grouping_filter>: GroupingFilter
                    <grouping>: Collapsed
                        "name": "Collapsed",
                        "image": "/Grouping/Collapsed.png"
        """
        data = {}
        for series in self.all_series:
            groupings = ['Collapsed', 'Expanded']
            for grouping in groupings:
                deep_set(
                    data,
                    keys=[series, 'GroupingFilter', grouping],
                    value=dict(
                        name=grouping,
                        image=f'/Grouping/{equipment_to_image(grouping)}.png'
                    )
                )
        return data

    @cached_property
    def blueprint_filter(self):
        """
        Returns:
            <series>: 1 to 5
                <blueprint_filter>: Blueprint
                    <item>: BlueprintPRY
                        "name": "BlueprintPRY",
                        "image": "/Blueprint/BlueprintPRY.png"
        """
        data = {}
        for series in self.all_series:
            has_dr = False
            for ship in getattr(ResearchProjectJp, f'SHIP_S{series}'):
                if ship in ResearchProjectJp.DR_SHIP:
                    has_dr = True
            if has_dr:
                blueprints = ['BlueprintDR', 'BlueprintPRY']
            else:
                blueprints = ['BlueprintPRY']
            for blueprint in blueprints:
                deep_set(
                    data,
                    keys=[series, 'Blueprint', blueprint],
                    value=dict(name=blueprint, image=f'/Blueprint/{blueprint}.png')
                )
        return data

    @cached_property
    def equipment_filter(self):
        """
        Returns:
            <series>: 1 to 5
                <equipment_filter>: EquipmentUltrarare
                    <item>: EquipmentUltrarare
                        "name": "EquipmentUltrarare",
                        "image": "/EquipmentRarity/EquipmentUltrarare.png"
        """
        data = {}
        for series in self.all_series:
            rarities = ['EquipmentUltrarare', 'EquipmentSuperrare', 'EquipmentElite', 'EquipmentRare']
            for rarity in rarities:
                deep_set(
                    data,
                    keys=[series, rarity, rarity],
                    value=dict(name=rarity, image=f'/EquipmentRarity/{rarity}.png')
                )
        for row in self.drop_data:
            row: DataResearchItemRow = row
            rarity = self.ItemName_to_ItemGenre(row.item)
            if rarity is None or not rarity.startswith('Equipment'):
                continue
            deep_set(
                data,
                keys=[row.series, rarity, row.item],
                value=dict(name=row.item, image=f'/Equipment/{equipment_to_image(row.item)}.png')
            )
        return data

    @cached_property
    def currency_filter(self):
        """
        Returns:
            <series>: 1 to 5
                <equipment_filter>: Currency
                    <item>: CognitiveChips
                        "name": "CognitiveChips",
                        "image": "/Currency/CognitiveChips.png"
        """
        data = {}
        items = ['CognitiveChips', 'Coins', 'SpecializedCores']
        for series in self.all_series:
            for item in items:
                deep_set(
                    data,
                    keys=[series, 'Currency', item],
                    value=dict(name=item, image=f'/Currency/{item}.png')
                )
            for tier in [3, 2, 1]:
                for ship in ['Destroyer', 'Cruiser', 'Battleship', 'Carrier']:
                    item = f'Retrofit{ship}T{tier}'
                    genre = self.ItemName_to_ItemGenre(item)
                    deep_set(
                        data,
                        keys=[series, genre, genre],
                        value=dict(name=genre, image=f'/Retrofit/{genre}.png')
                    )
                    deep_set(
                        data,
                        keys=[series, genre, item],
                        value=dict(name=item, image=f'/Retrofit/{item}.png')
                    )

        return data

    def get_i18n(self, *groupings):
        data = {}
        for grouping_filter in groupings:
            for path, row in deep_iter(grouping_filter, depth=3):
                series, grouping, item = path
                for lang in self.all_lang:
                    deep_set(data, keys=[lang, grouping], value=self.translate(grouping, lang))
                    deep_set(data, keys=[lang, item], value=self.translate(item, lang))
        for path, value in deep_iter(self.drop_result, depth=3):
            series, item, project = path
            for lang in self.all_lang:
                deep_set(data, keys=[lang, project], value=self.translate(project, lang))
        return data

    def get_default_filter(self, grouping):
        for path, value in deep_iter(grouping, depth=2):
            return value['name']

    def generate(self):
        def convert(rs):
            rs = SelectedGrids(list(rs.values()))
            rs = rs.select(is_show=True).sort('hourly')[::-1]
            return [r.output for r in rs]

        for path, rows in deep_iter(self.drop_data_expanded, depth=2):
            series, item = path
            self.output(convert(rows), f'ResearchS{series}', 'Expanded', f'{item}.json')
        for path, rows in deep_iter(self.drop_data_collapsed, depth=2):
            series, item = path
            self.output(convert(rows), f'ResearchS{series}', 'Collapsed', f'{item}.json')

        for series in self.all_series:
            data = dict(
                grouping_filter=self.grouping_filter[series],
                grouping_filter_default=self.get_default_filter(self.grouping_filter[series]),
                item_filter=self.blueprint_filter[series],
                item_filter_default=self.get_default_filter(self.blueprint_filter[series]),
                i18n=self.get_i18n(self.grouping_filter, self.blueprint_filter)
            )
            self.output(data, f'ResearchS{series}', f'blueprints.json')
            data = dict(
                grouping_filter=self.grouping_filter[series],
                grouping_filter_default=self.get_default_filter(self.grouping_filter[series]),
                item_filter=self.equipment_filter[series],
                item_filter_default=self.get_default_filter(self.equipment_filter[series]),
                i18n=self.get_i18n(self.grouping_filter, self.equipment_filter)
            )
            self.output(data, f'ResearchS{series}', f'equipments.json')
            data = dict(
                grouping_filter=self.grouping_filter[series],
                grouping_filter_default=self.get_default_filter(self.grouping_filter[series]),
                item_filter=self.currency_filter[series],
                item_filter_default=self.get_default_filter(self.currency_filter[series]),
                i18n=self.get_i18n(self.grouping_filter, self.currency_filter)
            )
            self.output(data, f'ResearchS{series}', f'others.json')
        logger.info('generate')


if __name__ == '__main__':
    self = StatsResearchItem()
    self.generate()
