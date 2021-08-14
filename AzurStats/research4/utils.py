import json

with open('./AzurStats/equipment/data.json', 'r', encoding='utf-8') as f:
    EQUIPMENT_DATA = json.load(f)

with open('./AzurStats/research4/i18n.json', 'r', encoding='utf-8') as f:
    DEFAULT_I18N = json.load(f)

GENRE_I18N = {
    'zh-CN': {
        'B': '数据收集',
        'C': '基础研究',
        'D': '定向研发',
        'E': '实验品招募',
        'G': '资金募集',
        'H': '魔方解析',
        'Q': '舰装解析',
        'T': '科研委托',
        'DR': '彩船定向',
        'PRY': '金船定向',
    },
    'en-US': {
        'B': 'Data Collection',
        'C': 'Basic Research',
        'D': 'Face Research',
        'E': 'Gear Collection',
        'G': 'Grant Donation',
        'H': 'Cube Analysis',
        'Q': 'Rigging Analysis',
        'T': 'Commission',
        'DR': 'DR Face',
        'PRY': 'PRY Face',
    }
}


def name_to_i18n_project(name, lang):
    """
    Args:
        name (str): Project name, such as `DR-2.5`
        lang:

    Returns:
        Such as: `彩船定向2.5h (DR-2.5)` and `DR Face 2.5h (DR-2.5)`
    """
    count = name.count('-')
    if count == 0:
        if name.replace('.', '', 1).isdigit():
            return f'{name}h'
        else:
            genre = GENRE_I18N[lang][name]
            return f'{genre}'

    elif count == 1:
        genre, duration = name.split('-')
        genre = GENRE_I18N[lang][genre]
        return f'{genre} {duration}h'
    else:
        return name


def human_project(project):
    """
    Args:
        project (ResearchProject):

    Returns:
        str: Such as 'H-5', 'Anchorage-5'
    """
    if project.ship == '':
        return f'{project.genre.upper()}-{project.duration}'
    else:
        return f'{project.ship.capitalize()}-{project.duration}'
