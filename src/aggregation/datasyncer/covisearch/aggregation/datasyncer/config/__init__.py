def get_resync_threshold_in_days() -> int:
    # TODO
    return 0


class Config:
    def __init__(self):
        self._idle_resync_threshold_in_days = get_resync_threshold_in_days()

    @property
    def idle_resync_threshold_in_days(self):
        return self._idle_resync_threshold_in_days


config = Config()
