import os
import re
from typing import Dict, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from business_objects.video import (NotHotlinkableVideo, RegularVideo,
                                    UnavailableVideo, Video)
from constants import PERMANENTDIR, TEMPDIR, THUMBDIR
from scrapers.scraper import Scraper
from tools.cached_downloader import download_cached
from tools.misc import (download_image, get_cache_name_for_start_page,
                        get_category_shortname, group_by)


class SachgeschichtenMetaScraper(Scraper):
    def __init__(self):
        self.name = 'Sachgeschichten'
        # This has by far the most videos, but the videos cannot be hotlinked.
        self.link_wdrmaus = 'https://www.wdrmaus.de/filme/sachgeschichten/index.php5?filter=alle'
        # This has fewer videos, but they can be downloaded (or hotlinked).
        self.link_kinder_wdr = 'https://kinder.wdr.de/hoerensehen/podcast-maus-102.html'
        # This has about the same number of videos, but can be parsed more easily.
        self.link_kinder_wdr_podcast = 'https://kinder.wdr.de/hoerensehen/podcast-maus-102.podcast'

    def _scrape(self) -> List[Video]:

        result = []

        result.extend(self._parse_wdrmaus())
        result.extend(self._parse_wdr_kinder())
        result.extend(self._parse_wdr_kinder_podcast())

        return result

    def _parse_wdrmaus(self) -> List[Video]:
        category_name = 'WDRMaus'
        link_shortname = get_category_shortname(category_name)
        start_page_filename = os.path.join(
            TEMPDIR,
            get_cache_name_for_start_page(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )
        html = download_cached(
            uri=self.link_wdrmaus,
            cache_filename=start_page_filename,
        )

        soup = BeautifulSoup(html, 'html.parser')
        result = []
        elements = soup.select('li.dynamicteaser')
        print(f'Found {len(elements)} video(s) for “{category_name}”.')
        for element in elements:
            title = element.text.strip()
            subpage_uri = element.select_one('a').attrs['href']
            subpage_uri = re.sub(
                pattern='^../../', repl='', string=subpage_uri)
            absolute_subpage_uri = f'https://www.wdrmaus.de/{subpage_uri}'
            short_title = re.compile('.+/(?P<shortname>[^/]+).php5').match(
                subpage_uri).group('shortname')

            # fetch the page for the thumbnail
            sub_page_filename = os.path.join(
                PERMANENTDIR, f'wdrmaus-{short_title}.html')
            subpage_html = download_cached(
                uri=absolute_subpage_uri,
                cache_filename=sub_page_filename,
            )
            subpage_soup = BeautifulSoup(subpage_html, 'html.parser')
            relative_image_path = subpage_soup.select_one(
                'div.teaser.helper4krv2 img').attrs['src']
            relative_image_path = re.sub(
                pattern='^../../', repl='', string=relative_image_path)
            absolute_image_path = f'https://www.wdrmaus.de/{relative_image_path}'
            image_filename = os.path.join(
                THUMBDIR, f'wdrmaus-{short_title}.jpg')
            download_image(uri=absolute_image_path,
                           target_filename=image_filename)

            result.append(NotHotlinkableVideo(
                thumbnail=image_filename,
                title=title,
                watch_page=absolute_subpage_uri,
                series=self.name,
                shortname=short_title,
            ))

        return result

    def _parse_wdr_kinder(self) -> List[Video]:
        parsed_url = urlparse(self.link_kinder_wdr)
        base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
        result = []

        category_name = 'WDRKinder'
        link_shortname = get_category_shortname(category_name)
        start_page_filename = os.path.join(
            TEMPDIR,
            get_cache_name_for_start_page(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )
        html = download_cached(
            uri=self.link_kinder_wdr,
            cache_filename=start_page_filename,
        )

        soup = BeautifulSoup(html, 'html.parser')

        items = soup.select('div.box')
        print(f'Found {len(items)} video(s) for “{category_name}”.')

        first_item_seen = False

        for item in items:
            if not first_item_seen:
                # We just hit the first item. It has to be handled specially.
                first_item_seen = True

                # This is a video but has not h3 and the image is also different.
                title = item.select_one('h2.headline').text
                image_element = item.select_one('img.img')
            else:
                if not item.select('h3'):
                    # This was not a video item.
                    continue

                title = item.select_one('h3 a').text
                image_element = item.select_one('img.cover')

            if title.endswith(' (mit Gebärdensprache)'):
                # We need the regular video.
                continue

            if title.startswith('Lachgeschichte: '):
                # ignore it
                continue

            title = title.strip()

            title = re.compile('^Sachgeschichte: ').sub(
                string=title, repl='')

            short_name = get_category_shortname(title)

            video_link = item.select_one('a.button.download').attrs['href']
            video_link = video_link[1:]  # remove leading // and replace by /
            video_link = f'https:{video_link}'

            if image_element:
                image = image_element.attrs['src']
                if image.startswith('//'):
                    original_image = f'{parsed_url.scheme}:{image}'
                else:
                    original_image = base_url + image
                local_image_filename = os.path.join(
                    THUMBDIR, f'wdrkinder-{short_name}.jpg')
                download_image(uri=original_image,
                               target_filename=local_image_filename)
            else:
                local_image_filename = None

            result.append(RegularVideo(
                thumbnail=local_image_filename,
                title=title,
                video=video_link,
                series=self.name,
                shortname=short_name,
            ))

        return result

    def _parse_wdr_kinder_podcast(self) -> List[Video]:
        result = []

        category_name = 'WDRKinderPodcast'
        link_shortname = get_category_shortname(category_name)
        start_page_filename = os.path.join(
            TEMPDIR,
            get_cache_name_for_start_page(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )
        xml = download_cached(
            uri=self.link_kinder_wdr_podcast,
            cache_filename=start_page_filename,
        )

        soup = BeautifulSoup(xml, 'xml')

        items = soup.select('item')
        print(f'Found {len(items)} video(s) for “{category_name}”.')

        for item in items:
            title = item.select_one('title').text

            if title.endswith(' (mit Gebärdensprache)'):
                # We need the regular video.
                continue

            if title.startswith('Lachgeschichte: '):
                # ignore it
                continue

            title = title.strip()

            title = re.compile('^Sachgeschichte: ').sub(
                string=title, repl='')

            short_name = get_category_shortname(title)

            video_link = item.select_one('enclosure').attrs['url']

            video = RegularVideo(
                thumbnail=None,
                title=title,
                video=video_link,
                series=self.name,
                shortname=short_name,
            )
            result.append(video)

        return result

    def _deduplicate_and_fuse_videos(self, videos: List[Video]) -> List[Video]:
        # Some sources have duplicates in them. And even after deduplicting the sources, still not two sets of video are the same.

        # Put everything together and hope that the title is a unique key and two same videos have exactly the same title.
        everything = group_by(items=videos, criterion=lambda x: x.title)

        result = []

        # We need this later…
        descending_priorities = [
            RegularVideo,
            NotHotlinkableVideo,
            UnavailableVideo,
        ]
        priority_lookup = {
            priority.__name__: index
            for index, priority
            in enumerate(descending_priorities)
        }

        # Now we go through each cluster and fuse all the information together.
        # We take the largest image, a hotlinkable video, the largest video, etc…
        for list_of_videos in everything.values():
            if len(list_of_videos) == 1:
                result.append(list_of_videos.pop())
                continue

            # So we need to decide…
            # As prototype, we pick the best video object that we can find.
            list_of_videos.sort(
                key=lambda x: priority_lookup[type(x).__name__])

            prototype = list_of_videos[0]

            # We can keep title, series, and shortname.

            # We might need to get the thumbnail from somewhere else.
            if not prototype.thumbnail:
                prototype.thumbnail = [
                    video.thumbnail for video in list_of_videos if video.thumbnail].pop()

            result.append(prototype)
        return result

    def _get_page_links(self) -> Dict[str, List[str]]:
        return {
            self.name: [
                self.link_wdrmaus,
                self.link_kinder_wdr,
                self.link_kinder_wdr_podcast,
            ]
        }
