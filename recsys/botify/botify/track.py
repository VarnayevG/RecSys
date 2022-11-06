import itertools
import json
import pickle
from dataclasses import dataclass, field
from typing import List


@dataclass
class Track:
    track: int
    artist: str
    title: str
    recommendations: List[int] = field(default=lambda: [])


class Catalog:
    """
    A helper class used to load track data upon server startup
    and store the data to redis.
    """

    def __init__(self, app):
        self.app = app
        self.tracks = []
        self.top_tracks = []
        self.tracks_with_diverse_recs = []
        self.tracks_with_updated_recs = []

    # TODO Seminar 6 step 1: Configure reading tracks with diverse recommendations
    def load(self, catalog_path, top_tracks_path, tracks_with_diverse_recs_path, tracks_with_updated_recs_path):
        self.app.logger.info(f"Loading tracks from {catalog_path}")
        with open(catalog_path) as catalog_file:
            for j, line in enumerate(catalog_file):
                data = json.loads(line)
                self.tracks.append(Track(data["track"], data["artist"], data["title"], data["recommendations"], ))
        self.app.logger.info(f"Loaded {j + 1} tracks")

        self.app.logger.info(f"Loading tracks with diverse recommendations from {tracks_with_diverse_recs_path}")
        # your code is here
        with open(tracks_with_diverse_recs_path) as tracks_with_diverse_recs_file:
            for j, line in enumerate(tracks_with_diverse_recs_file):
                data = json.loads(line)
                self.tracks_with_diverse_recs.append(
                    Track(data["track"], data["artist"], data["title"], data["recommendations"], ))
        self.app.logger.info(f"Loaded {j + 1} tracks with diverse recs")

        self.app.logger.info(f"Loading top tracks from {top_tracks_path}")
        with open(top_tracks_path) as top_tracks_file:
            self.top_tracks = json.load(top_tracks_file)
        self.app.logger.info(f"Loaded {len(self.top_tracks)} top tracks")


        self.app.logger.info(f"Loading tracks with new recommendations from {tracks_with_updated_recs_path}")
        # your code is here
        with open(tracks_with_updated_recs_path) as tracks_with_updated_recs_file:
            for j, line in enumerate(tracks_with_updated_recs_file):
                data = json.loads(line)
                self.tracks_with_updated_recs.append(
                    Track(data["track"], data["artist"], data["title"], data["recommendations"], ))
        self.app.logger.info(f"Loaded {j + 1} tracks with new recs")

        return self

    # TODO Seminar 6 step 2: Configure uploading tracks with diverse recommendations to redis DB
    def upload_tracks(self, redis_tracks, redis_tracks_with_diverse_recs, redis_tracks_with_updated_recs):
        self.app.logger.info(f"Uploading tracks to redis")
        for track in self.tracks:
            redis_tracks.set(track.track, self.to_bytes(track))

        # your code is here
        for track in self.tracks_with_diverse_recs:
            redis_tracks_with_diverse_recs.set(track.track, self.to_bytes(track))

        self.app.logger.info(
            f"Uploaded {len(self.tracks)} tracks, {len(self.tracks_with_diverse_recs)} tracks with diverse recs"
        )

        for track in self.tracks_with_updated_recs:
            redis_tracks_with_updated_recs.set(track.track, self.to_bytes(track))
        self.app.logger.info(
            f"Uploaded {len(self.tracks_with_updated_recs)} tracks with new recs"
        )

    def upload_artists(self, redis):
        self.app.logger.info(f"Uploading artists to redis")
        sorted_tracks = sorted(self.tracks, key=lambda t: t.artist)
        for j, (artist, artist_catalog) in enumerate(
                itertools.groupby(sorted_tracks, key=lambda t: t.artist)
        ):
            artist_tracks = [t.track for t in artist_catalog]
            redis.set(artist, self.to_bytes(artist_tracks))
        self.app.logger.info(f"Uploaded {j + 1} artists")

    def upload_recommendations(self, redis, recommendations_path="RECOMMENDATIONS_FILE_PATH"):
        self.app.logger.info(f"Uploading recommendations to redis")
        recommendations_file_path = self.app.config[recommendations_path]
        with open(recommendations_file_path) as recommendations_file:
            for j, line in enumerate(recommendations_file):
                recommendations = json.loads(line)
                redis.set(
                    recommendations["user"], self.to_bytes(recommendations["tracks"])
                )
        self.app.logger.info(f"Uploaded recommendations for {j + 1} users")

    def to_bytes(self, instance):
        return pickle.dumps(instance)

    def from_bytes(self, bts):
        return pickle.loads(bts)
