import json
import os
import re
from typing import List

from bs4 import BeautifulSoup
from business_objects.video import Video
from constants import TEMPDIR
from tools.cached_downloader import download_cached
from tools.misc import get_cache_name_for_start_page


class WikipediaScraper:
    def __init__(self, link_name: str, link: str):
        self.link_name = link_name
        self.link = link

    def process_source(self) -> List[Video]:
        # Get the page name from the link:
        wikipedia_language = re.compile('^https://(?P<language>[^\.]+).wikipedia.org/.+').match(self.link).group('language')
        page_name = re.compile('^.+wikipedia.org/wiki/(?P<page_name>.+)$').match(self.link).group('page_name')

        # Read the content of that Wikipedia page.
        uri = f'https://{wikipedia_language}.wikipedia.org/w/api.php?action=parse&format=json&origin=*&page={page_name}&prop=text'
        cache_filename = os.path.join(TEMPDIR, get_cache_name_for_start_page(page_name + '-wikipedia'))
        content = download_cached(uri=uri, cache_filename=cache_filename)
        html_text = json.loads(content)['parse']['text']['*']
        soup = BeautifulSoup(html_text, 'html.parser')

        titles = set()

        html_titles = soup.select('table.wikitable tbody tr td:nth-child(2) i')
        for html_title in html_titles:
            title = html_title.contents.pop()
            titles.add(title)

        print(titles)
