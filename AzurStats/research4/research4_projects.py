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


def get_data():
    connection = pymysql.connect(**CONFIG['database'])
    try:
        with connection.cursor() as cursor:
            SQL = """
            SELECT project, COUNT(*) FROM research4_projects WHERE valid = 1 AND series = 4 GROUP BY project ORDER BY project
            """
            cursor.execute(SQL)
            amounts = cursor.fetchall()

    finally:
        connection.close()

    total = sum([row[1] for row in amounts])

    by_all = {}
    by_genre = {}
    by_duration = {}
    by_genre_duration = {}
    for name, amount in amounts:
        def dic_add_row(dic, key, project):
            value = dic.get(key, {}).get('samples', 0) + amount
            percent = value / total * 100
            dic[key] = {'project': project, 'samples': value, 'percentage': f'{percent:.3f}%'}

        project = ResearchProject(name=name, series=4)
        dic_add_row(by_all, key=name, project=f'{name} ({human_project(project)})')
        dic_add_row(by_genre, key=project.genre, project=project.genre)
        dic_add_row(by_duration, key=float(project.duration), project=f'{project.duration}H')
        dic_add_row(by_genre_duration, key=(project.genre, float(project.duration)),
                    project=f'{project.genre}-{project.duration}')

    def dic_prepare(dic):
        dic = dict(sorted(dic.items()))
        return list(dic.values())

    by_all = dic_prepare(by_all)
    by_genre = dic_prepare(by_genre)
    by_duration = dic_prepare(by_duration)
    by_genre_duration = dic_prepare(by_genre_duration)

    return {
        'by_all': by_all,
        'by_genre': by_genre,
        'by_duration': by_duration,
        'by_genre_duration': by_genre_duration,
    }


def run():
    logger.info('Extract research4 project to database')
    Research4Projects().run()
    logger.info('Generate research4 project data')
    write_json(get_data(), 'research4_projects')
