from abc import ABC, abstractmethod
import enum


class Serializable:
    curr_version = 1
    k_nested_objects = "nested_objects"
    k_class_name = "class_name"
    k_data = "data"
    k_variable = "variable"

    def __init__(self):
        self.version = self.__class__.curr_version

    @classmethod
    def to_object(cls, data_dict: dict):
        self = cls.__new__(cls)
        if Serializable.k_nested_objects in data_dict:
            nested_objects = data_dict[Serializable.k_nested_objects]
            for nested_object in nested_objects:
                nested_cls = globals()[nested_object[Serializable.k_class_name]]
                nested_obj = nested_cls.to_object(nested_object[Serializable.k_data])
                data_dict[nested_object[Serializable.k_variable]] = nested_obj
            data_dict.pop(Serializable.k_nested_objects)
        self.__dict__.update(data_dict)
        return self

    def to_data(self) -> dict:
        d = self.__dict__.copy()
        for k, v in self.__dict__.items():
            if isinstance(v, Serializable):
                d.pop(k)
                nested_object = {Serializable.k_variable: k,
                                 Serializable.k_data: v.to_data(),
                                 Serializable.k_class_name: v.__class__.__name__}
                if Serializable.k_nested_objects in d:
                    d[Serializable.k_nested_objects].append(nested_object)
                else:
                    d[Serializable.k_nested_objects] = [nested_object]
        return d


class Address(Serializable):
    def __init__(self, address1: str, city: str, state: str, pin_code: int):
        self.address1 = address1
        self.city = city
        self.state = state
        self.pin_code = pin_code


class ResourceInfo(Serializable):
    def __init__(self, name: str, resource_name: str, address: Address):
        self.name = name
        self.resource_name = resource_name
        self.address = address


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

    def __init__(self, blood_group: BloodGroup):
        self.blood_group = blood_group


class OxygenInfo(ResourceInfo):
    resource_name = "Oxygen"

    def __init__(self, litres: int):
        self.litres = litres


class HospitalBedsInfo(ResourceInfo):
    resource_name = "HospitalBeds"

    def __init__(self, beds: int):
        self.beds = beds


class FilteredAggregatedResourceInfo(Serializable):
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
