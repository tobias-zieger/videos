from typing import List, Set, Tuple

from business_objects.video import RegularVideo, Video

from tools.misc import group_by


def is_duplicate(video1: Video, video2: Video) -> bool:
    return all([
        video1.title == video2.title,
        video1.video == video2.video,
    ])


def calculate_transitive_closure(pairs: List[Tuple]) -> Set[Tuple]:
    # This doesn't scale well but is quick and dirty for small numbers.
    # https://stackoverflow.com/a/8674062

    closure = set(pairs)
    while True:
        new_relations = set((a, c)
                            for a, b1 in closure for b2, c in closure if b2 == b1)

        closure_until_now = closure | new_relations

        if closure_until_now == closure:
            break

        closure = closure_until_now

    return closure


def create_pairs_from_cluster(cluster: List[Video]) -> Set[Tuple]:
    pairs = set()
    for index1, video1 in enumerate(cluster):
        for index2, video2 in enumerate(cluster):
            if index1 <= index2:
                # Since index1 can be equal to index2, we have reflexive pairs, i.e., singletons.
                # We want that because then even singleton clusters are part of the set of pairs.
                pairs.add((video1.get_id(), video2.get_id()))
    return pairs


def convert_pairs_to_clustering(pairs: List[Tuple]) -> List[List]:
    # We convert the pairs back into clusters.
    # We assume that the input is transitively closed, reflexive, and sorted. Otherwise it will produce garbage.
    # For example, [(1, 1), (1, 2), (1, 4), (2, 2), (2, 4), (3, 3), (4, 4), (5, 5), (5, 6), (6, 6)] becomes [[1, 2, 4], [3], [5, 6]].
    # Each pair has 2 IDs (head, tail). Each cluster has a number. This cluster number is determined by the pair's lower number, the head.

    already_processed_ids = set()

    clustering = {}

    for pair in pairs:
        head = pair[0]
        tail = pair[1]

        if head in already_processed_ids:
            # There must be a cluster for this, but not neccessarily with the same number. We can ignore head.

            # We need to handle tail, though:
            if tail not in already_processed_ids:
                clustering[head].append(tail)
                already_processed_ids.add(tail)
        else:
            # We have never seen head. Due to the transitive closure, reflexivity, and ordering, it must be a new cluster and tail must be the same.
            if tail != head:
                raise Exception('This cannot be.')
            clustering[head] = [head]
            already_processed_ids.add(head)
            # We ignore tail here, because it must equal head.

    return clustering


def sort_pairs(pairs: Set[Tuple]) -> List[Tuple]:
    # A set makes them unique.
    sorted_tuples = set()

    # First, sort the tuples. ({(4, 3), (2, 1), (1, 2)} -> {(3, 4), (1, 2)})
    for pair in pairs:
        # We know that the tuples have 2 components. The following works even for reflexive pairs like (x, x).
        sorted_tuples.add((min(pair), max(pair)))

    # Second, sort the set of sorted tuples. ({(3, 4), (1, 2)} -> {(1, 2), (3, 4)})
    result = sorted(sorted_tuples)

    return result


def cluster_by_duplicity(videos: List[Video]) -> List[List[Video]]:
    pairs = set()

    # The graph theory stuff (transitive closure, converting clusters to pairs and pairs to a clustering)
    # is best done in ID space. So we give each video an ID (a hash) to work with it more easily.
    # In the end, we have to convert the clustering of IDs back to a clustering.
    # We use this dictionary for that:
    hash_2_video = {video.get_id(): video for video in videos}

    clustering_by_title = group_by(items=videos, criterion=lambda x: x.title)
    for cluster in clustering_by_title.values():
        pairs.update(create_pairs_from_cluster(cluster=cluster))

    clustering_by_uri = group_by(
        items=videos, criterion=lambda x: x.video_link())
    for cluster in clustering_by_uri.values():
        pairs.update(create_pairs_from_cluster(cluster=cluster))

    pairs = sort_pairs(pairs=pairs)

    pairs = calculate_transitive_closure(pairs=pairs)

    # Sort them again because transitively closing might have added pairs.
    pairs = sort_pairs(pairs=pairs)

    # Put it back to a transitively closed clustering (list of lists).
    clustering = convert_pairs_to_clustering(pairs=pairs)

    # Leave the ID space to have clusters of videos.
    clustering_of_videos = []
    for cluster in clustering.values():
        cluster_of_videos = [hash_2_video[id] for id in cluster]
        clustering_of_videos.append(cluster_of_videos)

    return clustering_of_videos


def deduplicate(videos: List[Video]) -> List[Video]:
    def duplicates_any_other_video_within_the_window(video: Video, other_videos: List[Video]) -> bool:
        for other_video in other_videos:
            if is_duplicate(video1=video, video2=other_video):
                return True
        return False

    # We do a sliding window algorithm.
    videos.sort(key=lambda x: x.title)

    window_size = 3

    # This way (discarding duplicates right away) we don't need to calculate the transitive closure.

    videos_to_keep = []
    while videos:
        video = videos.pop(0)

        # Is it a duplicate to any other video inside the window?
        is_dup = duplicates_any_other_video_within_the_window(
            video=video, other_videos=videos[0:window_size - 1])

        if is_dup:
            # We can ignore this video because its duplicate is still there (later in the list).
            pass
        else:
            # This video is unique. We need to keep it.
            videos_to_keep.append(video)

    return videos_to_keep


def order_by_frequency(strings: List[str]) -> List[str]:
    # This makes the input list unique, but orders by frequency and ignores empty strings.
    # I.e., ["a", "", "", "b", "b", ""] -> ["b", "a"].
    strings_without_empty_strings = [string for string in strings if string]
    string_2_strings = group_by(
        items=strings_without_empty_strings, criterion=lambda x: x)
    string_2_frequency = {string: len(strings)
                          for string, strings in string_2_strings.items()}
    strings_sorted_by_frequency = sorted(string_2_frequency.keys(
    ), key=lambda key: string_2_frequency[key], reverse=True)
    return strings_sorted_by_frequency


def fuse_videos(videos: List[Video]) -> Video:
    if len(videos) == 1:
        return videos.pop()

    classes = set([type(video).__class__ for video in videos])

    # If we have videos with and without series, take those with series first, because the video link is more likely correct.
    videos_with_series = []
    videos_without_series = []
    for video in videos:
        if video.series:
            videos_with_series.append(video)
        else:
            videos_without_series.append(video)

    if videos_with_series:
        videos_to_merge = videos_with_series
    else:
        videos_to_merge = videos_without_series

    # For those attributes, we don't know which is better and order by frequency (discarding empty strings).
    title = order_by_frequency([video.title for video in videos_to_merge]).pop()
    thumbnail = order_by_frequency([video.thumbnail for video in videos_to_merge]).pop()
    shortname = order_by_frequency([video.shortname for video in videos_to_merge]).pop()
    series = order_by_frequency([video.series for video in videos_to_merge]).pop()

    #video_links = set([video.video for video in videos_to_merge])

    # We should pick that one with the best quality. But this is not stored in the object as of now.
    video = order_by_frequency([video.video_link() for video in videos_to_merge]).pop()

    return RegularVideo(
        thumbnail=thumbnail,
        title=title,
        series=series,
        shortname=shortname,
        video=video,
    )
