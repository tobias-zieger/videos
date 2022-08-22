from typing import Dict, List

from business_objects.video import Video


class Scraper:
    def get_name(self) -> str:
        return self.name

    def process(self) -> List[Video]:
        videos = self._scrape()
        videos = self._deduplicate_and_fuse_videos(videos)
        videos = self._sort_videos(videos)

        links = self._get_page_links()

        return videos, links

    def _deduplicate_and_fuse_videos(self, videos: List[Video]) -> List[Video]:
        # To be overwritten in subclasses…
        return videos

    def _sort_videos(self, videos: List[Video]) -> List[Video]:
        # To be overwritten in subclasses…
        # default implementation: alphabetical sorting by title
        videos.sort(key=lambda x: x.title)
        return videos

    def _get_page_links(self) -> Dict[str, List[str]]:
        return {self.name: [self.link]}
