import enum
from datetime import datetime, timezone, timedelta
from dateutil import relativedelta
import dateutil.parser as dateutilparser
import re


class DatetimeFormat(enum.Enum):
    # '5 hours ago', '2 days ago', etc.
    AGO = 1
    # 2021-05-16T21:06:17.000000+05:30
    ISOFORMAT = 2
    # 2/05 5:35 PM (2-May), 27/12 at 6:09 AM, etc.
    SHORT_DATETIME_DD_MM = 3
    # 2/05 5:35 PM (5-Feb), 12/27 at 6:09 AM, etc.
    SHORT_DATETIME_MM_DD = 4
    # eg: 1622140319 (number of seconds since January 1, 1970 (midnight UTC/GMT), not counting leap seconds)
    UNIX_TIMESTAMP_SEC = 5
    # eg: 1622140319000 (number of millisecs since January 1, 1970 (midnight UTC/GMT), not counting leap seconds)
    UNIX_TIMESTAMP_MILLISEC = 6


# NOTE: KAPIL: Refer 'https://regexr.com/' to test out regex
re_mins_ago_pattern = re.compile('(\d+|a)\s+minutes?\s+ago', re.IGNORECASE)
re_hrs_ago_pattern = re.compile('(\d+|an)\s+hours?\s+ago', re.IGNORECASE)
re_days_ago_pattern = re.compile('(\d+|a)\s+days?\s+ago', re.IGNORECASE)
re_weeks_ago_pattern = re.compile('(\d+|a)\s+weeks?\s+ago', re.IGNORECASE)
re_months_ago_pattern = re.compile('(\d+|a)\s+months?\s+ago', re.IGNORECASE)
re_yrs_ago_pattern = re.compile('(\d+|a)\s+years?\s+ago', re.IGNORECASE)


def map_ago_format_timestamp_to_utc_datetime(ago_format_datetime: str) -> datetime:
    # Minutes
    re_minutes_result = re_mins_ago_pattern.search(ago_format_datetime)
    if re_minutes_result is not None:
        mins_ago_str = re_minutes_result.group(1)
        if mins_ago_str.lower() == 'a':
            mins_ago = 1
        else:
            mins_ago = float(mins_ago_str)
        return datetime.now(timezone.utc) - timedelta(minutes=mins_ago)

    # Hours
    re_hours_result = re_hrs_ago_pattern.search(ago_format_datetime)
    if re_hours_result is not None:
        hrs_ago_str = re_hours_result.group(1)
        if hrs_ago_str.lower() == 'an':
            hrs_ago = 1
        else:
            hrs_ago = float(hrs_ago_str)
        return datetime.now(timezone.utc) - timedelta(hours=hrs_ago)

    # Days
    re_days_result = re_days_ago_pattern.search(ago_format_datetime)
    if re_days_result is not None:
        days_ago_str = re_days_result.group(1)
        if days_ago_str.lower() == 'a':
            days_ago = 1
        else:
            days_ago = float(days_ago_str)
        return datetime.now(timezone.utc) - timedelta(days=days_ago)

    # Weeks
    re_weeks_result = re_weeks_ago_pattern.search(ago_format_datetime)
    if re_weeks_result is not None:
        weeks_ago_str = re_weeks_result.group(1)
        if weeks_ago_str.lower() == 'a':
            weeks_ago = 1
        else:
            weeks_ago = float(weeks_ago_str)
        return datetime.now(timezone.utc) - timedelta(weeks=weeks_ago)

    # Months
    re_months_result = re_months_ago_pattern.search(ago_format_datetime)
    if re_months_result is not None:
        months_ago_str = re_months_result.group(1)
        if months_ago_str.lower() == 'a':
            months_ago = 1
        else:
            months_ago = float(months_ago_str)
        return datetime.now(timezone.utc) - relativedelta.relativedelta(months=months_ago)

    # Years
    re_years_result = re_yrs_ago_pattern.search(ago_format_datetime)
    if re_years_result is not None:
        years_ago_str = re_years_result.group(1)
        if years_ago_str.lower() == 'a':
            years_ago = 1
        else:
            years_ago = float(years_ago_str)
        return datetime.now(timezone.utc) - relativedelta.relativedelta(years=years_ago)
    return None


def map_short_datetime_dd_mm_to_utc_datetime(short_datetime_str: str, time_zone) -> datetime:
    # NOTE: KAPIL: SO: https://stackoverflow.com/questions/15491894/regex-to-validate-date-format-dd-mm-yyyy
    # re_date_result = re.search('(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)'
    #                          '(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)'
    #                          '?\d{2})|(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?'
    #                          '(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|'
    #                          '[3579][26])00))))|(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:'
    #                          '(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})',
    #                          short_datetime_str, re.IGNORECASE)
    # NOTE: KAPIL: SO:
    # https://stackoverflow.com/questions/7536755/regular-expression-for-matching-hhmm-time-format/7536768
    # re_time_result = re.search('([0-1]?[0-9]|2[0-3]):[0-5][0-9]\s(pm|am)')

    # NOTE:KAPIL: Giving preference to DD-MM-YY
    utc_datetime = dateutilparser.parse(short_datetime_str,
                                        parserinfo=dateutilparser.parserinfo(dayfirst=True))
    utc_datetime = set_timezone_if_not_present(utc_datetime, time_zone)
    return utc_datetime.astimezone(tz=timezone.utc)


def map_short_datetime_mm_dd_to_utc_datetime(short_datetime_str: str, time_zone) -> datetime:
    # NOTE:KAPIL: Giving preference to MM-DD-YY
    utc_datetime = dateutilparser.parse(short_datetime_str,
                                        parserinfo=dateutilparser.parserinfo(dayfirst=False))
    utc_datetime = set_timezone_if_not_present(utc_datetime, time_zone)
    return utc_datetime.astimezone(tz=timezone.utc)


def map_unix_timestamp_to_utc_datetime(unix_timestamp_str: str, in_millisec: bool) -> datetime:
    unix_timestamp = int(unix_timestamp_str)
    if in_millisec:
        unix_timestamp_sec = unix_timestamp / 1000
    else:
        unix_timestamp_sec = unix_timestamp
    return datetime.utcfromtimestamp(unix_timestamp_sec).astimezone(tz=timezone.utc)


def is_timezone_aware(timestamp: datetime):
    return timestamp.tzinfo is not None and \
           timestamp.tzinfo.utcoffset(timestamp) is not None


# NOTE: KAPIL: Brings None datetime objects to start of list.
def compare_datetimes_ascending(datetime_a, datetime_b) -> int:
    if datetime_a is None and datetime_b is None:
        return 0
    if datetime_a is not None and datetime_b is None:
        return 1
    if datetime_b is not None and datetime_a is None:
        return -1
    if datetime_a < datetime_b:
        return -1
    if datetime_a > datetime_b:
        return 1
    return 0


def set_timezone_if_not_present(timestamp: datetime, time_zone) -> datetime:
    if not is_timezone_aware(timestamp):
        timestamp = timestamp.replace(tzinfo=time_zone)
    return timestamp


# from dateutil import tz
#
#
# if __name__=='__main__':
#     verified_pat = re.compile('mumbai$', re.IGNORECASE)
#     res1 = verified_pat.search('available mumbai verifimumbaied')
#     res2 = verified_pat.search('mUmbai')
#     res3 = verified_pat.search('Not verified')
#     # dateutil is handling this datetime string format successfully!
#     isofmt1 = map_short_datetime_dd_mm_to_utc_datetime('Mon May 31 21:27:42 +0000 2021', tz.gettz('Asia/Kolkata'))
#     isofmt2 = map_short_datetime_dd_mm_to_utc_datetime('29/4 20:03', tz.gettz('Asia/Kolkata'))
#     print(9)
