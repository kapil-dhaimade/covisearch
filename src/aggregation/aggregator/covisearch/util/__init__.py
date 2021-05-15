from datetime import datetime

import covisearch.util.types as types


def elapsed_days(date: datetime) -> int:
    curr = datetime.now()
    diff = date - curr
    return diff.days


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


class PY3CMP:

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0
