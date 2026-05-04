import os


class TrackDataController:
    def __init__(self, track, variant):
        # type: (str, str | None) -> None
        self.track = track
        self.variant = variant
        self.circuit_dir = os.path.join(os.getcwd(), "content", "tracks", self.track)

    def load(self):
        self._load_track_ini()
        self._load_track_map()

    @property
    def track_id(self):
        return "{}_{}".format(self.track, self.variant) if self.variant else self.track

    def _load_track_ini(self):
        pass

    def _load_track_map(self):
        pass
