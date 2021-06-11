from typing import Dict
import enum
from datetime import datetime

import regex

from covisearch.aggregation.core.domain.entities import CovidResourceInfo, \
    HospitalBedsICUInfo, HospitalBedsInfo, MedicineInfo, CovidResourceType, SearchFilter, OxygenInfo
import covisearch.util.datetimeutil as datetimeutil


def get_res_info_comparator(search_filter: SearchFilter):
    comparator_class = _get_resource_info_comparator_class(search_filter.resource_type)
    return comparator_class(search_filter).compare


class CovidResourceInfoComparator:
    def __init__(self, search_filter: SearchFilter):
        self._search_filter = search_filter

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_times_comp = self._compare_datetime_field(
            res_info_a, res_info_b, CovidResourceInfo.LAST_VERIFIED_UTC_LABEL)
        if last_verified_times_comp is not 0:
            return -1 * last_verified_times_comp

        post_times_comp = self._compare_datetime_field(
            res_info_a, res_info_b, CovidResourceInfo.POST_TIME_LABEL)
        if post_times_comp is not 0:
            return -1 * post_times_comp

        return 0

    @classmethod
    def _get_more_recently_verified_res_info(cls, res_info_a: Dict, res_info_b: Dict) -> Dict:
        last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
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


class HospitalBedsInfoComparator(CovidResourceInfoComparator):
    TOTAL_BEDS_WEIGHTAGE_THRESHOLD = 10

    def __init__(self, search_filter: SearchFilter):
        super().__init__(search_filter)

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        if self._is_any_of_last_verified_and_total_beds_fields_none(res_info_a, res_info_b):
            common_info_compare_result = super().compare(res_info_a, res_info_b)
            if common_info_compare_result is not 0:
                return common_info_compare_result
            return self.get_total_available_bed_compare_result(res_info_a, res_info_b)

        if self._is_any_of_last_verified_and_total_beds_fields_equal(res_info_a, res_info_b):
            return self._get_compare_result_in_case_of_one_field_equal(res_info_a, res_info_b)

        winner = self._get_winner_of_last_verified_vs_total_beds_compare(res_info_a, res_info_b)
        if winner is res_info_a:
            return -1
        else:
            return 1

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
        last_verified_label = HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recently_verified_res_info[last_verified_label]
        last_verified_older: datetime = older_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = (last_verified_recent - last_verified_older).days

        total_available_beds_label = HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL
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
        if res_info_a[HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL] == \
                res_info_b[HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL] == \
                res_info_b[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL]:
            return True
        return False

    @classmethod
    def get_total_available_bed_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        total_available_beds_a = res_info_a[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL]
        total_available_beds_b = res_info_b[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL]
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
        last_verified_label = HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL
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
        if not res_info_a[HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if not res_info_b[HospitalBedsInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        if res_info_b[HospitalBedsInfo.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        return False


class HospitalBedsICUInfoComparator(CovidResourceInfoComparator):
    TOTAL_BEDS_WEIGHTAGE_THRESHOLD = 2

    def __init__(self, search_filter: SearchFilter):
        super().__init__(search_filter)

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        if self._is_any_of_last_verified_and_total_beds_fields_none(res_info_a, res_info_b):
            common_info_compare_result = super().compare(res_info_a, res_info_b)
            if common_info_compare_result is not 0:
                return common_info_compare_result
            return self.get_total_available_bed_compare_result(res_info_a, res_info_b)

        if self._is_any_of_last_verified_and_total_beds_fields_equal(res_info_a, res_info_b):
            return self._get_compare_result_in_case_of_one_field_equal(res_info_a, res_info_b)

        winner = self._get_winner_of_last_verified_vs_total_beds_compare(res_info_a, res_info_b)
        if winner is res_info_a:
            return -1
        else:
            return 1

    @classmethod
    def get_total_available_bed_compare_result(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        total_available_beds_a = res_info_a[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL]
        total_available_beds_b = res_info_b[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL]
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
        last_verified_label = HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL
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
        if not res_info_a[HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if not res_info_b[HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        if res_info_b[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            return True
        return False

    @classmethod
    def _is_any_of_last_verified_and_total_beds_fields_equal(cls, res_info_a: Dict, res_info_b: Dict) -> bool:
        if res_info_a[HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL] == \
                res_info_b[HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL]:
            return True
        if res_info_a[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL] == \
                res_info_b[HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL]:
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
        last_verified_label = HospitalBedsICUInfo.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recently_verified_res_info[last_verified_label]
        last_verified_older: datetime = older_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = (last_verified_recent - last_verified_older).days

        total_available_beds_label = HospitalBedsICUInfo.TOTAL_AVAILABLE_BEDS_LABEL
        total_beds_of_recent_res_info: int = recently_verified_res_info[total_available_beds_label]
        total_beds_of_older_res_info: int = older_verified_res_info[total_available_beds_label]
        diff_between_total_beds_of_older_and_recent = total_beds_of_older_res_info - total_beds_of_recent_res_info

        if diff_between_total_beds_of_older_and_recent > \
                ((days_between_verification_of_recent_and_earlier + 1) * cls.TOTAL_BEDS_WEIGHTAGE_THRESHOLD):
            return True
        else:
            return False


class MedicineSubtypeInfoComparator(CovidResourceInfoComparator):
    THRESHOLD_FOR_STRING_COMPARISION = 3
    THRESHOLD_FOR_VERIFICATION_DAYS = 30

    def __init__(self, search_filter: SearchFilter):
        super().__init__(search_filter)
        med_name_to_match = MedicineInfo.get_med_name(self._search_filter.resource_type)
        self._resource_subtype_comparator = ResourceSubtypeInfoComparator(
            search_filter, med_name_to_match, self.THRESHOLD_FOR_STRING_COMPARISION,
            self.THRESHOLD_FOR_VERIFICATION_DAYS)

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        return self._resource_subtype_comparator.compare(res_info_a, res_info_b)


class OxygenSubtypeInfoComparator(CovidResourceInfoComparator):
    THRESHOLD_FOR_STRING_COMPARISION = 2
    THRESHOLD_FOR_VERIFICATION_DAYS = 30

    def __init__(self, search_filter: SearchFilter):
        super().__init__(search_filter)
        oxy_subtype_name_to_match = OxygenInfo.get_oxy_subtype_name(self._search_filter.resource_type)
        self._resource_subtype_comparator = ResourceSubtypeInfoComparator(
            search_filter, oxy_subtype_name_to_match, self.THRESHOLD_FOR_STRING_COMPARISION,
            self.THRESHOLD_FOR_VERIFICATION_DAYS)

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        return self._resource_subtype_comparator.compare(res_info_a, res_info_b)


class ResourceSubtypeInfoComparator(CovidResourceInfoComparator):
    MAX_DAYS_DIFF = 100000

    def __init__(self, search_filter: SearchFilter, resource_name_to_match: str,
                 threshold_for_string_match: int, threshold_for_verification_days: int):
        super().__init__(search_filter)
        # NOTE: KAPIL: Resource info Id vs. resource string match val True/False
        self._resource_match_cache: Dict[int, bool] = {}
        self._resource_name_to_match = resource_name_to_match
        self._threshold_for_string_match: int = threshold_for_string_match
        self._threshold_for_verification_days: int = threshold_for_verification_days

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        res_info_a_details_has_match = self._is_res_name_present_in_resource_fields(res_info_a)
        res_info_b_details_has_match = self._is_res_name_present_in_resource_fields(res_info_b)

        return self._compare_basedon_relevence(res_info_a, res_info_a_details_has_match,
                                               res_info_b, res_info_b_details_has_match)

    def _is_res_name_present_in_resource_fields(self, res_info: Dict) -> bool:
        res_info_id = res_info[CovidResourceInfo.ID_LABEL]

        if res_info_id in self._resource_match_cache:
            return self._resource_match_cache[res_info_id]

        if not self._is_smart_match_needed_for_resource(res_info):
            self._resource_match_cache[res_info_id] = True
            return True

        if _is_fuzzy_match(self._resource_name_to_match, res_info[CovidResourceInfo.RESOURCE_SUBTYPE_LABEL],
                           self._threshold_for_string_match):
            return True

        res_info_details_has_match = _is_fuzzy_match(
            self._resource_name_to_match, res_info[CovidResourceInfo.DETAILS_LABEL].lower(),
            self._threshold_for_string_match)

        self._resource_match_cache[res_info_id] = res_info_details_has_match
        return res_info_details_has_match

    @staticmethod
    def _is_smart_match_needed_for_resource(res_info: Dict) -> bool:
        first_src_for_resource = res_info[CovidResourceInfo.SOURCES_LABEL][0]
        return first_src_for_resource[CovidResourceInfo.SOURCE_NEEDS_SMART_MATCH]

    @classmethod
    def _check_if_res_value_present_or_absent_in_both(cls, res_info_a_details_has_match,
                                                      res_info_b_details_has_match) -> bool:
        if res_info_a_details_has_match is True and res_info_b_details_has_match is True:
            return True
        if res_info_a_details_has_match is False and res_info_b_details_has_match is False:
            return True
        return False

    def _compare_basedon_relevence(self, res_info_a, res_info_a_details_has_match,
                                   res_info_b, res_info_b_details_has_match):

        if self._check_if_res_value_present_or_absent_in_both(res_info_a_details_has_match,
                                                              res_info_b_details_has_match):
            return super().compare(res_info_a, res_info_b)

        relevent_res_info = self._get_most_relevent_res_info(
            res_info_a, res_info_a_details_has_match, res_info_b, res_info_b_details_has_match)

        if relevent_res_info is res_info_a:
            return -1
        else:
            return 1

    def _get_most_relevent_res_info(self, res_info_a, res_info_a_details_has_match, res_info_b,
                                    res_info_b_details_has_match):
        recent_verified_res_info = self._get_more_recently_verified_res_info(res_info_a, res_info_b)
        old_verified_res_info = res_info_a if recent_verified_res_info is res_info_b else res_info_b

        if res_info_a_details_has_match is True and recent_verified_res_info is res_info_a:
            return res_info_a
        if res_info_b_details_has_match is True and recent_verified_res_info is res_info_b:
            return res_info_b

        last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recent_verified_res_info[last_verified_label]
        last_verified_older: datetime = old_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = \
            self._get_days_between_recent_and_earlier_for_threshold_check(
                last_verified_older, last_verified_recent)

        if days_between_verification_of_recent_and_earlier > self._threshold_for_verification_days:
            return recent_verified_res_info
        else:
            return old_verified_res_info

    @classmethod
    def _get_days_between_recent_and_earlier_for_threshold_check(cls, last_verified_older, last_verified_recent):
        if not last_verified_older and not last_verified_recent:
            return 0

        if not last_verified_older and last_verified_recent:
            return cls.MAX_DAYS_DIFF

        if last_verified_older and not last_verified_recent:
            return 0

        return (last_verified_recent - last_verified_older).days


def _is_fuzzy_match(str1, str2, threshold) -> bool:
    fuzzy_threshold = '{e<=' + str(threshold) + '}'
    return bool(regex.search('(' + str1 + ')' + fuzzy_threshold, str2, regex.IGNORECASE))


def _get_resource_info_comparator_class(resource_type: CovidResourceType):
    res_type_comparator_classes = {
        CovidResourceType.HOSPITAL_BED: HospitalBedsInfoComparator,
        CovidResourceType.HOSPITAL_BED_ICU: HospitalBedsICUInfoComparator,
        CovidResourceType.MED_AMPHOTERICIN_B: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_AMPHOLYN: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_CRESEMBA: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_OSELTAMIVIR: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_TOCILIZUMAB: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_POSACONAZOLE: MedicineSubtypeInfoComparator,
        CovidResourceType.MED_FABIFLU: MedicineSubtypeInfoComparator,
        CovidResourceType.OXY_CONCENTRATOR: OxygenSubtypeInfoComparator,
        CovidResourceType.OXY_REGULATOR: OxygenSubtypeInfoComparator,
        CovidResourceType.OXY_REFILL: OxygenSubtypeInfoComparator,
        CovidResourceType.OXY_CYLINDER: OxygenSubtypeInfoComparator
    }
    return res_type_comparator_classes.get(resource_type, CovidResourceInfoComparator)
