import os
import re
import shutil
from typing import List

from bs4 import BeautifulSoup
from business_objects.video import RegularVideo, UnavailableVideo, Video
from constants import TEMPDIR, THUMBDIR
from filmliste.filmliste import Filmliste
from tools.cached_downloader import download_cached
from tools.misc import (download_image, get_cache_name_for_paginated_page,
                        get_cache_name_for_start_page,
                        get_cache_name_for_summary_file,
                        get_category_shortname, read_file_to_string)

from scrapers.scraper import Scraper

base_uri = 'https://www.br.de'


def get_page_links(page: str) -> List[str]:
    soup = BeautifulSoup(page, 'html.parser')
    links = {
        base_uri + link.get('href')
        for link
        in soup.find_all('a', {'class': 'pageItem'})
    }

    return sorted(links)


class BrScraper(Scraper):

    def __init__(self, name: str, link: str):
        self.name = name
        self.link = link

    def _prepare_corpus(self):
        link_shortname = get_category_shortname(self.name)
        start_page_filename = os.path.join(
            TEMPDIR,
            get_cache_name_for_start_page(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )
        start_page = download_cached(
            uri=self.link,
            cache_filename=start_page_filename,
        )

        page_links = get_page_links(start_page)
        if not page_links:
            # There is no pagination.
            # Copy the start page to page 1 and add this as a pseudo page link.
            filename_for_page_1 = os.path.join(
                TEMPDIR,
                get_cache_name_for_paginated_page(
                    scraper_name=self.scraper_name,
                    category_shortname=link_shortname,
                    page_number=1,
                ),
            )
            # Don't copy it if we have done this already.
            if not os.path.exists(filename_for_page_1):
                shutil.copyfile(start_page_filename, filename_for_page_1)
            # Just append something so that we have something to iterate over in the next loop.
            # Because we just copied the file, we have a cache hit anyways and will never read this fake URI.
            page_links.append('')

        summary_file_name = os.path.join(
            TEMPDIR,
            get_cache_name_for_summary_file(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )

        if not os.path.exists(summary_file_name):
            # download each page and put the relevant part into the summary file
            for page_number, page_link in enumerate(page_links, start=1):
                paginated_page_filename = os.path.join(
                    TEMPDIR,
                    get_cache_name_for_paginated_page(
                        scraper_name=self.scraper_name,
                        category_shortname=link_shortname,
                        page_number=page_number,
                    ),
                )
                paginated_page = download_cached(
                    uri=page_link,
                    cache_filename=paginated_page_filename,
                )

                # Here, we don't use BeautifulSoup to write the relevant part to the file because that would change the HTML code (due to pretty printing).
                matches = re \
                    .compile(r'.*<div class="section_inner clearFix">(?P<content>.*)<div class="detail">.*', re.DOTALL) \
                    .match(paginated_page)
                if not matches:
                    raise Exception
                main_part = matches.group('content')
                with open(summary_file_name, 'a') as file:
                    file.write(main_part)

        # parse each entry of that file
        items = re.split(
            pattern=r'(?=<div class="box box_standard">)',
            string=read_file_to_string(summary_file_name),
        )[1:]

        return items

    def _scrape(self) -> List[Video]:
        # Don't use a set here as it swallows some items. Also, a list retains the order.
        result = []

        filmliste = Filmliste()

        items = self._prepare_corpus()

        print(f'Found {len(items)} video(s) for “{self.get_name()}”.')

        for item in items:
            soup = BeautifulSoup(item, 'html.parser')

            series = soup.select_one('span.teaser_overline').contents.pop()

            if series != self.name:
                continue

            original_title = soup.select_one(
                'span.teaser_title').contents.pop()

            # Clean away surrounding whitespaces.
            original_title = original_title.strip()

            # Clean away trailing numbers.
            clean_title = re.sub(
                pattern=r'^[0-9]+\. ', repl='', string=original_title)

            original_image = soup.select_one('img').attrs['src']
            # Download (i.e., cache) the thumbnail.
            original_image = base_uri + original_image

            short_name = set(soup.select_one('a.link_video.contenttype_standard').attrs['class']).difference(
                ['link_video', 'contenttype_standard']).pop()
            # short_name = re.search(
            #     pattern=r'(?<=/)(?P<last>[^/]+)$', string=short_name).group('last')
            short_name = re.sub(
                pattern=r'-[0-9]+$',
                repl='',
                string=short_name,
            )

            local_image_filename = os.path.join(THUMBDIR, short_name) + '.jpg'
            download_image(
                uri=original_image,
                target_filename=local_image_filename,
            )

            # Now, fetch the video link.
            candidates = filmliste.search(
                original_title=original_title,
                clean_title=clean_title,
                series=series,
            )

            # Maybe the video was not found.
            video_link = candidates[0]['link'] if candidates else None

            if video_link:
                video = RegularVideo(
                    thumbnail=local_image_filename,
                    title=clean_title,
                    video=video_link,
                    series=series,
                    shortname=short_name,
                )
            else:
                video = UnavailableVideo(
                    thumbnail=local_image_filename,
                    title=clean_title,
                    replacement_video_link=f'https://mediathekviewweb.de/#query={clean_title}',
                    series=series,
                    shortname=short_name,
                )
            result.append(video)

        return result
