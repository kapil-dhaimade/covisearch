import datetime
from abc import ABC, abstractmethod

from covisearch.aggregation.datasyncer.config import Config


# ----Resync policy----
# Resync policy for resource
def should_resync_filter_data(filter_stats: 'FilterStats', config: Config) -> bool:
    raise NotImplementedError('should_resync_filter_data is an interface function')


def should_resync_filter_data_generic(filter_stats: 'FilterStats', config: Config) -> bool:
    if(_days_since_last_query(filter_stats._last_query_time_utc) >
            config.idle_resync_threshold_in_days):
        return False
    else:
        return True


def _days_since_last_query(_last_query_time_utc: datetime.datetime) -> int:
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    return (utc_now - _last_query_time_utc).days


class FilterStats:
    def __init__(self, data_filter: str, last_query_time_utc: datetime.datetime):
        self._data_filter = data_filter
        self._last_query_time_utc = last_query_time_utc

    @property
    def data_filter(self):
        return self._data_filter

    @property
    def last_query_time_utc(self):
        return self._last_query_time_utc


class FilterStatsRepo(ABC):
    @abstractmethod
    def get_all(self) -> list[FilterStats]:
        raise NotImplementedError('FilterStatsRepo is an interface')
