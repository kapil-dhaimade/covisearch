from typing import Dict

import google.cloud.firestore as firestore

import covisearch.aggregation.core.domain.entities as entities
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.util.mytypes as types
import covisearch.util.geoutil as geoutil


class AggregatedResourceInfoRepoImpl(entities.AggregatedResourceInfoRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    # # NOTE: KAPIL: Uncommenting as implemented in covisearchapi project.
    # def get_resources_for_filter(self, search_filter: entities.SearchFilter) -> \
    #         entities.FilteredAggregatedResourceInfo:
    #
    #     res_info_filter_id = search_filter.to_url_query_string_fmt()
    #     res_info_doc = self._db.collection('filtered_aggregated_resource_info').\
    #         document(res_info_filter_id).get()
    #
    #     if not res_info_doc.exists:
    #         return None
    #
    #     return entities.FilteredAggregatedResourceInfo(
    #         search_filter, res_info_doc.get('resource_info_data'))

    def set_resources_for_filter(
            self, filtered_aggregated_resource_info: entities.FilteredAggregatedResourceInfo):

        res_info_filter_id = filtered_aggregated_resource_info.\
            search_filter.to_url_query_string_fmt()
        self._db.collection('filtered_aggregated_resource_info').\
            document(res_info_filter_id).set(
            {'resource_info_data': filtered_aggregated_resource_info.data})

    def remove_resources_for_filter(self, search_filter: entities.SearchFilter):
        self._db.collection('filtered_aggregated_resource_info').\
            document(search_filter.to_url_query_string_fmt()).delete()


class WebSourceRepoImpl(resourcemapping.WebSourceRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    def get_web_sources_for_filter(self, search_filter: entities.SearchFilter) -> \
            Dict[str, resourcemapping.WebSource]:
        web_src_doc_collection = self._db.collection('web_sources').stream()
        web_src_dicts = [x.to_dict() for x in web_src_doc_collection]
        web_srcs_for_filter = [_firestore_to_web_src(x, search_filter)
                               for x in web_src_dicts if _web_src_scope_matches_filter(x, search_filter)]
        return {web_src.web_resource_url: web_src
                for web_src in web_srcs_for_filter if web_src is not None}


# Eg: location_scope=maharashtra AND resource_type_label_mapping has oxygen,plasma,ambulance
# Eg: location_scope=pan_india AND resource_type_label_mapping has
#     oxygen,hospital_bed,hospital_bed_icu,ambulance,plasma
# Eg: location_scope=delhi,maharashtra,andhra pradesh AND resource_type_label_mapping has hospital_bed
def _web_src_scope_matches_filter(web_src_dict: Dict,
                                  search_filter: entities.SearchFilter) -> bool:
    location_scope: str = web_src_dict['location_scope']
    location_match = False
    if location_scope == 'pan_india':
        location_match = True
    else:
        supported_locations = location_scope.split(',')
        supported_locations = [x.lower() for x in supported_locations]
        if search_filter.city in supported_locations:
            location_match = True
        else:
            possible_states_for_city_filter = geoutil.get_states_for_city(search_filter.city)
            if set(possible_states_for_city_filter).intersection(supported_locations):
                location_match = True

    resource_type_label_mapping_dict: Dict[str, str] = web_src_dict['resource_type_label_mapping']
    resource_type_str = entities.CovidResourceType.to_string(search_filter.resource_type)
    resource_type_match = True if resource_type_str in resource_type_label_mapping_dict else False

    return location_match and resource_type_match


def _firestore_to_web_src(
        web_src_dict: Dict,
        search_filter: entities.SearchFilter) -> resourcemapping.WebSource:

    try:
        request_content_type = _content_type_from_string(web_src_dict['request_content_type']) \
            if 'request_content_type' in web_src_dict else None

        request_body_template = web_src_dict['request_body_template'] \
            if 'request_body_template' in web_src_dict else None

        city_name_case_mapping = _letter_case_from_string(web_src_dict['city_name_case_mapping']) \
            if 'city_name_case_mapping' in web_src_dict else None

        card_source_url_template = web_src_dict['card_source_url_template'] \
            if 'card_source_url_template' in web_src_dict else None

        data_table_filter_templates = web_src_dict['data_table_filter_templates'] \
            if 'data_table_filter_templates' in web_src_dict else None

        return resourcemapping.WebSource(
            web_src_dict['name'], web_src_dict['homepage_url'],
            web_src_dict['web_resource_url_template'],
            card_source_url_template,
            request_content_type, request_body_template,
            _content_type_from_string(web_src_dict['response_content_type']),
            web_src_dict['data_table_extract_selectors'],
            data_table_filter_templates,
            _get_resource_mapping_desc_model(web_src_dict['resource_mapping_desc']),
            web_src_dict['resource_type_label_mapping'],
            city_name_case_mapping, search_filter)

    except resourcemapping.NoResourceTypeMappingError:
        return None


def _get_resource_mapping_desc_model(resource_mapping_desc_dict: Dict[str, str]) -> \
        Dict[str, resourcemapping.FieldMappingDesc]:

    return {
        field_mapping_tuple[0]: resourcemapping.FieldMappingDesc(field_mapping_tuple)
        for field_mapping_tuple in resource_mapping_desc_dict.items()
    }


def _content_type_from_string(content_type_str: str) -> types.ContentType:
    content_type_str_mapping = {
        'json': types.ContentType.JSON,
        'html': types.ContentType.HTML,
        'formdata': types.ContentType.FORMDATA
    }
    return content_type_str_mapping[content_type_str]


def _letter_case_from_string(letter_case_str: str) -> types.LetterCaseType:
    letter_case_str_mapping = {
        'lowercase': types.LetterCaseType.LOWERCASE,
        'uppercase': types.LetterCaseType.UPPERCASE,
        'titlecase': types.LetterCaseType.TITLECASE
    }
    return letter_case_str_mapping[letter_case_str]
