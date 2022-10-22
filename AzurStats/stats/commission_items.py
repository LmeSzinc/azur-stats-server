import typing as t
from dataclasses import dataclass

import inflection

from AzurStats.commission.data import LIST_COMMISSION_DATA
from AzurStats.database.base import AzurStatsDatabase
from module.base.decorator import cached_property
from module.commission.project_data import dictionary_en
from module.config.utils import deep_get, deep_set, deep_iter
from module.logger import logger
from module.map.map_grids import SelectedGrids


def merge_min(prev, new):
    if prev == 0:
        return new
    elif new > 0:
        return min(prev, new)
    else:
        return prev


@dataclass
class DataCommissionSample:
    comm: str
    status: int
    samples: int

    def __post_init__(self):
        self.status = int(self.status)
        self.samples = int(self.samples)


@dataclass
class DataCommissionItem:
    comm: str
    status: int
    item: str
    drop_count: int
    drop_total: int
    drop_min: int
    drop_max: int
    samples: int = 0

    def __post_init__(self):
        self.status = int(self.status)
        self.drop_count = int(self.drop_count)
        self.drop_total = int(self.drop_total)
        self.drop_min = int(self.drop_min)
        self.drop_max = int(self.drop_max)

    @cached_property
    def valid(self):
        if self.status not in [0, 1]:
            return False
        if self.item == 'PlaceHolder':
            return True
        if self.item.isdigit():
            return False
        if self.drop_count < 50 or self.samples < 50:
            return False
        return True


@dataclass
class DataCommissionItemRow:
    comm: str
    item: str
    done_samples: int = 0
    done_count: int = 0
    done_total: int = 0
    done_min: int = 0
    done_max: int = 0
    perfect_samples: int = 0
    perfect_count: int = 0
    perfect_total: int = 0
    perfect_min: int = 0
    perfect_max: int = 0

    def load_drop(self, data: DataCommissionItem):
        if data.status == 1:
            self.perfect_samples += data.samples
            self.perfect_count += data.drop_count
            self.perfect_total += data.drop_total
            self.perfect_min = merge_min(self.perfect_min, data.drop_min)
            self.perfect_max = max(self.perfect_max, data.drop_max)
        elif data.status == 0:
            self.done_samples += data.samples
            self.done_count += data.drop_count
            self.done_total += data.drop_total
            self.done_min = merge_min(self.done_min, data.drop_min)
            self.done_max = max(self.done_max, data.drop_max)

    def __bool__(self):
        return True

    @cached_property
    def is_perfect_item(self):
        """ Whether drops on PERFECT only """
        return self.done_count == 0

    @cached_property
    def samples(self):
        return self.done_samples + self.perfect_samples

    @cached_property
    def perfect_rate(self) -> float:
        if self.is_perfect_item:
            return self.perfect_samples / self.samples
        else:
            return 1.

    @cached_property
    def min(self):
        if self.drop_rate < 1:
            return 0
        elif self.is_perfect_item:
            return self.perfect_min
        elif self.perfect_min == 0:
            return self.done_min
        else:
            return min(self.done_min, self.perfect_min)

    @cached_property
    def max(self):
        if self.is_perfect_item:
            return self.perfect_max
        elif self.perfect_max == 0:
            return self.done_max
        else:
            return max(self.done_max, self.perfect_max)

    @cached_property
    def avg(self):
        return (self.done_total + self.perfect_total) \
               / (self.done_count + self.perfect_count) * self.perfect_rate * self.drop_rate

    @cached_property
    def drop_rate(self):
        # return (self.done_count + self.perfect_count) / self.samples
        # 0~2
        if self.comm == 'Short-range Sailing Training' and self.item == 'CognitiveChips':
            return 2 / 3
        if self.item == 'DecorCoins':
            # 0~1
            if self.comm == 'Forest Protection Commission Ⅰ':
                return 1 / 2
            if self.comm == 'Vein Protection Commission Ⅰ':
                return 1 / 2
            if self.comm == 'Small-scale Oil Extraction Ⅰ':
                return 1 / 2
            # 0~2
            if self.comm == 'Small-scale Oil Extraction Ⅱ':
                return 2 / 3
        return 1

    @cached_property
    def is_show(self):
        if self.item == 'PlaceHolder' or self.item == 'EventTicket':
            return False
        return True

    @cached_property
    def is_night(self):
        return self.comm.endswith(' N')

    @cached_property
    def commission_data(self) -> t.Dict:
        if self.is_night:
            comm = self.comm[:-2]
        else:
            comm = self.comm
        for data in LIST_COMMISSION_DATA:
            if data['comm'] == comm:
                return data
        raise Exception(f'Commission {comm} is not in LIST_COMMISSION_DATA')

    @cached_property
    def duration(self) -> int:
        """ Duration in hours """
        h, m, s = self.commission_data['duration'].split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)

    @cached_property
    def expiration(self) -> int:
        """ Expiration in hours """
        h, m, s = self.commission_data['expiration'].split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)

    @cached_property
    def genre(self):
        comm = self.comm.upper().strip(' ⅠⅡⅢⅣⅤⅥ')
        for key, value in dictionary_en.items():
            for keyword in value:
                if keyword in comm:
                    if self.is_night:
                        return key.replace('extra', 'night')
                    else:
                        return key
        raise Exception(f'Commission {self.comm} is not in dictionary_en')

    @cached_property
    def alias(self):
        genre = inflection.camelize(self.genre).replace('Comm', '')
        if self.duration % 3600 == 0:
            duration = str(self.duration // 3600)
        else:
            duration = f'{self.duration // 3600}:{self.duration % 3600 // 60}'
        return f'{genre}-{duration}'

    @cached_property
    def en(self):
        return self.comm

    @cached_property
    def cn(self):
        return ''.join(self.commission_data['cn'])

    @cached_property
    def hourly(self):
        return self.avg / self.duration * 3600

    @cached_property
    def output_cn(self):
        return dict(
            委托别称=self.alias,
            委托类别=self.genre,
            中文名=self.cn,
            英文名=self.en,
            消耗时间=self.duration,
            过期时间=self.expiration,
            物品名称=self.item,
            样本数=self.samples,
            大成功概率=self.perfect_rate if self.perfect_rate < 1 else '',
            掉落范围=f'{self.min}~{self.max}',
            单次掉落=self.avg,
            时均掉落=self.hourly
        )


class StatsResearchItem(AzurStatsDatabase):
    @cached_property
    def drop_data(self) -> SelectedGrids(DataCommissionItem):
        # return self.record_from_json('./commission_items.json', DataCommissionItem)
        sql = """
        SELECT
           `comm`,
           `status`,
           item,
           COUNT(DISTINCT imgid) AS drop_count,
           SUM(amount) AS drop_total,
           MIN(amount) AS drop_min,
           MAX(amount) AS drop_max
        FROM commission_items
        GROUP BY `comm`, `status`, item
        ORDER BY `comm`, `status`, item
        """
        data = self.query(sql, data_class=DataCommissionItem)
        logger.info('raw_drop_data')

        sql = """
        SELECT
           `comm`,
           `status`,
           COUNT(DISTINCT imgid) AS samples
        FROM commission_items
        GROUP BY `comm`, `status`
        ORDER BY `comm`, `status`
        """
        sample = self.query(sql, data_class=DataCommissionSample)
        logger.info('raw_drop_samples')

        data = data.left_join(sample, on_attr=('comm', 'status'), set_attr=('samples',), default=0)
        data = data.select(valid=True)
        data = data.sort('comm', 'status', 'item')
        logger.info('drop_data')
        return data

    @cached_property
    def drop_result(self) -> SelectedGrids(DataCommissionItemRow):
        """
        Returns:
            <item>: Item name, with item genre in it
                <comm>: Commission name in English.
                    DataCommissionItemRow:
        """
        data: t.Dict[str, t.Dict[str, DataCommissionItemRow]] = {}

        def new_row(item, comm):
            return DataCommissionItemRow(comm, item)

        def load_drop(r, path):
            filter_row = deep_get(data, keys=path)
            if filter_row is None:
                filter_row = new_row(*path)
                deep_set(data, keys=path, value=filter_row)
            filter_row.load_drop(r)

        def is_daily_bonus_item(item):
            if item in ['Cubes', 'Drills']:
                return True
            if item.startswith('Book') or item.startswith('Retrofit') or item.startswith('Box'):
                return True
            return False

        # Backup samples count
        samples_done = {}
        samples_perfect = {}
        daily_bonus = {}
        for row in self.drop_data:
            if row.status == 1:
                samples_perfect[row.comm] = max(samples_perfect.get(row.comm, 0), row.samples)
            elif row.status == 0:
                samples_done[row.comm] = max(samples_done.get(row.comm, 0), row.samples)
            if row.status == 1 and is_daily_bonus_item(row.item):
                daily_bonus[row.comm] = daily_bonus.get(row.comm, 0) + row.drop_count

        # Create new objects and its structure.
        for row in self.drop_data:
            item_genre = self.ItemName_to_ItemGenre(row.item)
            if item_genre is not None:
                load_drop(row, [item_genre, row.comm])
            load_drop(row, [row.item, row.comm])

        # Recover samples count
        for path, row in deep_iter(data, depth=2):
            item, comm = path
            row.done_samples = samples_done.get(comm, 0)
            row.perfect_samples = samples_perfect.get(comm, 0)

            item_genre = self.ItemName_to_ItemGenre(row.item)
            if item_genre is not None:
                _ = row.drop_rate
                genre_row = deep_get(data, keys=[item_genre, comm])
                row.drop_rate = (row.done_count + row.perfect_count) / (genre_row.done_count + genre_row.perfect_count)
            if comm.startswith('Awakening Tactical Research') or comm.startswith('Daily Resource Extraction'):
                if is_daily_bonus_item(item):
                    _ = row.drop_rate
                    row.drop_rate = row.perfect_count / daily_bonus[row.comm]

        return data


if __name__ == '__main__':
    self = StatsResearchItem()
    # self.record_to_json(self.drop_data, './commission_items.json')

    # out = SelectedGrids([v for _, v in deep_iter(self.drop_result, depth=2)])
    # self.record_to_csv(out.sort('genre', 'duration', 'comm'), 'commission_items.csv', encoding='gbk')

    out = SelectedGrids([v for _, v in deep_iter(self.drop_result, depth=2)])
    out = out.select(is_show=True).sort('genre', 'duration', 'comm')
    self.record_to_csv(SelectedGrids(out.get('output_cn')), 'commission_items.csv', encoding='gbk')
