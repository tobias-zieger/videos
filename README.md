# Video-Player

This is a simple video player I made for my daughter. She likes to watch some videos from public broadcast. However, she had an old iPad mini running Mobile Safari 9. I factory-reset it, but since its iOS version was so old, many pages (with their videos) don't load in Safari. So I decided to go back to the roots and develop a web app (how it was originally intended from Apple but without the `<meta name="apple-mobile-web-app-capable" content="yes">` that made it appear like a real app, because then no audio is played). And here we are. I'm not a frontend engineer which you can tell from both the code and the user interface, but it does the trick.

There is a well-known project, [https://github.com/mediathekview] that features a stand-alone client [MediathekView](https://github.com/mediathekview/MediathekView), a crawler, and a web player ([MediathekViewWeb](https://mediathekviewweb.de/)). I re-use the crawled index of all videos that are currently available directly via the URI and I'm scraping the pages to retrieve the episodes and the thumbnails from. This is all done in Python.

![Screenshot](./assets/screenshot.jpg)


## How it works
The task is basically to join titles, thumbnails, and video links together. The thumbnails are downloaded (i.e., cached) and I am hotlinking the videos.

We get the titles and thumbnails from various places and we get the video links from MediathekView's filmliste.

We try to cache as much as possible to slip under their radar and to not induce too much load on their servers.


## Installation

### Filmliste

This list contains all the videos that are available on all the different public broadcast programs. The project crawls that regularly to provide it to MediathekView and MediathekViewWeb. We need to download it regularly. It's a compressed JSON-like file. Run `assets/updatefilmliste.sh` to update `filmliste.txt`. You need `unxz` for decompression. It's recommendable to run it regularly (e.g., as a cronjob).

### Scraper

This is the python code that scrapes the different public broadcast pages for the desired series. Set the desired series in `src/sources.py`. Then run `main.py`. After some time of waiting, it will create `database.js` which contains all the videos (including title, thumbnail link, and video link). This should also be run regularly (as a cronjob).

### Python requirements

You need at least Python 3.8. Otherwise it will error out at some places.

Further, you need to install the following libraries (maybe with `python3 -m pip install …`):
* beautifulsoup4
* lxml
* python-dateutil
* requests
* sqlite (or pysqlite3?)

## Future work
* The whole process takes some minutes due to the large amount of regex processing. Maybe some optimization/parallelism could help.
