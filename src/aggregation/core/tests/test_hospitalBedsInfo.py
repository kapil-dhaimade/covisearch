from unittest import TestCase
from datetime import datetime

from covisearch.aggregation.core.domain.entities import CovidResourceInfo, HospitalBedsInfo, HospitalBedsICUInfo
import covisearch.util.datetimeutil as datetimeutil


class TestHospitalBedsInfo(TestCase):
    def test_compare_when_any_of_last_verified_or_total_beds_is_none(self):
        last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
        post_time_label = CovidResourceInfo.POST_TIME_LABEL
        available_covid_beds_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_LABEL
        available_beds_without_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITHOUT_OXYGEN_LABEL
        available_beds_with_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITH_OXYGEN_LABEL
        total_beds_label = HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: 5,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 0)


        a = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: 5, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 5,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)

        a = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 10,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 0)


        a = {
            last_verified_label: datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 5,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 5,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label: None,
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 10,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label: datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 5, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)

    def test_compare_when_any_of_last_verified_and_total_beds_is_equal(self):
        last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
        post_time_label = CovidResourceInfo.POST_TIME_LABEL
        available_covid_beds_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_LABEL
        available_beds_without_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITHOUT_OXYGEN_LABEL
        available_beds_with_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITH_OXYGEN_LABEL
        total_beds_label = HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL

        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 10,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 0)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 2, available_beds_with_oxygen_label: 2,
            available_beds_without_oxygen_label: 2
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 2, available_beds_with_oxygen_label: 2,
            available_beds_without_oxygen_label: 10
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('1 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('1 days ago'),
            post_time_label: None,
            available_covid_beds_label: 3, available_beds_with_oxygen_label: 3,
            available_beds_without_oxygen_label: 3
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)

    def test_compare_with_total_beds_weightage_vs_last_verified(self):
        last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
        post_time_label = CovidResourceInfo.POST_TIME_LABEL
        available_covid_beds_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_LABEL
        available_beds_without_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITHOUT_OXYGEN_LABEL
        available_beds_with_oxygen_label = HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITH_OXYGEN_LABEL
        total_beds_label = HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL

        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 19,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: 10, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 21,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: 21, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 10,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('3 days ago'),
            post_time_label: None,
            available_covid_beds_label: 19, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('2 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 10,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('a minute ago'),
            post_time_label: None,
            available_covid_beds_label: 19, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('5 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 70,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), 1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('a minute ago'),
            post_time_label: None,
            available_covid_beds_label: 60, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('5 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 70,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)


        a = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('a minute ago'),
            post_time_label: None,
            available_covid_beds_label: 120, available_beds_with_oxygen_label: None,
            available_beds_without_oxygen_label: None
        }
        b = {
            last_verified_label:
                datetimeutil.map_ago_format_timestamp_to_utc_datetime('5 days ago'),
            post_time_label: None,
            available_covid_beds_label: None, available_beds_with_oxygen_label: 70,
            available_beds_without_oxygen_label: None
        }
        HospitalBedsInfo.add_total_available_beds(a)
        HospitalBedsInfo.add_total_available_beds(b)
        self.assertEqual(HospitalBedsInfo.compare(a, b), -1)
