from enum import Enum
from typing import List, Dict, Tuple

from covisearch.util.types import *
import covisearch.aggregation.aggregator.domain.entities as entities
from covisearch.aggregation.aggregator.domain.entities import CovidResourceInfo, CovidResourceType


# NOTE: KAPIL: Python Dict convertible to JSON provided data types are
# serializable. None gets converted to null in JSON. Dict has objects
# like datetime, etc. as values, but JSON needs it to be serializable.


# Classes related to Covid resource websites and resource mapping
class WebSourceType(Enum):
    PAN_INDIA = 1,
    CITY_SPECIFIC = 2,
    RESOURCE_SPECIFIC = 3


class WebSource:
    def __init__(self, url: URL, source_type: WebSourceType,
                 response_content_type: ContentType,
                 data_table_extract_selectors: List[Tuple[str, str]],
                 res_mapping_desc: List[Tuple[str, str]]):
        self._url: URL = url
        self._source_type: WebSourceType = source_type
        self._response_content_type: ContentType = response_content_type
        self._data_table_extract_selectors: List[Tuple[str, str]] = \
            data_table_extract_selectors
        self._res_mapping_desc: List[Tuple[str, str]] = res_mapping_desc


# maps covid resource from third-party source format to Covisearch format
def map_to_covisearch(web_src_res_info: Dict, res_type: CovidResourceType,
                      res_mapping_desc: List[Tuple[str, str]]) -> CovidResourceInfo:
    _map_res_to_covisearch_res = {
        entities.CovidResourceType.PLASMA: _map_plasma,
        entities.CovidResourceType.OXYGEN: _map_oxygen,
        entities.CovidResourceType.HOSPITAL_BED: _map_hospital_bed,
        entities.CovidResourceType.HOSPITAL_BED_ICU: _map_hospital_bed_icu,
    }
    covisearch_res: Dict = {}
    _map_common_res_info(web_src_res_info, res_mapping_desc, covisearch_res)
    _map_res_to_covisearch_res[res_type](web_src_res_info, res_mapping_desc, covisearch_res)
    return None


def _map_plasma(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                covisearch_res: Dict):
    pass


def _map_oxygen(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                covisearch_res: Dict):
    pass


def _map_hospital_bed(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                      covisearch_res: Dict):
    pass


def _map_hospital_bed_icu(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                          covisearch_res: Dict):
    pass


def _map_common_res_info(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                         covisearch_res: Dict):
    for field_mapping in res_mapping_desc:
        pass


# NOTE: KAPIL: Desc format:
# -Tuple['covisearch_res_field_name',
#       'optional remove_chars(chars) split_on(delim) datetimeconvert(ago/none) web_src_field_name']
# Eg: Mandatory field, remove '+' and 'space' chars, split multiple numbers on '\n'
#       -('phone_no', 'remove_chars(+\ ) split_on(\n) mobile-nos')
# Eg: Optional last verified, web src res format is 'hours/days ago', convert to UTC
#       -('last_verified_utc', 'optional datetimeconvert(ago) lastVerified')
# TODO: KAPIL: Implement remove_chars(), split_on() later.
class ResMappingDesc:
    def __init__(self, res_mapping_desc: List[Tuple[str, str]]):
        pass

    def _split_mapping_desc_csv(self, desc: str) -> List[str]:
        pass
# verified/updated time, phone number separation, mandatory, remove chars
# ----Covid Resource Web Source - ENDS ----
