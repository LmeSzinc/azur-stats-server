import pymysql

from AzurStats.config.config import *
from module.research.project import *


def human_project(project):
    """
    Args:
        project (ResearchProject):

    Returns:
        str: Such as 'H-5', 'DR-5'
    """
    if project.ship_rarity == '':
        return f'{project.genre.upper()}-{project.duration}'
    else:
        return f'{project.ship_rarity.upper()}-{project.duration}'


def get_data():
    data = []
    for row in LIST_RESEARCH_PROJECT:
        project = ResearchProject(name=row['name'], series=row['series'])
        row = (row['series'], project.name, human_project(project), project.genre, project.duration)
        data.append(row)
    return data


def insert_data(data):
    connection = pymysql.connect(**CONFIG['database'])
    try:
        with connection.cursor() as cursor:
            sql = """
            TRUNCATE TABLE research_group
            """
            cursor.execute(sql)
            connection.commit()
            sql = f"""
                    INSERT INTO research_group (series, project, genre_duration, genre, duration)
                    VALUES (%s, %s, %s, %s, %s)
                    """
            cursor.executemany(sql, data)
            connection.commit()
    finally:
        connection.close()


def run():
    insert_data(get_data())


if __name__ == '__main__':
    run()
