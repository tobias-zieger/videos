from typing import Dict, List

from business_objects.video import Video
from scrapers.kikascraper import KikaScraper
from scrapers.scraper import Scraper
from tools.deduplication import cluster_by_duplicity, fuse_videos


class WildeWeltMetaScraper(Scraper):
    def __init__(self):
        self.name = 'Wilde Welt'
        self.links = {}

    def _scrape(self):
        videos = []
        # We collect all those videos and merge them later.

        sub_sources = [
            (
                'Anna auf dem Bauernhof',
                'https://www.kika.de/anna-auf-dem-bauernhof/sendungen/videos-anna-auf-dem-bauernhof-102.html',
            ),

            (
                'Anna auf der Alm',
                'https://www.kika.de/anna-auf-der-alm/buendelgruppe2682.html',
            ),

            (
                'Anna und das wilde Wissen',
                'https://www.kika.de/wilde-welt/anna-und-das-wilde-wissen/videos-anna-und-das-wilde-wissen-102.html',
            ),

            (
                'Anna und der wilde Wald',
                'https://www.kika.de/anna-und-der-wilde-wald/buendelgruppe2814.html',
            ),

            (
                'Anna und die Haustiere',
                'https://www.kika.de/anna-und-die-haustiere/buendelgruppe2112.html',
            ),

            (
                'Anna und die wilden Tiere',
                'https://www.kika.de/anna-und-die-wilden-tiere/buendelgruppe2118.html',
            ),

            (
                'Frag Anna!',
                'https://www.kika.de/wilde-welt/frag-anna/videos-frag-anna-100.html',
            ),

            (
                'Paula und die wilden Tiere',
                'https://www.kika.de/paula-und-die-wilden-tiere/buendelgruppe1688.html',
            ),

            (
                'Pia und die Haustiere',
                'https://www.kika.de/pia-und-die-haustiere/buendelgruppe2922.html',
            ),

            (
                'Pia und die wilde Natur',
                'https://www.kika.de/pia-und-die-wilde-natur/alle-folgen-100.html',
            ),

            (
                'Pia und die wilden Tiere',
                'https://www.kika.de/pia-und-die-wilden-tiere/buendelgruppe2858.html',
            ),

            (
                'Wilde Welt',
                'https://www.kika.de/wilde-welt/alle-videos-116_page-8_zc-bac7c88f.html',
            ),
        ]

        for name, link in sub_sources:
            additional_videos, additional_links = KikaScraper(
                name=name,
                link=link,
            ).process()

            if name == 'Wilde Welt':
                for video in additional_videos:
                    video.series = ''

            videos.extend(additional_videos)
            self.links.update(additional_links)

        return videos

    def _deduplicate_and_fuse_videos(self, videos: List[Video]) -> List[Video]:
        fused_videos = []

        clusters = cluster_by_duplicity(videos=videos)
        # These clusters are meant to be a preliminary duplicate detection to reduce the search space for duplicate detection
        # (which grows to the square of the number of items).
        # Actually, it seems to be good already so we don't actually need to find duplicates within them. Every cluster *is* a
        # duplicate cluster already.

        # We still need to fuse.
        for cluster in clusters:
            fused_video = fuse_videos(cluster)
            if not fused_video.series:
                fused_video.series = 'Pia und das wilde Wissen'
            fused_videos.append(fused_video)

        return fused_videos

    def _get_page_links(self) -> Dict[str, List[str]]:
        return self.links
