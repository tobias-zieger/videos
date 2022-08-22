from dataclasses import dataclass


@dataclass
class Video:
    thumbnail: str
    title: str
    series: str
    shortname: str

    def video_link(self):
        return None

    def get_id(self) -> int:
        return hash((self.thumbnail, self.title, self.shortname, self.series, self.video_link()))


@dataclass
class RegularVideo(Video):
    video: str

    def video_link(self):
        return self.video


@dataclass
class NotHotlinkableVideo(Video):
    watch_page: str

    def video_link(self):
        return self.watch_page


@dataclass
class UnavailableVideo(Video):
    replacement_video_link: str

    def video_link(self):
        return self.replacement_video_link
