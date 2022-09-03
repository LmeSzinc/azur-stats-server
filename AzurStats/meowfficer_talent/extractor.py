import re

from AzurStats.utils.lua_loader import LuaLoader
from module.base.decorator import cached_property

FOLDER = r''
loader = LuaLoader(FOLDER, server='zh-CN')


class TalentParser:
    def __init__(self, data):
        self.data = data

    @cached_property
    def name(self):
        return self.data['name'].replace('·', '')

    @cached_property
    def info(self):
        info = self.data['desc'].replace('、', '').replace('，', '')
        info = re.sub(r'</color>', '', info)
        return info

    @cached_property
    def level(self):
        icon = self.data['icon']
        if icon.endswith('_1'):
            return 1
        if icon.endswith('_2'):
            return 2
        if icon.endswith('_3'):
            return 3
        return 0

    @cached_property
    def regex(self):
        def remove_increase(t):
            return t.replace('提高', '.{1,3}').replace('降低', '.{1,3}')

        res = re.search(r'(\w\w\w\w提高\d{1,2}|\w\w\w\w降低\d{1,2}).*(\w\w提高\d{1,2}|\w\w降低\d{1,2})', self.info)
        if res:
            res = [remove_increase(r) for r in res.groups()]
            return '.*'.join(res)
        res = re.search(r'(\w\w\w\w提高\d{1,2}|\w\w\w\w降低\d{1,2})', self.info)
        if res:
            return remove_increase(res.group(0))
        print(self.info)
        raise Exception
        # r = [rr.replace('提高', '.{1,3}').replace('降低', '.{1,3}') for rr in r]
        # if not r:
        #     print(self.data)
        #     raise Exception
        # return '.*'.join(r)

    @cached_property
    def genre(self):
        if self.level == 0:
            return self.name
        chinese = re.findall(r'([\u4e00-\u9fa5])', self.regex)
        res = ''.join(chinese)

        if res[:2] in ['白鹰', '皇家', '重樱', '铁血']:
            res = f'{res[:2]}指挥'
        res = res.replace('潜母', '潜艇').replace('超巡', '巡洋').replace('重炮', '战列').replace('正航', '航母')
        return res

    @cached_property
    def code(self):
        result = re.search(self.regex, self.info)
        if not result:
            print(self.data)
            raise Exception

        return f'("{self.genre}", {self.level}, "{self.name}"): re.compile("{self.regex}"),'


out = []
data = loader.load(r'./sharecfg/commander_ability_template.lua')
for key, talent in data.items():
    if key == 'all':
        continue
    talent = TalentParser(talent)
    if talent.name[-2:] in ['东煌', '北联', '鸢尾', '维希']:
        continue
    # print(talent.name, talent.level, talent.regex, talent.info)
    # print(talent.code)
    out.append(talent.code)
for row in out[::-1]:
    print(row)
