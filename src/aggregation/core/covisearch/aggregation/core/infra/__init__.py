from typing import Dict

import google.cloud.firestore as firestore

import covisearch.aggregation.core.domain.entities as entities
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.util.types as types
import covisearch.util.geoutil as geoutil


class AggregatedResourceInfoRepoImpl(entities.AggregatedResourceInfoRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    # # NOTE: KAPIL: Uncommenting as implemented in covisearchapi project.
    # def get_resources_for_filter(self, search_filter: entities.SearchFilter) -> \
    #         entities.FilteredAggregatedResourceInfo:
    #
    #     res_info_filter_id = search_filter.to_url_query_string_fmt()
    #     res_info_doc = self._db.collection('filtered-aggregated-resource-info').\
    #         document(res_info_filter_id).get()
    #
    #     if not res_info_doc.exists:
    #         return None
    #
    #     return entities.FilteredAggregatedResourceInfo(
    #         search_filter, res_info_doc.get('res-info-data'))

    def set_resources_for_filter(
            self, filtered_aggregated_resource_info: entities.FilteredAggregatedResourceInfo):

        res_info_filter_id = filtered_aggregated_resource_info.\
            search_filter.to_url_query_string_fmt()
        self._db.collection('filtered-aggregated-resource-info').\
            document(res_info_filter_id).set(
            {'resource-info-data': filtered_aggregated_resource_info.data})


class WebSourceRepoImpl(resourcemapping.WebSourceRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    def get_web_sources_for_filter(self, search_filter: entities.SearchFilter) -> \
            Dict[str, resourcemapping.WebSource]:
        web_src_doc_collection = self._db.collection('web-sources').where(
            'scope', 'in', _possible_web_src_scopes_for_filter(search_filter)).stream()
        web_srcs_for_filter = [_firestore_to_web_src(x, search_filter)
                               for x in web_src_doc_collection]
        return {web_src.web_resource_url: web_src for web_src in web_srcs_for_filter}


# NOTE: KAPIL: Take care of state-wide sources and subset of resources later. Eg: mumbai-oxygen-plasma
# Eg. values: pan-india-all-resources, maharashtra-plasma, bengaluru-hospital-bed,
def _possible_web_src_scopes_for_filter(search_filter: entities.SearchFilter):
    res_type_string = entities.CovidResourceType.to_string(search_filter.resource_type)
    possible_web_scopes = [
        'pan-india-all-resources', 'pan-india-' + res_type_string,
        search_filter.city + '-all-resources',
        search_filter.city + '-' + res_type_string,
    ]
    possible_states_for_city = geoutil.get_state_for_city(search_filter.city)
    for state in possible_states_for_city:
        possible_web_scopes.extend(
            [
                state + '-all-resources', state + '-' + res_type_string
            ])
    return possible_web_scopes


def _firestore_to_web_src(
        web_src_doc: firestore.DocumentSnapshot,
        search_filter: entities.SearchFilter) -> resourcemapping.WebSource:

    web_src_dict = web_src_doc.to_dict()
    return resourcemapping.WebSource(
        web_src_dict['name'], web_src_dict['homepage-url'],
        web_src_dict['web-resource-url-template'],
        _response_content_type_from_string(web_src_dict['response-content-type']),
        web_src_dict['data-table-extract-selectors'],
        _get_resource_mapping_desc_model(web_src_dict['resource-mapping-desc']),
        web_src_dict['resource-type-label-mapping'],
        search_filter)


def _get_resource_mapping_desc_model(resource_mapping_desc_dict: Dict[str, str]) -> \
        Dict[str, resourcemapping.FieldMappingDesc]:

    return {
        field_mapping_tuple[0]: resourcemapping.FieldMappingDesc(field_mapping_tuple)
        for field_mapping_tuple in resource_mapping_desc_dict.items()
    }


def _response_content_type_from_string(response_content_type_str: str) -> types.ContentType:
    res_content_type_str_mapping = {
        'json': types.ContentType.JSON,
        'html': types.ContentType.HTML
    }
    return res_content_type_str_mapping[response_content_type_str]
