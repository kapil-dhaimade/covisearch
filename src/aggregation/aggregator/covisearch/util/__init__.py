from datetime import datetime

import covisearch.util.types as types


def elapsed_days(date: datetime) -> int:
    curr = datetime.now()
    diff = date - curr
    return diff.days
