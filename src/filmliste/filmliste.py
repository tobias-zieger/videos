from ast import parse
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Tuple

import requests
from constants import (ASSETDIR, FILMLISTE_FILENAME, MAX_CACHE_AGE,
                       PERMANENTDIR, QUALITY_HIGH, QUALITY_MEDIUM)

from filmliste.matchers.cleantitlematcher import CleanTitleMatcher
from filmliste.matchers.cleantitlesubstringmatcher import \
    CleanTitleSubstringMatcher
from filmliste.matchers.originaltitlematcher import OriginalTitleMatcher
from filmliste.matchers.prefixfreecleantitlesubstringmatcher import \
    PrefixFreeCleanTitleSubstringMatcher
from filmliste.matchers.prefixfreetokenizedcleantitlesubsetmatcher import \
    PrefixFreeTokenizedCleanTitleSubsetMatcher


class Filmliste:

    data = None
    connection = None

    # Thise are fields that we derive from the data and cannot be found in the source file.
    VIDEO_LINK_COLUMN_NAME = 'link'
    VIDEO_LINK_QUALITY_COLUMN_NAME = 'link_quality'

    # These are the headers in the Filmliste and in SQL (with the corresponding SQL type).
    # If new keys arise, they are silently ignored.
    header_lookup = [
        ('Sender', 'channel', 'TEXT NOT NULL'),
        ('Thema', 'series', 'TEXT NOT NULL'),
        # In some very rare cases, the title is missing (and it's not a compression issue).
        ('Titel', 'title', 'TEXT'),
        ('Datum', 'date', 'TEXT'),  # Seen to be null, but video works.
        ('Zeit', 'time', 'TEXT'),  # Seen to be null, but video works.
        ('Dauer', 'duration', 'TEXT'),  # Seen to be null, but video works.
        # This is the size of the middle-sized video. Sometimes it's not provided. The video still works.
        ('Größe [MB]', 'size', 'INTEGER'),
        # Sometimes, the description is missing (and it's not a compression issue).
        ('Beschreibung', 'description', 'TEXT'),
        (None, VIDEO_LINK_COLUMN_NAME, 'TEXT'),
        (None, VIDEO_LINK_QUALITY_COLUMN_NAME, 'INTEGER'),
        ('Url', 'url', 'TEXT NOT NULL'),
        # Some channels don't provide a website.
        ('Website', 'website', 'TEXT'),
        ('Url Untertitel', 'url_subtitle', 'TEXT'),
        ('Url RTMP', 'url_rtmp', 'TEXT'),
        ('Url Klein', 'url_small', 'TEXT'),
        ('Url RTMP Klein', 'url_rtmp_small', 'TEXT'),
        ('Url HD', 'url_hd', 'TEXT'),
        ('Url RTMP HD', 'url_rtml_hd', 'TEXT'),
        # Seen to be null, but video works.
        ('DatumL', 'utc_timestamp', 'INTEGER'),
        ('Url History', 'url_history', 'TEXT'),
        ('Geo', 'geo', 'TEXT'),
        ('neu', 'new', 'INTEGER NOT NULL'),
    ]
    database_columns = [column_name for (_, column_name, _) in header_lookup]
    database_column_2_create_clause = {
        column_name: create_clause
        for (_, column_name, create_clause)
        in header_lookup
    }

    def _setup_database() -> None:
        cursor = Filmliste.connection.cursor()

        cursor.execute('DROP TABLE IF EXISTS videos')
        cursor.execute('DROP INDEX IF EXISTS title_index')
        cursor.execute('DROP INDEX IF EXISTS series_index')

        create_videos_table_statement = 'CREATE TABLE videos ('

        column_create_clause_pairs = [
            f'{column_name} {Filmliste.database_column_2_create_clause[column_name]}'
            for column_name
            in Filmliste.database_columns
        ]

        create_videos_table_statement += ', '.join(column_create_clause_pairs)
        create_videos_table_statement += ')'

        cursor.execute(create_videos_table_statement)

        # Create some helpful indexes.
        cursor.execute('CREATE INDEX title_index ON videos(title)')
        cursor.execute('CREATE INDEX series_index ON videos(series)')

        # Add the cache table.
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS cache ('
            'uri TEXT UNIQUE, '
            'works INTEGER, '
            'last_checked INTEGER'
            ')'
        )

    def __init__(self) -> None:
        if not Filmliste.connection:
            sqlite_file = os.path.join(PERMANENTDIR, 'database.sqlite')
            Filmliste.connection = sqlite3.connect(sqlite_file)
            Filmliste.connection.row_factory = sqlite3.Row
            Filmliste._setup_database()
            self._parse_filmliste()

    def _parse_filmliste(self):
        lines = []
        with open(os.path.join(ASSETDIR, FILMLISTE_FILENAME), 'r') as filmliste:
            for line in filmliste:
                lines.append(line)

        header = json.loads(lines.pop(0))

        # This contains for each column in the database the 0-indiced column number in the input file.
        database_column_name_2_source_file_column_index = {}
        for column_index, head in enumerate(header):
            column_name_in_database = [
                column_name
                for (header_name, column_name, _)
                in Filmliste.header_lookup
                if header_name == head
            ].pop()
            database_column_name_2_source_file_column_index[column_name_in_database] = column_index
        database_column_name_2_source_file_column_index[Filmliste.VIDEO_LINK_COLUMN_NAME] = None
        database_column_name_2_source_file_column_index[Filmliste.VIDEO_LINK_QUALITY_COLUMN_NAME] = None

        data_to_insert = []

        # There is some weird compression performed on some columns: To save bytes, consecutive lines with the same field value are
        # compressed by having the real value only in the first occurrence and empty strings in the following lines.
        # We need to undo this here.
        current_values_for_compressed_columns = {
            'channel': None,
            'series': None,
        }
        for line in lines:
            parsed_line = json.loads(line)

            # parse that line
            video_as_dict = {}
            for database_column in Filmliste.database_columns:
                original_file_index = database_column_name_2_source_file_column_index[
                    database_column]
                if original_file_index is None:
                    # It's an artificial column. Ignore it here.
                    pass
                else:
                    video_as_dict[database_column] = parsed_line[original_file_index] or None

            # decompress
            for column in current_values_for_compressed_columns.keys():
                current_value = video_as_dict[column]
                if current_value:
                    # This line constitues a new value.
                    current_values_for_compressed_columns[column] = current_value
                else:
                    # This line is meant to have the same value as the line above, so artificially add it back.
                    current_value = current_values_for_compressed_columns[column]

                # Now we need to set the value to the entry to persist it.
                video_as_dict[column] = current_value

            # We add the best video link for later processing. This is the absolute link with the highest video quality.
            best_video = self._generate_best_video_link(video_as_dict)
            if best_video[1].endswith('.m3u8'):
                # This is not a playable video. Discard this row.
                continue
            video_as_dict[Filmliste.VIDEO_LINK_QUALITY_COLUMN_NAME] = best_video[0]
            video_as_dict[Filmliste.VIDEO_LINK_COLUMN_NAME] = best_video[1]

            data_to_insert.append(video_as_dict)

        insertion_cursor = Filmliste.connection.cursor()
        list_of_columns = ', '.join(Filmliste.database_columns)

        list_of_placeholders = ', '.join(
            [f':{header}' for header in Filmliste.database_columns])
        insert_statement = f'INSERT INTO videos ({list_of_columns}) values ({list_of_placeholders})'
        insertion_cursor.executemany(insert_statement, data_to_insert)
        Filmliste.connection.commit()

    def _find_candidates(self, clean_title: str, original_title: str, series: str) -> list:
        # We don't apply the full toolset on each search because that would take very long and also find a lot of false positives.
        # Instead, we relax the matching mechanism more and more.
        matcher_classes = [
            OriginalTitleMatcher,
            CleanTitleMatcher,
            CleanTitleSubstringMatcher,
            PrefixFreeCleanTitleSubstringMatcher,
            PrefixFreeTokenizedCleanTitleSubsetMatcher,
        ]

        # We need to filter once more strict, additionally by series, and then, more relaxedly, not by series.
        # The series is so powerful that we try all matchers first with series.
        # If there is no hit, we (desperately) try it without series.
        for with_series in [True, False]:
            for matcher_class in matcher_classes:
                matcher = matcher_class(
                    connection=Filmliste.connection,
                    original_title=original_title,
                    clean_title=clean_title,
                    series=series,
                )
                result = matcher.filter(series_must_match=with_series)
                if result:
                    # We are satisfied as soon as we find something.
                    return result

        return []

    def _generate_best_video_link(self, candidate: dict) -> Tuple[int, str]:
        link = candidate['url']
        # Try the quality links descendingly.
        # Medium seems to always exist, so we start with that and try to upgrade to High afterwards.
        quality = QUALITY_MEDIUM
        if candidate['url_hd']:
            hq_details = candidate['url_hd']
            if '|' in hq_details:
                offset, replacement = hq_details.split('|')
                link = link[:int(offset)] + replacement
            else:
                # There is no offsetting with |. Instead, just append hq_details to url.
                link = candidate['url'] + hq_details
            # Convert HTTPS link to HTTP link.
            link = re.sub(pattern=r'^https://', repl='http://', string=link)
            quality = QUALITY_HIGH

        return quality, link

    def search(self, clean_title: str, original_title: str = None, series: str = None) -> list:
        candidates = self._find_candidates(
            clean_title=clean_title,
            original_title=original_title,
            series=series,
        )

        # rank by best video link
        candidates.sort(key=lambda x: x['link_quality'])

        # Some videos don't work even though they look good. We need to check them (and cache the result).
        # Those that don't work are filtered out.
        candidates = list(
            filter(lambda candidate: self.video_works(candidate), candidates)
        )

        return candidates

    def video_works(self, candidate) -> bool:

        # Get cached value for candidate.
        cursor = self.connection.cursor()

        uri = candidate['link']
        bad_before_this_time = round(
            (datetime.now(tz=timezone.utc) - MAX_CACHE_AGE).timestamp())

        select_query = 'SELECT works FROM cache WHERE uri = :uri AND last_checked > :some_time_ago'
        parameters = {
            'uri': uri,
            'some_time_ago': bad_before_this_time
        }

        row = cursor.execute(select_query, parameters).fetchone()

        if row:
            return row['works']

        # Apparently, there was no entry (or it was too old). Get fresh information from the internet.
        response = requests.head(uri)

        works = response.status_code == 200

        insert_query = 'INSERT OR REPLACE INTO cache (uri, works, last_checked) VALUES (:uri, :works, :last_checked)'
        parameters = {
            'uri': uri,
            'works': works,
            'last_checked': round(datetime.now(tz=timezone.utc).timestamp())
        }

        cursor.execute(insert_query, parameters)
        self.connection.commit()

        return works
