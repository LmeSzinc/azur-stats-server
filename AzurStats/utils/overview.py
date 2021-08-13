from datetime import datetime

import pymysql

from AzurStats.utils.utils import *


def get_data():
    connection = pymysql.connect(**CONFIG['database'])
    try:
        with connection.cursor() as cursor:
            SQL = """
            SELECT
                t1.HOUR time,
                COUNT( t2.HOUR ) num 
            FROM
                (
                SELECT
                    DATE_FORMAT( @cdate := DATE_ADD( @cdate, INTERVAL - 1 HOUR ), '%Y-%m-%d %H:00:00' ) HOUR 
                FROM
                    ( SELECT @cdate := DATE_ADD( DATE_FORMAT( NOW( ), '%Y-%m-%d %H:00:00' ), INTERVAL + 1 HOUR ) FROM azurstat.`img_images` ) t0 
                    LIMIT 24 
                ) t1
                LEFT JOIN ( 
                    SELECT DATE_ADD( DATE_FORMAT( date, '%Y-%m-%d %H:00:00' ), INTERVAL + 1 HOUR ) HOUR 
                    FROM azurstat.`img_images` WHERE date >= ( NOW( ) - INTERVAL 24 HOUR ) 
                ) t2 
            ON 
                t1.HOUR = t2.HOUR 
            GROUP BY
                t1.HOUR 
            ORDER BY
                t1.HOUR DESC
            """
            cursor.execute(SQL)
            uploads_history_24h = cursor.fetchall()
            SQL = """
            SELECT COUNT(*) AS num 
            FROM azurstat.`img_images` 
            WHERE date < DATE_FORMAT(NOW(), '%Y-%m-%d %H:00:00') 
            """
            cursor.execute(SQL)
            uploads_total = cursor.fetchall()
    finally:
        connection.close()

    return {
        "update_time": str(datetime.now().strftime("%H:%M:%S")),
        "update_time_full": str(datetime.now().astimezone().replace(microsecond=0).isoformat()),
        "uploads_in_24h": human_format(sum([row[1] for row in uploads_history_24h])),
        "uploads_total": human_format(uploads_total[0][0]),
        "uploads_history_24h": {
            "columns": ["time", "uploads"],
            "rows": [{"time": datetime.fromisoformat(row[0]).strftime("%H:%M"), "uploads": row[1]}
                     for row in uploads_history_24h][::-1]
        }
    }

def run():
    write_json(get_data(), 'overview')
    copy_to_output_folder()
