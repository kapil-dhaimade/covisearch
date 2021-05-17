from abc import ABC, abstractmethod
from typing import Dict, List
import enum

import covisearch.util as util


class VerificationInfo:
    LAST_VERIFIED_UTC_LABEL = 'last_verified_utc'


class CovidResourceType(enum.Enum):
    OXYGEN = 1,
    PLASMA = 2,
    HOSPITAL_BED = 3,
    HOSPITAL_BED_ICU = 4

    @staticmethod
    def to_string(resource_type: 'CovidResourceType') -> str:
        res_type_strings = {
            CovidResourceType.PLASMA: 'plasma',
            CovidResourceType.HOSPITAL_BED_ICU: 'hospital_bed_icu',
            CovidResourceType.HOSPITAL_BED: 'hospital_bed',
            CovidResourceType.OXYGEN: 'oxygen'
        }
        return res_type_strings[resource_type]


class CovidResourceInfo(util.PY3CMP):
    CONTACT_NAME_LABEL = 'contact_name'
    ADDRESS_LABEL = 'address'
    DETAILS_LABEL = 'details'
    PHONE_NO_LABEL = 'phone_no'
    VERIFICATION_INFO_LABEL = 'verification_info'
    POST_TIME_LABEL = 'post_time'
    RESOURCE_TYPE_LABEL = 'resource_type'

    def __eq__(self, other):
        # No need to check resource type as isinstance will do the needful check
        if isinstance(other, self.__class__):
            return self.phone_no == other.phone_no
        return False

    def __cmp__(self, other):
        if self == other:
            return 0
        return self.score() > other.score()

    @classmethod
    def score(cls, res_info: Dict) -> int:
        score = 0
        verification_info = res_info[cls.VERIFICATION_INFO_LABEL]
        if verification_info is not None:
            verified_ago = util.elapsed_days(
                verification_info[VerificationInfo.LAST_VERIFIED_UTC_LABEL])
            if verified_ago < 5:
                score += 5 - verified_ago

        post_time = res_info[cls.POST_TIME_LABEL]
        if post_time is not None:
            posted_ago = util.elapsed_days(post_time)
            if posted_ago < 1:
                score += 1 - posted_ago
        return score


# todo - check serialization of enum
class BloodGroup(enum.Enum):
    A_P = 1
    A_N = 2
    B_P = 3
    B_N = 4
    O_P = 5
    O_N = 6
    AB_P = 7
    AB_N = 8


class PlasmaInfo(CovidResourceInfo):
    BLOOD_GROUP_LABEL = 'blood_group'


class OxygenInfo(CovidResourceInfo):
    LITRES_LABEL = 'litre'

    @classmethod
    def score(cls, res_info: Dict) -> int:
        score = super().score(res_info)
        litres = res_info[cls.LITRES_LABEL]
        if litres is not None:
            score += litres
        return score


class HospitalBedsInfo(CovidResourceInfo):
    AVAILABLE_BEDS_LABEL = 'available_beds'

    @classmethod
    def score(cls, res_info: Dict) -> int:
        score = super().score(res_info)
        available_beds = res_info[cls.AVAILABLE_BEDS_LABEL]
        if available_beds is not None:
            score += available_beds
        return score


class SearchFilter:
    def __init__(self, city: str, resource_type: CovidResourceType, blood_group: BloodGroup):
        self._city: str = city
        self._resource_type: CovidResourceType = resource_type
        self._blood_group: BloodGroup = blood_group

    @property
    def city(self) -> str:
        return self._city

    @property
    def resource_type(self) -> CovidResourceType:
        return self._resource_type

    @property
    def blood_group(self) -> BloodGroup:
        return self._blood_group

    @staticmethod
    def create_from_url_query_params_fmt(search_filter: str) -> 'SearchFilter':
        filter_tokens = search_filter.split('&')
        city_param = [city for city in filter_tokens if 'city=' in city][0]


class FilteredAggregatedResourceInfo(util.Serializable):
    def __init__(self, search_filter: Dict, data: List[CovidResourceInfo]):
        super().__init__()
        self.search_filter = search_filter
        self.data = data


class AggregatedResourceInfoRepo(ABC):
    @abstractmethod
    def get_filtered_resources(self, search_filter: Dict) -> FilteredAggregatedResourceInfo:
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')

    @abstractmethod
    def set_filtered_resources(self, search_filter: Dict,
                               filtered_aggregated_resource_info: FilteredAggregatedResourceInfo):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')
