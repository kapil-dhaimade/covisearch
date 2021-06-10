from typing import Dict
import enum
from datetime import datetime

from fuzzywuzzy import fuzz

from covisearch.aggregation.core.domain.entities import CovidResourceInfo, \
    HospitalBedsICUInfo, HospitalBedsInfo, MedicineInfo, CovidResourceType, SearchFilter
from covisearch.aggregation.core.domain.resourcemapping import WebSource
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


class MedicineInfoComparator(CovidResourceInfoComparator):
    THRESHOLD_FOR_STRING_COMPARISION = 77
    THRESHOLD_FOR_VERIFICATION_DAYS = 15
    MAX_DAYS_DIFF = 100000

    def __init__(self, search_filter: SearchFilter):
        super().__init__(search_filter)
        # NOTE: KAPIL: Resource info Id vs. med name match val True/False
        self._med_match_cache: Dict[int, bool] = {}

    def compare(self, res_info_a: Dict, res_info_b: Dict) -> int:
        med_name_str = MedicineInfo.get_med_name(self._search_filter.resource_type)
        res_info_a_details_has_med = self._is_med_name_present_in_resource_fields(med_name_str, res_info_a)
        res_info_b_details_has_med = self._is_med_name_present_in_resource_fields(med_name_str, res_info_b)

        return self.compare_basedon_relevence(res_info_a, res_info_a_details_has_med,
                                              res_info_b, res_info_b_details_has_med)

    def _is_med_name_present_in_resource_fields(self, medicine_name, res_info: Dict) -> bool:
        res_info_id = res_info[MedicineInfo.ID_LABEL]

        if res_info_id in self._med_match_cache:
            return self._med_match_cache[res_info_id]

        if not self._is_smart_match_needed_for_resource(res_info):
            self._med_match_cache[res_info_id] = True
            return True

        med_match_ratio_in_res_subtype = _get_ratio(medicine_name, res_info[MedicineInfo.RESOURCE_SUBTYPE_LABEL])
        if med_match_ratio_in_res_subtype >= self.THRESHOLD_FOR_STRING_COMPARISION:
            self._med_match_cache[res_info_id] = True
            return True

        med_match_ratio_in_details = _get_ratio(medicine_name, res_info[MedicineInfo.DETAILS_LABEL])
        res_info_details_has_med = True if med_match_ratio_in_details >= self.THRESHOLD_FOR_STRING_COMPARISION \
            else False
        self._med_match_cache[res_info_id] = res_info_details_has_med
        return res_info_details_has_med

    @staticmethod
    def _is_smart_match_needed_for_resource(res_info: Dict) -> bool:
        first_src_for_resource = res_info[MedicineInfo.SOURCES_LABEL][0]
        return first_src_for_resource[MedicineInfo.SOURCE_NEEDS_SMART_MATCH]

    @classmethod
    def _check_if_med_value_present_or_absent_in_both(cls, res_info_a_details_has_med,
                                                      res_info_b_details_has_med) -> bool:
        if res_info_a_details_has_med is True and res_info_b_details_has_med is True:
            return True
        if res_info_a_details_has_med is False and res_info_b_details_has_med is False:
            return True
        return False

    def compare_basedon_relevence(self, res_info_a, res_info_a_details_has_med,
                                  res_info_b, res_info_b_details_has_med):

        if self._check_if_med_value_present_or_absent_in_both(res_info_a_details_has_med,
                                                             res_info_b_details_has_med):
            return super().compare(res_info_a, res_info_b)

        relevent_res_info = self._get_most_relevent_res_info(
            res_info_a, res_info_a_details_has_med, res_info_b, res_info_b_details_has_med)

        if relevent_res_info is res_info_a:
            return -1
        else:
            return 1

    @classmethod
    def _get_most_relevent_res_info(cls, res_info_a, res_info_a_details_has_med, res_info_b,
                                    res_info_b_details_has_med):
        recent_verified_res_info = cls._get_more_recently_verified_res_info(res_info_a, res_info_b)
        old_verified_res_info = res_info_a if recent_verified_res_info is res_info_b else res_info_b

        if res_info_a_details_has_med is True and recent_verified_res_info is res_info_a:
            return res_info_a
        if res_info_b_details_has_med is True and recent_verified_res_info is res_info_b:
            return res_info_b

        last_verified_label = MedicineInfo.LAST_VERIFIED_UTC_LABEL
        last_verified_recent: datetime = recent_verified_res_info[last_verified_label]
        last_verified_older: datetime = old_verified_res_info[last_verified_label]
        days_between_verification_of_recent_and_earlier = cls._get_days_between_recent_and_earlier(
            last_verified_older, last_verified_recent)

        if days_between_verification_of_recent_and_earlier > cls.THRESHOLD_FOR_VERIFICATION_DAYS:
            return recent_verified_res_info
        else:
            return old_verified_res_info

    @classmethod
    def _get_days_between_recent_and_earlier(cls, last_verified_older, last_verified_recent):
        if not last_verified_older and not last_verified_recent:
            return cls.MAX_DAYS_DIFF

        if not last_verified_older and last_verified_recent:
            return cls.MAX_DAYS_DIFF

        if last_verified_older and not last_verified_recent:
            return 0

        return (last_verified_recent - last_verified_older).days


def _get_ratio(str1, str2):
    return fuzz.partial_ratio(str1, str2)


def _get_resource_info_comparator_class(resource_type: CovidResourceType):
    res_type_comparator_classes = {
        CovidResourceType.HOSPITAL_BED: HospitalBedsInfoComparator,
        CovidResourceType.HOSPITAL_BED_ICU: HospitalBedsICUInfoComparator,
        CovidResourceType.MED_AMPHOTERICIN_B: MedicineInfoComparator,
        CovidResourceType.MED_AMPHOLYN: MedicineInfoComparator,
        CovidResourceType.MED_CRESEMBA: MedicineInfoComparator,
        CovidResourceType.MED_OSELTAMIVIR: MedicineInfoComparator,
        CovidResourceType.MED_TOCILIZUMAB: MedicineInfoComparator,
        CovidResourceType.MED_POSACONAZOLE: MedicineInfoComparator
    }
    return res_type_comparator_classes.get(resource_type, CovidResourceInfoComparator)
