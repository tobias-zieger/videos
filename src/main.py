import os
from typing import List

from business_objects.video import Video
from constants import PERMANENTDIR, TEMPDIR, THUMBDIR
from sources import SOURCES
from tools.misc import save_to_json


def scrape_everything() -> List[Video]:
    videos = []
    page_links = {}
    for scraper in SOURCES:
        print(f'Processing “{scraper.get_name()}”…')
        additional_videos, additional_page_links = scraper.process()
        videos.extend(additional_videos)

        for page, links in additional_page_links.items():
            existing_links = page_links.get(page, [])
            existing_links.extend(links)
            page_links[page] = links

    return videos, page_links


if __name__ == '__main__':
    # Prepare some directories.
    os.makedirs(TEMPDIR, exist_ok=True)
    os.makedirs(PERMANENTDIR, exist_ok=True)
    os.makedirs(THUMBDIR, exist_ok=True)

    videos, page_links = scrape_everything()

    save_to_json(videos=videos, page_links=page_links)

    print('Done.')
