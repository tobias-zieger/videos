import os

from dateutil.relativedelta import relativedelta

cachedir = 'cache'

TEMPDIR = os.path.join(cachedir, 'temp')
PERMANENTDIR = os.path.join(cachedir, 'permanent')

ASSETDIR = 'assets'

THUMBDIR = os.path.join(ASSETDIR, 'thumbnails')

FILMLISTE_FILENAME = 'filmliste.txt'

QUALITY_HIGH = 3
QUALITY_MEDIUM = 2
QUALITY_LOW = 1

MAX_CACHE_AGE = relativedelta(months=1)
