from abc import ABC, abstractmethod
import enum


class Serializable:
    version=1

    @staticmethod
    def to_object(self, data_dict: dict):
        self.version = data_dict["version"]

    def to_data(self) -> dict:
        return {"version":self.version}


class Address:
    address1: str
    city: str
    state: str
    pin_code: int


class ResourceInfo(Serializable):
    name: str
    resource_name: str
    address: Address


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
    resource_name = "Plasma"
    blood_group: BloodGroup


class OxygenInfo(ResourceInfo):
    resource_name = "Oxygen"
    litres: int


class HospitalBedsInfo(ResourceInfo):
    resource_name = "HospitalBeds"
    beds: int


class FilteredAggregatedResourceInfo(Serializable):
    filter: dict
    curr_end_page: int
    data: list[ResourceInfo]

    def __init__(self, data_dict: dict):
        self.filter = data_dict["filter"]
        self.curr_end_page = data_dict["curr_end_page"]
        self.data = []
        for data in data_dict["data"]:
            data[]
            if(data)
            self.data.append()

    def to_data(self) -> dict:
        raise NotImplementedError('Serializable is an interface')


class AggregatedResourceInfoRepo(ABC):
    @abstractmethod
    def get_filtered_resources(self, search_filter: dict) -> FilteredAggregatedResourceInfo:
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')

    @abstractmethod
    def set_filtered_resources(self, search_filter: dict,
                               filtered_aggregated_resource_info: FilteredAggregatedResourceInfo):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')
