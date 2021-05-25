import datetime
from typing import List, Callable
from abc import ABC, abstractmethod


# ----Resync policy----
# Resync policy factory function
def get_resync_policy_for_filter(filter_stats: 'FilterStats') -> \
        Callable[['FilterStats', 'ResyncerConfig'], bool]:
    return should_resync_filter_data_generic


# Resync policy interface function
def should_resync_filter_data(filter_stats: 'FilterStats',
                              config: 'ResyncerConfig') -> bool:
    raise NotImplementedError('should_resync_filter_data is an interface function')


# Concrete resync policies
def should_resync_filter_data_generic(filter_stats: 'FilterStats',
                                      config: 'ResyncerConfig') -> bool:
    if(_days_since_last_query(filter_stats._last_query_time_utc) >
            config.idle_resync_threshold_in_days):
        return False
    else:
        return True
# ----Resync policy----


def _days_since_last_query(_last_query_time_utc: datetime.datetime) -> int:
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    return (utc_now - _last_query_time_utc).days


class FilterStats:
    def __init__(self, search_filter: str, last_query_time_utc: datetime.datetime):
        self._search_filter = search_filter
        self._last_query_time_utc = last_query_time_utc

    @property
    def search_filter(self) -> str:
        return self._search_filter

    @property
    def last_query_time_utc(self) -> datetime.datetime:
        return self._last_query_time_utc


class FilterStatsRepo(ABC):
    # convert to return enumerator if performance concern
    @abstractmethod
    def get_all(self) -> List[FilterStats]:
        raise NotImplementedError('FilterStatsRepo is an interface')

    @abstractmethod
    def remove_for_filter(self, search_filter: str):
        raise NotImplementedError('FilterStatsRepo is an interface')


class ResyncerConfig:
    def __init__(self, idle_resync_threshold_in_days: int):
        self._idle_resync_threshold_in_days = idle_resync_threshold_in_days

    @property
    def idle_resync_threshold_in_days(self):
        return self._idle_resync_threshold_in_days
