from abc import ABC, abstractmethod
import enum
import datetime
import covisearch.aggregation.aggregator.infra.util as util


class Address(util.Serializable):
    def __init__(self, address1: str, city: str, state: str, pin_code: int):
        self.address1 = address1
        self.city = city
        self.state = state
        self.pin_code = pin_code


class VerificationInfo:
    def __init__(self,
                 last_verified: datetime,
                 description: str):
        self.last_verified = last_verified
        self.description = description


class ResourceInfo(util.Serializable, util.PY3CMP):
    def __init__(self,
                 contact_name: str,
                 address: Address,
                 description: str,
                 phone_no: str,
                 verification_info: VerificationInfo,
                 post_time: datetime):
        self.contact_name = contact_name
        self.address = address
        self.description = description
        self.phone_no = phone_no
        # verification_info None means not verified
        self.verification_info = verification_info
        self.post_time = post_time

    def __eq__(self, other):
        # No need to check resource type as isinstance will do the needful check
        if isinstance(other, self.__class__):
            return self.phone_no == other.phone_no
        return False

    def __cmp__(self, other):
        if self == other:
            return 0
        return self.rank() > other.rank()

    def rank(self) -> int:
        rank = 0
        if self.verification_info is not None:
            verified_ago = util.elapsed_days(self.verification_info.last_verified)
            if verified_ago < 5:
                rank += 5 - verified_ago
        if self.post_time:
            posted_ago = util.elapsed_days(self.post_time)
            if posted_ago < 1:
                rank += 1 - posted_ago
        return rank


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


class PlasmaInfo(ResourceInfo):

    def __init__(self,
                 contact_name: str,
                 address: Address,
                 description: str,
                 phone_no: str,
                 verification_info: VerificationInfo,
                 post_time: datetime,
                 blood_group: BloodGroup):
        super().__init__(contact_name,
                         address,
                         description,
                         phone_no,
                         verification_info,
                         post_time)
        self.blood_group = blood_group


class OxygenInfo(ResourceInfo):

    def __init__(self,
                 contact_name: str,
                 address: Address,
                 description: str,
                 phone_no: str,
                 verification_info: VerificationInfo,
                 post_time: datetime,
                 litres: int):
        super().__init__(contact_name,
                         address,
                         description,
                         phone_no,
                         verification_info,
                         post_time)
        self.litres = litres

    def rank(self) -> int:
        rank = super().rank()
        rank += self.litres
        return rank


class HospitalBedsInfo(ResourceInfo):

    def __init__(self,
                 contact_name: str,
                 address: Address,
                 description: str,
                 phone_no: str,
                 verification_info: VerificationInfo,
                 post_time: datetime,
                 beds: int):
        super().__init__(contact_name,
                         address,
                         description,
                         phone_no,
                         verification_info,
                         post_time)
        self.beds = beds

    def rank(self) -> int:
        rank = super().rank()
        rank += self.beds
        return rank


class FilteredAggregatedResourceInfo(util.Serializable):
    def __init__(self, search_filter: dict, curr_end_page: int, data: list[ResourceInfo]):
        self.search_filter = search_filter
        self.curr_end_page = curr_end_page
        self.data = data


class AggregatedResourceInfoRepo(ABC):
    @abstractmethod
    def get_filtered_resources(self, search_filter: dict) -> FilteredAggregatedResourceInfo:
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')

    @abstractmethod
    def set_filtered_resources(self, search_filter: dict,
                               filtered_aggregated_resource_info: FilteredAggregatedResourceInfo):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')
