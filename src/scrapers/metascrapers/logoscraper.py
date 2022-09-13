
import os
from datetime import datetime
from typing import List

from business_objects.video import RegularVideo, Video
from constants import TEMPDIR, THUMBDIR
from filmliste.filmliste import Filmliste
from scrapers.kikascraper import KikaScraper
from tools.cached_downloader import download_cached
from tools.misc import (download_image, get_cache_name_for_start_page,
                        get_category_shortname)


class LogoScraper(KikaScraper):
    def __init__(self):
        self.name = 'Logo!'
        self.link = 'https://www.kika.de/logo/sendungen/videos-logo-100.html'

    def _scrape(self):
        # All episodes have the same thumbnail. The URI of that thumbnail is created by Javascript in the browser, so it's hard/impossible to scrape that.
        # And even if, the effort and amount of hard-coded knowledge is larger than just hard-coding a working URI. Thus, it's hard-coded.
        thumbnail_uri = 'https://cdn.kika.de/logo/sendungen/videos/logo-sendungspromo-weltkugel-zweitausendeinundzwanzig-704-resimage_v-tlarge169_w-1472.jpg?version=8563'
        local_filename = os.path.join(THUMBDIR, 'logo-thumbnail.jpg')
        download_image(uri=thumbnail_uri, target_filename=local_filename)

        # Fetch the logo.
        link_shortname = get_category_shortname(self.name)
        start_page_filename = os.path.join(
            TEMPDIR,
            get_cache_name_for_start_page(
                scraper_name=self.scraper_name,
                category_shortname=link_shortname,
            ),
        )
        start_page = download_cached(
            uri=self.link, cache_filename=start_page_filename)

        self._download_logo(html=start_page)

        videos = []
        episodes = Filmliste().search(clean_title='logo! vom')
        print(f'Found {len(episodes)} video(s) for “{self.name}”.')
        for episode in episodes:
            title = episode['title']
            if 'Gebärdensprache' in title:
                continue

            sortable_date = datetime.strptime(episode['date'], '%d.%m.%Y')

            shortname = f'Logo {sortable_date}'

            video_uri = episode['link']

            videos.append(RegularVideo(
                title=title,
                thumbnail=local_filename,
                series=self.name,
                shortname=shortname,
                video=video_uri,
            ))

        return videos

    def _deduplicate_and_fuse_videos(self, videos: List[Video]) -> List[Video]:
        # There is nothing to fuse. They are all even as good. Just pick any from each cluster of duplicates.
        unique_videos = {}

        for video in videos:
            unique_videos[video.shortname] = video

        return list(unique_videos.values())

    def _sort_videos(self, videos: List[Video]) -> List[Video]:
        videos.sort(key=lambda x: x.shortname, reverse=True)
        return videos
