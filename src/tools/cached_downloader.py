import os
import time

import requests


def download_cached(uri: str, cache_filename: str) -> str:
    if not os.path.exists(cache_filename):
        # Put some sleep here when an actual HTTP request is done.
        time.sleep(1)

        response = requests.get(uri)

        if response.status_code != 200:
            raise Exception

        # Some pages return UTF-8, but don't declare it as such.
        response.encoding = response.apparent_encoding

        with open(cache_filename, 'w') as file:
            file.write(response.text)

    lines = []
    with open(cache_filename, 'r') as file:
        for line in file:
            lines.append(line)

    result = ''.join(lines)
    return result
