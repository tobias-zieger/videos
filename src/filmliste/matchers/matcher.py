import sqlite3
from typing import List


class Matcher:

    def __init__(self, connection: sqlite3.Connection, original_title: str, clean_title: str, series: str = None) -> None:
        self.original_title = original_title
        self.clean_title = clean_title
        self.connection = connection
        self.series = series

    def parameters(self) -> dict:
        return {
            'original_title': self.original_title,
            'clean_title': self.clean_title,
            'series': self.series,
        }

    def additional_filter(self, rows: list) -> list:
        return rows

    def filter(self, series_must_match: bool = False) -> List:
        cursor = self.connection.cursor()
        query = f'SELECT series, title, date, link, link_quality FROM videos WHERE '
        query += self.where_clause()
        query += ' AND series = :series' if series_must_match else ''

        parameters = self.parameters()
        rows = cursor.execute(query, parameters).fetchall()

        rows = self.additional_filter(rows)

        return rows
