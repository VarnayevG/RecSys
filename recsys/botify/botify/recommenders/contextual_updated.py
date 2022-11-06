from .user_based import Collaborative
from .recommender import Recommender
from .sticky_artist import StickyArtist
from .top_pop import TopPop
import random
import numpy as np


def get_shuffled_item(recommendations, track):
    shuffled = list(recommendations)
    random.shuffle(shuffled)
    return shuffled[0] if shuffled[0] != track else shuffled[1]


class СontextualUpdated(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self,
                 tracks_redis,
                 recommendations_redis,
                 catalog,
                 basic_tracks_redis,
                 artists_redis,
                 top_tracks):
        self.tracks_redis = tracks_redis
        self.recommendations_redis = recommendations_redis
        self.sticky_artist = StickyArtist(basic_tracks_redis, artists_redis, catalog)
        self.top_pop = TopPop(tracks_redis, top_tracks)
        self.fallback = Collaborative(recommendations_redis, tracks_redis, top_tracks, catalog)
        self.catalog = catalog

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float, history) -> int:
        if user in history:
            history[user]['track_time'].append(prev_track_time)
            history[user]['track'].append(prev_track)
        else:
            history[user] = {}
            history[user]['track_time'] = [prev_track_time]
            history[user]['track'] = [prev_track]

        # Doesn't seem to be benefitial
        # if random.random() < 0.1:
        #     return self.top_pop.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.tracks_redis.get(prev_track)

        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)

        if len(history[user]['track_time']) > 3 and np.mean(history[user]['track_time'][-3:]) < 0.3:
            return self.sticky_artist.recommend_next(user, history[user]['track'][0], history[user]['track_time'][0])

        if prev_track_time >= 0.1:
            recommendations = previous_track.recommendations if previous_track.recommendations \
                            else self.recommendations_redis.get(user)
        else:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        shuffled = list(recommendations)
        # random.shuffle(shuffled)
        for item in shuffled:
            if item not in history[user]['track']:
                return item
        return self.sticky_artist.recommend_next(user, history[user]['track'][0], history[user]['track_time'][0])
