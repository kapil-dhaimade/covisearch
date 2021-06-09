from abc import ABC, abstractmethod
from typing import Dict, List, Callable
import enum
import urllib.parse
from datetime import  datetime

from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import covisearch.util as util
import covisearch.util.datetimeutil as datetimeutil

# import covisearch.aggregation.core.domain.entities

from covisearch.aggregation.core.domain.entities import *


class CovidResourceInfo:
    CONTACT_NAME_LABEL = 'contact_name'
    ADDRESS_LABEL = 'address'
    DETAILS_LABEL = 'details'
    PHONES_LABEL = 'phones'
    POST_TIME_LABEL = 'post_time'
    LAST_VERIFIED_UTC_LABEL = 'last_verified_utc'
    CARD_SOURCE_URL_LABEL = 'card_source_url'
    SOURCES_LABEL = 'sources'
    SOURCE_URL_LABEL = 'url'
    SOURCE_NAME_LABEL = 'name'

    RESOURCE_TYPE_LABEL = 'resource_type'
    CITY_LABEL = 'city'

    @classmethod
    def _is_source_already_present_in_newer_resource_info(cls, source: Dict,
                                                          newer_resource_info: Dict) -> bool:
        src_name_label = cls.SOURCE_NAME_LABEL
        for newer_resource_info_source in newer_resource_info[cls.SOURCES_LABEL]:
            if newer_resource_info_source[src_name_label] == source[src_name_label]:
                return True
        return False

    @classmethod
    def _is_resource_info_in_merged_resources_list(cls, resource_info: Dict,
                                                   merged_resources: List[Dict]) -> bool:
        for merged_resource_item in merged_resources:
            # NOTE: KAPIL: This specifically checks if dict reference is present in list
            # or not. This is not dict value or hash check. Hence, we need to use 'is' and
            # not 'if resource_info in merged_resources' as 'in' returns true if values of
            # dicts are matching even though they're different objects.
            if resource_info is merged_resource_item:
                return True
        return False


    @classmethod
    def remove_redundant_fields(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        return covisearch_resources

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_times_comp = cls._compare_datetime_field(
            res_info_a, res_info_b, cls.LAST_VERIFIED_UTC_LABEL)
        if last_verified_times_comp is not 0:
            return -1 * last_verified_times_comp

        post_times_comp = cls._compare_datetime_field(
            res_info_a, res_info_b, cls.POST_TIME_LABEL)
        if post_times_comp is not 0:
            return -1 * post_times_comp

        return 0

    @classmethod
    def _get_more_recently_verified_res_info(cls, res_info_a: Dict, res_info_b: Dict) -> Dict:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_a = res_info_a[last_verified_label]
        last_verified_b = res_info_b[last_verified_label]

        if last_verified_a is None and last_verified_b is None:
            return res_info_a
        if last_verified_a is None and last_verified_b is not None:
            return res_info_b
        if last_verified_b is None and last_verified_a is not None:
            return res_info_a
        if last_verified_a > last_verified_b:
            return res_info_a
        else:
            return res_info_b

    @classmethod
    def _compare_datetime_field(cls, res_info_a: Dict, res_info_b: Dict,
                                field_name: str) -> int:
        return datetimeutil.compare_datetimes_ascending(res_info_a[field_name], res_info_b[field_name])


class BloodGroup(enum.Enum):
    A_P = 1
    A_N = 2
    B_P = 3
    B_N = 4
    O_P = 5
    O_N = 6
    AB_P = 7
    AB_N = 8
    ALL = 9

    @classmethod
    def to_string(cls, blood_grp: 'BloodGroup') -> str:
        blood_grp_str_mapping = {
            cls.A_P: 'a+',
            cls.A_N: 'a-',
            cls.B_P: 'b+',
            cls.B_N: 'b-',
            cls.O_P: 'o+',
            cls.O_N: 'o-',
            cls.AB_P: 'ab+',
            cls.AB_N: 'ab-',
            cls.ALL: 'all'
        }
        return blood_grp_str_mapping[blood_grp]

    @classmethod
    def from_string(cls, blood_grp_str: str) -> 'BloodGroup':
        blood_grp_str_mapping = {
            'a+': cls.A_P,
            'a-': cls.A_N,
            'b+': cls.B_P,
            'b-': cls.B_N,
            'o+': cls.O_P,
            'o-': cls.O_N,
            'ab+': cls.AB_P,
            'ab-': cls.AB_N,
            'all': cls.ALL
        }
        return blood_grp_str_mapping[blood_grp_str.lower()]


class PlasmaInfo(CovidResourceInfo):
    BLOOD_GROUP_LABEL = 'blood_group'

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.BLOOD_GROUP_LABEL, older_resource_info, newer_resource_info)


class BloodInfo(CovidResourceInfo):
    BLOOD_GROUP_LABEL = 'blood_group'

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.BLOOD_GROUP_LABEL, older_resource_info, newer_resource_info)


class OxygenInfo(CovidResourceInfo):
    LITRES_LABEL = 'litres'

    # TODO: Change when oxygen litres are implemented.
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.LITRES_LABEL, older_resource_info, newer_resource_info)


class HospitalBedsInfo(CovidResourceInfo):
    AVAILABLE_COVID_BEDS_LABEL = 'available_covid_beds'
    AVAILABLE_NO_OXYGEN_BEDS_LABEL = 'available_no_oxygen_beds'
    AVAILABLE_OXYGEN_BEDS_LABEL = 'available_oxygen_beds'
    TOTAL_AVAILABLE_BEDS_LABEL = 'total_available_beds'
    HOSPITAL_TYPE_LABEL = 'hospital_type'

    TOTAL_BEDS_WEIGHTAGE_THRESHOLD = 10

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        if cls._is_any_of_last_verified_and_total_beds_fields_none(res_info_a, res_info_b):
            common_info_compare_result = super().compare(res_info_a, res_info_b)
            if common_info_compare_result is not 0:
                return common_info_compare_result
            return cls.get_total_available_bed_compare_result(res_info_a, res_info_b)

        if cls._is_any_of_last_verified_and_total_beds_fields_equal(res_info_a, res_info_b):
            return cls._get_compare_result_in_case_of_one_field_equal(res_info_a, res_info_b)

        winner = cls._get_winner_of_last_verified_vs_total_beds_compare(res_info_a, res_info_b)
        if winner is res_info_a:
            return -1
        else:
            return 1

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_COVID_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_NO_OXYGEN_BEDS_LABEL,
                                   older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_OXYGEN_BEDS_LABEL,
                                   older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.TOTAL_AVAILABLE_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.HOSPITAL_TYPE_LABEL, older_resource_info, newer_resource_info)

    @classmethod
    def _get_winner_of_last_verified_vs_total_beds_compare(cls, res_info_a: Dict, res_info_b: Dict) -> Dict:
        recently_verified_res_info = cls._get_more_recently_verified_res_info(res_info_a, res_info_b)
        older_verified_res_info = res_info_b if recently_verified_res_info is res_info_a else res_info_a

        if cls._do_total_beds_of_older_res_info_have_more_weightage(
                older_verified_res_info, recently_verified_res_info):
            return older_verified_res_info
        else:
            return recently_verified_res_info

    # NOTE: KAPIL: Eg: Returns true if there's gap of 2 days between A's last verified and
    # B's last verified, but if B's total beds higher than A's total beds by more than 10 (say 11).
    # Calculation: 11 > 2 * 5 (5 is weightage threshold)
    # Other examples:
    #   -100 > 12 * 5 (if older res info's total beds are 100 more than recent res info's total beds)
    # The purpose of this function is to show hospitals with higher number of beds before those
    # with fewer beds but which happened to be recently verified.
    @classmethod
    def _do_total_beds_of_older_res_info_have_more_weightage(
            cls, older_verified_res_info: Dict, recently_verified_res_info: Dict) -> bool:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recently_verified_res_info[last_verified_label]
        last_verified_older: datetime = older_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = (last_verified_recent - last_verified_older).days

        total_available_beds_label = cls.TOTAL_AVAILABLE_BEDS_LABEL
        total_beds_of_recent_res_info: int = recently_verified_res_info[total_available_beds_label]
        total_beds_of_older_res_info: int = older_verified_res_info[total_available_beds_label]
        diff_between_total_beds_of_older_and_recent = total_beds_of_older_res_info - total_beds_of_recent_res_info

        if diff_between_total_beds_of_older_and_recent > \
                ((days_between_verification_of_recent_and_earlier + 1) * cls.TOTAL_BEDS_WEIGHTAGE_THRESHOLD):
            return True
        else:
            return False

    @classmethod
    def _is_any_of_last_verified_and_total_beds_fields_equal(cls, res_info_a: Dict, res_info_b: Dict) -> bool:
        if res_info_a[cls.LAST_VERIFIED_UTC_LABEL] == res_info_b[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL] == res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL]:
            return True
        return False

    @classmethod
    def get_total_available_bed_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        total_available_beds_a = res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL]
        total_available_beds_b = res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL]
        if total_available_beds_a is not None and total_available_beds_b is None:
            return -1
        if total_available_beds_b is not None and total_available_beds_a is None:
            return 1
        if total_available_beds_a is None and total_available_beds_b is None:
            return 0
        if total_available_beds_a > total_available_beds_b:
            return -1
        if total_available_beds_b > total_available_beds_a:
            return 1
        return 0

    @classmethod
    def _get_compare_result_in_case_of_one_field_equal(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_compare_result = cls._get_last_verified_compare_result(res_info_a, res_info_b)
        total_beds_compare_result = cls.get_total_available_bed_compare_result(res_info_a, res_info_b)
        if last_verified_compare_result == 0 and total_beds_compare_result == 0:
            return 0
        if last_verified_compare_result == 0 and total_beds_compare_result == -1:
            return -1
        if last_verified_compare_result == 0 and total_beds_compare_result == 1:
            return 1
        if last_verified_compare_result == -1 and total_beds_compare_result == 0:
            return -1
        if last_verified_compare_result == 1 and total_beds_compare_result == 0:
            return 1

    @classmethod
    def _get_last_verified_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_a = res_info_a[last_verified_label]
        last_verified_b = res_info_b[last_verified_label]
        if last_verified_a == last_verified_b:
            return 0
        if last_verified_a < last_verified_b:
            return 1
        if last_verified_a > last_verified_b:
            return -1

    @classmethod
    def _is_any_of_last_verified_and_total_beds_fields_none(cls, res_info_a: Dict, res_info_b: Dict) -> bool:
        if not res_info_a[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if not res_info_b[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        if res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        return False


class HospitalBedsICUInfo(CovidResourceInfo):
    AVAILABLE_NO_VENTILATOR_BEDS_LABEL = 'available_no_ventilator_beds'
    AVAILABLE_VENTILATOR_BEDS_LABEL = 'available_ventilator_beds'
    TOTAL_AVAILABLE_BEDS_LABEL = 'total_available_icu_beds'
    HOSPITAL_TYPE_LABEL = 'hospital_type'
    # NOTE: KAPIL: Difference between 'AVAILABLE_VENTILATORS_LABEL' and 'AVAILABLE_VENTILATOR_BEDS_LABEL'
    # is that some hospitals have column for available ventilator devices and another column for ICU beds,
    # while some hospitals have split up of available beds with and without ventilators.
    AVAILABLE_VENTILATORS_LABEL = 'available_ventilators'

    TOTAL_BEDS_WEIGHTAGE_THRESHOLD = 2

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        if cls._is_any_of_last_verified_and_total_beds_fields_none(res_info_a, res_info_b):
            common_info_compare_result = super().compare(res_info_a, res_info_b)
            if common_info_compare_result is not 0:
                return common_info_compare_result
            return cls.get_total_available_bed_compare_result(res_info_a, res_info_b)

        if cls._is_any_of_last_verified_and_total_beds_fields_equal(res_info_a, res_info_b):
            return cls._get_compare_result_in_case_of_one_field_equal(res_info_a, res_info_b)

        winner = cls._get_winner_of_last_verified_vs_total_beds_compare(res_info_a, res_info_b)
        if winner is res_info_a:
            return -1
        else:
            return 1

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_NO_VENTILATOR_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_VENTILATOR_BEDS_LABEL,
                                   older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.TOTAL_AVAILABLE_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.HOSPITAL_TYPE_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_VENTILATORS_LABEL, older_resource_info, newer_resource_info)

    @classmethod
    def get_total_available_bed_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        total_available_beds_a = res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL]
        total_available_beds_b = res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL]
        if total_available_beds_a is not None and total_available_beds_b is None:
            return -1
        if total_available_beds_b is not None and total_available_beds_a is None:
            return 1
        if total_available_beds_a is None and total_available_beds_b is None:
            return 0
        if total_available_beds_a > total_available_beds_b:
            return -1
        if total_available_beds_b > total_available_beds_a:
            return 1
        return 0

    @classmethod
    def _get_winner_of_last_verified_vs_total_beds_compare(cls, res_info_a: Dict, res_info_b: Dict) -> Dict:
        recently_verified_res_info = cls._get_more_recently_verified_res_info(res_info_a, res_info_b)
        older_verified_res_info = res_info_b if recently_verified_res_info is res_info_a else res_info_a

        if cls._do_total_beds_of_older_res_info_have_more_weightage(
                older_verified_res_info, recently_verified_res_info):
            return older_verified_res_info
        else:
            return recently_verified_res_info

    @classmethod
    def _get_last_verified_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_a = res_info_a[last_verified_label]
        last_verified_b = res_info_b[last_verified_label]
        if last_verified_a == last_verified_b:
            return 0
        if last_verified_a < last_verified_b:
            return 1
        if last_verified_a > last_verified_b:
            return -1

    @classmethod
    def _is_any_of_last_verified_and_total_beds_fields_none(cls, res_info_a: Dict, res_info_b: Dict) -> bool:
        if not res_info_a[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if not res_info_b[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        if res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        return False

    @classmethod
    def _is_any_of_last_verified_and_total_beds_fields_equal(cls, res_info_a: Dict, res_info_b: Dict) -> bool:
        if res_info_a[cls.LAST_VERIFIED_UTC_LABEL] == res_info_b[cls.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[cls.TOTAL_AVAILABLE_BEDS_LABEL] == res_info_b[cls.TOTAL_AVAILABLE_BEDS_LABEL]:
            return True
        return False

    @classmethod
    def _get_compare_result_in_case_of_one_field_equal(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_compare_result = cls._get_last_verified_compare_result(res_info_a, res_info_b)
        total_beds_compare_result = cls.get_total_available_bed_compare_result(res_info_a, res_info_b)
        if last_verified_compare_result == 0 and total_beds_compare_result == 0:
            return 0
        if last_verified_compare_result == 0 and total_beds_compare_result == -1:
            return -1
        if last_verified_compare_result == 0 and total_beds_compare_result == 1:
            return 1
        if last_verified_compare_result == -1 and total_beds_compare_result == 0:
            return -1
        if last_verified_compare_result == 1 and total_beds_compare_result == 0:
            return 1

    # NOTE: KAPIL: Eg: Returns true if there's gap of 2 days between A's last verified and
    # B's last verified, but if B's total beds higher than A's total beds by more than 10 (say 11).
    # Calculation: 11 > 2 * 5 (5 is weightage threshold)
    # Other examples:
    #   -100 > 12 * 5 (if older res info's total beds are 100 more than recent res info's total beds)
    # The purpose of this function is to show hospitals with higher number of beds before those
    # with fewer beds but which happened to be recently verified.
    @classmethod
    def _do_total_beds_of_older_res_info_have_more_weightage(
            cls, older_verified_res_info: Dict, recently_verified_res_info: Dict) -> bool:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recently_verified_res_info[last_verified_label]
        last_verified_older: datetime = older_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = (last_verified_recent - last_verified_older).days

        total_available_beds_label = cls.TOTAL_AVAILABLE_BEDS_LABEL
        total_beds_of_recent_res_info: int = recently_verified_res_info[total_available_beds_label]
        total_beds_of_older_res_info: int = older_verified_res_info[total_available_beds_label]
        diff_between_total_beds_of_older_and_recent = total_beds_of_older_res_info - total_beds_of_recent_res_info

        if diff_between_total_beds_of_older_and_recent > \
                ((days_between_verification_of_recent_and_earlier + 1) * cls.TOTAL_BEDS_WEIGHTAGE_THRESHOLD):
            return True
        else:
            return False


class AmbulanceInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class EcmoInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def merge_duplicates(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        return super().merge_duplicates(covisearch_resources)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class FoodInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class TestingInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class MedicineInfo(CovidResourceInfo):
    THRESHOLD_FOR_STRING_COMPARISION = 80
    THRESHOLD_FOR_VERIFICATION_DAYS = 5

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _is_med_name_present_in_details(cls, medicine_name, res_info: Dict) -> int:
        res_info_ratio = get_ratio(medicine_name, res_info[cls.DETAILS_LABEL])
        res_info_details_has_med = 1 if res_info_ratio >= cls.THRESHOLD_FOR_STRING_COMPARISION else 0
        return res_info_details_has_med

    @classmethod
    def _check_if_value_present_or_absent_in_both(cls, res_info_a_details_has_med, res_info_b_details_has_med) -> bool:
        if res_info_a_details_has_med == 1 and res_info_b_details_has_med == 1:
            return True
        if res_info_a_details_has_med == 0 and res_info_b_details_has_med == 0:
            return True
        return False

    @classmethod
    def compare_basedon_relevence(cls, res_info_a, res_info_a_details_has_med, res_info_b, res_info_b_details_has_med):
        if cls._check_if_value_present_or_absent_in_both(res_info_a_details_has_med, res_info_b_details_has_med):
            return super().compare(res_info_a, res_info_b)

        relevent_res_info = cls._get_most_relevent_res_info(res_info_a, res_info_a_details_has_med,
                                                            res_info_b, res_info_b_details_has_med)

        if relevent_res_info is res_info_a:
            return -1
        else:
            return 1

    def _get_most_relevent_res_info(cls, res_info_a, res_info_a_details_has_med, res_info_b, res_info_b_details_has_med):
        recent_verified_res_info = cls._get_more_recently_verified_res_info(res_info_a, res_info_b)
        old_verified_res_info = res_info_a if recent_verified_res_info is res_info_b else res_info_b

        if res_info_a_details_has_med == 1 and recent_verified_res_info is res_info_a:
            return res_info_a
        if res_info_b_details_has_med == 1 and recent_verified_res_info is res_info_b:
            return res_info_b

        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recent_verified_res_info[last_verified_label]
        last_verified_older: datetime = old_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = (last_verified_recent - last_verified_older).days

        if days_between_verification_of_recent_and_earlier > cls.THRESHOLD_FOR_VERIFICATION_DAYS:
            return recent_verified_res_info


class MedAmphotericinInfo(MedicineInfo):
    MEDICINE_NAME = "Amphotericine"

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:

        res_info_a_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_a)
        res_info_b_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_b)

        return cls.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                             res_info_b, res_info_b_details_has_med)


class MedCresembaInfo(MedicineInfo):
    MEDICINE_NAME = "Cresemba"

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:

        res_info_a_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_a)
        res_info_b_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_b)

        return cls.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                             res_info_b, res_info_b_details_has_med)


class MedTocilizumabInfo(MedicineInfo):
    MEDICINE_NAME = "Tocilizumab"

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:

        res_info_a_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_a)
        res_info_b_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_b)

        return cls.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                             res_info_b, res_info_b_details_has_med)


class MedOseltamivirInfo(MedicineInfo):
    MEDICINE_NAME = "Oseltamivir"

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:

        res_info_a_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_a)
        res_info_b_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_b)

        return cls.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                             res_info_b, res_info_b_details_has_med)


class MedAmpholynInfo(MedicineInfo):
    MEDICINE_NAME = "Ampholyn"

    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:

        res_info_a_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_a)
        res_info_b_details_has_med = cls._is_med_name_present_in_details(cls.MEDICINE_NAME, res_info_b)

        return cls.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                             res_info_b, res_info_b_details_has_med)

class VentilatorInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)


class HelplineInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)

def get_ratio(str1,str2):
    return fuzz.partial_ratio(str1,str2)

def get_res_info_comparator(resource_type: CovidResourceType):
    return get_resource_info_class(resource_type).compare


def get_resource_info_class(resource_type: CovidResourceType):
    res_type_classes = {
        CovidResourceType.PLASMA: PlasmaInfo,
        CovidResourceType.OXYGEN: OxygenInfo,
        CovidResourceType.HOSPITAL_BED: HospitalBedsInfo,
        CovidResourceType.HOSPITAL_BED_ICU: HospitalBedsICUInfo,
        CovidResourceType.AMBULANCE: AmbulanceInfo,
        CovidResourceType.ECMO: EcmoInfo,
        CovidResourceType.FOOD: FoodInfo,
        CovidResourceType.TESTING: TestingInfo,
        CovidResourceType.MEDICINE: MedicineInfo,
        CovidResourceType.VENTILATOR: VentilatorInfo,
        CovidResourceType.HELPLINE: HelplineInfo,
        CovidResourceType.BLOOD: BloodInfo,
        CovidResourceType.MED_AMPHOTERICIN_B: MedicineInfo,
        CovidResourceType.MED_AMPHOLYN: MedicineInfo,
        CovidResourceType.MED_CRESEMBA: MedicineInfo,
        CovidResourceType.MED_OSELTAMIVIR: MedicineInfo,
        CovidResourceType.MED_TOCILIZUMAB: MedicineInfo,
        CovidResourceType.MED_POSACONAZOLE: MedicineInfo
    }
    return res_type_classes[resource_type]
