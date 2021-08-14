import pymysql

from AzurStats.classification.image_classification import ImageClassification
from AzurStats.utils.utils import *
from module.research.project import *


class Research4Projects(ImageClassification):
    SQL_SOURCE = 'images'
    SQL_SOURCE_COLUMN = 'imgid, path, server'
    SQL_TARGET = 'research4_projects'
    SQL_TARGET_COLUMN = 'imgid, server, valid, series, project, project_ocr, finish, error'
    SQL_WHERE = "AND valid = 1 AND stats <=> 'research4'"

    def images_to_data(self, images):
        """
        Args:
            images: List of pillow images

        Returns:
            List of output data
        """
        image = images[0]
        series = get_research_series(image)
        finish = get_research_finished(image)
        names_ocr = get_research_name(image)
        projects = [ResearchProject(name=name, series=series) for name, series in zip(names_ocr, series)]
        amount = sum([s == 4 for s in series])
        if amount < 3:
            raise ImageError('Not a S4 project list')
        # valid, series, project, project_ocr, finish
        data = [[p.valid, s, p.name, n_ocr, 0] for s, p, n_ocr in zip(series, projects, names_ocr)]
        if finish is not None:
            data[finish][4] = 1
        return data

    def merge_data(self, data_in, data_out):
        """
        Args:
            data_in: Results in SQL query
            data_out: A row of data to insert

        Returns:
            list:
        """
        # imgid, server, valid, series, project, project_ocr, finish, error
        return [data_in[0], data_in[2], *data_out, None]

    def merge_data_error(self, data_in, error):
        """
        Args:
            data_in: Results in SQL query
            error: Error messages

        Returns:
            list:
        """
        # imgid, server, valid, series, project, project_ocr, finish, error
        return [data_in[0], data_in[2], 0, 0, None, None, 0, error]


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


GENRE_I18N = {
    'zh-CN': {
        'ResearchS4': '四期科研',
        'ResearchS3': '三期科研',
        'ResearchS2': '二期科研',
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
        'ResearchS4': 'Research S4',
        'ResearchS3': 'Research S3',
        'ResearchS2': 'Research S2',
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
        lang_short:

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


def get_data():
    connection = pymysql.connect(**CONFIG['database'])
    try:
        with connection.cursor() as cursor:
            # 7jntvgh is the client ID of admin
            # Samples of project appear rate statistics is limited to admin,
            # because other users may select the projects they like,
            # and forget to send screenshots of the rest.
            sql = """
            SELECT project, COUNT(*)
            FROM research4_projects AS proj
            LEFT JOIN (
                SELECT imgid, ua
                FROM azurstat.img_images
            ) AS info
            ON proj.imgid = info.imgid
            WHERE valid = 1 AND series = 4 AND ua LIKE '%7jntvgh%'
            GROUP BY project
            ORDER BY project
            """
            cursor.execute(sql)
            amounts = cursor.fetchall()

            sql = """
            SELECT series, COUNT(*)
            FROM research4_projects AS proj
            LEFT JOIN (
                SELECT imgid, ua
                FROM azurstat.img_images
            ) AS info
            ON proj.imgid = info.imgid
            WHERE valid = 1 AND ua LIKE '%7jntvgh%'
            GROUP BY series
            ORDER BY series
            """
            cursor.execute(sql)
            seasons = cursor.fetchall()

    finally:
        connection.close()

    total_count = sum([row[1] for row in amounts])
    genre_count = {}
    group_count = {}
    project_count = {}

    for name, amount in amounts:
        project = ResearchProject(name=name, series=4)
        name, group, genre = project.name, f'{project.genre}-{project.duration}', project.genre
        project_count[name] = project_count.get(name, 0) + amount
        group_count[group] = group_count.get(group, 0) + amount
        genre_count[genre] = genre_count.get(genre, 0) + amount

    by_series = {}
    by_genre_and_duration = {}
    by_all = {}
    i18n = {
        'zh-CN': {},
        'en-US': {}
    }

    seasons_total = sum([row[1] for row in seasons])
    for series, amount in seasons:
        name = f'ResearchS{series}'
        for lang in GENRE_I18N.keys():
            i18n[lang][name] = name_to_i18n_project(name, lang)
        by_series[name] = {
            'series': name,
            'samples': amount,
            'rate': f'{(amount / seasons_total * 100):.3f}%'
        }
    for name, amount in amounts:
        project = ResearchProject(name=name, series=4)
        name, group, genre = project.name, f'{project.genre}-{project.duration}', project.genre
        project_rate = project_count[name] / total_count * 100
        group_rate = group_count[group] / total_count * 100
        genre_rate = genre_count[genre] / total_count * 100
        for lang in GENRE_I18N.keys():
            i18n[lang][name] = human_project(project)
            i18n[lang][group] = name_to_i18n_project(group, lang)
            i18n[lang][genre] = name_to_i18n_project(genre, lang)
        if group not in by_genre_and_duration:
            by_genre_and_duration[group] = {
                'project': group,
                'samples': group_count[group],
                'rate': f'{group_rate:.3f}%',
                'group_to_genre': f'{(group_rate / genre_rate * 100):.3f}%',
                'genre': genre,
                'genre_to_all': f'{genre_rate:.3f}%',

            }
        if name not in by_all:
            by_all[name] = {
                'project': name,
                'samples': project_count[name],
                'rate': f'{project_rate:.3f}%',
                'project_to_group': f'{(project_rate / group_rate * 100):.3f}%',
                'group': group,
                'group_to_genre': f'{(group_rate / genre_rate * 100):.3f}%',
                'genre': genre,
                'genre_to_all': f'{genre_rate:.3f}%',

            }

    def dic_prepare(dic, attr):
        def split(name):
            name = name.split('-')
            name[1] = float(name[1])
            return name

        dic = dict(sorted(dic.items(), key=lambda item: split(item[1][attr])))
        return list(dic.values())

    by_genre_and_duration = dic_prepare(by_genre_and_duration, 'project')
    by_all = dic_prepare(by_all, 'group')

    return {
        'by_series': by_series,
        'by_genre_and_duration': by_genre_and_duration,
        'by_all': by_all,
        'i18n': i18n,
    }


def check_name():
    """
    Print invalid OCR results in project name
    """
    connection = pymysql.connect(**CONFIG['database'])
    try:
        with connection.cursor() as cursor:
            sql = f"""
            SELECT imgid, project_ocr, series
            FROM research4_projects
            WHERE valid = 0 AND error is NULL
            """
            cursor.execute(sql)
            error = []
            for imgid, name, series in cursor.fetchall():
                if not series or not name:
                    continue
                project = ResearchProject(name=name, series=series)
                if not project.valid:
                    error.append((imgid, series, name))
            for row in error:
                print(row)
            print(len(error))
    finally:
        connection.close()


def run():
    logger.info('Extract research4 project to database')
    Research4Projects().run()
    logger.info('Generate research4 project data')
    write_json(get_data(), 'research4_projects')
