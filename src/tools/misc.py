import os
import re
import time
from typing import Any, Dict, List

import requests
from business_objects.video import Video


def get_category_shortname(category: str) -> str:
    result = category

    # make lower case
    result = result.lower()

    # remove everything that is not a-z
    result = re.sub('[^a-z]', '', result)

    return result


def get_cache_name_for_start_page(
    scraper_name: str,
    category_shortname: str,
) -> str:
    return f'{scraper_name}-{category_shortname}-start.html'


def get_cache_name_for_paginated_page(
    scraper_name: str,
    category_shortname: str,
    page_number: int,
) -> str:
    return f'{scraper_name}-{category_shortname}-page-{page_number}.html'


def get_cache_name_for_summary_file(
    scraper_name: str,
    category_shortname: str,
) -> str:
    return f'{scraper_name}-{category_shortname}-summary.txt'


def read_file_to_string(filename: str) -> str:
    if not os.path.exists(filename):
        raise Exception

    content = []
    with open(filename, 'r') as file:
        for line in file:
            content.append(line)

    result = ''.join(content)
    return result


def save_to_json(videos: List[Video], page_links: Dict[str, List[str]]) -> None:
    filename = 'database.js'

    with open(file=filename, mode='w') as file:
        file.write('pageLinks = {\n')
        for page_name, page_links in page_links.items():
            links = ', '.join([f'"{link}"' for link in page_links])
            file.write(f'"{page_name}": [{links}],\n')
        file.write('}\n')
        file.write('\n')

        file.write('videos = [\n')
        for video in videos:
            line = '{'
            line += f'"img": "{video.thumbnail}", '
            line += f'"title": "{video.title}", '
            line += f'"video": "{video.video_link()}", '
            line += f'"type": "{type(video).__name__}", '
            line += f'"series": "{video.series}", '
            line += f'"shortname": "{video.shortname}"'
            line += '},\n'
            file.write(line)
        file.write(']\n\n')


def download_image(uri: str, target_filename: str) -> None:
    if not os.path.exists(target_filename):
        # Put some sleep here when an actual HTTP request is done.
        time.sleep(1)
        response = requests.get(uri)
        if response.status_code != 200:
            # Then we go without the image.
            return

        with open(target_filename, 'wb') as file:
            file.write(response.content)


def group_by(items: List[Any], criterion) -> Dict[str, Any]:
    result = {}
    for item in items:
        key = criterion(item)
        items_with_this_key = result.get(key, [])
        items_with_this_key.append(item)
        result[key] = items_with_this_key

    return result
