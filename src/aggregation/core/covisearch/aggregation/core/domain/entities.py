from abc import ABC, abstractmethod
from typing import Dict, List
import enum
import urllib.parse


class CovidResourceType(enum.Enum):
    OXYGEN = 1
    PLASMA = 2
    HOSPITAL_BED = 3
    HOSPITAL_BED_ICU = 4
    AMBULANCE = 5
    ECMO = 6
    FOOD = 7
    TESTING = 8
    MEDICINE = 9
    VENTILATOR = 10
    HELPLINE = 11
    BLOOD = 12
    MED_AMPHOTERICIN_B = 13
    MED_CRESEMBA = 14
    MED_TOCILIZUMAB = 15
    MED_OSELTAMIVIR = 16
    MED_AMPHOLYN = 17
    MED_POSACONAZOLE = 18
    MED_FABIFLU = 19
    OXY_CYLINDER = 20
    OXY_CONCENTRATOR = 21
    OXY_REFILL = 22
    OXY_REGULATOR = 23

    @staticmethod
    def to_string(resource_type: 'CovidResourceType') -> str:
        res_type_strings = {
            CovidResourceType.PLASMA: 'plasma',
            CovidResourceType.HOSPITAL_BED_ICU: 'hospital_bed_icu',
            CovidResourceType.HOSPITAL_BED: 'hospital_bed',
            CovidResourceType.OXYGEN: 'oxygen',
            CovidResourceType.AMBULANCE: 'ambulance',
            CovidResourceType.ECMO: 'ecmo',
            CovidResourceType.FOOD: 'food',
            CovidResourceType.TESTING: 'testing',
            CovidResourceType.MEDICINE: 'medicine',
            CovidResourceType.VENTILATOR: 'ventilator',
            CovidResourceType.HELPLINE: 'helpline',
            CovidResourceType.BLOOD: 'blood',
            CovidResourceType.MED_AMPHOTERICIN_B: 'med_amphotericin',
            CovidResourceType.MED_CRESEMBA: 'med_cresemba',
            CovidResourceType.MED_TOCILIZUMAB: 'med_tocilizumab',
            CovidResourceType.MED_OSELTAMIVIR: 'med_oseltamivir',
            CovidResourceType.MED_AMPHOLYN: 'med_ampholyn',
            CovidResourceType.MED_POSACONAZOLE: 'med_posaconazole',
            CovidResourceType.MED_FABIFLU: 'med_fabiflu',
            CovidResourceType.OXY_CONCENTRATOR: 'oxy_concentrator',
            CovidResourceType.OXY_CYLINDER: 'oxy_cylinder',
            CovidResourceType.OXY_REFILL: 'oxy_refill',
            CovidResourceType.OXY_REGULATOR: 'oxy_regulator'
        }
        return res_type_strings[resource_type]

    @staticmethod
    def from_string(resource_type_str: str) -> 'CovidResourceType':
        res_types = {
            'plasma': CovidResourceType.PLASMA,
            'hospital_bed_icu': CovidResourceType.HOSPITAL_BED_ICU,
            'hospital_bed': CovidResourceType.HOSPITAL_BED,
            'oxygen': CovidResourceType.OXYGEN,
            'ambulance': CovidResourceType.AMBULANCE,
            'ecmo': CovidResourceType.ECMO,
            'food': CovidResourceType.FOOD,
            'testing': CovidResourceType.TESTING,
            'medicine': CovidResourceType.MEDICINE,
            'ventilator': CovidResourceType.VENTILATOR,
            'helpline': CovidResourceType.HELPLINE,
            'blood': CovidResourceType.BLOOD,
            'med_amphotericin': CovidResourceType.MED_AMPHOTERICIN_B,
            'med_cresemba': CovidResourceType.MED_CRESEMBA,
            'med_tocilizumab': CovidResourceType.MED_TOCILIZUMAB,
            'med_oseltamivir':	CovidResourceType.MED_OSELTAMIVIR,
            'med_ampholyn': CovidResourceType.MED_AMPHOLYN,
            'med_posaconazole': CovidResourceType.MED_POSACONAZOLE,
            'med_fabiflu': CovidResourceType.MED_FABIFLU,
            'oxy_concentrator': CovidResourceType.OXY_CONCENTRATOR,
            'oxy_regulator': CovidResourceType.OXY_REGULATOR,
            'oxy_refill': CovidResourceType.OXY_REFILL,
            'oxy_cylinder': CovidResourceType.OXY_CYLINDER,
        }
        return res_types[resource_type_str.lower()]


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
    SOURCE_NEEDS_SMART_MATCH = 'needs_smart_match'
    LATITUDE_LABEL = 'lat'
    LONGITUDE_LABEL = 'lng'
    ID_LABEL = 'id'
    # NOTE: KAPIL: For cases like resource type 'Medicine' and subtype 'Amphotericin B'.
    RESOURCE_SUBTYPE_LABEL = 'resource_subtype'

    @classmethod
    def merge_duplicates(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        covisearch_res_by_phone: Dict[str, Dict] = {}
        covisearch_res_without_phone: List[Dict] = []
        phones_label = cls.PHONES_LABEL
        for covisearch_res_info in covisearch_resources:
            phones: List[str] = covisearch_res_info[phones_label]
            if not phones:
                covisearch_res_without_phone.append(covisearch_res_info)

            for phone in phones:
                if phone in covisearch_res_by_phone:
                    old_covisearch_res_for_phone = covisearch_res_by_phone[phone]
                    covisearch_res_by_phone[phone] = \
                        cls._get_more_recently_verified_res_info(
                            covisearch_res_info, covisearch_res_by_phone[phone])

                    newer_resource_info = covisearch_res_by_phone[phone]
                    older_resource_info = old_covisearch_res_for_phone \
                        if newer_resource_info is covisearch_res_info else covisearch_res_info
                    cls._merge_older_with_newer(older_resource_info, newer_resource_info)

                else:
                    covisearch_res_by_phone[phone] = covisearch_res_info

        return cls._merge_entries_with_multiple_phones(covisearch_res_by_phone, covisearch_res_without_phone)

    @classmethod
    def get_resource_subtype_search_name(cls, med_resource_type: CovidResourceType) -> str:
        return ''

    @classmethod
    def _merge_entries_with_multiple_phones(cls, covisearch_res_by_phone, covisearch_res_without_phone) -> List[Dict]:
        duplicates_removed_resources = list(covisearch_res_by_phone.values())
        merged_resources = []

        for resource_info in duplicates_removed_resources:
            if not cls._is_resource_info_in_merged_resources_list(resource_info, merged_resources):
                merged_resources.append(resource_info)

        for resource_info in covisearch_res_without_phone:
            if not cls._is_resource_info_in_merged_resources_list(resource_info, merged_resources):
                merged_resources.append(resource_info)

        return merged_resources

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        cls._merge_field_if_absent(cls.CONTACT_NAME_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.PHONES_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.DETAILS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.ADDRESS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.POST_TIME_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.RESOURCE_SUBTYPE_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.LATITUDE_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.LONGITUDE_LABEL, older_resource_info, newer_resource_info)
        cls._merge_sources_field(older_resource_info, newer_resource_info)

    @classmethod
    def _merge_field_if_absent(cls, field_label: str, older_resource_info: Dict, newer_resource_info: Dict):
        if field_label not in newer_resource_info and field_label not in older_resource_info:
            return

        if newer_resource_info[field_label] is None:
            newer_resource_info[field_label] = older_resource_info[field_label]
        elif type(newer_resource_info[field_label]) is str and newer_resource_info[field_label] == '':
            newer_resource_info[field_label] = older_resource_info[field_label]

    @classmethod
    def _merge_sources_field(cls, older_resource_info: Dict, newer_resource_info: Dict):
        sources_label = cls.SOURCES_LABEL
        for older_resource_info_source in older_resource_info[sources_label]:
            if not cls._is_source_already_present_in_newer_resource_info(
                    older_resource_info_source, newer_resource_info):
                newer_resource_info[sources_label].append(
                    {
                        cls.SOURCE_NAME_LABEL: older_resource_info_source[cls.SOURCE_NAME_LABEL],
                        cls.SOURCE_URL_LABEL: older_resource_info_source[cls.SOURCE_URL_LABEL],
                        cls.SOURCE_NEEDS_SMART_MATCH: older_resource_info_source[cls.SOURCE_NEEDS_SMART_MATCH]
                    }
                )

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
        for resource_info in covisearch_resources:
            resource_info.pop(cls.ID_LABEL)

            for source in resource_info[cls.SOURCES_LABEL]:
                source.pop(cls.SOURCE_NEEDS_SMART_MATCH)

        return covisearch_resources

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
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.BLOOD_GROUP_LABEL, older_resource_info, newer_resource_info)


class BloodInfo(CovidResourceInfo):
    BLOOD_GROUP_LABEL = 'blood_group'

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.BLOOD_GROUP_LABEL, older_resource_info, newer_resource_info)


class OxygenInfo(CovidResourceInfo):
    LITRES_LABEL = 'litres'

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.LITRES_LABEL, older_resource_info, newer_resource_info)

    @classmethod
    def get_resource_subtype_search_name(cls, med_resource_type: CovidResourceType) -> str:
        med_type_vs_name = {
            CovidResourceType.OXY_CYLINDER: 'cylinder',
            CovidResourceType.OXY_REFILL: 'refill',
            CovidResourceType.OXY_REGULATOR: 'regulator',
            CovidResourceType.OXY_CONCENTRATOR: 'concentrator'
        }
        return med_type_vs_name.get(med_resource_type, '')


class HospitalBedsInfo(CovidResourceInfo):
    AVAILABLE_COVID_BEDS_LABEL = 'available_covid_beds'
    AVAILABLE_NO_OXYGEN_BEDS_LABEL = 'available_no_oxygen_beds'
    AVAILABLE_OXYGEN_BEDS_LABEL = 'available_oxygen_beds'
    TOTAL_AVAILABLE_BEDS_LABEL = 'total_available_beds'
    HOSPITAL_TYPE_LABEL = 'hospital_type'

    TOTAL_BEDS_WEIGHTAGE_THRESHOLD = 10

    @classmethod
    def fill_remaining_bed_fields(cls, resource_info: Dict):
        available_beds_label = cls.AVAILABLE_COVID_BEDS_LABEL
        no_oxygen_beds_label = cls.AVAILABLE_NO_OXYGEN_BEDS_LABEL
        oxygen_beds_label = cls.AVAILABLE_OXYGEN_BEDS_LABEL
        total_beds_label = cls.TOTAL_AVAILABLE_BEDS_LABEL

        if total_beds_label not in resource_info:
            resource_info[total_beds_label] = None

        if resource_info[available_beds_label] is None and \
                resource_info[oxygen_beds_label] is None and \
                resource_info[no_oxygen_beds_label] is None:
            return

        cls._fill_missing_field_if_others_are_present(
            available_beds_label, oxygen_beds_label, no_oxygen_beds_label, resource_info)

        cls._fill_missing_field_if_others_are_present(
            oxygen_beds_label, available_beds_label, no_oxygen_beds_label, resource_info)

        cls._fill_missing_field_if_others_are_present(
            no_oxygen_beds_label, available_beds_label, oxygen_beds_label, resource_info)

        cls._fill_total_field_if_missing(resource_info)

    @classmethod
    def _fill_missing_field_if_others_are_present(
            cls, missing_field_label, other_field_1_label, other_field_2_label, resource_info):

        total_beds_label = cls.TOTAL_AVAILABLE_BEDS_LABEL

        if resource_info[missing_field_label] is None and \
                resource_info[other_field_2_label] is not None and \
                resource_info[other_field_1_label] is not None and \
                resource_info[total_beds_label] is not None:

            resource_info[missing_field_label] = \
                resource_info[total_beds_label] - resource_info[other_field_1_label] - \
                resource_info[other_field_2_label]

    @classmethod
    def _fill_total_field_if_missing(cls, resource_info):
        if resource_info[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            total_available_beds = 0

            if resource_info[cls.AVAILABLE_COVID_BEDS_LABEL] is not None:
                total_available_beds = total_available_beds + resource_info[cls.AVAILABLE_COVID_BEDS_LABEL]

            if resource_info[cls.AVAILABLE_OXYGEN_BEDS_LABEL] is not None:
                total_available_beds = total_available_beds + resource_info[cls.AVAILABLE_OXYGEN_BEDS_LABEL]

            if resource_info[cls.AVAILABLE_NO_OXYGEN_BEDS_LABEL] is not None:
                total_available_beds = total_available_beds + resource_info[cls.AVAILABLE_NO_OXYGEN_BEDS_LABEL]

            resource_info[cls.TOTAL_AVAILABLE_BEDS_LABEL] = total_available_beds

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

    @classmethod
    def fill_remaining_bed_fields(cls, resource_info: Dict):
        no_ventilator_beds_label = cls.AVAILABLE_NO_VENTILATOR_BEDS_LABEL
        ventilator_beds_label = cls.AVAILABLE_VENTILATOR_BEDS_LABEL

        if resource_info[ventilator_beds_label] is None and \
                resource_info[no_ventilator_beds_label] is None:
            return

        cls._fill_missing_field_if_others_are_present(
            no_ventilator_beds_label, ventilator_beds_label, resource_info)

        cls._fill_missing_field_if_others_are_present(
            ventilator_beds_label, no_ventilator_beds_label, resource_info)

        cls._fill_total_field_if_missing(resource_info)

    @classmethod
    def _fill_missing_field_if_others_are_present(
            cls, missing_field_label, other_field_label, resource_info):

        total_beds_label = cls.TOTAL_AVAILABLE_BEDS_LABEL

        if resource_info[missing_field_label] is None and \
                resource_info[other_field_label] is not None and \
                resource_info[total_beds_label] is not None:

            resource_info[missing_field_label] = \
                resource_info[total_beds_label] - resource_info[other_field_label]

    @classmethod
    def _fill_total_field_if_missing(cls, resource_info):
        if resource_info[cls.TOTAL_AVAILABLE_BEDS_LABEL] is None:
            total_available_beds = 0

            if resource_info[cls.AVAILABLE_NO_VENTILATOR_BEDS_LABEL] is not None:
                total_available_beds = total_available_beds + resource_info[cls.AVAILABLE_NO_VENTILATOR_BEDS_LABEL]

            if resource_info[cls.AVAILABLE_VENTILATOR_BEDS_LABEL] is not None:
                total_available_beds = total_available_beds + resource_info[cls.AVAILABLE_VENTILATOR_BEDS_LABEL]

            resource_info[cls.TOTAL_AVAILABLE_BEDS_LABEL] = total_available_beds

    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_NO_VENTILATOR_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_VENTILATOR_BEDS_LABEL,
                                   older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.TOTAL_AVAILABLE_BEDS_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.HOSPITAL_TYPE_LABEL, older_resource_info, newer_resource_info)
        cls._merge_field_if_absent(cls.AVAILABLE_VENTILATORS_LABEL, older_resource_info, newer_resource_info)


class AmbulanceInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class EcmoInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class FoodInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class TestingInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class MedicineInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)

    @classmethod
    def get_resource_subtype_search_name(cls, med_resource_type: CovidResourceType) -> str:
        med_type_vs_name = {
            CovidResourceType.MED_POSACONAZOLE: 'posaconazole',
            CovidResourceType.MED_AMPHOLYN: 'ampholyn',
            CovidResourceType.MED_AMPHOTERICIN_B: 'amphotericin b',
            CovidResourceType.MED_CRESEMBA: 'cresemba',
            CovidResourceType.MED_OSELTAMIVIR: 'oseltamivir',
            CovidResourceType.MED_TOCILIZUMAB: 'tocilizumab',
            CovidResourceType.MED_FABIFLU: 'fabiflu'
        }
        return med_type_vs_name.get(med_resource_type, '')


class VentilatorInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


class HelplineInfo(CovidResourceInfo):
    @classmethod
    def _merge_older_with_newer(cls, older_resource_info: Dict, newer_resource_info: Dict):
        super()._merge_older_with_newer(older_resource_info, newer_resource_info)


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
        CovidResourceType.MED_POSACONAZOLE: MedicineInfo,
        CovidResourceType.MED_FABIFLU: MedicineInfo,
        CovidResourceType.OXY_CYLINDER: OxygenInfo,
        CovidResourceType.OXY_REFILL: OxygenInfo,
        CovidResourceType.OXY_REGULATOR: OxygenInfo,
        CovidResourceType.OXY_CONCENTRATOR: OxygenInfo
    }
    return res_type_classes[resource_type]


class SearchFilter:
    CITY_LABEL = 'city'
    RESOURCE_TYPE_LABEL = 'resource_type'
    BLOOD_GROUP_LABEL = 'blood_group'

    def __init__(self, city: str, resource_type: CovidResourceType, blood_group: BloodGroup):
        self._city: str = city.lower()
        self._resource_type: CovidResourceType = resource_type
        self._blood_group: BloodGroup = blood_group
        self._validate()

    @property
    def city(self) -> str:
        return self._city

    @property
    def resource_type(self) -> CovidResourceType:
        return self._resource_type

    @property
    def blood_group(self) -> BloodGroup:
        return self._blood_group

    def to_url_query_string_fmt(self) -> str:
        query_string = \
            self.CITY_LABEL + '=' + urllib.parse.quote(self._city) + '&' + \
            self.RESOURCE_TYPE_LABEL + '=' + \
            urllib.parse.quote(CovidResourceType.to_string(self._resource_type))
        if self._blood_group is not None and self._blood_group is not '':
            query_string = query_string + '&' + self.BLOOD_GROUP_LABEL + '=' + \
                           urllib.parse.quote(BloodGroup.to_string(self._blood_group))
        return query_string

    def _validate(self):
        if self._city is None or self._city is '':
            raise ValueError('city param must have non-empty value')
        if self._resource_type is None or self._resource_type is '':
            raise ValueError('resource_type param must have non-empty value')

    @classmethod
    def create_from_url_query_string_fmt(cls, search_filter: str) -> 'SearchFilter':
        query_params = \
            urllib.parse.parse_qs(search_filter, keep_blank_values=True, strict_parsing=True)

        if cls.CITY_LABEL not in query_params:
            raise ValueError('city param is mandatory')
        city = query_params[cls.CITY_LABEL][0]

        if cls.RESOURCE_TYPE_LABEL not in query_params:
            raise ValueError('resource_type param is mandatory')
        resource_type = CovidResourceType.from_string(query_params[cls.RESOURCE_TYPE_LABEL][0])

        if cls.BLOOD_GROUP_LABEL in query_params:
            blood_group = BloodGroup.from_string(query_params[cls.BLOOD_GROUP_LABEL][0])
        else:
            blood_group = None

        return SearchFilter(city, resource_type, blood_group)


class FilteredAggregatedResourceInfo:
    def __init__(self, search_filter: SearchFilter, res_info_data: List[Dict]):
        super().__init__()
        self.search_filter = search_filter
        self.data = res_info_data


class AggregatedResourceInfoRepo(ABC):
    @abstractmethod
    def set_resources_for_filter(self,
                                 filtered_aggregated_resource_info: FilteredAggregatedResourceInfo):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')

    @abstractmethod
    def remove_resources_for_filter(self, search_filter: SearchFilter):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')
